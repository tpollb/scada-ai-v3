"""SCADA.AI v3.0.0 — Main application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from structlog import get_logger

from config.settings import settings
from core.module_registry import get_registry
from core.tool_executor import get_executor

log = get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown"""
    log.info(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    
    # Load modules
    registry = get_registry()
    registry.load_all(settings.enabled_modules)
    
    # Register tools
    executor = get_executor()
    for tool in registry.get_all_tools():
        executor.register_tool(
            name=tool["name"],
            func=tool["function"],
            schema=tool
        )
    
    log.info(f"✅ Loaded {len(registry._modules)} modules, {len(executor._tools)} tools")
    
    yield
    
    log.info("👋 Shutting down")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan
)

# CORS
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
    registry = get_registry()
    return {
        "status": "ok",
        "modules": list(registry._modules.keys()),
        "tools": len(get_executor()._tools)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
