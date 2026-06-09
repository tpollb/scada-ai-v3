"""Energy Electricity module — расчёт стоимости электроэнергии"""
from structlog import get_logger

__version__ = "1.0.0"
log = get_logger()


def on_load():
    """Вызывается при загрузке модуля"""
    log.info("Energy Electricity module loaded", version=__version__)
