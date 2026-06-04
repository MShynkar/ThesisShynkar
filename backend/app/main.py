"""FastAPI application entrypoint."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.rate_limit import limiter
from app.api.v1 import api_router
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.services.ollama_client import OllamaClient

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("app_starting", env=settings.APP_ENV)
    # Make sure the upload dir exists
    import os
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    # Best-effort Ollama health check
    try:
        ok = await OllamaClient().health()
        logger.info("ollama_health", reachable=ok, url=settings.OLLAMA_BASE_URL)
    except Exception as e:
        logger.warning("ollama_health_failed", error=str(e))
    yield
    logger.info("app_stopping")


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description=(
        "Document RAG system with role-based access control. "
        "Semantic search via pgvector, generation via Ollama."
    ),
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": f"Rate limit exceeded: {exc.detail}"},
    )


app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.APP_ENV}


@app.get("/", tags=["health"])
async def root():
    return {
        "name": settings.APP_NAME,
        "docs": "/docs",
        "api": settings.API_V1_PREFIX,
    }
