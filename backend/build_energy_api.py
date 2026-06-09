from pathlib import Path

print('=== build_energy_api.py (Шаг 3) ===')
print()

# ============================================================================
# 1. Создаём api/routes/energy.py
# ============================================================================
energy_route_content = '''"""Energy API — endpoints для модуля энергоучёта"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import date
from structlog import get_logger

from core.energy.tariff_store import (
    load_tariffs, add_tariff, update_tariff, delete_tariff, get_active_tariffs
)
from core.energy.config_store import load_config, save_config, get_resource_config
from core.energy.calculator import calculate_cost
from modules.energy_electricity.data_collector import collect_electricity_consumption

log = get_logger()
router = APIRouter(prefix="/energy", tags=["energy"])


# ============================================================================
# Pydantic models
# ============================================================================

class TariffCreate(BaseModel):
    resource: str  # electricity / water / heat
    start_date: str  # ISO format: 2025-01-01
    end_date: str | None = None  # null = бессрочный
    price_per_unit: float
    currency: str = "RUB"
    note: str | None = None


class TariffUpdate(BaseModel):
    start_date: str | None = None
    end_date: str | None = None
    price_per_unit: float | None = None
    currency: str | None = None
    note: str | None = None


class MeterConfig(BaseModel):
    id: str
    name: str
    tag_current: str
    tag_last: str


class ResourceConfigUpdate(BaseModel):
    enabled: bool | None = None
    unit: str | None = None
    meters: list[MeterConfig] | None = None


# ============================================================================
# Summary endpoints
# ============================================================================

@router.get("/summary")
async def get_energy_summary():
    """Сводка по всем ресурсам: текущий + прошлый месяц + стоимость"""
    result = {
        "electricity": None,
        "water": None,
        "heat": None,
        "total_cost_current": 0.0,
        "total_cost_last": 0.0,
        "errors": [],
    }
    
    # Электричество
    try:
        from modules.energy_electricity.tools import calculate_electricity_cost
        elec_data = await calculate_electricity_cost()
        result["electricity"] = elec_data
        if elec_data.get("current_month", {}).get("cost_rub"):
            result["total_cost_current"] += elec_data["current_month"]["cost_rub"]
        if elec_data.get("last_month", {}).get("cost_rub"):
            result["total_cost_last"] += elec_data["last_month"]["cost_rub"]
        result["errors"].extend(elec_data.get("errors", []))
    except Exception as e:
        log.error("Failed to get electricity data", error=str(e))
        result["errors"].append(f"electricity: {str(e)}")
    
    # Вода (заглушка)
    try:
        from modules.energy_water.tools import calculate_water_cost
        water_data = await calculate_water_cost()
        result["water"] = water_data
        result["errors"].extend(water_data.get("errors", []))
    except Exception as e:
        log.error("Failed to get water data", error=str(e))
    
    # Тепло (заглушка)
    try:
        from modules.energy_heat.tools import calculate_heat_cost
        heat_data = await calculate_heat_cost()
        result["heat"] = heat_data
        result["errors"].extend(heat_data.get("errors", []))
    except Exception as e:
        log.error("Failed to get heat data", error=str(e))
    
    result["total_cost_current"] = round(result["total_cost_current"], 2)
    result["total_cost_last"] = round(result["total_cost_last"], 2)
    
    return result


# ============================================================================
# Tariffs CRUD
# ============================================================================

@router.get("/tariffs")
async def list_tariffs():
    """Список всех тарифов по ресурсам"""
    return load_tariffs()


@router.get("/tariffs/{resource}")
async def list_resource_tariffs(resource: str):
    """Тарифы конкретного ресурса"""
    tariffs = load_tariffs()
    if resource not in tariffs:
        raise HTTPException(status_code=404, detail=f"Resource '{resource}' not found")
    return {"resource": resource, "tariffs": tariffs[resource]}


@router.get("/tariffs/{resource}/active")
async def get_active_tariffs_for_resource(resource: str, on_date: str | None = None):
    """Активные тарифы на указанную дату"""
    try:
        check_date = date.fromisoformat(on_date) if on_date else date.today()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format (use YYYY-MM-DD)")
    
    active = get_active_tariffs(resource, check_date)
    return {
        "resource": resource,
        "date": str(check_date),
        "active_tariffs": active,
    }


@router.post("/tariffs")
async def create_tariff(req: TariffCreate):
    """Создать новый тариф"""
    tariff_data = {
        "start_date": req.start_date,
        "end_date": req.end_date,
        "price_per_unit": req.price_per_unit,
        "currency": req.currency,
        "note": req.note,
    }
    
    created = add_tariff(req.resource, tariff_data)
    log.info("Tariff created via API", resource=req.resource, id=created["id"])
    
    return {
        "status": "ok",
        "message": f"Тариф создан: {created['id']}",
        "tariff": created,
    }


@router.put("/tariffs/{resource}/{tariff_id}")
async def update_existing_tariff(resource: str, tariff_id: str, req: TariffUpdate):
    """Обновить тариф"""
    updates = {k: v for k, v in req.dict().items() if v is not None}
    
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    success = update_tariff(resource, tariff_id, updates)
    if not success:
        raise HTTPException(status_code=404, detail=f"Tariff '{tariff_id}' not found in '{resource}'")
    
    log.info("Tariff updated via API", resource=resource, id=tariff_id)
    return {
        "status": "ok",
        "message": f"Тариф {tariff_id} обновлён",
    }


@router.delete("/tariffs/{resource}/{tariff_id}")
async def delete_existing_tariff(resource: str, tariff_id: str):
    """Удалить тариф"""
    success = delete_tariff(resource, tariff_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Tariff '{tariff_id}' not found in '{resource}'")
    
    log.info("Tariff deleted via API", resource=resource, id=tariff_id)
    return {
        "status": "ok",
        "message": f"Тариф {tariff_id} удалён",
    }


# ============================================================================
# Config CRUD (теги счётчиков)
# ============================================================================

@router.get("/config")
async def get_energy_config():
    """Полный конфиг энергоучёта"""
    return load_config()


@router.get("/config/{resource}")
async def get_resource_config_endpoint(resource: str):
    """Конфиг конкретного ресурса"""
    config = get_resource_config(resource)
    return {"resource": resource, "config": config}


@router.put("/config/{resource}")
async def update_resource_config_endpoint(resource: str, req: ResourceConfigUpdate):
    """Обновить конфиг ресурса (enabled, unit, meters)"""
    current = load_config()
    
    if resource not in current:
        current[resource] = {"enabled": False, "unit": "", "meters": []}
    
    # Обновляем поля
    if req.enabled is not None:
        current[resource]["enabled"] = req.enabled
    if req.unit is not None:
        current[resource]["unit"] = req.unit
    if req.meters is not None:
        current[resource]["meters"] = [m.dict() for m in req.meters]
    
    save_config(current)
    log.info("Energy config updated via API", resource=resource)
    
    return {
        "status": "ok",
        "message": f"Конфиг ресурса '{resource}' обновлён",
        "config": current[resource],
    }
'''

energy_path = Path('api/routes/energy.py')
energy_path.write_text(energy_route_content, encoding='utf-8', newline='\n')
print('✓ Создан: api/routes/energy.py')
print('  Endpoints:')
print('    GET  /energy/summary — сводка по всем ресурсам')
print('    GET  /energy/tariffs — все тарифы')
print('    GET  /energy/tariffs/{resource} — тарифы ресурса')
print('    GET  /energy/tariffs/{resource}/active — активные на дату')
print('    POST /energy/tariffs — создать тариф')
print('    PUT  /energy/tariffs/{resource}/{id} — обновить')
print('    DELETE /energy/tariffs/{resource}/{id} — удалить')
print('    GET  /energy/config — полный конфиг')
print('    GET  /energy/config/{resource} — конфиг ресурса')
print('    PUT  /energy/config/{resource} — обновить конфиг')

# ============================================================================
# 2. Патчим main.py — добавляем import и регистрацию energy роутера
# ============================================================================
main_path = Path('main.py')
main_content = main_path.read_text(encoding='utf-8')

# 2.1. Добавляем energy в импорт
old_import = 'from api.routes import chat, config, health, system, docs  # noqa: E402'
new_import = 'from api.routes import chat, config, health, system, docs, energy  # noqa: E402'

if old_import in main_content:
    main_content = main_content.replace(old_import, new_import)
    print('✓ main.py: добавлен импорт energy роутера')
elif 'from api.routes import chat, config, health, system, docs, energy' in main_content:
    print('ℹ main.py: импорт energy уже есть')
else:
    print('⚠ main.py: не нашёл точный паттерн импорта')

# 2.2. Добавляем include_router для energy
old_register = 'app.include_router(docs.router)'
new_register = 'app.include_router(docs.router)\napp.include_router(energy.router)'

if 'app.include_router(energy.router)' not in main_content:
    if old_register in main_content:
        main_content = main_content.replace(old_register, new_register, 1)
        print('✓ main.py: добавлен include_router(energy.router)')
    else:
        print('⚠ main.py: не нашёл точный паттерн регистрации')
else:
    print('ℹ main.py: energy.router уже зарегистрирован')

main_path.write_text(main_content, encoding='utf-8', newline='\n')
print('✓ Обновлён: main.py')

print()
print('=' * 60)
print('ШАГ 3 ЗАВЕРШЁН')
print('=' * 60)
print()
print('Создано:')
print('  ✓ api/routes/energy.py — 10 endpoints для энергоучёта')
print('  ✓ main.py — зарегистрирован energy.router')
print()
print('Endpoints:')
print('  • GET /energy/summary — сводка по всем ресурсам')
print('  • GET/POST/PUT/DELETE /energy/tariffs — CRUD тарифов')
print('  • GET/PUT /energy/config — CRUD тегов счётчиков')
print()
print('СЛЕДУЮЩИЙ ШАГ:')
print('  1. Перезапусти backend: Ctrl+C, uvicorn main:app --port 8081')
print('  2. Проверь API:')
print('     curl http://localhost:8081/energy/summary')
print('     curl http://localhost:8081/energy/tariffs')
print('     curl http://localhost:8081/energy/config')
print()
print('  3. Когда API работает — скажи "energy api ok"')
print()
print('Потом пойдём к Шагу 4: Frontend виджет EnergyCostCard + конфигуратор')