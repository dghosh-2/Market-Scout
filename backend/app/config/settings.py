from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    openai_api_key: str = ""
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    smoldb_url: str = "https://smoldb.fly.dev/api/projects/f5bf20a2-76d0-4626-905a-14690bcf69f1"
    smoldb_key: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
