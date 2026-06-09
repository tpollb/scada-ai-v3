"""Tariff Store — CRUD для интервальных тарифов в tariffs.json"""
import json
from pathlib import Path
from datetime import date, datetime
from structlog import get_logger

log = get_logger()

TARIFFS_FILE = Path(__file__).parent.parent.parent / "data" / "tariffs.json"


def _ensure_file():
    """Создаёт tariffs.json если не существует"""
    if not TARIFFS_FILE.exists():
        TARIFFS_FILE.parent.mkdir(parents=True, exist_ok=True)
        default = {
            "electricity": [],
            "water": [],
            "heat": [],
        }
        TARIFFS_FILE.write_text(json.dumps(default, indent=2, ensure_ascii=False), encoding="utf-8")
        log.info("Created default tariffs.json")


def load_tariffs() -> dict:
    """Загружает все тарифы из JSON"""
    _ensure_file()
    try:
        return json.loads(TARIFFS_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        log.error("Failed to load tariffs", error=str(e))
        return {"electricity": [], "water": [], "heat": []}


def save_tariffs(data: dict) -> None:
    """Сохраняет тарифы в JSON"""
    TARIFFS_FILE.parent.mkdir(parents=True, exist_ok=True)
    TARIFFS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info("Tariffs saved", resources=list(data.keys()))


def get_active_tariffs(resource: str, on_date: date | None = None) -> list:
    """Возвращает тарифы активные на указанную дату.
    
    Если on_date не указан — используется сегодня.
    Тариф активен если start_date <= on_date и (end_date is None или end_date >= on_date).
    """
    _ensure_file()
    all_tariffs = load_tariffs()
    tariffs = all_tariffs.get(resource, [])
    
    if on_date is None:
        on_date = date.today()
    elif isinstance(on_date, datetime):
        on_date = on_date.date()
    elif isinstance(on_date, str):
        on_date = datetime.fromisoformat(on_date).date()
    
    active = []
    for t in tariffs:
        try:
            start = datetime.fromisoformat(t["start_date"]).date()
            end = datetime.fromisoformat(t["end_date"]).date() if t.get("end_date") else None
            
            if start <= on_date and (end is None or end >= on_date):
                active.append(t)
        except (KeyError, ValueError) as e:
            log.warning("Invalid tariff record", tariff=t, error=str(e))
    
    return active


def get_tariff_for_date(resource: str, on_date: date | None = None) -> dict | None:
    """Возвращает один активный тариф на дату (первый найденный)."""
    active = get_active_tariffs(resource, on_date)
    if not active:
        log.warning("No active tariff found", resource=resource, date=str(on_date or date.today()))
        return None
    if len(active) > 1:
        log.warning("Multiple active tariffs, using first", resource=resource, count=len(active))
    return active[0]


def add_tariff(resource: str, tariff: dict) -> dict:
    """Добавляет новый тариф. Возвращает тариф с присвоенным id."""
    all_tariffs = load_tariffs()
    if resource not in all_tariffs:
        all_tariffs[resource] = []
    
    # Генерируем id
    existing_ids = [t.get("id", "") for t in all_tariffs[resource]]
    idx = 1
    while f"tariff_{idx:03d}" in existing_ids:
        idx += 1
    tariff["id"] = f"tariff_{idx:03d}"
    
    all_tariffs[resource].append(tariff)
    save_tariffs(all_tariffs)
    log.info("Tariff added", resource=resource, id=tariff["id"])
    return tariff


def update_tariff(resource: str, tariff_id: str, updates: dict) -> bool:
    """Обновляет тариф по id. Возвращает True если успешно."""
    all_tariffs = load_tariffs()
    tariffs = all_tariffs.get(resource, [])
    
    for t in tariffs:
        if t.get("id") == tariff_id:
            t.update(updates)
            save_tariffs(all_tariffs)
            log.info("Tariff updated", resource=resource, id=tariff_id)
            return True
    
    log.warning("Tariff not found for update", resource=resource, id=tariff_id)
    return False


def delete_tariff(resource: str, tariff_id: str) -> bool:
    """Удаляет тариф по id."""
    all_tariffs = load_tariffs()
    tariffs = all_tariffs.get(resource, [])
    original_len = len(tariffs)
    
    all_tariffs[resource] = [t for t in tariffs if t.get("id") != tariff_id]
    
    if len(all_tariffs[resource]) < original_len:
        save_tariffs(all_tariffs)
        log.info("Tariff deleted", resource=resource, id=tariff_id)
        return True
    
    return False
