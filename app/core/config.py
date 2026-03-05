from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    # App
    APP_NAME: str = "AI Business Analysis"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_business"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@localhost:5432/ai_business"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # LLM API Keys
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""

    # LLM defaults
    DEFAULT_MODEL: str = "claude-sonnet-4-20250514"
    FALLBACK_MODELS: list[str] = [
        "gpt-4o",
        "gemini/gemini-2.0-flash",
    ]

    # Search tools
    TAVILY_API_KEY: str = ""
    SERPAPI_API_KEY: str = ""

    # S3 / Object Storage
    S3_BUCKET: str = ""
    S3_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""

    # Auth
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60 * 24  # 24 hours

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"


@lru_cache
def get_settings() -> Settings:
    return Settings()
