"""Application settings — все настройки в .env"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from urllib.parse import quote_plus


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_name: str = "SCADA.AI v3"
    app_version: str = "3.2.0"
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

    # Database
    db_host: str = "172.27.10.216"
    db_port: int = 5432
    db_name: str = "scada_ai"
    db_user: str = "postgres"
    db_password: str = "postgres"
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_connect_timeout: int = 30
    db_command_timeout: int = 120

    # YandexGPT
    yandex_api_key: str = ""
    yandex_folder_id: str = ""
    yandex_gpt_model: str = "yandexgpt-lite"
    llm_temperature: float = 0.3
    llm_max_tokens: int = 1500
    llm_timeout: int = 60

    # SCADA REST API
    scada_base_url: str = "http://localhost:8080"
    scada_timeout: int = 30

    # Location
    city: str = "Нижний Тагил"
    timezone: str = "Asia/Yekaterinburg"
    latitude: float = 57.9167
    longitude: float = 59.9417

    # Security
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    # Modules
    enabled_modules: str = "hello,health,logs"

    @property
    def enabled_modules_list(self) -> list[str]:
        """Возвращает список активных модулей (парсит CSV)"""
        if not self.enabled_modules:
            return []
        return [m.strip() for m in self.enabled_modules.split(",") if m.strip()]

    # Logs
    log_poll_interval_ms: int = 2000
    log_poll_max_entries: int = 500

    @property
    def database_url(self) -> str:
        """Полный URL для подключения к PostgreSQL"""
        password = quote_plus(self.db_password)
        return f"postgresql://{self.db_user}:{password}@{self.db_host}:{self.db_port}/{self.db_name}"


settings = Settings()
