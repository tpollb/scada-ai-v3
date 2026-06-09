"""Заглушка — возвращает 0"""

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
