from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    APP_NAME: str = "LLM Gateway"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/llmgateway"

    # Redis
    REDIS_URL: str = "redis://redis:6379"
    CACHE_TTL: int = 3600  # seconds

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_ORG_ID: str = ""

    # Together AI (Llama)
    TOGETHER_API_KEY: str = ""
    TOGETHER_BASE_URL: str = "https://api.together.xyz/v1"

    # Mistral
    MISTRAL_API_KEY: str = ""
    MISTRAL_BASE_URL: str = "https://api.mistral.ai/v1"

    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_PER_1K_TOKENS: float = 0.002  # USD

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_DAY: int = 10000

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]

    # Models
    DEFAULT_MODEL: str = "gpt-3.5-turbo"
    FALLBACK_ORDER: List[str] = ["gpt-3.5-turbo", "mistral-small", "llama-3-8b"]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
