"""System API — информация для инфопанели сайдбара"""
from fastapi import APIRouter
from datetime import datetime
from structlog import get_logger
from pathlib import Path
import yaml

log = get_logger()
router = APIRouter(prefix="/system", tags=["system"])


# In-memory кэш последнего health-запроса (для отображения в сайдбаре)
_last_health_check = {"timestamp": None, "duration_sec": None, "score": None}


def update_last_health_check(duration_sec: float, score: int | None):
    """Вызывается из chat.py после каждого health-запроса"""
    _last_health_check["timestamp"] = datetime.now().isoformat()
    _last_health_check["duration_sec"] = round(duration_sec, 2)
    _last_health_check["score"] = score


@router.get("/info")
async def get_system_info():
    """Информация о системе для инфопанели"""
    from core.module_registry import get_registry
    from core.tool_executor import get_executor
    from core.db import get_pool
    from config.settings import settings
    
    registry = get_registry()
    executor = get_executor()
    
    # Проверяем статус БД
    db_status = "unknown"
    db_stats = None
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            # Проверяем живость
            await conn.fetchval("SELECT 1")
            # Считаем теги
            tags_count = await conn.fetchval("SELECT COUNT(*) FROM tags_dict")
            db_status = "ok"
            db_stats = {"tags_count": tags_count}
    except Exception as e:
        db_status = "error"
        log.warning("DB status check failed", error=str(e))
    
    # Проверяем статус LLM
    llm_status = "unknown"
    try:
        from core.llm import get_provider
        provider = get_provider()
        ok = await provider.health_check()
        llm_status = "ok" if ok else "error"
    except Exception:
        llm_status = "not_configured"
    
    # Список реальных возможностей (на основе загруженных модулей)
    capabilities = []
    
    if "health" in registry._modules:
        capabilities.extend([
            {"text": "покажи здоровье здания", "category": "health"},
            {"text": "какие аварии за сутки?", "category": "health"},
            {"text": "температура и влажность", "category": "health"},
            {"text": "битые датчики", "category": "health"},
            {"text": "топ аварий", "category": "health"},
        ])
    
    # Навигационные подсказки (всегда доступны)
    capabilities.extend([
        {"text": "открой конфигуратор", "category": "navigation", "action": "config"},
    ])
    
    return {
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "modules": list(registry._modules.keys()),
        "tools_count": len(executor._tools),
        "db_status": db_status,
        "db_stats": db_stats,
        "db_host": settings.db_host,
        "llm_status": llm_status,
        "llm_model": settings.yandex_gpt_model,
        "scada_url": settings.scada_base_url,
        "last_health_check": _last_health_check,
        "capabilities": capabilities,
        "server_time": datetime.now().isoformat(),
    }
