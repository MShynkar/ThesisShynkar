"""Point 2: n=10 sequential end-to-end latency with per-stage breakdown.

This harness reproduces RagService.search step by step at the service layer so
it can time each stage separately (query embedding, hybrid retrieval, LLM
generation) without modifying application code. Parameters match the request the
task specifies: top_k=5, threshold=0.4, hybrid=True, generate_answer=True, the
same query repeated, role=admin. Two warm-up runs precede the measured ones and
are discarded.

Note on scope: timings are measured at the service layer (the exact functions the
API calls), so they exclude the HTTP/JSON and JWT overhead, which is negligible
relative to LLM generation. The search-history insert is performed (as in
production) but excluded from the per-stage table; it is included in end-to-end.
"""
import asyncio
import json
import statistics
import time

import _common  # noqa: F401
from sqlalchemy import select

from app.core.permissions import Role, allowed_levels_for_role
from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.repositories.audit_repo import SearchHistoryRepository
from app.repositories.document_repo import ChunkRepository
from app.schemas.search import Source
from app.services.ollama_client import OllamaClient
from app.services.rag_service import SYSTEM_PROMPT, _build_prompt

QUERY = "What is the company's data retention policy?"
N = 10
WARMUP = 2
TOP_K = 5
THRESHOLD = 0.4


async def one_run(record: bool) -> dict:
    """Execute the full pipeline once, timing each stage. Returns timings in ms."""
    ollama = OllamaClient()
    async with AsyncSessionLocal() as session:
        admin = (
            await session.execute(select(User).where(User.role == Role.ADMIN.value))
        ).scalars().first()
        allowed = allowed_levels_for_role(admin.role)
        chunks = ChunkRepository(session)

        t_e2e = time.perf_counter()

        t = time.perf_counter()
        embedding = await ollama.embed(QUERY)
        embed_ms = (time.perf_counter() - t) * 1000

        t = time.perf_counter()
        rows = await chunks.hybrid_search(
            query_text=QUERY,
            query_embedding=embedding,
            allowed_levels=allowed,
            top_k=TOP_K,
            threshold=THRESHOLD,
        )
        search_ms = (time.perf_counter() - t) * 1000

        sources = [
            Source(
                chunk_id=r["chunk_id"], document_id=r["document_id"],
                document_title=r["document_title"], chunk_index=r["chunk_index"],
                content=r["content"], similarity=float(r["similarity"]),
            )
            for r in rows
        ]

        t = time.perf_counter()
        answer = None
        if sources:
            prompt = _build_prompt(QUERY, sources)
            answer = await ollama.generate(prompt, system=SYSTEM_PROMPT, temperature=0.2)
        gen_ms = (time.perf_counter() - t) * 1000

        # history persist (as in production); part of e2e, excluded from stage table
        if record:
            try:
                await SearchHistoryRepository(session).add(
                    user_id=admin.id, query=QUERY, answer=answer,
                    sources=[s.model_dump(mode="json") for s in sources],
                )
            except Exception:
                pass

        e2e_ms = (time.perf_counter() - t_e2e) * 1000

    return {
        "embed_ms": round(embed_ms, 1),
        "search_ms": round(search_ms, 1),
        "gen_ms": round(gen_ms, 1),
        "e2e_ms": round(e2e_ms, 1),
        "n_sources": len(sources),
        "answer_chars": len(answer or ""),
    }


def agg(values: list[float]) -> dict:
    return {
        "mean": round(statistics.mean(values), 1),
        "median": round(statistics.median(values), 1),
        "min": round(min(values), 1),
        "max": round(max(values), 1),
        "stdev": round(statistics.pstdev(values), 1) if len(values) > 1 else 0.0,
    }


async def main() -> None:
    print(f"Query: {QUERY!r}")
    print(f"Warmup x{WARMUP} (discarded) ...")
    for _ in range(WARMUP):
        await one_run(record=False)

    runs = []
    print(f"\nMeasured runs x{N}:")
    print(f"{'#':>2} {'embed':>9} {'search':>9} {'LLM gen':>11} {'e2e':>11} {'src':>4} {'ans_ch':>7}")
    for i in range(1, N + 1):
        r = await one_run(record=True)
        runs.append(r)
        print(f"{i:>2} {r['embed_ms']:>8.1f} {r['search_ms']:>8.1f} "
              f"{r['gen_ms']:>10.1f} {r['e2e_ms']:>10.1f} {r['n_sources']:>4} {r['answer_chars']:>7}")

    aggs = {
        "Query embedding": agg([r["embed_ms"] for r in runs]),
        "Hybrid retrieval": agg([r["search_ms"] for r in runs]),
        "LLM generation": agg([r["gen_ms"] for r in runs]),
        "End-to-end": agg([r["e2e_ms"] for r in runs]),
    }
    print("\nAggregates (ms):")
    print(f"{'Stage':<18}{'mean':>10}{'median':>10}{'min':>10}{'max':>10}{'stdev':>10}")
    for k, a in aggs.items():
        print(f"{k:<18}{a['mean']:>10}{a['median']:>10}{a['min']:>10}{a['max']:>10}{a['stdev']:>10}")

    out = {"query": QUERY, "n": N, "top_k": TOP_K, "threshold": THRESHOLD,
           "runs": runs, "aggregates": aggs}
    with open("../scripts/dipl_measurements/results/latency_sequential.json", "w") as f:
        json.dump(out, f, indent=2)
    print("\nSaved -> results/latency_sequential.json")


if __name__ == "__main__":
    asyncio.run(main())
