#!/usr/bin/env bash
# Pull the embedding and LLM models inside the Ollama container.
# Run after `docker compose up -d` and before issuing queries.
set -e

EMBEDDING_MODEL="${OLLAMA_EMBEDDING_MODEL:-nomic-embed-text}"
LLM_MODEL="${OLLAMA_LLM_MODEL:-llama3.1}"

echo "→ Pulling embedding model: ${EMBEDDING_MODEL}"
docker compose exec -T ollama ollama pull "${EMBEDDING_MODEL}"

echo "→ Pulling LLM: ${LLM_MODEL}"
docker compose exec -T ollama ollama pull "${LLM_MODEL}"

echo "✓ Done. You can verify with:"
echo "    docker compose exec ollama ollama list"
