"""Локализация статусов и severity для модуля health"""

# Статусы системы и индекса жизнеобеспечения
STATUS_RU = {
    "EXCELLENT": "Отлично",
    "GOOD": "Хорошо",
    "WARNING": "Внимание",
    "CRITICAL": "Критично",
    "NO_DATA": "Нет данных",
    "UNKNOWN": "Неизвестно",
}

# Severity в issues
SEVERITY_RU = {
    "critical": "Критический",
    "major": "Высокий",
    "warning": "Средний",
    "info": "Низкий",
}

# Приоритеты аварий (by_priority ключи)
PRIORITY_RU = {
    "high": "Высокий",
    "medium": "Средний",
    "low": "Низкий",
}

# Подписи параметров жизнеобеспечения
PARAM_LABELS_RU = {
    "co2": "CO2",
    "temperature": "Температура",
    "voc": "VOC",
    "humidity": "Влажность",
    "pressure": "Давление",
}


def translate_status(value: str) -> str:
    """Переводит status в русский. Возвращает оригинал если нет в словаре."""
    if not value:
        return "-"
    return STATUS_RU.get(value.upper(), value)


def translate_severity(value: str) -> str:
    """Переводит severity в русский. Возвращает оригинал если нет в словаре."""
    if not value:
        return "-"
    return SEVERITY_RU.get(value.lower(), value)


def translate_priority(value: str) -> str:
    """Переводит priority в русский. Возвращает оригинал если нет в словаре."""
    if not value:
        return "-"
    return PRIORITY_RU.get(value.lower(), value)
