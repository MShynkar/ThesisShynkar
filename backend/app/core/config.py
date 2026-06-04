"""Application configuration loaded from environment variables."""
from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    APP_NAME: str = "RAG-RBAC"
    APP_ENV: str = "development"
    DEBUG: bool = False  # MUST be False in production — True enables SQLAlchemy echo (logs all SQL)
    API_V1_PREFIX: str = "/api/v1"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Security
    SECRET_KEY: str = Field(default="change-me-in-production-please-use-a-long-random-string")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    BACKEND_CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.BACKEND_CORS_ORIGINS.split(",") if o.strip()]

    # Database
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "rag"
    POSTGRES_PASSWORD: str = "rag"
    POSTGRES_DB: str = "ragdb"
    POSTGRES_SSL: str = ""

    @property
    def database_url(self) -> str:
        base = (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
        return f"{base}?ssl={self.POSTGRES_SSL}" if self.POSTGRES_SSL else base

    @property
    def database_url_sync(self) -> str:
        base = (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
        return f"{base}?sslmode={self.POSTGRES_SSL}" if self.POSTGRES_SSL else base

    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"
    OLLAMA_LLM_MODEL: str = "llama3.2:3b"
    EMBEDDING_DIMENSION: int = 768  # nomic-embed-text default
    OLLAMA_TIMEOUT: int = 120

    # RAG
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 100
    TOP_K: int = 5
    RELEVANCE_THRESHOLD: float = 0.4  # min similarity; 0.3 was too permissive — irrelevant queries surfaced borderline matches
    HYBRID_VECTOR_WEIGHT: float = 0.7
    HYBRID_TEXT_WEIGHT: float = 0.3

    # File upload
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: str = "pdf,docx,txt,md"

    @property
    def allowed_extensions(self) -> List[str]:
        return [e.strip().lower() for e in self.ALLOWED_EXTENSIONS.split(",")]

    # Rate limiting
    RATE_LIMIT_DEFAULT: str = "100/minute"
    RATE_LIMIT_SEARCH: str = "30/minute"
    RATE_LIMIT_AUTH: str = "10/minute"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
