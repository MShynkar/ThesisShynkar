"""Data access for Document and Chunk, including hybrid search."""
from uuid import UUID

from sqlalchemy import and_, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from app.models.document import Chunk, Document


class DocumentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(
        self,
        document_id: UUID,
        allowed_levels: list[str] | None = None,
    ) -> Document | None:
        stmt = select(Document).where(Document.id == document_id)
        if allowed_levels is not None:
            stmt = stmt.where(Document.access_level.in_(allowed_levels))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        allowed_levels: list[str],
        owner_id: UUID | None = None,
        category: str | None = None,
        tag: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Document], int]:
        conditions: list[ColumnElement[bool]] = [Document.access_level.in_(allowed_levels)]
        if owner_id is not None:
            conditions.append(Document.owner_id == owner_id)
        if category:
            conditions.append(Document.category == category)
        if tag:
            conditions.append(Document.tags.any(tag))  # type: ignore[arg-type]

        stmt = (
            select(Document)
            .where(and_(*conditions))
            .order_by(Document.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        items = list(result.scalars().all())

        count_stmt = select(func.count(Document.id)).where(and_(*conditions))
        total = (await self.session.execute(count_stmt)).scalar_one()

        return items, total

    async def create(self, doc: Document) -> Document:
        self.session.add(doc)
        await self.session.flush()
        await self.session.refresh(doc)
        return doc

    async def update(self, doc: Document) -> Document:
        await self.session.flush()
        await self.session.refresh(doc)
        return doc

    async def delete(self, doc: Document) -> None:
        await self.session.delete(doc)
        await self.session.flush()


class ChunkRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def bulk_create(self, chunks: list[Chunk]) -> None:
        self.session.add_all(chunks)
        await self.session.flush()

    async def semantic_search(
        self,
        query_embedding: list[float],
        allowed_levels: list[str],
        top_k: int = 5,
        threshold: float = 0.0,
        categories: list[str] | None = None,
        tags: list[str] | None = None,
    ) -> list[dict]:
        """
        Cosine-similarity search via pgvector.

        The RBAC pre-filter is on chunks.access_level (denormalized) so it sits on the
        same table as the HNSW index — the vector ORDER BY can then use the index instead
        of a brute-force sort. hnsw.iterative_scan ensures the post-filter still returns
        a full top_k for low-privilege roles whose visible chunks are sparse in the index.
        """
        await self.session.execute(text("SET LOCAL hnsw.iterative_scan = relaxed_order"))
        # The inner CTE scans ONLY chunks (access_level + embedding) ordered by distance,
        # which is the exact shape the HNSW index accelerates. Document-level filters
        # (status, category, tags) and the title join run afterwards on the small
        # prefetched set, so they don't prevent the planner from using the index.
        sql = text(
            """
            WITH topk AS (
                SELECT
                    c.id,
                    c.document_id,
                    c.chunk_index,
                    c.content,
                    1 - (c.embedding <=> CAST(:query_embedding AS vector)) AS similarity
                FROM chunks c
                WHERE c.access_level = ANY(:allowed_levels)
                  AND c.embedding IS NOT NULL
                ORDER BY c.embedding <=> CAST(:query_embedding AS vector)
                LIMIT :prefetch
            )
            SELECT
                t.id AS chunk_id,
                t.document_id,
                t.chunk_index,
                t.content,
                d.title AS document_title,
                t.similarity
            FROM topk t
            JOIN documents d ON t.document_id = d.id
            WHERE d.status = 'ready'
              AND t.similarity >= :threshold
              AND (CAST(:categories AS VARCHAR[]) IS NULL OR d.category = ANY(CAST(:categories AS VARCHAR[])))
              AND (CAST(:tags AS VARCHAR[]) IS NULL OR d.tags && CAST(:tags AS VARCHAR[]))
            ORDER BY t.similarity DESC
            LIMIT :top_k
            """
        )

        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

        result = await self.session.execute(
            sql,
            {
                "query_embedding": embedding_str,
                "allowed_levels": allowed_levels,
                "threshold": threshold,
                "top_k": top_k,
                "prefetch": top_k * 4,
                "categories": categories,
                "tags": tags,
            },
        )
        return [dict(r._mapping) for r in result.fetchall()]

    async def hybrid_search(
        self,
        query_text: str,
        query_embedding: list[float],
        allowed_levels: list[str],
        top_k: int = 5,
        threshold: float = 0.0,
        vec_weight: float = 0.7,
        text_weight: float = 0.3,
        categories: list[str] | None = None,
        tags: list[str] | None = None,
    ) -> list[dict]:
        """
        Combined vector + full-text search.
        Score = vec_weight * cosine_sim + text_weight * normalized_ts_rank.
        RBAC pre-filter is on chunks.access_level (same table as the HNSW index) so the
        vector CTE can use the index; iterative_scan keeps top_k full after filtering.
        """
        await self.session.execute(text("SET LOCAL hnsw.iterative_scan = relaxed_order"))
        # Both CTEs filter on chunks-only columns so the vector CTE can use the HNSW
        # index and the text CTE the GIN index. Document-level filters (status, category,
        # tags) and the title join are applied once on the small combined candidate set.
        sql = text(
            """
            WITH vec AS (
                SELECT
                    c.id,
                    1 - (c.embedding <=> CAST(:query_embedding AS vector)) AS sim
                FROM chunks c
                WHERE c.access_level = ANY(:allowed_levels)
                  AND c.embedding IS NOT NULL
                ORDER BY c.embedding <=> CAST(:query_embedding AS vector)
                LIMIT :prefetch
            ),
            txt AS (
                SELECT
                    c.id,
                    ts_rank(c.content_tsv, plainto_tsquery('english', :query_text)) AS rank
                FROM chunks c
                WHERE c.access_level = ANY(:allowed_levels)
                  AND c.content_tsv @@ plainto_tsquery('english', :query_text)
                ORDER BY rank DESC
                LIMIT :prefetch
            ),
            combined AS (
                SELECT id FROM vec
                UNION
                SELECT id FROM txt
            )
            SELECT
                c.id AS chunk_id,
                c.document_id,
                c.chunk_index,
                c.content,
                d.title AS document_title,
                COALESCE(vec.sim, 0) AS vec_sim,
                COALESCE(txt.rank, 0) AS text_rank,
                (:vec_w * COALESCE(vec.sim, 0)
                 + :txt_w * LEAST(COALESCE(txt.rank, 0), 1.0)) AS similarity
            FROM combined cb
            JOIN chunks c ON c.id = cb.id
            JOIN documents d ON c.document_id = d.id
            LEFT JOIN vec ON vec.id = cb.id
            LEFT JOIN txt ON txt.id = cb.id
            WHERE d.status = 'ready'
              AND (:vec_w * COALESCE(vec.sim, 0)
                   + :txt_w * LEAST(COALESCE(txt.rank, 0), 1.0)) >= :threshold
              AND (CAST(:categories AS VARCHAR[]) IS NULL OR d.category = ANY(CAST(:categories AS VARCHAR[])))
              AND (CAST(:tags AS VARCHAR[]) IS NULL OR d.tags && CAST(:tags AS VARCHAR[]))
            ORDER BY similarity DESC
            LIMIT :top_k
            """
        )

        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

        result = await self.session.execute(
            sql,
            {
                "query_text": query_text,
                "query_embedding": embedding_str,
                "allowed_levels": allowed_levels,
                "threshold": threshold,
                "top_k": top_k,
                "prefetch": top_k * 4,
                "vec_w": vec_weight,
                "txt_w": text_weight,
                "categories": categories,
                "tags": tags,
            },
        )
        return [dict(r._mapping) for r in result.fetchall()]

    async def delete_by_document(self, document_id: UUID) -> None:
        await self.session.execute(
            text("DELETE FROM chunks WHERE document_id = :doc_id"),
            {"doc_id": str(document_id)},
        )
