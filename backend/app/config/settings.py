"""
Centralized application configuration loaded from environment variables.
All secrets MUST come from the environment / .env file - never hardcode.
"""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- App ---
    APP_NAME: str = "AI Service Platform"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # --- Security / JWT ---
    JWT_SECRET_KEY: str = "CHANGE_ME_SUPER_SECRET"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- Database ---
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_service_platform"

    # --- CORS ---
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # --- Rate limiting ---
    RATE_LIMIT_PER_MINUTE: int = 60

    # --- LLM Providers ---
    OPENAI_API_KEY: str = "sk-REPLACE_WITH_OPENAI_KEY"
    OPENAI_MODEL: str = "gpt-4o"
    GEMINI_API_KEY: str = "REPLACE_WITH_GEMINI_KEY"
    GEMINI_MODEL: str = "gemini-1.5-pro"
    LLM_REQUEST_TIMEOUT_SECONDS: int = 30

    # --- Credit Economy ---
    SIGNUP_BONUS_CREDITS: int = 50
    CREDIT_COST_LLM_REQUEST: int = 5
    CREDIT_COST_VIDEO_SHORT: int = 40
    CREDIT_COST_VIDEO_MAIN: int = 100

    # --- Stripe ---
    STRIPE_SECRET_KEY: str = "sk_test_REPLACE_WITH_STRIPE_SECRET"
    STRIPE_WEBHOOK_SECRET: str = "whsec_REPLACE_WITH_STRIPE_WEBHOOK_SECRET"
    STRIPE_PUBLISHABLE_KEY: str = "pk_test_REPLACE_WITH_STRIPE_PUBLISHABLE"

    # --- Video Engine ---
    VIDEO_STORAGE_PATH: str = "./storage/videos"
    VIDEO_RENDERER_BACKEND: str = "mock"  # mock | ffmpeg | external

    # --- xAI / Grok ---
    XAI_API_KEY: str = "REPLACE_WITH_XAI_KEY"
    XAI_MODEL: str = "grok-beta"

    # --- n8n ---
    N8N_WEBHOOK_URL: str = "http://localhost:5678/webhook/astroengine"
    N8N_API_KEY: str = ""

    # --- Celery / Redis ---
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"


@lru_cache
def get_settings() -> Settings:
    return Settings()
