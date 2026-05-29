"""Application settings loaded from environment"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # App
    app_name: str = "SCADA.AI v3"
    app_version: str = "3.0.0"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8081

    # SCADA
    scada_base_url: str = "http://localhost:9002"
    scada_username: str = ""
    scada_password: str = ""
    scada_poll_interval: int = 5  # seconds

    # Database (PostgreSQL → TimescaleDB later)
    database_url: str = "postgresql+asyncpg://user:pass@localhost:5432/scada"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # LLM (YandexGPT)
    yandex_api_key: str = ""
    yandex_folder_id: str = ""
    yandex_gpt_model: str = "yandexgpt/latest"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 8192
    llm_timeout: int = 30

    # Auth
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440  # 24 hours

    # Modules
    enabled_modules: list[str] = ["hello", "health", "schedules"]


settings = Settings()
