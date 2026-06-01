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
    app_version: str = "3.0.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8081

    # === База данных ===
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "scada"
    db_user: str = "postgres"
    db_password: str = ""

    # === SCADA ===
    scada_base_url: str = "http://localhost:9002"
    scada_username: str = ""
    scada_password: str = ""
    scada_poll_interval: int = 5

    # === LLM Provider ===
    llm_provider: str = "yandexgpt"
    yandex_api_key: str = ""
    yandex_folder_id: str = ""
    yandex_gpt_model: str = "yandexgpt-5.1/latest"
    llm_temperature: float = 0.05
    llm_max_tokens: int = 32000
    llm_timeout: int = 30

    # === Локация (для энергоэффективности) ===
    city: str = "Нижний Тагил"
    timezone: str = "Asia/Yekaterinburg"
    latitude: float = 57.9167
    longitude: float = 59.9417

    # === Auth ===
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    # === Modules ===
    enabled_modules: list[str] = ["hello", "health"]

    @property
    def database_url(self) -> str:
        pwd = quote_plus(self.db_password) if self.db_password else ""
        return f"postgresql://{self.db_user}:{pwd}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def database_url_masked(self) -> str:
        pwd = "***" if self.db_password else ""
        return f"postgresql://{self.db_user}:{pwd}@{self.db_host}:{self.db_port}/{self.db_name}"


settings = Settings()
