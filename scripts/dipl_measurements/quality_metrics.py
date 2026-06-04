"""Point 5: retrieval quality — Precision@5 and MRR over 15 annotated queries.

For each query we run the SAME hybrid_search the app uses, with top_k=5 and the
role-appropriate access levels, then score against a hand-annotated set of
relevant documents (referenced by title, resolved to ids at runtime).

Definitions (document-level relevance, chunk-level ranking):
  * a top-5 position counts as a hit if its chunk belongs to a relevant document;
  * Precision@5 = (# of the 5 positions that are hits) / 5;
  * RR = 1 / rank of the first hit (0 if none in top-5);
  * MRR = mean RR over all queries; Mean P@5 = mean Precision@5.

threshold is set to 0.0 so the top-5 ranking is always evaluated in full
(otherwise low-scoring relevant chunks would be hidden and the metric would
measure the threshold, not the ranker).
"""
import asyncio
import json
import statistics

import _common  # noqa: F401
from sqlalchemy import select

from app.core.permissions import allowed_levels_for_role
from app.db.session import AsyncSessionLocal
from app.models.document import Document
from app.repositories.document_repo import ChunkRepository
from app.services.ollama_client import OllamaClient

TOP_K = 5
THRESHOLD = 0.0


async def title_to_id(session) -> dict[str, str]:
    rows = (await session.execute(select(Document.title, Document.id))).all()
    return {t: str(i) for t, i in rows}


async def main() -> None:
    with open("../scripts/dipl_measurements/test_queries.json", encoding="utf-8") as f:
        queries = json.load(f)

    ollama = OllamaClient()
    results = []

    async with AsyncSessionLocal() as session:
        t2id = await title_to_id(session)
        chunks = ChunkRepository(session)

        for q in queries:
            relevant_ids = set()
            missing = []
            for title in q["relevant_titles"]:
                if title in t2id:
                    relevant_ids.add(t2id[title])
                else:
                    missing.append(title)
            if missing:
                print(f"  WARNING: titles not found in DB: {missing}")

            allowed = allowed_levels_for_role(q["role"])
            emb = await ollama.embed(q["query"])
            rows = await chunks.hybrid_search(
                query_text=q["query"], query_embedding=emb,
                allowed_levels=allowed, top_k=TOP_K, threshold=THRESHOLD,
            )

            top_doc_ids = [str(r["document_id"]) for r in rows]
            top_titles = [r["document_title"] for r in rows]
            hits = [1 if d in relevant_ids else 0 for d in top_doc_ids]
            found = sum(hits)
            precision = found / TOP_K
            rank_first = next((i + 1 for i, h in enumerate(hits) if h), None)
            rr = (1.0 / rank_first) if rank_first else 0.0

            results.append({
                "query": q["query"],
                "role": q["role"],
                "note": q.get("note", ""),
                "relevant_in_corpus": len(relevant_ids),
                "found_in_top5": found,
                "precision_at_5": round(precision, 2),
                "rank_first_relevant": rank_first,
                "rr": round(rr, 3),
                "top5_titles": top_titles,
            })

    print(f"\n{'#':>2}  {'P@5':>4} {'rank':>4} {'RR':>5}  query")
    for i, r in enumerate(results, 1):
        print(f"{i:>2}  {r['precision_at_5']:>4} {str(r['rank_first_relevant']):>4} "
              f"{r['rr']:>5}  {r['query'][:50]}")

    mean_p = round(statistics.mean(r["precision_at_5"] for r in results), 3)
    mrr = round(statistics.mean(r["rr"] for r in results), 3)
    print(f"\nMean Precision@5 = {mean_p}")
    print(f"MRR             = {mrr}")

    out = {"top_k": TOP_K, "threshold": THRESHOLD, "n_queries": len(results),
           "mean_precision_at_5": mean_p, "mrr": mrr, "per_query": results}
    with open("../scripts/dipl_measurements/results/quality_metrics.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print("Saved -> results/quality_metrics.json")


if __name__ == "__main__":
    asyncio.run(main())
