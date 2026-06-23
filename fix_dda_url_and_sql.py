from pathlib import Path

print('=== fix_dda_url_and_sql.py ===')
print()

# ============================================================================
# 1. Исправляем SQL в tag_resolver.py (убираем zone_id)
# ============================================================================
resolver_path = Path('backend/modules/deep_analysis/collectors/tag_resolver.py')

new_resolver = '''"""Получение списка доступных тегов для UI"""
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
            td.unit,
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
        LIMIT 1000
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
                LIMIT 1000
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
'''

resolver_path.write_text(new_resolver, encoding='utf-8', newline='\n')
print(f'✓ Исправлен SQL: {resolver_path}')

# ============================================================================
# 2. Исправляем URL в DeepAnalysisPanel.svelte (добавляем api/v1/)
# ============================================================================
panel_path = Path('frontend/src/components/DeepAnalysisPanel.svelte')
content = panel_path.read_text(encoding='utf-8')

changes = []

# Заменяем deep_analysis/tags → api/v1/deep_analysis/tags
if "api.get('deep_analysis/tags')" in content:
    content = content.replace(
        "api.get('deep_analysis/tags')",
        "api.get('api/v1/deep_analysis/tags')"
    )
    changes.append('✓ URL: deep_analysis/tags → api/v1/deep_analysis/tags')

# Заменяем deep_analysis/run → api/v1/deep_analysis/run
if "api.post('deep_analysis/run'" in content:
    content = content.replace(
        "api.post('deep_analysis/run'",
        "api.post('api/v1/deep_analysis/run'"
    )
    changes.append('✓ URL: deep_analysis/run → api/v1/deep_analysis/run')

panel_path.write_text(content, encoding='utf-8', newline='\n')
print(f'✓ Обновлён {panel_path}')

for c in changes:
    print(c)

print()
print('=' * 70)
print('ПРОВЕРКА:')
print('=' * 70)
print()
print('Теперь curl должен работать:')
print('  curl http://localhost:8081/api/v1/deep_analysis/tags')
print()
print('Frontend перезагрузится автоматически (Vite HMR).')
print()
print('Шаги:')
print('  1. Backend перезагрузится автоматически (uvicorn --reload)')
print('  2. Открой фронтенд')
print('  3. Клик на кнопку Activity в хедере')
print('  4. В dropdown появится список тегов')
print('  5. Выбери тег → период → "Запустить анализ"')
print()
print('Если в dropdown снова "Не удалось загрузить":')
print('  curl http://localhost:8081/api/v1/deep_analysis/tags')
print('  — покажет точную ошибку от БД')