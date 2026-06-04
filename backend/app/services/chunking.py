"""Split documents into overlapping chunks suitable for embedding."""
import re


def chunk_text(
    text: str,
    chunk_size: int = 800,
    overlap: int = 100,
) -> list[str]:
    """
    Split text into chunks of approximately `chunk_size` characters,
    with `overlap` characters of context between adjacent chunks.

    Tries to respect sentence boundaries when possible.
    """
    text = text.strip()
    if not text:
        return []
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be in [0, chunk_size)")

    # Normalize whitespace lightly (preserve paragraph breaks)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + chunk_size, n)
        # Try to break on a sentence boundary in the last 20% of the window
        if end < n:
            window_start = max(start + int(chunk_size * 0.8), start + 1)
            slice_ = text[window_start:end]
            # Prefer paragraph break, then sentence end
            for sep in ("\n\n", ". ", "! ", "? ", "\n"):
                idx = slice_.rfind(sep)
                if idx != -1:
                    end = window_start + idx + len(sep)
                    break
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= n:
            break
        start = max(end - overlap, start + 1)
    return chunks
