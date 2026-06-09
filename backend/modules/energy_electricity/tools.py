"""Tools для LLM — расчёт стоимости электроэнергии"""
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
