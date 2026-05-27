from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # OpenAI
    openai_api_key: str = ""

    # FastAPI
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    # Postgres (Supabase) — DATABASE_URL must use the async driver, e.g.:
    # postgresql+asyncpg://postgres:<pw>@db.<ref>.supabase.co:5432/postgres
    database_url: str = ""
    db_default_user_id: int = 0

    # Redis (Upstash) — accepts redis:// or rediss:// URLs
    redis_url: str = ""

    # Semantic cache tuning
    embedding_model: str = "text-embedding-3-small"
    embedding_dim: int = 1536
    semantic_cache_threshold: float = 0.85
    semantic_cache_ttl_seconds: int = 60 * 60 * 24  # 24 hours
    semantic_cache_prefix: str = "marketscout:cache"
    semantic_cache_max_scan: int = 500

    # Langfuse
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"
    langfuse_enabled: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
