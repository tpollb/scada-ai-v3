"""Health module — анализ здоровья системы по историческим данным"""
from structlog import get_logger

__version__ = "1.0.0"
log = get_logger()


def on_load():
    """Вызывается при загрузке модуля"""
    log.info("Health module loaded", version=__version__)
