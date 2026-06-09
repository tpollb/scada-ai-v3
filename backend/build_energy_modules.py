from pathlib import Path
import json

print('=== build_energy_modules.py (Шаг 2) ===')
print()

# ============================================================================
# 1. modules/energy_electricity/ — реальный модуль
# ============================================================================
elec_dir = Path('modules/energy_electricity')
elec_dir.mkdir(parents=True, exist_ok=True)

# __init__.py
(elec_dir / '__init__.py').write_text('''"""Energy Electricity module — расчёт стоимости электроэнергии"""
from structlog import get_logger

__version__ = "1.0.0"
log = get_logger()


def on_load():
    """Вызывается при загрузке модуля"""
    log.info("Energy Electricity module loaded", version=__version__)
''', encoding='utf-8', newline='\n')

# config.yaml
(elec_dir / 'config.yaml').write_text('''name: energy_electricity
version: 1.0.0
description: Расчёт стоимости электроэнергии на основе тегов ЛЭРС
enabled: true

# Единицы измерения
unit: kWh
currency: RUB

# Периоды анализа
default_periods:
  current_month: true
  last_month: true
''', encoding='utf-8', newline='\n')

# data_collector.py
(elec_dir / 'data_collector.py').write_text('''"""Data Collector — читает значения тегов счётчиков из БД"""
from datetime import date, datetime
from structlog import get_logger
from core.db import fetch
from core.energy.config_store import get_meters, is_resource_enabled

log = get_logger()


async def get_tag_value(tag_name: str) -> float | None:
    """Читает последнее значение тега из БД.
    
    Args:
        tag_name: полное имя тега (например "LERS.electricity meter current month 1")
    
    Returns:
        Значение тега или None если тег не найден / нет данных
    """
    try:
        # Сначала находим tag_id по имени
        tag_rows = await fetch(
            "SELECT tag_id FROM tags_dict WHERE tag_name = $1 LIMIT 1",
            tag_name
        )
        
        if not tag_rows:
            log.warning("Tag not found in DB", tag_name=tag_name)
            return None
        
        tag_id = tag_rows[0]["tag_id"]
        
        # Читаем последнее значение
        value_rows = await fetch(
            """
            SELECT value, date_created
            FROM tags_value
            WHERE tag_id = $1
            ORDER BY date_created DESC
            LIMIT 1
            """,
            tag_id
        )
        
        if not value_rows:
            log.warning("No values found for tag", tag_name=tag_name, tag_id=tag_id)
            return None
        
        value = value_rows[0]["value"]
        if value is None:
            return None
        
        try:
            return float(value)
        except (ValueError, TypeError):
            log.warning("Invalid tag value", tag_name=tag_name, value=value)
            return None
            
    except Exception as e:
        log.error("Failed to read tag value", tag_name=tag_name, error=str(e))
        return None


async def collect_electricity_consumption() -> dict:
    """Собирает потребление электрики по всем счётчикам.
    
    Returns:
        {
            "resource": "electricity",
            "enabled": True,
            "meters": [
                {
                    "id": "input_1",
                    "name": "Первый ввод",
                    "current_month": {"kwh": 1234.5, "tag": "...", "error": null},
                    "last_month": {"kwh": 1150.0, "tag": "...", "error": null},
                },
                ...
            ],
            "total_current": float | None,
            "total_last": float | None,
            "errors": [str],
        }
    """
    if not is_resource_enabled("electricity"):
        return {
            "resource": "electricity",
            "enabled": False,
            "meters": [],
            "total_current": None,
            "total_last": None,
            "errors": [],
        }
    
    meters_config = get_meters("electricity")
    meters_data = []
    total_current = 0.0
    total_last = 0.0
    errors = []
    has_current_data = False
    has_last_data = False
    
    for meter in meters_config:
        meter_id = meter.get("id", "unknown")
        meter_name = meter.get("name", meter_id)
        tag_current = meter.get("tag_current")
        tag_last = meter.get("tag_last")
        
        # Читаем текущий месяц
        current_data = {"kwh": None, "tag": tag_current, "error": None}
        if tag_current:
            value = await get_tag_value(tag_current)
            if value is not None:
                current_data["kwh"] = round(value, 2)
                total_current += value
                has_current_data = True
            else:
                current_data["error"] = f"Тег не найден или нет данных: {tag_current}"
                errors.append(f"{meter_name}: {current_data['error']}")
        else:
            current_data["error"] = "Тег current_month не настроен"
        
        # Читаем прошлый месяц
        last_data = {"kwh": None, "tag": tag_last, "error": None}
        if tag_last:
            value = await get_tag_value(tag_last)
            if value is not None:
                last_data["kwh"] = round(value, 2)
                total_last += value
                has_last_data = True
            else:
                last_data["error"] = f"Тег не найден или нет данных: {tag_last}"
                errors.append(f"{meter_name} (прошлый): {last_data['error']}")
        else:
            last_data["error"] = "Тег last_month не настроен"
        
        meters_data.append({
            "id": meter_id,
            "name": meter_name,
            "current_month": current_data,
            "last_month": last_data,
        })
    
    log.info("Electricity consumption collected",
             meters=len(meters_data),
             total_current=total_current if has_current_data else None,
             total_last=total_last if has_last_data else None,
             errors=len(errors))
    
    return {
        "resource": "electricity",
        "enabled": True,
        "meters": meters_data,
        "total_current": round(total_current, 2) if has_current_data else None,
        "total_last": round(total_last, 2) if has_last_data else None,
        "errors": errors,
    }
''', encoding='utf-8', newline='\n')

# tools.py
(elec_dir / 'tools.py').write_text('''"""Tools для LLM — расчёт стоимости электроэнергии"""
from core.energy.calculator import calculate_cost
from modules.energy_electricity.data_collector import collect_electricity_consumption
from structlog import get_logger

log = get_logger()


async def get_electricity_consumption() -> dict:
    """Возвращает потребление электрики (текущий + прошлый месяц).
    
    Для tool calling LLM.
    """
    return await collect_electricity_consumption()


async def calculate_electricity_cost() -> dict:
    """Рассчитывает стоимость электроэнергии за текущий и прошлый месяц.
    
    Возвращает:
        {
            "current_month": {
                "consumption_kwh": float | None,
                "cost_rub": float | None,
                "tariff_id": str | None,
                "price_per_kwh": float,
                "error": str | None,
            },
            "last_month": { ... },
            "comparison": {
                "delta_kwh": float | None,
                "delta_cost_rub": float | None,
                "delta_percent": float | None,
            },
            "errors": [str],
        }
    """
    consumption = await collect_electricity_consumption()
    
    if not consumption.get("enabled"):
        return {
            "current_month": None,
            "last_month": None,
            "comparison": None,
            "errors": ["Модуль electricity отключен"],
        }
    
    errors = list(consumption.get("errors", []))
    
    # Текущий месяц
    current_result = {
        "consumption_kwh": None,
        "cost_rub": None,
        "tariff_id": None,
        "price_per_kwh": 0.0,
        "error": None,
    }
    if consumption["total_current"] is not None:
        calc = calculate_cost(consumption["total_current"], "electricity")
        if calc.get("no_tariff"):
            current_result["error"] = "Не найден активный тариф на текущую дату"
            errors.append(current_result["error"])
        else:
            current_result["consumption_kwh"] = calc["consumption"]
            current_result["cost_rub"] = calc["total_cost"]
            current_result["tariff_id"] = calc["tariff_id"]
            current_result["price_per_kwh"] = calc["price_per_unit"]
    else:
        current_result["error"] = "Нет данных о потреблении за текущий месяц"
    
    # Прошлый месяц (используем тариф на 1-е число прошлого месяца)
    last_result = {
        "consumption_kwh": None,
        "cost_rub": None,
        "tariff_id": None,
        "price_per_kwh": 0.0,
        "error": None,
    }
    if consumption["total_last"] is not None:
        # Берём дату "месяц назад"
        from datetime import date, timedelta
        today = date.today()
        # Первый день прошлого месяца
        first_of_this_month = today.replace(day=1)
        last_month_date = (first_of_this_month - timedelta(days=1)).replace(day=1)
        
        calc = calculate_cost(consumption["total_last"], "electricity", last_month_date)
        if calc.get("no_tariff"):
            last_result["error"] = f"Не найден тариф на {last_month_date}"
            errors.append(last_result["error"])
        else:
            last_result["consumption_kwh"] = calc["consumption"]
            last_result["cost_rub"] = calc["total_cost"]
            last_result["tariff_id"] = calc["tariff_id"]
            last_result["price_per_kwh"] = calc["price_per_unit"]
    else:
        last_result["error"] = "Нет данных о потреблении за прошлый месяц"
    
    # Сравнение
    comparison = {
        "delta_kwh": None,
        "delta_cost_rub": None,
        "delta_percent": None,
    }
    if current_result["consumption_kwh"] is not None and last_result["consumption_kwh"] is not None:
        delta = current_result["consumption_kwh"] - last_result["consumption_kwh"]
        comparison["delta_kwh"] = round(delta, 2)
        if last_result["consumption_kwh"] > 0:
            comparison["delta_percent"] = round(delta / last_result["consumption_kwh"] * 100, 1)
    
    if current_result["cost_rub"] is not None and last_result["cost_rub"] is not None:
        comparison["delta_cost_rub"] = round(current_result["cost_rub"] - last_result["cost_rub"], 2)
    
    return {
        "current_month": current_result,
        "last_month": last_result,
        "comparison": comparison,
        "errors": errors,
    }


# Tools registration для ModuleRegistry
TOOLS = [
    {
        "name": "get_electricity_consumption",
        "function": get_electricity_consumption,
        "description": "Возвращает потребление электроэнергии за текущий и прошлый месяц (в kWh) по всем счётчикам. Используй когда пользователь спрашивает 'сколько потратили электричества', 'потребление электрики'.",
        "parameters": {
            "type": "object",
            "properties": {},
        }
    },
    {
        "name": "calculate_electricity_cost",
        "function": calculate_electricity_cost,
        "description": "Рассчитывает стоимость электроэнергии за текущий и прошлый месяц с учётом тарифов. Возвращает сумму в рублях, тариф и сравнение периодов. Используй когда пользователь спрашивает 'сколько денег на электричество', 'стоимость электроэнергии', 'бабло за свет'.",
        "parameters": {
            "type": "object",
            "properties": {},
        }
    },
]
''', encoding='utf-8', newline='\n')

# prompts.py
(elec_dir / 'prompts.py').write_text('''"""Промпты для работы с модулем электроэнергии"""

ENERGY_ELECTRICITY_SYSTEM_PROMPT = """Ты — AI-ассистент для оператора SCADA-системы.
У тебя есть доступ к tools для работы с данными об электроэнергии.

Когда пользователь спрашивает про электричество / деньги / стоимость:
1. Вызови tool calculate_electricity_cost()
2. Используй возвращённые данные для ответа
3. Отвечай кратко на русском языке
4. Если данные недоступжны — объясни почему (нет тарифа, нет счётчиков)

Пример ответа:
"За текущий месяц потребление составило 15 230 кВт·ч, стоимость — 83 765 рублей по тарифу 5.50 руб/кВт·ч. 
По сравнению с прошлым месяцем расход вырос на 8% (+1 120 кВт·ч)."
"""
''', encoding='utf-8', newline='\n')

print('✓ Создан: modules/energy_electricity/')
print('  • __init__.py, config.yaml')
print('  • data_collector.py — чтение тегов ЛЭРС из БД')
print('  • tools.py — get_electricity_consumption, calculate_electricity_cost')
print('  • prompts.py — ENERGY_ELECTRICITY_SYSTEM_PROMPT')

# ============================================================================
# 2. modules/energy_water/ — заглушка
# ============================================================================
water_dir = Path('modules/energy_water')
water_dir.mkdir(parents=True, exist_ok=True)

(water_dir / '__init__.py').write_text('''"""Energy Water module — заглушка (счётчики не подключены)"""
from structlog import get_logger

__version__ = "1.0.0"
log = get_logger()


def on_load():
    log.info("Energy Water module loaded (stub)", version=__version__)
''', encoding='utf-8', newline='\n')

(water_dir / 'config.yaml').write_text('''name: energy_water
version: 1.0.0
description: Учёт водопотребления (счётчики не подключены)
enabled: false

unit: m3
currency: RUB
''', encoding='utf-8', newline='\n')

(water_dir / 'tools.py').write_text('''"""Заглушка — возвращает 0"""

async def get_water_consumption() -> dict:
    return {
        "resource": "water",
        "enabled": False,
        "meters": [],
        "total_current": None,
        "total_last": None,
        "errors": ["Счётчики воды не подключены"],
    }


async def calculate_water_cost() -> dict:
    return {
        "current_month": None,
        "last_month": None,
        "comparison": None,
        "errors": ["Счётчики воды не подключены"],
    }


TOOLS = [
    {
        "name": "get_water_consumption",
        "function": get_water_consumption,
        "description": "Возвращает потребление воды. Сейчас не доступно (счётчики не подключены).",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "calculate_water_cost",
        "function": calculate_water_cost,
        "description": "Рассчитывает стоимость водопотребления. Сейчас не доступно.",
        "parameters": {"type": "object", "properties": {}},
    },
]
''', encoding='utf-8', newline='\n')

(water_dir / 'prompts.py').write_text('# Заглушка\n', encoding='utf-8')

print('✓ Создан: modules/energy_water/ (заглушка, enabled=false)')

# ============================================================================
# 3. modules/energy_heat/ — заглушка
# ============================================================================
heat_dir = Path('modules/energy_heat')
heat_dir.mkdir(parents=True, exist_ok=True)

(heat_dir / '__init__.py').write_text('''"""Energy Heat module — заглушка (счётчики не подключены)"""
from structlog import get_logger

__version__ = "1.0.0"
log = get_logger()


def on_load():
    log.info("Energy Heat module loaded (stub)", version=__version__)
''', encoding='utf-8', newline='\n')

(heat_dir / 'config.yaml').write_text('''name: energy_heat
version: 1.0.0
description: Учёт теплопотребления (счётчики не подключены)
enabled: false

unit: Gcal
currency: RUB
''', encoding='utf-8', newline='\n')

(heat_dir / 'tools.py').write_text('''"""Заглушка — возвращает 0"""

async def get_heat_consumption() -> dict:
    return {
        "resource": "heat",
        "enabled": False,
        "meters": [],
        "total_current": None,
        "total_last": None,
        "errors": ["Счётчики тепла не подключены"],
    }


async def calculate_heat_cost() -> dict:
    return {
        "current_month": None,
        "last_month": None,
        "comparison": None,
        "errors": ["Счётчики тепла не подключены"],
    }


TOOLS = [
    {
        "name": "get_heat_consumption",
        "function": get_heat_consumption,
        "description": "Возвращает потребление тепла. Сейчас не доступно.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "calculate_heat_cost",
        "function": calculate_heat_cost,
        "description": "Рассчитывает стоимость теплопотребления. Сейчас не доступно.",
        "parameters": {"type": "object", "properties": {}},
    },
]
''', encoding='utf-8', newline='\n')

(heat_dir / 'prompts.py').write_text('# Заглушка\n', encoding='utf-8')

print('✓ Создан: modules/energy_heat/ (заглушка, enabled=false)')

# ============================================================================
# 4. Дефолтные конфиги (data/)
# ============================================================================
data_dir = Path('data')
data_dir.mkdir(parents=True, exist_ok=True)

# tariffs.json
tariffs_file = data_dir / 'tariffs.json'
if not tariffs_file.exists():
    tariffs_file.write_text(json.dumps({
        "electricity": [
            {
                "id": "tariff_001",
                "start_date": "2025-01-01",
                "end_date": "2026-02-01",
                "price_per_unit": 5.50,
                "currency": "RUB",
                "note": "Тариф 2025 года",
            },
            {
                "id": "tariff_002",
                "start_date": "2026-02-01",
                "end_date": None,
                "price_per_unit": 6.20,
                "currency": "RUB",
                "note": "Текущий тариф 2026",
            },
        ],
        "water": [],
        "heat": [],
    }, indent=2, ensure_ascii=False), encoding='utf-8', newline='\n')
    print('✓ Создан: data/tariffs.json (с интервальными тарифами)')
else:
    print('ℹ data/tariffs.json уже существует')

# energy_config.json
config_file = data_dir / 'energy_config.json'
if not config_file.exists():
    config_file.write_text(json.dumps({
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
    }, indent=2, ensure_ascii=False), encoding='utf-8', newline='\n')
    print('✓ Создан: data/energy_config.json (дефолтные теги ЛЭРС)')
else:
    print('ℹ data/energy_config.json уже существует')

print()
print('=' * 60)
print('ШАГ 2 ЗАВЕРШЁН')
print('=' * 60)
print()
print('Создано:')
print('  ✓ modules/energy_electricity/ — полный модуль')
print('    - data_collector.py: читает теги ЛЭРС из БД')
print('    - tools.py: 2 tools для LLM')
print('    - prompts.py: системный промпт')
print()
print('  ✓ modules/energy_water/ — заглушка (enabled=false)')
print('  ✓ modules/energy_heat/ — заглушка (enabled=false)')
print()
print('  ✓ data/tariffs.json — интервальные тарифы')
print('    - tariff_001: 2025-01-01 → 2026-02-01 (5.50 руб/кВт·ч)')
print('    - tariff_002: 2026-02-01 → ∞ (6.20 руб/кВт·ч)')
print()
print('  ✓ data/energy_config.json — дефолтные теги ЛЭРС')
print('    - input_1: current month 1 + last month 1')
print('    - input_2: current month 2 + last month 2')
print()
print('Следующий шаг: api/routes/energy.py + регистрация в main.py')
print('Проверь файлы и скажи "modules ok" — пойдём дальше')