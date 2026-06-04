"""Unit tests for OllamaClient — httpx layer mocked, no real Ollama needed."""
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.ollama_client import OllamaClient, OllamaError


def _resp(status: int, payload: dict | None = None) -> MagicMock:
    """Construct a mock httpx.Response with both status_code and .json()."""
    r = MagicMock()
    r.status_code = status
    r.text = "" if payload is None else str(payload)
    r.json = MagicMock(return_value=payload or {})
    return r


def _mock_async_client(response):
    """Patch httpx.AsyncClient so its context manager yields a client whose
    post()/get() return the given response."""
    instance = MagicMock()
    instance.post = AsyncMock(return_value=response)
    instance.get = AsyncMock(return_value=response)
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=instance)
    cm.__aexit__ = AsyncMock(return_value=None)
    return patch("app.services.ollama_client.httpx.AsyncClient", return_value=cm)


# ---------------------------------------------------------------------------
# embed
# ---------------------------------------------------------------------------

class TestEmbed:
    @pytest.mark.asyncio
    async def test_returns_embedding_on_200(self):
        client = OllamaClient()
        emb = [0.1, 0.2, 0.3]
        with _mock_async_client(_resp(200, {"embedding": emb})):
            result = await client.embed("hello")
        assert result == emb

    @pytest.mark.asyncio
    async def test_empty_text_raises(self):
        client = OllamaClient()
        with pytest.raises(OllamaError, match="empty"):
            await client.embed("   ")

    @pytest.mark.asyncio
    async def test_non_200_raises_after_retries(self):
        client = OllamaClient()
        with _mock_async_client(_resp(500)):
            with pytest.raises(OllamaError):
                await client.embed("hello")

    @pytest.mark.asyncio
    async def test_missing_embedding_field_raises(self):
        client = OllamaClient()
        with _mock_async_client(_resp(200, {})):
            with pytest.raises(OllamaError, match="No embedding"):
                await client.embed("hello")


class TestEmbedBatch:
    @pytest.mark.asyncio
    async def test_batch_returns_all(self):
        client = OllamaClient()
        with _mock_async_client(_resp(200, {"embedding": [0.5]})):
            out = await client.embed_batch(["a", "b", "c"])
        assert out == [[0.5], [0.5], [0.5]]


# ---------------------------------------------------------------------------
# generate
# ---------------------------------------------------------------------------

class TestGenerate:
    @pytest.mark.asyncio
    async def test_returns_response_text(self):
        client = OllamaClient()
        with _mock_async_client(_resp(200, {"response": "  answer text  "})):
            out = await client.generate("prompt")
        assert out == "answer text"

    @pytest.mark.asyncio
    async def test_passes_system_and_temperature(self):
        """The request payload must carry system + temperature options."""
        client = OllamaClient()
        captured = {}

        instance = MagicMock()
        async def _capture_post(url, json=None):
            captured["url"] = url
            captured["payload"] = json
            return _resp(200, {"response": "ok"})
        instance.post = _capture_post
        cm = MagicMock()
        cm.__aenter__ = AsyncMock(return_value=instance)
        cm.__aexit__ = AsyncMock(return_value=None)

        with patch("app.services.ollama_client.httpx.AsyncClient", return_value=cm):
            await client.generate("user prompt", system="be precise", temperature=0.5)

        assert captured["url"].endswith("/api/generate")
        assert captured["payload"]["system"] == "be precise"
        assert captured["payload"]["options"]["temperature"] == 0.5
        assert captured["payload"]["stream"] is False

    @pytest.mark.asyncio
    async def test_non_200_raises(self):
        client = OllamaClient()
        with _mock_async_client(_resp(503)):
            with pytest.raises(OllamaError):
                await client.generate("x")


# ---------------------------------------------------------------------------
# health
# ---------------------------------------------------------------------------

class TestHealth:
    @pytest.mark.asyncio
    async def test_returns_true_on_200(self):
        client = OllamaClient()
        with _mock_async_client(_resp(200, {"models": []})):
            assert await client.health() is True

    @pytest.mark.asyncio
    async def test_returns_false_on_non_200(self):
        client = OllamaClient()
        with _mock_async_client(_resp(500)):
            assert await client.health() is False

    @pytest.mark.asyncio
    async def test_returns_false_on_connection_error(self):
        client = OllamaClient()
        instance = MagicMock()
        instance.get = AsyncMock(side_effect=httpx.ConnectError("refused"))
        cm = MagicMock()
        cm.__aenter__ = AsyncMock(return_value=instance)
        cm.__aexit__ = AsyncMock(return_value=None)
        with patch("app.services.ollama_client.httpx.AsyncClient", return_value=cm):
            assert await client.health() is False


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_overrides_take_precedence_over_settings():
    client = OllamaClient(base_url="http://x:1", embedding_model="m1", llm_model="m2", timeout=42)
    assert client.base_url == "http://x:1"
    assert client.embedding_model == "m1"
    assert client.llm_model == "m2"
    assert client.timeout == 42


def test_trailing_slash_stripped():
    assert OllamaClient(base_url="http://x:1/").base_url == "http://x:1"
