from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    openai_api_key: str = ""
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
