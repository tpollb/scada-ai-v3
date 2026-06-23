#!/usr/bin/env python3
"""
fix_alignment_performance.py — переписываем alignment через общий grid
"""

from pathlib import Path

print('=' * 70)
print('ФИКС: O(n²) alignment → O(n log n) через общий grid')
print('=' * 70)
print()

fetcher_path = Path('backend/modules/deep_analysis/collectors/data_fetcher.py')

new_fetcher = '''"""Сбор данных из tags_value с обработкой пропусков и синхронизацией"""
from datetime import datetime, timedelta
from typing import Optional
from structlog import get_logger
import numpy as np
import pandas as pd

from core.db import fetch

log = get_logger()


def _build_common_grid(start_date: datetime, end_date: datetime, freq: str = '5min') -> pd.DatetimeIndex:
    """
    Создаёт общую сетку timestamps для выравнивания рядов.
    Все теги будут ресемплированы к этим timestamps.
    """
    return pd.date_range(start=start_date, end=end_date, freq=freq)


def _resample_to_grid(
    timestamps: list[datetime],
    values: list[float],
    grid: pd.DatetimeIndex,
) -> list[Optional[float]]:
    """
    Ресемплирует временной ряд к общему grid с линейной интерполяцией.
    
    Args:
        timestamps: исходные timestamps
        values: исходные значения
        grid: общая сетка (pd.DatetimeIndex)
    
    Returns:
        Список значений с той же длиной что и grid (с None для пропусков)
    """
    if not timestamps or not values:
        return [None] * len(grid)
    
    try:
        # Создаём Series и сортируем по времени
        series = pd.Series(
            values,
            index=pd.to_datetime(timestamps)
        ).sort_index()
        
        # Убираем дубликаты (берём среднее)
        series = series.groupby(series.index).mean()
        
        # Ресемплинг к общему grid (используем asfreq + reindex для точного соответствия)
        resampled = series.reindex(grid)
        
        # Интерполяция пропусков внутри диапазона данных
        # limit_area='inside' — не экстраполируем за границы данных
        resampled = resampled.interpolate(method='linear', limit_area='inside')
        
        # Конвертируем в список с None для NaN
        result = []
        for v in resampled.values:
            if pd.isna(v):
                result.append(None)
            else:
                result.append(float(v))
        
        return result
    
    except Exception as e:
        log.warning("Resample to grid failed", error=str(e))
        return [None] * len(grid)


async def fetch_tag_data(
    tag_name: str,
    start_date: datetime,
    end_date: datetime,
    exclude_nulls: bool = True,
) -> dict:
    """
    Собирает СЫРЫЕ данные по конкретному тегу (без ресемплинга).
    Ресемплинг делается отдельно в fetch_multiple_tags через общий grid.
    """
    log.info(
        "Fetching tag data",
        tag=tag_name,
        start=start_date.isoformat(),
        end=end_date.isoformat()
    )
    
    null_clause = "AND tv.value IS NOT NULL" if exclude_nulls else ""
    
    query = f"""
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
          {null_clause}
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
    
    metadata = {}
    if rows:
        metadata = {
            "tag_id": rows[0].get('tag_id'),
            "tag_name": rows[0].get('tag_name'),
        }
    
    return {
        "tag_name": tag_name,
        "raw_timestamps": timestamps,
        "raw_values": values,
        "total_count": len(rows),
        "valid_count": len(values),
        "null_count": null_count,
        "metadata": metadata,
    }


async def fetch_multiple_tags(
    tag_names: list[str],
    start_date: datetime,
    end_date: datetime,
    exclude_nulls: bool = True,
    resample_freq: Optional[str] = '5min',
    align: bool = True,
) -> dict:
    """
    Собирает данные по группе тегов с ЭФФЕКТИВНЫМ выравниванием.
    
    Алгоритм:
    1. Создаём общий grid timestamps (каждые resample_freq)
    2. Для каждого тега: resample + reindex к grid
    3. Все теги имеют одинаковые timestamps = common_timestamps
    
    Время работы: O(n log n) вместо O(n²)
    """
    log.info(
        "Fetching multiple tags",
        count=len(tag_names),
        resample=resample_freq,
        align=align
    )
    
    # Шаг 1: Создаём общий grid
    common_grid = None
    if resample_freq and align:
        common_grid = _build_common_grid(start_date, end_date, resample_freq)
        log.info(
            "Common grid built",
            points=len(common_grid),
            freq=resample_freq
        )
    
    # Шаг 2: Собираем сырые данные по каждому тегу
    raw_data = {}
    for tag_name in tag_names:
        raw_data[tag_name] = await fetch_tag_data(
            tag_name, start_date, end_date, exclude_nulls
        )
    
    # Шаг 3: Ресемплируем каждый тег к общему grid
    tags_data = {}
    common_timestamps_list = []
    
    if common_grid is not None:
        common_timestamps_list = common_grid.to_pydatetime().tolist()
        
        for tag_name, raw in raw_data.items():
            aligned_values = _resample_to_grid(
                raw['raw_timestamps'],
                raw['raw_values'],
                common_grid
            )
            
            valid_count = sum(1 for v in aligned_values if v is not None)
            
            tags_data[tag_name] = {
                "tag_name": tag_name,
                "timestamps": common_timestamps_list,
                "values": [v for v in aligned_values if v is not None],
                "aligned_values": aligned_values,  # с None для пропусков
                "total_count": raw['total_count'],
                "valid_count": valid_count,
                "null_count": raw['null_count'],
                "metadata": raw['metadata'],
                "resampled": True,
                "resample_freq": resample_freq,
            }
            
            log.info(
                "Tag resampled to grid",
                tag=tag_name,
                raw=raw['total_count'],
                grid=len(common_grid),
                valid=valid_count
            )
    else:
        # Без ресемплинга — просто сырые данные
        for tag_name, raw in raw_data.items():
            tags_data[tag_name] = {
                "tag_name": tag_name,
                "timestamps": raw['raw_timestamps'],
                "values": raw['raw_values'],
                "aligned_values": raw['raw_values'],
                "total_count": raw['total_count'],
                "valid_count": raw['valid_count'],
                "null_count": raw['null_count'],
                "metadata": raw['metadata'],
                "resampled": False,
                "resample_freq": None,
            }
    
    result = {
        "tags": tags_data,
        "common_timestamps": common_timestamps_list,
        "resample_freq": resample_freq if common_grid else None,
        "aligned": align and common_grid is not None,
    }
    
    log.info(
        "Multiple tags fetched",
        tags=list(tags_data.keys()),
        common_count=len(common_timestamps_list)
    )
    
    return result
'''

fetcher_path.write_text(new_fetcher, encoding='utf-8', newline='\n')

print('✓ backend/modules/deep_analysis/collectors/data_fetcher.py переписан')
print()
print('Ключевые изменения:')
print('  1. Убран неэффективный _align_timestamps (был O(n²))')
print('  2. Добавлен _build_common_grid — создаёт общий grid заранее')
print('  3. Добавлен _resample_to_grid — O(n log n) через pandas.reindex')
print('  4. fetch_tag_data теперь возвращает сырые данные (без ресемплинга)')
print('  5. fetch_multiple_tags ресемплирует все теги к одному grid')
print()
print('Ожидаемое ускорение:')
print('  • Было: ~30-60 секунд для 3 тегов с 8000 точками')
print('  • Стало: ~1-2 секунды (pandas оптимизирован)')
print()
print('=' * 70)
print('Перезапусти backend и проверь:')
print('=' * 70)
print()
print('  curl -X POST http://localhost:8081/api/v1/deep_analysis/run \\')
print('    -H "Content-Type: application/json" \\')
print('    -d \'{"tags": ["R203-Temperature", "R203-CO2", "R203-Humidity"], "period": 30}\'')
print()
print('Должно вернуться за 2-5 секунд с:')
print('  • "correlations": {матрица 3x3}')
print('  • "pair_analysis": {детальный анализ первой пары}')
print('  • "visualizations": {"heatmap": {...}, "scatter": {...}}')