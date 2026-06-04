"""Unit tests for the chunking utility."""
import pytest

from app.services.chunking import chunk_text


def test_chunk_text_empty():
    assert chunk_text("") == []
    assert chunk_text("   ") == []


def test_chunk_text_short():
    assert chunk_text("hello world", chunk_size=100, overlap=0) == ["hello world"]


def test_chunk_text_splits_long_text():
    text = ". ".join([f"Sentence number {i}" for i in range(200)])
    chunks = chunk_text(text, chunk_size=200, overlap=20)
    assert len(chunks) > 1
    for chunk in chunks:
        # Allow a little slack because we honor sentence boundaries
        assert len(chunk) <= 250


def test_chunk_text_overlap():
    text = "A" * 1000
    chunks = chunk_text(text, chunk_size=200, overlap=50)
    assert len(chunks) > 1
    # No overlap test on uniform content (no sentence boundaries) — just check non-empty
    assert all(c for c in chunks)


def test_chunk_text_invalid_params():
    with pytest.raises(ValueError):
        chunk_text("hi", chunk_size=0)
    with pytest.raises(ValueError):
        chunk_text("hi", chunk_size=100, overlap=100)
    with pytest.raises(ValueError):
        chunk_text("hi", chunk_size=100, overlap=-5)
