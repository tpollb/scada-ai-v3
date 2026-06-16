"""Analytics module — тренды, корреляции, рекомендации"""
from structlog import get_logger

__version__ = "1.0.0"
log = get_logger()


def on_load():
    """Вызывается при загрузке модуля"""
    log.info("Analytics module loaded", version=__version__)
