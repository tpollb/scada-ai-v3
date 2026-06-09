"""Config Store — CRUD для energy_config.json (теги счётчиков)"""
import json
from pathlib import Path
from structlog import get_logger

log = get_logger()

CONFIG_FILE = Path(__file__).parent.parent.parent / "data" / "energy_config.json"

DEFAULT_CONFIG = {
    "electricity": {
        "enabled": True,
        "unit": "kWh",
        "meters": [
            {
                "id": "input_1",
                "name": "Первый ввод",
                "tag_current": "LERS.electricity meter current month 1",
                "tag_last": "LERS.electricity meter last month 1",
            },
            {
                "id": "input_2",
                "name": "Второй ввод",
                "tag_current": "LERS.electricity meter current month 2",
                "tag_last": "LERS.electricity meter last month 2",
            },
        ],
    },
    "water": {
        "enabled": False,
        "unit": "m3",
        "meters": [],
    },
    "heat": {
        "enabled": False,
        "unit": "Gcal",
        "meters": [],
    },
}


def _ensure_file():
    """Создаёт energy_config.json если не существует"""
    if not CONFIG_FILE.exists():
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(
            json.dumps(DEFAULT_CONFIG, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        log.info("Created default energy_config.json")


def load_config() -> dict:
    """Загружает конфиг из JSON"""
    _ensure_file()
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        log.error("Failed to load energy config", error=str(e))
        return DEFAULT_CONFIG.copy()


def save_config(data: dict) -> None:
    """Сохраняет конфиг в JSON"""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info("Energy config saved")


def get_resource_config(resource: str) -> dict:
    """Возвращает конфиг конкретного ресурса."""
    config = load_config()
    return config.get(resource, {"enabled": False, "unit": "", "meters": []})


def is_resource_enabled(resource: str) -> bool:
    """Проверяет включён ли ресурс."""
    return bool(get_resource_config(resource).get("enabled", False))


def get_meters(resource: str) -> list:
    """Возвращает список счётчиков ресурса."""
    return get_resource_config(resource).get("meters", [])


def update_resource_config(resource: str, updates: dict) -> None:
    """Обновляет конфиг ресурса."""
    config = load_config()
    if resource not in config:
        config[resource] = {"enabled": False, "unit": "", "meters": []}
    config[resource].update(updates)
    save_config(config)
