from pathlib import Path
import json

print('=== build_energy_backend.py (День 1) ===')
print()

# ============================================================================
# 1. core/energy/ — библиотека утилит
# ============================================================================
core_energy_dir = Path('core/energy')
core_energy_dir.mkdir(parents=True, exist_ok=True)

# __init__.py
(core_energy_dir / '__init__.py').write_text(
    '"""Energy utilities — tariff store, config store, calculator"""\n',
    encoding='utf-8'
)
print('✓ Создан: core/energy/__init__.py')

# tariff_store.py
tariff_store_content = '''"""Tariff Store — CRUD для интервальных тарифов в tariffs.json"""
import json
from pathlib import Path
from datetime import date, datetime
from structlog import get_logger

log = get_logger()

TARIFFS_FILE = Path(__file__).parent.parent.parent / "data" / "tariffs.json"


def _ensure_file():
    """Создаёт tariffs.json если не существует"""
    if not TARIFFS_FILE.exists():
        TARIFFS_FILE.parent.mkdir(parents=True, exist_ok=True)
        default = {
            "electricity": [],
            "water": [],
            "heat": [],
        }
        TARIFFS_FILE.write_text(json.dumps(default, indent=2, ensure_ascii=False), encoding="utf-8")
        log.info("Created default tariffs.json")


def load_tariffs() -> dict:
    """Загружает все тарифы из JSON"""
    _ensure_file()
    try:
        return json.loads(TARIFFS_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        log.error("Failed to load tariffs", error=str(e))
        return {"electricity": [], "water": [], "heat": []}


def save_tariffs(data: dict) -> None:
    """Сохраняет тарифы в JSON"""
    TARIFFS_FILE.parent.mkdir(parents=True, exist_ok=True)
    TARIFFS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info("Tariffs saved", resources=list(data.keys()))


def get_active_tariffs(resource: str, on_date: date | None = None) -> list:
    """Возвращает тарифы активные на указанную дату.
    
    Если on_date не указан — используется сегодня.
    Тариф активен если start_date <= on_date и (end_date is None или end_date >= on_date).
    """
    _ensure_file()
    all_tariffs = load_tariffs()
    tariffs = all_tariffs.get(resource, [])
    
    if on_date is None:
        on_date = date.today()
    elif isinstance(on_date, datetime):
        on_date = on_date.date()
    elif isinstance(on_date, str):
        on_date = datetime.fromisoformat(on_date).date()
    
    active = []
    for t in tariffs:
        try:
            start = datetime.fromisoformat(t["start_date"]).date()
            end = datetime.fromisoformat(t["end_date"]).date() if t.get("end_date") else None
            
            if start <= on_date and (end is None or end >= on_date):
                active.append(t)
        except (KeyError, ValueError) as e:
            log.warning("Invalid tariff record", tariff=t, error=str(e))
    
    return active


def get_tariff_for_date(resource: str, on_date: date | None = None) -> dict | None:
    """Возвращает один активный тариф на дату (первый найденный)."""
    active = get_active_tariffs(resource, on_date)
    if not active:
        log.warning("No active tariff found", resource=resource, date=str(on_date or date.today()))
        return None
    if len(active) > 1:
        log.warning("Multiple active tariffs, using first", resource=resource, count=len(active))
    return active[0]


def add_tariff(resource: str, tariff: dict) -> dict:
    """Добавляет новый тариф. Возвращает тариф с присвоенным id."""
    all_tariffs = load_tariffs()
    if resource not in all_tariffs:
        all_tariffs[resource] = []
    
    # Генерируем id
    existing_ids = [t.get("id", "") for t in all_tariffs[resource]]
    idx = 1
    while f"tariff_{idx:03d}" in existing_ids:
        idx += 1
    tariff["id"] = f"tariff_{idx:03d}"
    
    all_tariffs[resource].append(tariff)
    save_tariffs(all_tariffs)
    log.info("Tariff added", resource=resource, id=tariff["id"])
    return tariff


def update_tariff(resource: str, tariff_id: str, updates: dict) -> bool:
    """Обновляет тариф по id. Возвращает True если успешно."""
    all_tariffs = load_tariffs()
    tariffs = all_tariffs.get(resource, [])
    
    for t in tariffs:
        if t.get("id") == tariff_id:
            t.update(updates)
            save_tariffs(all_tariffs)
            log.info("Tariff updated", resource=resource, id=tariff_id)
            return True
    
    log.warning("Tariff not found for update", resource=resource, id=tariff_id)
    return False


def delete_tariff(resource: str, tariff_id: str) -> bool:
    """Удаляет тариф по id."""
    all_tariffs = load_tariffs()
    tariffs = all_tariffs.get(resource, [])
    original_len = len(tariffs)
    
    all_tariffs[resource] = [t for t in tariffs if t.get("id") != tariff_id]
    
    if len(all_tariffs[resource]) < original_len:
        save_tariffs(all_tariffs)
        log.info("Tariff deleted", resource=resource, id=tariff_id)
        return True
    
    return False
'''

(core_energy_dir / 'tariff_store.py').write_text(tariff_store_content, encoding='utf-8', newline='\n')
print('✓ Создан: core/energy/tariff_store.py')

# config_store.py
config_store_content = '''"""Config Store — CRUD для energy_config.json (теги счётчиков)"""
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
'''

(core_energy_dir / 'config_store.py').write_text(config_store_content, encoding='utf-8', newline='\n')
print('✓ Создан: core/energy/config_store.py')

# calculator.py
calculator_content = '''"""Calculator — расчёт стоимости по интервальным тарифам"""
from datetime import date, datetime
from core.energy.tariff_store import get_tariff_for_date
from structlog import get_logger

log = get_logger()


def calculate_cost(consumption: float, resource: str, on_date: date | None = None) -> dict:
    """Рассчитывает стоимость потребления.
    
    Args:
        consumption: объём потребления (kWh, m3, Gcal)
        resource: electricity / water / heat
        on_date: дата для выбора тарифа (по умолчанию сегодня)
    
    Returns:
        {
            "consumption": float,
            "tariff_id": str | None,
            "price_per_unit": float,
            "total_cost": float,
            "currency": str,
            "tariff_note": str | None,
            "no_tariff": bool,  # True если тариф не найден
        }
    """
    if on_date is None:
        on_date = date.today()
    elif isinstance(on_date, datetime):
        on_date = on_date.date()
    
    tariff = get_tariff_for_date(resource, on_date)
    
    if tariff is None:
        log.warning("No tariff found", resource=resource, date=str(on_date))
        return {
            "consumption": consumption,
            "tariff_id": None,
            "price_per_unit": 0.0,
            "total_cost": 0.0,
            "currency": "RUB",
            "tariff_note": None,
            "no_tariff": True,
        }
    
    price = float(tariff.get("price_per_unit", 0.0))
    total = round(consumption * price, 2)
    
    return {
        "consumption": consumption,
        "tariff_id": tariff.get("id"),
        "price_per_unit": price,
        "total_cost": total,
        "currency": tariff.get("currency", "RUB"),
        "tariff_note": tariff.get("note"),
        "no_tariff": False,
    }


def calculate_period_cost(
    consumption_by_day: dict[str, float],
    resource: str,
) -> dict:
    """Рассчитывает стоимость за период с учётом смены тарифов.
    
    Args:
        consumption_by_day: {"2026-01-15": 1250.5, "2026-01-16": 1320.0, ...}
        resource: electricity / water / heat
    
    Returns:
        {
            "total_consumption": float,
            "total_cost": float,
            "days_count": int,
            "daily_breakdown": [{"date": str, "consumption": float, "cost": float, "tariff_id": str}],
            "tariff_changes": int,  # сколько раз менялся тариф
        }
    """
    daily_breakdown = []
    total_consumption = 0.0
    total_cost = 0.0
    prev_tariff_id = None
    tariff_changes = 0
    
    for date_str, consumption in sorted(consumption_by_day.items()):
        try:
            day = datetime.fromisoformat(date_str).date()
        except ValueError:
            continue
        
        result = calculate_cost(consumption, resource, day)
        daily_breakdown.append({
            "date": date_str,
            "consumption": consumption,
            "cost": result["total_cost"],
            "tariff_id": result.get("tariff_id"),
            "price_per_unit": result.get("price_per_unit", 0),
        })
        
        total_consumption += consumption
        total_cost += result["total_cost"]
        
        # Считаем смены тарифа
        current_tariff_id = result.get("tariff_id")
        if prev_tariff_id is not None and current_tariff_id != prev_tariff_id:
            tariff_changes += 1
        prev_tariff_id = current_tariff_id
    
    return {
        "total_consumption": round(total_consumption, 2),
        "total_cost": round(total_cost, 2),
        "days_count": len(daily_breakdown),
        "daily_breakdown": daily_breakdown,
        "tariff_changes": tariff_changes,
    }
'''

(core_energy_dir / 'calculator.py').write_text(calculator_content, encoding='utf-8', newline='\n')
print('✓ Создан: core/energy/calculator.py')

print()
print('=' * 60)
print('ШАГ 1 ЗАВЕРШЁН: core/energy/ создана')
print('=' * 60)
print('  • tariff_store.py — CRUD тарифов с интервалами')
print('  • config_store.py — CRUD тегов счётчиков')
print('  • calculator.py — расчёт стоимости (один день + период)')
print()
print('Следующий шаг: создаём modules/energy_* и api/routes/energy.py')
print('Запусти этот скрипт — потом скажи "core ok" — и пойдём дальше')