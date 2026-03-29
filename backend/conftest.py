"""pytest configuration and fixtures for backend tests."""
import os

# Override settings BEFORE any app imports
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["REDIS_URL"] = "redis://localhost:6379"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["OPENAI_API_KEY"] = "sk-test"
os.environ["TOGETHER_API_KEY"] = "test"
os.environ["MISTRAL_API_KEY"] = "test"
os.environ["STRIPE_SECRET_KEY"] = "sk_test_fake"
os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_test_fake"

# Clear lru_cache so settings pick up new env vars
from app.config import get_settings
get_settings.cache_clear()
