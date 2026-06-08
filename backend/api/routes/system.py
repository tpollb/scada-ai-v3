"""System API — информация о системе и логи"""
from fastapi import APIRouter, HTTPException
from datetime import datetime
from structlog import get_logger
from pathlib import Path

log = get_logger()
router = APIRouter(prefix="/system", tags=["system"])

_last_health_check = {"timestamp": None, "duration_sec": None, "score": None}

def update_last_health_check(duration_sec: float, score: int | None):
    _last_health_check["timestamp"] = datetime.now().isoformat()
    _last_health_check["duration_sec"] = round(duration_sec, 2)
    _last_health_check["score"] = score


@router.get("/info")
async def system_info():
    from config.settings import settings
    from core.module_registry import get_registry
    from core.tool_executor import get_executor
    
    registry = get_registry()
    executor = get_executor()
    
    # === Проверка БД ===
    db_status = "unknown"
    try:
        from core.db import get_pool
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        db_status = "ok"
    except Exception as e:
        db_status = "error"
        log.warning("DB check failed", error=str(e))
    
    # === Проверка LLM ===
    llm_status = "unknown"
    try:
        from core.llm import get_provider
        provider = get_provider()
        if provider and getattr(provider, 'provider_name', None):
            llm_status = "ok"
        elif not settings.yandex_api_key:
            llm_status = "not_configured"
        else:
            llm_status = "error"
    except Exception as e:
        llm_status = "error"
        log.warning("LLM check failed", error=str(e))
    
    return {
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "modules": list(registry._modules.keys()),
        "tools_count": len(executor._tools),
        "tools_names": list(executor._tools.keys()),
        "db_host": settings.db_host,
        "db_status": db_status,
        "llm_model": settings.yandex_gpt_model,
        "llm_status": llm_status,
        "scada_url": settings.scada_base_url,
        "last_health_check": _last_health_check,
        "server_time": datetime.now().isoformat()
    }


@router.get("/logs/files")
async def list_log_files():
    from core.logger import system_logger
    files = system_logger.list_files()
    return {"count": len(files), "files": files}


@router.get("/logs/current")
async def get_current_logs(limit: int = 100, level: str | None = None):
    from core.logger import system_logger
    logs = system_logger.get_logs(limit=limit, level=level)
    return {"count": len(logs), "logs": logs, "source": "current", "file": system_logger.current_file.name}


@router.get("/logs/file/{filename}")
async def get_log_file(filename: str, limit: int = 1000):
    from core.logger import system_logger
    try:
        logs = system_logger.read_file(filename, limit=limit)
        return {"count": len(logs), "logs": logs, "source": "file", "file": filename}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Log file not found: {filename}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/logs/config")
async def logs_config():
    from core.logger import system_logger
    return {
        "logs_dir": str(system_logger.current_file.parent),
        "current_file": system_logger.current_file.name,
    }


@router.post("/logs/clear")
async def clear_logs():
    from core.logger import system_logger
    system_logger.clear()
    return {"status": "ok", "message": "Буфер очищен"}

@router.put("/logs/config")
async def update_logs_config(poll_interval_ms: int = 2000):
    """Update logs module settings"""
    from config.settings import settings
    
    # Update runtime value
    settings.log_poll_interval_ms = poll_interval_ms
    
    # Update .env
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        content = env_path.read_text(encoding="utf-8")
        if "LOG_POLL_INTERVAL_MS=" in content:
            import re
            content = re.sub(
                r"LOG_POLL_INTERVAL_MS=\d+",
                f"LOG_POLL_INTERVAL_MS={poll_interval_ms}",
                content
            )
        else:
            content = content.rstrip() + f"\nLOG_POLL_INTERVAL_MS={poll_interval_ms}\n"
        env_path.write_text(content, encoding="utf-8", newline="\n")
    
    log.info("Logs config updated", poll_interval_ms=poll_interval_ms)
    
    return {
        "status": "ok",
        "message": f"Интервал polling обновлён: {poll_interval_ms} мс",
        "restart_required": False,
        "config": {
            "poll_interval_ms": poll_interval_ms,
        }
    }

@router.put("/logs/config")
async def update_logs_config(poll_interval_ms: int = 2000):
    """Update logs module settings"""
    from config.settings import settings
    
    settings.log_poll_interval_ms = poll_interval_ms
    
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        content = env_path.read_text(encoding="utf-8")
        if "LOG_POLL_INTERVAL_MS=" in content:
            import re as _re
            content = _re.sub(
                r"LOG_POLL_INTERVAL_MS=\d+",
                f"LOG_POLL_INTERVAL_MS={poll_interval_ms}",
                content
            )
        else:
            content = content.rstrip() + f"\nLOG_POLL_INTERVAL_MS={poll_interval_ms}\n"
        env_path.write_text(content, encoding="utf-8", newline="\n")
    
    log.info("Logs config updated", poll_interval_ms=poll_interval_ms)
    
    return {
        "status": "ok",
        "message": f"Интервал polling обновлён: {poll_interval_ms} мс",
        "restart_required": False,
        "config": {"poll_interval_ms": poll_interval_ms},
    }
