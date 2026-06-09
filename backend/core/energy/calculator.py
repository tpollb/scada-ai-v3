"""Calculator — расчёт стоимости по интервальным тарифам"""
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
