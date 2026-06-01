"""SCADA.AI v3.0.0 — Main application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from structlog import get_logger

from config.settings import settings

log = get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info(f"🚀 Starting {settings.app_name} v{settings.app_version}")

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
    registry.load_all(settings.enabled_modules)

    executor = get_executor()
    for tool in registry.get_all_tools():
        executor.register_tool(name=tool["name"], func=tool["function"], schema=tool)

    log.info(f"✅ Loaded {len(registry._modules)} modules, {len(executor._tools)} tools")

    # Инициализируем LLM provider (чтобы увидеть ошибки сразу)
    try:
        from core.llm import get_provider
        provider = get_provider()
        log.info(f"✅ LLM provider ready", provider=provider.provider_name)
    except Exception as e:
        log.error("❌ LLM provider failed to initialize", error=str(e))

    yield

    # Shutdown
    try:
        from core.db import close_pool
        await close_pool()
    except Exception:
        pass
    log.info("👋 Shutting down")


app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)

# CORS — разрешаем всё для разработки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Базовые эндпоинты
# ============================================================================
@app.get("/")
async def root():
    return {"name": settings.app_name, "version": settings.app_version, "status": "ok"}


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
    """Показывает все зарегистрированные роуты — полезно для дебага"""
    routes = []
    for route in app.routes:
        routes.append({
            "path": getattr(route, "path", None),
            "methods": list(getattr(route, "methods", []) or []),
            "name": getattr(route, "name", None),
        })
    return {"routes": routes}


# ============================================================================
# ВАЖНО: подключаем роутеры ПОСЛЕ определения базовых эндпоинтов
# ============================================================================
from api.routes import chat, config, health, system  # noqa: E402

app.include_router(chat.router, tags=["chat"])
app.include_router(config.router, tags=["config"])
app.include_router(health.router)
app.include_router(system.router)

log.info("✅ Chat router registered at /chat")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=settings.debug)
