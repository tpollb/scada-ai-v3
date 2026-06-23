"""Сохранение результатов анализа в JSON файлы"""
from pathlib import Path
from datetime import datetime
from typing import Optional
import json
import hashlib
from structlog import get_logger

log = get_logger()

# Папка для хранения истории (создаётся автоматически)
HISTORY_DIR = Path("backend/data/analysis_history")


def ensure_history_dir():
    """Создаёт папку для истории если её нет"""
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def save_analysis(
    analysis_id: str,
    params: dict,
    results: dict,
) -> str:
    """
    Сохраняет результат анализа в JSON файл.
    
    Args:
        analysis_id: уникальный ID анализа (timestamp + hash тегов)
        params: параметры запроса (теги, период, опции)
        results: результаты анализа (статистика, аномалии, etc)
    
    Returns:
        Путь к сохранённому файлу
    """
    ensure_history_dir()
    
    filepath = HISTORY_DIR / f"{analysis_id}.json"
    
    data = {
        "analysis_id": analysis_id,
        "created_at": datetime.now().isoformat(),
        "params": params,
        "results": results,
    }
    
    # Сериализуем datetime объекты
    def json_serializer(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=json_serializer)
    
    log.info("Analysis saved", id=analysis_id, path=str(filepath))
    return str(filepath)


def load_analysis(analysis_id: str) -> Optional[dict]:
    """
    Загружает сохранённый анализ по ID.
    
    Returns:
        Данные анализа или None если не найден
    """
    ensure_history_dir()
    
    filepath = HISTORY_DIR / f"{analysis_id}.json"
    
    if not filepath.exists():
        log.warning("Analysis not found", id=analysis_id)
        return None
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    log.info("Analysis loaded", id=analysis_id)
    return data


def list_analyses(limit: int = 50) -> list[dict]:
    """
    Возвращает список сохранённых анализов.
    
    Returns:
        [
            {
                "analysis_id": str,
                "created_at": str,
                "tags": list[str],
                "period": str,
            },
            ...
        ]
    """
    ensure_history_dir()
    
    analyses = []
    for filepath in sorted(HISTORY_DIR.glob("*.json"), reverse=True)[:limit]:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            analyses.append({
                "analysis_id": data['analysis_id'],
                "created_at": data['created_at'],
                "tags": data['params'].get('tags', []),
                "period": data['params'].get('period', 'unknown'),
            })
        except Exception as e:
            log.warning("Failed to load analysis", file=filepath.name, error=str(e))
    
    return analyses


def delete_analysis(analysis_id: str) -> bool:
    """Удаляет анализ по ID"""
    ensure_history_dir()
    
    filepath = HISTORY_DIR / f"{analysis_id}.json"
    
    if filepath.exists():
        filepath.unlink()
        log.info("Analysis deleted", id=analysis_id)
        return True
    
    return False


def generate_analysis_id(tags: list[str], period: str) -> str:
    """
    Генерирует уникальный ID для анализа.
    
    Формат: {timestamp}_{hash_тегов}
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Hash от тегов и периода
    tags_str = "|".join(sorted(tags)) + f"|{period}"
    hash_obj = hashlib.md5(tags_str.encode('utf-8'))
    hash_short = hash_obj.hexdigest()[:8]
    
    return f"{timestamp}_{hash_short}"
