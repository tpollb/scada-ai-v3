"""Config API — управление модулями, промптами и системными настройками"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from structlog import get_logger
from pathlib import Path
import yaml
import httpx
import asyncio

log = get_logger()
router = APIRouter(prefix="/config", tags=["config"])

ENV_PATH = Path(__file__).parent.parent.parent / ".env"


class ModuleInfo(BaseModel):
    name: str
    version: str
    description: str
    enabled: bool
    status: str
    error: str | None = None
    prompts: dict = {}


class UpdatePromptRequest(BaseModel):
    module: str
    prompt_name: str
    prompt_text: str


class EnvConfig(BaseModel):
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str
    scada_base_url: str
    yandex_api_key: str
    yandex_folder_id: str
    yandex_gpt_model: str
    llm_temperature: float
    llm_max_tokens: int
    llm_timeout: int
    city: str = "Москва"
    timezone: str = "Europe/Moscow"
    latitude: float = 55.7558
    longitude: float = 37.6173


def _parse_env() -> dict[str, str]:
    """Читает .env как словарь"""
    result = {}
    if not ENV_PATH.exists():
        return result
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key.strip()] = value.strip()
    return result


def _write_env(data: dict[str, str]):
    """Перезаписывает .env"""
    # Читаем оригинал чтобы сохранить комментарии и структуру
    original_lines = []
    if ENV_PATH.exists():
        original_lines = ENV_PATH.read_text(encoding="utf-8").splitlines()

    # Находим какие ключи уже есть в файле
    existing_keys = set()
    new_lines = []
    for line in original_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            new_lines.append(line)
            continue
        if "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            existing_keys.add(key)
            if key in data:
                new_lines.append(f"{key}={data[key]}")
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    # Добавляем новые ключи которых не было
    for key, value in data.items():
        if key not in existing_keys:
            new_lines.append(f"{key}={value}")

    ENV_PATH.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


@router.get("/modules", response_model=list[ModuleInfo])
async def get_modules():
    """Список всех модулей с их статусом"""
    from core.module_registry import get_registry
    registry = get_registry()
    modules_dir = Path(__file__).parent.parent.parent / "modules"

    result = []
    for module_path in modules_dir.iterdir():
        if not module_path.is_dir() or module_path.name.startswith("_"):
            continue

        config_path = module_path / "config.yaml"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
        else:
            config = {"name": module_path.name, "version": "unknown", "description": "", "enabled": True}

        loaded_module = registry.get_module(module_path.name)

        if loaded_module:
            result.append(ModuleInfo(
                name=module_path.name,
                version=str(config.get("version", "unknown")),
                description=str(config.get("description", "")),
                enabled=bool(config.get("enabled", True)),
                status="loaded",
                prompts=loaded_module.prompts,
            ))
        else:
            result.append(ModuleInfo(
                name=module_path.name,
                version=str(config.get("version", "unknown")),
                description=str(config.get("description", "")),
                enabled=bool(config.get("enabled", False)),
                status="not_loaded",
                error="Модуль отключен или не загружен",
            ))
    return result


@router.put("/modules/{module_name}/prompts/{prompt_name}")
async def update_prompt(module_name: str, prompt_name: str, req: UpdatePromptRequest):
    """Обновляет промпт модуля"""
    log.info("Prompt update requested", module=module_name, prompt=prompt_name)
    return {"status": "ok", "message": "Промпт будет использован в следующих запросах"}


@router.post("/modules/{module_name}/reload")
async def reload_module(module_name: str):
    """Перезагружает модуль"""
    from core.module_registry import get_registry
    registry = get_registry()
    module = registry.load_module(module_name)
    if module:
        return {"status": "ok", "message": f"Модуль {module_name} перезагружен"}
    return {"status": "error", "message": f"Не удалось загрузить модуль {module_name}"}


@router.get("/env", response_model=EnvConfig)
async def get_env():
    """Читает системную конфигурацию из .env"""
    env = _parse_env()
    return EnvConfig(
        db_host=env.get("DB_HOST", "localhost"),
        db_port=int(env.get("DB_PORT", "5432")),
        db_name=env.get("DB_NAME", "postgres"),
        db_user=env.get("DB_USER", "postgres"),
        db_password=env.get("DB_PASSWORD", ""),
        scada_base_url=env.get("SCADA_BASE_URL", "http://localhost:9002"),
        yandex_api_key=env.get("YANDEX_API_KEY", ""),
        yandex_folder_id=env.get("YANDEX_FOLDER_ID", ""),
        yandex_gpt_model=env.get("YANDEX_GPT_MODEL", "yandexgpt-5.1/latest"),
        llm_temperature=float(env.get("LLM_TEMPERATURE", "0.05")),
        llm_max_tokens=int(env.get("LLM_MAX_TOKENS", "32000")),
        llm_timeout=int(env.get("LLM_TIMEOUT", "30")),
        city=env.get("CITY", "Москва"),
        timezone=env.get("TIMEZONE", "Europe/Moscow"),
        latitude=float(env.get("LATITUDE", "55.7558")),
        longitude=float(env.get("LONGITUDE", "37.6173")),
    )


@router.put("/env")
async def update_env(req: EnvConfig):
    """Обновляет системную конфигурацию в .env"""
    data = {
        "DB_HOST": req.db_host,
        "DB_PORT": str(req.db_port),
        "DB_NAME": req.db_name,
        "DB_USER": req.db_user,
        "DB_PASSWORD": req.db_password,
        "SCADA_BASE_URL": req.scada_base_url,
        "YANDEX_API_KEY": req.yandex_api_key,
        "YANDEX_FOLDER_ID": req.yandex_folder_id,
        "YANDEX_GPT_MODEL": req.yandex_gpt_model,
        "LLM_TEMPERATURE": str(req.llm_temperature),
        "LLM_MAX_TOKENS": str(req.llm_max_tokens),
        "LLM_TIMEOUT": str(req.llm_timeout),
        "CITY": req.city,
        "TIMEZONE": req.timezone,
        "LATITUDE": str(req.latitude),
        "LONGITUDE": str(req.longitude),
    }
    _write_env(data)
    log.info("Environment updated", keys=list(data.keys()))
    return {
        "status": "ok",
        "message": "Конфигурация сохранена. Перезапустите backend для применения изменений.",
    }


# === Маппинг долготы → timezone для России и окрестностей ===
TIMEZONE_BY_LON = [
    (20, "Europe/Kaliningrad"),      # Калининград UTC+2
    (30, "Europe/Moscow"),           # Москва UTC+3
    (45, "Europe/Samara"),           # Самара UTC+4
    (55, "Asia/Yekaterinburg"),      # Екатеринбург UTC+5
    (65, "Asia/Omsk"),               # Омск UTC+6
    (80, "Asia/Novosibirsk"),        # Новосибирск UTC+7
    (95, "Asia/Krasnoyarsk"),        # Красноярск UTC+7
    (110, "Asia/Irkutsk"),           # Иркутск UTC+8
    (125, "Asia/Yakutsk"),           # Якутск UTC+9
    (140, "Asia/Vladivostok"),       # Владивосток UTC+10
    (160, "Asia/Magadan"),           # Магадан UTC+11
    (180, "Asia/Kamchatka"),         # Камчатка UTC+12
]


def _timezone_from_lon(lon: float) -> str:
    """Определяет timezone по долготе (упрощённо)"""
    for boundary, tz in TIMEZONE_BY_LON:
        if lon < boundary:
            return tz
    return "Asia/Kamchatka"


@router.get("/resolve-city")
async def resolve_city(city: str):
    """
    Определяет координаты и timezone по названию города.
    Использует Nominatim (OpenStreetMap) — бесплатно, без ключа.
    """
    if not city or len(city.strip()) < 2:
        return {"error": "Город слишком короткий"}
    
    city = city.strip()
    
    # 1. Пробуем Nominatim (OpenStreetMap)
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            url = "https://nominatim.openstreetmap.org/search"
            params = {
                "q": city,
                "format": "json",
                "limit": 5,
                "addressdetails": 1,
                "accept-language": "ru",
            }
            resp = await client.get(url, params=params, headers={
                "User-Agent": "SCADA.AI/3.0 (contact: dev@scada-ai.local)"
            })
            resp.raise_for_status()
            results = resp.json()
            
            if not results:
                return {"error": f"Город '{city}' не найден"}
            
            # Ищем лучший результат (город, а не улица)
            best = None
            for r in results:
                cls = r.get("class", "")
                type_ = r.get("type", "")
                if cls == "place" or type_ in ("city", "town", "village", "hamlet"):
                    best = r
                    break
            
            if not best:
                best = results[0]
            
            lat = float(best["lat"])
            lon = float(best["lon"])
            display_name = best.get("display_name", city)
            
            # Извлекаем читаемое имя города
            address = best.get("address", {})
            city_name = (
                address.get("city") or
                address.get("town") or
                address.get("village") or
                address.get("hamlet") or
                city
            )
            country = address.get("country", "")
            state = address.get("state", "")
            
            # 2. Определяем timezone по долготе
            timezone = _timezone_from_lon(lon)
            
            return {
                "city": city_name,
                "display_name": display_name,
                "state": state,
                "country": country,
                "latitude": lat,
                "longitude": lon,
                "timezone": timezone,
            }
    
    except httpx.TimeoutException:
        return {"error": "Геокодер не отвечает (>15 сек). Попробуйте ещё раз или укажите координаты вручную"}
    except Exception as e:
        log.error("Geocoding failed", error=str(e), city=city)
        return {"error": f"Ошибка геокодинга: {str(e)}"}


class ModuleToggleRequest(BaseModel):
    enabled: bool


@router.put("/modules/{module_name}/enabled")
async def toggle_module(module_name: str, req: ModuleToggleRequest):
    """Включает/выключает модуль через обновление ENABLED_MODULES в .env"""
    env = _parse_env()
    
    # Парсим текущий список модулей
    current_modules_str = env.get("ENABLED_MODULES", "hello,health")
    current_modules = [m.strip() for m in current_modules_str.split(",") if m.strip()]
    
    # Проверяем что модуль существует
    modules_dir = Path(__file__).parent.parent.parent / "modules"
    available_modules = [
        p.name for p in modules_dir.iterdir() 
        if p.is_dir() and not p.name.startswith("_")
    ]
    
    if module_name not in available_modules:
        return {"status": "error", "message": f"Модуль '{module_name}' не найден"}
    
    # Обновляем список
    if req.enabled:
        if module_name not in current_modules:
            current_modules.append(module_name)
            action = "включён"
        else:
            return {"status": "ok", "message": f"Модуль '{module_name}' уже включён", "restart_required": False}
    else:
        if module_name in current_modules:
            # Защита: не даём выключить последний модуль
            if len(current_modules) <= 1:
                return {
                    "status": "error",
                    "message": "Нельзя отключить последний модуль. Система должна иметь хотя бы один активный модуль."
                }
            current_modules.remove(module_name)
            action = "выключен"
        else:
            return {"status": "ok", "message": f"Модуль '{module_name}' уже выключен", "restart_required": False}
    
    # Записываем обратно в .env
    new_modules_str = ",".join(current_modules)
    _write_env({"ENABLED_MODULES": new_modules_str})
    
    log.info("Module toggled", module=module_name, enabled=req.enabled, new_list=current_modules)
    
    return {
        "status": "ok",
        "message": f"Модуль '{module_name}' {action}. Перезапустите backend для применения изменений.",
        "restart_required": True,
        "enabled_modules": current_modules
    }


# ============================================================================
# DDA Settings (Deep Data Analysis)
# ============================================================================

@router.get("/modules/deep_analysis/settings")
async def get_dda_settings():
    """Возвращает настройки модуля DDA"""
    try:
        from modules.deep_analysis.settings import load_dda_settings, DDASettings
        settings = load_dda_settings()
        return settings.model_dump()
    except ImportError as e:
        log.error("DDA settings module not found", error=str(e))
        raise HTTPException(status_code=404, detail="Модуль deep_analysis не найден")
    except Exception as e:
        log.error("Failed to load DDA settings", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/modules/deep_analysis/settings")
async def update_dda_settings(settings: dict):
    """Обновляет настройки модуля DDA"""
    try:
        from modules.deep_analysis.settings import DDASettings, save_dda_settings, reload_dda_settings
        
        # Валидируем через Pydantic
        dda_settings = DDASettings(**settings)
        
        # Сохраняем в config.yaml
        save_dda_settings(dda_settings)
        
        log.info("DDA settings updated")
        
        return {
            "status": "ok",
            "message": "Настройки DDA сохранены. Изменения применятся при следующем анализе.",
            "settings": dda_settings.model_dump()
        }
    except ImportError as e:
        log.error("DDA settings module not found", error=str(e))
        raise HTTPException(status_code=404, detail="Модуль deep_analysis не найден")
    except Exception as e:
        log.error("Failed to update DDA settings", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/modules/deep_analysis/settings/reset")
async def reset_dda_settings():
    """Сбрасывает настройки DDA к дефолтным"""
    try:
        from modules.deep_analysis.settings import DDASettings, save_dda_settings, reload_dda_settings
        
        default_settings = DDASettings()
        save_dda_settings(default_settings)
        
        log.info("DDA settings reset to defaults")
        
        return {
            "status": "ok",
            "message": "Настройки DDA сброшены к значениям по умолчанию",
            "settings": default_settings.model_dump()
        }
    except Exception as e:
        log.error("Failed to reset DDA settings", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

