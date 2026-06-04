"""Point 4: EXPLAIN (ANALYZE, BUFFERS) of the semantic-search vector query.

Usage:
    python hnsw_explain.py                 # explain on the REAL chunks table (current size)
    python hnsw_explain.py --synth 3000    # insert N synthetic chunks, explain, then DELETE them

The synthetic rows are inserted straight into the real `chunks` table (marked
with a sentinel document_id) so the EXPLAIN exercises the production
`ix_chunks_embedding_hnsw` index exactly. They are removed again at the end,
restoring the table to its original size.
"""
import argparse
import asyncio
import random

import _common  # noqa: F401
from sqlalchemy import text

from app.core.config import settings
from app.db.session import engine
from app.services.ollama_client import OllamaClient

ALL_LEVELS = ["public", "internal", "confidential", "restricted"]
SENTINEL_DOC = "00000000-0000-0000-0000-0000000000ff"  # marks synthetic rows

# Exactly the inner shape used by ChunkRepository.semantic_search.
EXPLAIN_SQL = """
EXPLAIN (ANALYZE, BUFFERS)
WITH topk AS (
    SELECT c.id, c.document_id, c.chunk_index, c.content,
           1 - (c.embedding <=> CAST(:qe AS vector)) AS similarity
    FROM chunks c
    WHERE c.access_level = ANY(:levels)
      AND c.embedding IS NOT NULL
    ORDER BY c.embedding <=> CAST(:qe AS vector)
    LIMIT :prefetch
)
SELECT t.id, t.document_id, t.chunk_index, t.content, d.title, t.similarity
FROM topk t JOIN documents d ON t.document_id = d.id
WHERE d.status = 'ready' AND t.similarity >= :threshold
ORDER BY t.similarity DESC
LIMIT :top_k
"""


async def insert_synthetic(n: int) -> None:
    """Insert N chunks with random unit-ish vectors under a sentinel document."""
    # The sentinel document must exist (FK). Create a throwaway owner+doc if needed.
    async with engine.begin() as conn:
        owner = (await conn.execute(text("SELECT id FROM users LIMIT 1"))).scalar_one()
        await conn.execute(
            text(
                "INSERT INTO documents (id, title, filename, file_path, file_size, mime_type,"
                " owner_id, access_level, tags, doc_metadata, status, chunk_count, created_at, updated_at)"
                " VALUES (:id,'__SYNTH__','synth','synth',0,'text/plain',:owner,'public','{}','{}','ready',0,now(),now())"
                " ON CONFLICT (id) DO NOTHING"
            ),
            {"id": SENTINEL_DOC, "owner": owner},
        )

    dim = settings.EMBEDDING_DIMENSION
    batch = 500
    inserted = 0
    while inserted < n:
        rows = []
        params = {}
        this = min(batch, n - inserted)
        for i in range(this):
            vec = [random.gauss(0, 1) for _ in range(dim)]
            params[f"e{i}"] = "[" + ",".join(f"{x:.4f}" for x in vec) + "]"
            params[f"x{i}"] = inserted + i
            rows.append(
                f"(gen_random_uuid(), :id, :x{i}, 'synthetic chunk', CAST(:e{i} AS vector),"
                " 'public', 0, now())"
            )
        params["id"] = SENTINEL_DOC
        sql = (
            "INSERT INTO chunks (id, document_id, chunk_index, content, embedding, access_level,"
            " token_count, created_at) VALUES " + ",".join(rows)
        )
        async with engine.begin() as conn:
            await conn.execute(text(sql), params)
        inserted += this
        print(f"  inserted {inserted}/{n}")


async def cleanup_synthetic() -> None:
    async with engine.begin() as conn:
        await conn.execute(text("DELETE FROM chunks WHERE document_id = :id"), {"id": SENTINEL_DOC})
        await conn.execute(text("DELETE FROM documents WHERE id = :id"), {"id": SENTINEL_DOC})
    print("  synthetic rows removed")


async def run_explain(query: str) -> None:
    qe = "[" + ",".join(str(x) for x in await OllamaClient().embed(query)) + "]"
    async with engine.connect() as conn:
        total = (await conn.execute(text("SELECT count(*) FROM chunks"))).scalar_one()
        print(f"\n=== chunks in table: {total} ===")
        await conn.execute(text("SET LOCAL hnsw.iterative_scan = relaxed_order"))
        plan = (
            await conn.execute(
                text(EXPLAIN_SQL),
                {"qe": qe, "levels": ALL_LEVELS, "prefetch": 20, "threshold": 0.0, "top_k": 5},
            )
        ).all()
        for row in plan:
            print(row[0])


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--synth", type=int, default=0, help="insert N synthetic chunks first")
    ap.add_argument("--query", default="What is the company's data retention policy?")
    ap.add_argument("--keep", action="store_true", help="do not delete synthetic rows")
    args = ap.parse_args()

    try:
        if args.synth:
            print(f"Inserting {args.synth} synthetic chunks ...")
            await insert_synthetic(args.synth)
        await run_explain(args.query)
    finally:
        if args.synth and not args.keep:
            await cleanup_synthetic()


if __name__ == "__main__":
    asyncio.run(main())
