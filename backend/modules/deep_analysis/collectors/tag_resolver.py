"""Получение списка доступных тегов для UI"""
from structlog import get_logger
from core.db import fetch

log = get_logger()


async def get_available_tags() -> list[dict]:
    """
    Возвращает список всех тегов из tags_dict.
    
    Returns:
        [
            {
                "tag_id": int,
                "tag_name": str,
                "zone_name": str | None,
                "unit": str | None,
                "last_value": float | None,
                "last_update": datetime | None,
            },
            ...
        ]
    """
    log.info("Fetching available tags")
    
    # Упрощённый запрос БЕЗ JOIN на zones_dict
    # (зависит от реальной схемы БД)
    query = """
        SELECT 
            td.tag_id,
            td.tag_name,
            (
                SELECT tv.value 
                FROM tags_value tv 
                WHERE tv.tag_id = td.tag_id 
                ORDER BY tv.date_created DESC 
                LIMIT 1
            ) as last_value,
            (
                SELECT tv.date_created 
                FROM tags_value tv 
                WHERE tv.tag_id = td.tag_id 
                ORDER BY tv.date_created DESC 
                LIMIT 1
            ) as last_update
        FROM tags_dict td
        ORDER BY td.tag_name ASC
        LIMIT 10000
    """
    
    try:
        rows = await fetch(query)
    except Exception as e:
        log.error("Failed to fetch tags from DB", error=str(e))
        # Fallback: пробуем ещё более простой запрос без unit
        try:
            simple_query = """
                SELECT 
                    td.tag_id,
                    td.tag_name
                FROM tags_dict td
                ORDER BY td.tag_name ASC
                LIMIT 10000
            """
            rows = await fetch(simple_query)
        except Exception as e2:
            log.error("Fallback query also failed", error=str(e2))
            return []
    
    tags = []
    for row in rows:
        tags.append({
            "tag_id": row.get('tag_id'),
            "tag_name": row.get('tag_name'),
            "zone_name": None,  # Убрали зону из запроса
            "unit": row.get('unit'),
            "last_value": row.get('last_value'),
            "last_update": row.get('last_update'),
        })
    
    log.info("Available tags fetched", count=len(tags))
    return tags


async def get_tags_by_zone() -> dict:
    """
    Группирует теги по зонам (для UI с фильтрами).
    Сейчас возвращает все теги в одну группу 'Все'.
    """
    tags = await get_available_tags()
    
    return {"Все теги": tags}
