"""Energy Water module — заглушка (счётчики не подключены)"""
from structlog import get_logger

__version__ = "1.0.0"
log = get_logger()


def on_load():
    log.info("Energy Water module loaded (stub)", version=__version__)
