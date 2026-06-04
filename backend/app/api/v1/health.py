"""Versioned health endpoint — reports DB and Ollama reachability."""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.services.ollama_client import OllamaClient

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health(db: AsyncSession = Depends(get_db)):
    """
    Returns the reachability status of the database and Ollama.
    HTTP 200 is always returned; callers should inspect the component statuses.
    """
    db_ok = False
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    ollama_ok = await OllamaClient().health()

    return {
        "status": "ok" if (db_ok and ollama_ok) else "degraded",
        "version": settings.API_V1_PREFIX,
        "components": {
            "database": "ok" if db_ok else "unreachable",
            "ollama": "ok" if ollama_ok else "unreachable",
        },
    }
