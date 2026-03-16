"""app/core/config.py — centralised settings via pydantic-settings"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "Smart Finance Tracker"
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "CHANGE_ME_TO_RANDOM_32_BYTES_HEX"
    DEBUG: bool = True

    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/finance_db"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    ALLOWED_HOSTS:   List[str] = ["localhost", "127.0.0.1"]

    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL_SECONDS: int = 3600

    ML_MODEL_PATH: str = "./ai-model/models/spending_model.pkl"
    MIN_TX_FOR_PREDICTION: int = 30


settings = Settings()
