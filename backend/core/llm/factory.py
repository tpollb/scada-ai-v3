"""Фабрика LLM-провайдеров — параметры из .env"""
from pathlib import Path
from typing import Optional
import yaml
from structlog import get_logger

from .base import LLMProvider
from config.settings import settings

log = get_logger()

_provider: Optional[LLMProvider] = None
_config_path = Path(__file__).parent.parent.parent / "config" / "llm.yaml"


def _load_config() -> dict:
    if not _config_path.exists():
        return {"active": "yandex", "providers": {"yandex": {}}}
    with open(_config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {"active": "yandex", "providers": {"yandex": {}}}


def get_provider(force_reload: bool = False) -> LLMProvider:
    """
    Получить LLM-провайдер.
    - active берётся из llm.yaml
    - все параметры (api_key, model, etc.) из .env через settings
    """
    global _provider

    if _provider is not None and not force_reload:
        return _provider

    cfg = _load_config()
    active = cfg.get("active", "yandex")

    if active == "yandex":
        from .yandex import YandexLLMProvider
        _provider = YandexLLMProvider(
            # Все параметры из settings (читаются из .env)
            api_key=settings.yandex_api_key,
            folder_id=settings.yandex_folder_id,
            model=settings.yandex_gpt_model,
            max_tokens=settings.llm_max_tokens,
            temperature=settings.llm_temperature,
            timeout=settings.llm_timeout,
        )
    # elif active == "openai":
    #     from .openai import OpenAIProvider
    #     _provider = OpenAIProvider(api_key=settings.openai_api_key, ...)
    else:
        raise ValueError(f"Неизвестный провайдер: {active}. Поддерживаются: yandex")

    log.info("LLM provider loaded", provider=active, model=settings.yandex_gpt_model)
    return _provider


def reload_provider() -> LLMProvider:
    return get_provider(force_reload=True)


def get_available_providers() -> list[str]:
    cfg = _load_config()
    return list(cfg.get("providers", {}).keys())


def get_active_provider() -> str:
    cfg = _load_config()
    return cfg.get("active", "yandex")
