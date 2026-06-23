"""Deep Data Analysis — хирургический анализ тегов SCADA"""
from structlog import get_logger

__version__ = "0.1.0"
log = get_logger()


def on_load():
    """Вызывается при загрузке модуля"""
    log.info("Deep Analysis module loaded", version=__version__)
