#!/usr/bin/env bash
# Tear down all services AND wipe persistent volumes. Use with care.
set -e

read -p "This will DELETE all data (db, uploads, ollama models). Continue? [y/N] " ans
case "$ans" in
    [yY]*) ;;
    *) echo "Aborted."; exit 1 ;;
esac

docker compose down -v
echo "✓ Stack destroyed and volumes removed."
