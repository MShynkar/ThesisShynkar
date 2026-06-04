"""Point 0 + current corpus snapshot.

Reads DB/pgvector versions, current document/chunk counts and index sizes,
and the Ollama model list. Pure read-only.
"""
import asyncio
import json

import _common  # noqa: F401  (sets sys.path / cwd)
import httpx
from sqlalchemy import text

from app.core.config import settings
from app.db.session import engine


async def main() -> None:
    out: dict = {}

    async with engine.connect() as conn:
        out["pg_version"] = (await conn.execute(text("SELECT version()"))).scalar_one()
        out["pgvector_version"] = (
            await conn.execute(
                text("SELECT extversion FROM pg_extension WHERE extname='vector'")
            )
        ).scalar_one_or_none()

        out["documents_total"] = (
            await conn.execute(text("SELECT count(*) FROM documents"))
        ).scalar_one()
        out["documents_ready"] = (
            await conn.execute(text("SELECT count(*) FROM documents WHERE status='ready'"))
        ).scalar_one()
        out["chunks_total"] = (
            await conn.execute(text("SELECT count(*) FROM chunks"))
        ).scalar_one()
        out["chunks_with_embedding"] = (
            await conn.execute(text("SELECT count(*) FROM chunks WHERE embedding IS NOT NULL"))
        ).scalar_one()

        rows = (
            await conn.execute(
                text(
                    "SELECT access_level, count(*) FROM documents "
                    "GROUP BY access_level ORDER BY access_level"
                )
            )
        ).all()
        out["documents_by_level"] = {r[0]: r[1] for r in rows}

        # average document length in words (token_count is word count per chunk)
        out["avg_words_per_doc"] = (
            await conn.execute(
                text(
                    "SELECT COALESCE(round(avg(w)),0) FROM "
                    "(SELECT document_id, sum(token_count) AS w FROM chunks GROUP BY document_id) s"
                )
            )
        ).scalar_one()

        # index sizes (pretty + bytes)
        for idx in ("ix_chunks_embedding_hnsw", "ix_chunks_content_tsv"):
            try:
                size = (
                    await conn.execute(
                        text("SELECT pg_size_pretty(pg_relation_size(:i))"), {"i": idx}
                    )
                ).scalar_one()
                out[f"size_{idx}"] = size
            except Exception as e:  # noqa: BLE001
                out[f"size_{idx}"] = f"n/a ({e})"

        out["size_chunks_table"] = (
            await conn.execute(text("SELECT pg_size_pretty(pg_total_relation_size('chunks'))"))
        ).scalar_one()

    # Ollama models
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            out["ollama_models"] = [
                {
                    "name": m["name"],
                    "size_mb": round(m["size"] / 1e6, 1),
                    "param_size": m.get("details", {}).get("parameter_size"),
                    "quant": m.get("details", {}).get("quantization_level"),
                }
                for m in r.json().get("models", [])
            ]
    except Exception as e:  # noqa: BLE001
        out["ollama_models"] = f"unreachable: {e}"

    out["config"] = {
        "embedding_model": settings.OLLAMA_EMBEDDING_MODEL,
        "llm_model": settings.OLLAMA_LLM_MODEL,
        "embedding_dim": settings.EMBEDDING_DIMENSION,
        "chunk_size": settings.CHUNK_SIZE,
        "chunk_overlap": settings.CHUNK_OVERLAP,
        "top_k": settings.TOP_K,
        "threshold": settings.RELEVANCE_THRESHOLD,
        "hybrid_vector_weight": settings.HYBRID_VECTOR_WEIGHT,
        "hybrid_text_weight": settings.HYBRID_TEXT_WEIGHT,
        "db_host": settings.POSTGRES_HOST,
    }

    print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())
