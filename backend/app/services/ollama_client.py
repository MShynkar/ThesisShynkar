"""Async client for Ollama (embeddings + chat completion)."""
import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class OllamaError(Exception):
    pass


class OllamaClient:
    def __init__(
        self,
        base_url: str | None = None,
        embedding_model: str | None = None,
        llm_model: str | None = None,
        timeout: int | None = None,
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.embedding_model = embedding_model or settings.OLLAMA_EMBEDDING_MODEL
        self.llm_model = llm_model or settings.OLLAMA_LLM_MODEL
        self.timeout = timeout or settings.OLLAMA_TIMEOUT

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type((httpx.HTTPError, OllamaError)),
        reraise=True,
    )
    async def embed(self, text: str) -> list[float]:
        """Generate an embedding for a single string."""
        text = text.strip()
        if not text:
            raise OllamaError("Cannot embed empty text")

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.embedding_model, "prompt": text},
            )
            if response.status_code != 200:
                logger.error("ollama_embed_failed", status=response.status_code, body=response.text[:300])
                raise OllamaError(f"Embedding failed: {response.status_code}")
            data = response.json()
            embedding = data.get("embedding")
            if not embedding:
                raise OllamaError("No embedding in response")
            return embedding

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Sequentially embed a batch (Ollama doesn't support true batch embed)."""
        results = []
        for t in texts:
            results.append(await self.embed(t))
        return results

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        retry=retry_if_exception_type((httpx.HTTPError, OllamaError)),
        reraise=True,
    )
    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.2,
    ) -> str:
        """Generate a completion via Ollama's /api/generate."""
        payload = {
            "model": self.llm_model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature},
        }
        if system:
            payload["system"] = system

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{self.base_url}/api/generate", json=payload)
            if response.status_code != 200:
                logger.error("ollama_generate_failed", status=response.status_code, body=response.text[:300])
                raise OllamaError(f"Generation failed: {response.status_code}")
            data = response.json()
            return data.get("response", "").strip()

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False
