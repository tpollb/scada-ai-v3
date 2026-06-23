#!/usr/bin/env python3
"""
fix_resample_and_grid_check.py — исправляет 2 проблемы в data_fetcher.py
"""

from pathlib import Path

print('=' * 70)
print('ФИКС: DatetimeIndex bool + правильный resample')
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
    """Создаёт общую сетку timestamps для выравнивания рядов."""
    return pd.date_range(start=start_date, end=end_date, freq=freq)


def _resample_to_grid(
    timestamps: list[datetime],
    values: list[float],
    grid: pd.DatetimeIndex,
    resample_freq: str = '5min',
) -> list[Optional[float]]:
    """
    Ресемплирует временной ряд к общему grid.
    
    Алгоритм:
    1. Создаём Series из сырых данных
    2. Ресемплим к частоте (resample('5min').mean()) — усредняем в пределах каждого интервала
    3. Reindex к grid с method='nearest' и tolerance — ищем ближайшую точку
    4. Интерполируем пропуски внутри диапазона данных
    """
    if not timestamps or not values:
        return [None] * len(grid)
    
    try:
        # Создаём Series
        series = pd.Series(values, index=pd.to_datetime(timestamps))
        series = series.sort_index()
        
        # Убираем дубликаты
        series = series.groupby(series.index).mean()
        
        # Шаг 1: Ресемплинг к целевой частоте
        resampled = series.resample(resample_freq).mean()
        
        # Шаг 2: Reindex к общему grid с поиском ближайшей точки
        # tolerance = частота (5 минут) — ищем точки в пределах 5 минут
        tolerance = pd.Timedelta(resample_freq)
        reindexed = resampled.reindex(grid, method='nearest', tolerance=tolerance)
        
        # Шаг 3: Forward fill для оставшихся пропусков внутри диапазона данных
        # (когда данных нет в какой-то точке grid, но они есть рядом)
        reindexed = reindexed.interpolate(method='linear', limit_area='inside')
        
        # Шаг 4: ffill/bfill для краёв (опционально, чтобы не терять данные на границах)
        # Но не экстраполируем за границы исходных данных
        min_data_ts = series.index.min()
        max_data_ts = series.index.max()
        
        # Конвертируем в список с None для NaN
        result = []
        for ts, v in zip(grid, reindexed.values):
            # Если timestamp вне диапазона данных — оставляем None
            if ts < min_data_ts or ts > max_data_ts:
                result.append(None)
            elif pd.isna(v):
                result.append(None)
            else:
                result.append(float(v))
        
        valid_count = sum(1 for v in result if v is not None)
        log.debug(
            "Resample result",
            raw=len(timestamps),
            resampled=len(resampled),
            grid=len(grid),
            valid=valid_count
        )
        
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
    """Собирает СЫРЫЕ данные по конкретному тегу (без ресемплинга)."""
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
    """Собирает данные по группе тегов с эффективным выравниванием через общий grid."""
    log.info(
        "Fetching multiple tags",
        count=len(tag_names),
        resample=resample_freq,
        align=align
    )
    
    # Создаём общий grid
    common_grid = None
    if resample_freq and align:
        common_grid = _build_common_grid(start_date, end_date, resample_freq)
        log.info("Common grid built", points=len(common_grid), freq=resample_freq)
    
    # Собираем сырые данные
    raw_data = {}
    for tag_name in tag_names:
        raw_data[tag_name] = await fetch_tag_data(
            tag_name, start_date, end_date, exclude_nulls
        )
    
    # Ресемплируем к grid
    tags_data = {}
    common_timestamps_list = []
    
    if common_grid is not None:
        common_timestamps_list = common_grid.to_pydatetime().tolist()
        
        for tag_name, raw in raw_data.items():
            aligned_values = _resample_to_grid(
                raw['raw_timestamps'],
                raw['raw_values'],
                common_grid,
                resample_freq
            )
            
            valid_count = sum(1 for v in aligned_values if v is not None)
            
            tags_data[tag_name] = {
                "tag_name": tag_name,
                "timestamps": common_timestamps_list,
                "values": [v for v in aligned_values if v is not None],
                "aligned_values": aligned_values,
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
                valid=valid_count,
                coverage=f"{valid_count/len(common_grid)*100:.1f}%"
            )
    else:
        # Без ресемплинга
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
        "resample_freq": resample_freq if common_grid is not None else None,  # ← ИСПРАВЛЕНО!
        "aligned": align and common_grid is not None,
    }
    
    # Проверяем что есть хотя бы несколько валидных общих точек
    if common_grid is not None:
        min_valid = min(
            (tags_data[t]['valid_count'] for t in tag_names),
            default=0
        )
        if min_valid < 10:
            log.warning(
                "Very few valid aligned points",
                min_valid=min_valid,
                tags=tag_names
            )
    
    log.info(
        "Multiple tags fetched",
        tags=list(tags_data.keys()),
        common_count=len(common_timestamps_list)
    )
    
    return result
'''

fetcher_path.write_text(new_fetcher, encoding='utf-8', newline='\n')

print('✓ backend/modules/deep_analysis/collectors/data_fetcher.py исправлен')
print()
print('Что исправлено:')
print('  1. ✓ "if common_grid" → "if common_grid is not None" (исправлен ValueError)')
print('  2. ✓ Новый алгоритм _resample_to_grid:')
print('     • series.resample(freq).mean() — усреднение в пределах интервалов')
print('     • reindex(grid, method="nearest", tolerance=freq) — поиск ближайших')
print('     • interpolate(limit_area="inside") — интерполяция внутри диапазона')
print('     • Фильтрация по min_data_ts/max_data_ts (не экстраполируем)')
print('  3. ✓ Добавлено логирование coverage (процент валидных точек)')
print('  4. ✓ Предупреждение если < 10 валидных точек')
print()
print('=' * 70)
print('Перезапусти backend и проверь:')
print('=' * 70)
print()
print('  curl -X POST http://localhost:8081/api/v1/deep_analysis/run \\')
print('    -H "Content-Type: application/json" \\')
print('    -d \'{"tags": ["R203-Temperature", "R203-CO2", "R203-Humidity"], "period": 30}\'')
print()
print('В логах должен появиться coverage:')
print('  Tag resampled to grid tag=R203-Temperature raw=37612 grid=8641 valid=7234 coverage=83.7%')
print()
print('Если coverage всё ещё низкий (<10%):')
print('  • Возможно теги имеют разную временную зону')
print('  • Возможно в БД timestamps в UTC, а grid в local time')
print('  • Скинь вывод: SELECT min(date_created), max(date_created) FROM tags_value LIMIT 10')