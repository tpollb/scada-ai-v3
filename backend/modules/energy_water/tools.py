"""Заглушка — возвращает 0"""

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
