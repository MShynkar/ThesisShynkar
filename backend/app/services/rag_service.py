"""RAG pipeline: embed query → retrieve chunks → LLM answer with citations."""
import time

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.permissions import allowed_levels_for_role
from app.models.user import User
from app.repositories.audit_repo import SearchHistoryRepository
from app.repositories.document_repo import ChunkRepository
from app.schemas.search import SearchRequest, SearchResponse, Source
from app.services.ollama_client import OllamaClient

logger = get_logger(__name__)


SYSTEM_PROMPT = (
    "You are a precise document-grounded assistant. "
    "Answer ONLY using the provided context snippets. "
    "If the context doesn't contain the answer, say so clearly and do not invent facts. "
    "When you make a claim, cite the source by its number, e.g. [1] or [2]. "
    "Keep answers concise."
)


def _build_prompt(query: str, sources: list[Source]) -> str:
    parts = ["Context:\n"]
    for i, s in enumerate(sources, start=1):
        parts.append(f"[{i}] (from \"{s.document_title}\", chunk {s.chunk_index})\n{s.content}\n")
    parts.append(f"\nQuestion: {query}\n\nAnswer:")
    return "\n".join(parts)


class RAGService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.chunks = ChunkRepository(session)
        self.history = SearchHistoryRepository(session)
        self.ollama = OllamaClient()

    async def search(self, req: SearchRequest, user: User) -> SearchResponse:
        start = time.perf_counter()
        allowed = allowed_levels_for_role(user.role)

        # 1. Embed the query
        query_embedding = await self.ollama.embed(req.query)

        # 2. Retrieve top-K chunks (hybrid or pure vector)
        if req.hybrid:
            rows = await self.chunks.hybrid_search(
                query_text=req.query,
                query_embedding=query_embedding,
                allowed_levels=allowed,
                top_k=req.top_k,
                threshold=req.threshold,
                categories=req.categories,
                tags=req.tags,
            )
        else:
            rows = await self.chunks.semantic_search(
                query_embedding=query_embedding,
                allowed_levels=allowed,
                top_k=req.top_k,
                threshold=req.threshold,
                categories=req.categories,
                tags=req.tags,
            )

        sources = [
            Source(
                chunk_id=r["chunk_id"],
                document_id=r["document_id"],
                document_title=r["document_title"],
                chunk_index=r["chunk_index"],
                content=r["content"],
                similarity=float(r["similarity"]),
            )
            for r in rows
        ]

        # 3. Generate the answer with the LLM
        answer: str | None = None
        if req.generate_answer and sources:
            try:
                prompt = _build_prompt(req.query, sources)
                answer = await self.ollama.generate(prompt, system=SYSTEM_PROMPT, temperature=0.2)
            except Exception as e:
                logger.warning("llm_generation_failed", error=str(e))
                answer = (
                    "I retrieved relevant context but the language model is unavailable. "
                    "Please see the sources below."
                )
        elif req.generate_answer and not sources:
            answer = "I couldn't find any relevant documents for your query."

        # 4. Persist to history
        try:
            await self.history.add(
                user_id=user.id,
                query=req.query,
                answer=answer,
                sources=[s.model_dump(mode="json") for s in sources],
            )
        except Exception:
            logger.exception("search_history_persist_failed")

        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return SearchResponse(
            query=req.query,
            answer=answer,
            sources=sources,
            elapsed_ms=elapsed_ms,
        )
