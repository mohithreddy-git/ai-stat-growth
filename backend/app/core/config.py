from functools import lru_cache
from pathlib import Path
from typing import Annotated, List

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


ROOT_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    app_env: str = "development"
    app_name: str = "AI STAT-GROWTH"
    database_url: str = "sqlite:///./data/ai_stat_growth.db"
    jwt_secret: str = "development-only-change-me-use-a-longer-secret-26101"
    jwt_expire_minutes: int = 480
    llm_provider: str = "mock"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"
    openai_base_url: str = "https://api.openai.com/v1"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    telemetry_version: str = "3.0"
    cors_origins: Annotated[List[str], NoDecode] = [
        "http://localhost:5173",
        "http://localhost:4173",
        "http://localhost:5174",
        "http://localhost:5180",
        "http://localhost:5181",
        "http://localhost:5182",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:4173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5180",
    ]
    upload_max_mb: int = 20
    demo_mode: bool = True

    # Load the repository-level .env regardless of whether uvicorn is launched
    # from the repository root or from backend/. Docker/CI may still provide
    # environment variables directly, which take precedence over this file.
    model_config = SettingsConfigDict(env_file=ROOT_ENV_FILE, env_file_encoding="utf-8", extra="ignore")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @model_validator(mode="after")
    def add_local_dev_origins(self):
        if self.app_env.lower() in {"development", "demo", "test"}:
            local_origins = {
                "http://localhost:5173", "http://localhost:5174", "http://localhost:5180",
                "http://localhost:5181", "http://localhost:5182",
                "http://127.0.0.1:5173", "http://127.0.0.1:5174", "http://127.0.0.1:5180",
                "http://127.0.0.1:5181", "http://127.0.0.1:5182",
            }
            self.cors_origins = list(dict.fromkeys([*self.cors_origins, *local_origins]))
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
