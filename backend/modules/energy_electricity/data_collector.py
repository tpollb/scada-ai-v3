"""Data Collector — читает значения тегов счётчиков из БД"""
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
