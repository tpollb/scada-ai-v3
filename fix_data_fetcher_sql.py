from pathlib import Path

print('=== fix_data_fetcher_sql.py ===')
print()

fetcher_path = Path('backend/modules/deep_analysis/collectors/data_fetcher.py')

new_fetcher = '''"""Сбор данных из tags_value с обработкой пропусков"""
from datetime import datetime, timedelta
from typing import Optional
from structlog import get_logger
import numpy as np

from core.db import fetch

log = get_logger()


async def fetch_tag_data(
    tag_name: str,
    start_date: datetime,
    end_date: datetime,
    exclude_nulls: bool = True,
) -> dict:
    """
    Собирает данные по конкретному тегу за период.
    
    Args:
        tag_name: имя тега (например, "AIR0-1-Online")
        start_date: начало периода
        end_date: конец периода
        exclude_nulls: исключать NULL значения из расчётов
    
    Returns:
        {
            "tag_name": str,
            "timestamps": list[datetime],
            "values": list[float],
            "total_count": int,
            "valid_count": int,
            "null_count": int,
            "metadata": {...}
        }
    """
    log.info(
        "Fetching tag data",
        tag=tag_name,
        start=start_date.isoformat(),
        end=end_date.isoformat()
    )
    
    # SQL запрос к tags_value — УПРОЩЁННЫЙ (без JOIN с zones_dict)
    # т.к. в схеме БД нет td.zone_id
    
    if exclude_nulls:
        query = """
            SELECT 
                tv.date_created as timestamp,
                tv.value,
                td.tag_name,
                td.tag_id
            FROM tags_value tv
            JOIN tags_dict td ON td.tag_id = tv.tag_id
            WHERE td.tag_name = $1
              AND tv.date_created >= $2
              AND tv.date_created <= $3
              AND tv.value IS NOT NULL
            ORDER BY tv.date_created ASC
            LIMIT 100000
        """
    else:
        query = """
            SELECT 
                tv.date_created as timestamp,
                tv.value,
                td.tag_name,
                td.tag_id
            FROM tags_value tv
            JOIN tags_dict td ON td.tag_id = tv.tag_id
            WHERE td.tag_name = $1
              AND tv.date_created >= $2
              AND tv.date_created <= $3
            ORDER BY tv.date_created ASC
            LIMIT 100000
        """
    
    try:
        rows = await fetch(query, tag_name, start_date, end_date)
    except Exception as e:
        log.error("Failed to fetch tag data", tag=tag_name, error=str(e))
        raise
    
    timestamps = []
    values = []
    null_count = 0
    
    for row in rows:
        timestamps.append(row['timestamp'])
        if row['value'] is not None:
            try:
                values.append(float(row['value']))
            except (ValueError, TypeError):
                null_count += 1
        else:
            null_count += 1
    
    # Metadata (берём из первой строки)
    metadata = {}
    if rows:
        metadata = {
            "tag_id": rows[0].get('tag_id'),
            "tag_name": rows[0].get('tag_name'),
        }
    
    result = {
        "tag_name": tag_name,
        "timestamps": timestamps,
        "values": values,
        "total_count": len(rows),
        "valid_count": len(values),
        "null_count": null_count,
        "metadata": metadata,
    }
    
    log.info(
        "Tag data fetched",
        tag=tag_name,
        total=len(rows),
        valid=len(values),
        nulls=null_count
    )
    
    return result


async def fetch_multiple_tags(
    tag_names: list[str],
    start_date: datetime,
    end_date: datetime,
    exclude_nulls: bool = True,
) -> dict:
    """
    Собирает данные по группе тегов для кросс-анализа.
    
    Returns:
        {
            "tags": {tag_name: {...data...}, ...},
            "common_timestamps": list[datetime],  # общие точки для корреляций
        }
    """
    log.info("Fetching multiple tags", count=len(tag_names))
    
    tags_data = {}
    for tag_name in tag_names:
        tags_data[tag_name] = await fetch_tag_data(
            tag_name, start_date, end_date, exclude_nulls
        )
    
    # Находим общие timestamps для корреляций
    # (пока пропускаем — реализуем в Итерации 2)
    common_timestamps = []
    
    return {
        "tags": tags_data,
        "common_timestamps": common_timestamps,
    }
'''

fetcher_path.write_text(new_fetcher, encoding='utf-8', newline='\n')
print(f'✓ Исправлен SQL в: {fetcher_path}')
print('  - Убран JOIN zones_dict (нет td.zone_id в схеме)')
print('  - Добавлена обработка ошибок')
print('  - Добавлен try/except для float() конвертации')
print()

# Также добавим лучшую обработку ошибок в api.py
api_path = Path('backend/modules/deep_analysis/api.py')
content = api_path.read_text(encoding='utf-8')

# Добавляем детальное логирование в except блок
if 'import traceback' not in content:
    content = content.replace(
        'from structlog import get_logger',
        'from structlog import get_logger\nimport traceback'
    )

# Заменяем обработку ошибок на более детальную
old_except = '''    except HTTPException:
        raise
    except Exception as e:
        log.error("Analysis failed", error=str(e), tags=request.tags)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")'''

new_except = '''    except HTTPException:
        raise
    except Exception as e:
        tb = traceback.format_exc()
        log.error("Analysis failed", error=str(e), tags=request.tags, traceback=tb)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {type(e).__name__}: {str(e)}")'''

if old_except in content:
    content = content.replace(old_except, new_except)
    api_path.write_text(content, encoding='utf-8', newline='\n')
    print(f'✓ Улучшено логирование в: {api_path}')
    print('  - Добавлен traceback в логи')
    print('  - В ответе теперь тип ошибки')
else:
    print('ℹ api.py уже имеет улучшенное логирование')

print()
print('=' * 70)
print('ИСПРАВЛЕНИЯ ПРИМЕНЕНЫ')
print('=' * 70)
print()
print('Backend перезагрузится автоматически (uvicorn --reload).')
print()
print('Теперь проверь:')
print('  1. Открой фронтенд')
print('  2. Клик Activity → выбери тег → "Запустить анализ"')
print('  3. Если снова 500 — curl покажет тип ошибки:')
print()
print('  curl -X POST http://localhost:8081/api/v1/deep_analysis/run \\')
print('    -H "Content-Type: application/json" \\')
print('    -d \'{"tags": ["AIR0-1-Online"], "period": 30, "anomalies": true}\'')