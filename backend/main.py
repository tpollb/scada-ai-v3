"""SCADA.AI v3.0.0 — Main application"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from structlog import get_logger

from config.settings import settings
from core.logger import system_logger, install_structlog_bridge

log = get_logger()


# ============================================================================
# Фильтр для uvicorn access log — убирает спам от polling /system/logs
# ============================================================================
class AccessLogFilter(logging.Filter):
    """Фильтрует access log для polling endpoints"""
    def filter(self, record):
        if hasattr(record, 'args') and len(record.args) >= 3:
            _, method, path = record.args[:3]
            if path and '/system/logs' in path and method == 'GET':
                return False
        return True

logging.getLogger("uvicorn.access").addFilter(AccessLogFilter())


# Устанавливаем bridge ДО создания app — чтобы все логи шли в UI
install_structlog_bridge()


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info(f"Starting {settings.app_name} v{settings.app_version}")

    # Проверяем БД
    try:
        from core.db import get_pool
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        log.info("PostgreSQL connection OK", host=settings.db_host, port=settings.db_port)
    except Exception as e:
        log.error("PostgreSQL connection failed", error=str(e))
        log.warning("Backend will start, but health module will fail on DB queries")

    # Загружаем модули
    from core.module_registry import get_registry
    from core.tool_executor import get_executor

    registry = get_registry()
    registry.load_all(settings.enabled_modules_list)

    executor = get_executor()
    for tool in registry.get_all_tools():
        executor.register_tool(name=tool["name"], func=tool["function"], schema=tool)

    log.info(f"Loaded {len(registry._modules)} modules, {len(executor._tools)} tools")

    # Инициализируем LLM provider
    try:
        from core.llm import get_provider
        provider = get_provider()
        log.info("LLM provider ready", provider=provider.provider_name)
    except Exception as e:
        log.error("LLM provider failed to initialize", error=str(e))

    yield

    # Shutdown
    try:
        from core.db import close_pool
        await close_pool()
        from core.logger import system_logger
        system_logger.close()
        log.info("Database pool closed")
    except Exception as e:
        log.warning("Error closing database pool", error=str(e))

    log.info(f"{settings.app_name} stopped")


# ============================================================================
# Создаём FastAPI приложение
# ============================================================================
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "ok"
    }


@app.get("/health")
async def health():
    from core.module_registry import get_registry
    from core.tool_executor import get_executor
    registry = get_registry()
    return {
        "status": "ok",
        "modules": list(registry._modules.keys()),
        "tools": len(get_executor()._tools),
    }


@app.get("/debug/routes")
async def debug_routes():
    """Показывает все зарегистрированные роуты"""
    routes = []
    for route in app.routes:
        routes.append({
            "path": getattr(route, "path", None),
            "methods": list(getattr(route, "methods", []) or []),
            "name": getattr(route, "name", None),
        })
    return {"routes": routes}


# ============================================================================
# Подключаем роутеры
# ============================================================================
from api.routes import chat, config, health, system, docs  # noqa: E402

app.include_router(chat.router, tags=["chat"])
app.include_router(config.router, tags=["config"])
app.include_router(health.router)
app.include_router(system.router)
app.include_router(docs.router)

log.info("All routers registered")


if __name__ == "__main__":
    import uvicorn
    system_logger.info("Application starting", host=settings.host, port=settings.port)
    system_logger.info("Database configured", host=settings.db_host)
    system_logger.info("LLM configured", model=settings.yandex_gpt_model)
    
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=settings.debug)
