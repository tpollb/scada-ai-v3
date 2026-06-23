#!/usr/bin/env python3
"""
fix_data_fetcher_sync.py — Day 1: синхронизация timestamps для мульти-тега
"""

from pathlib import Path

print('=' * 70)
print('DAY 1: СИНХРОНИЗАЦИЯ ДАННЫХ ДЛЯ МУЛЬТИ-ТЕГА')
print('=' * 70)
print()

fetcher_path = Path('backend/modules/deep_analysis/collectors/data_fetcher.py')

new_fetcher = '''"""Сбор данных из tags_value с обработкой пропусков и синхронизацией"""
from datetime import datetime, timedelta
from typing import Optional, Literal
from structlog import get_logger
import numpy as np
import pandas as pd

from core.db import fetch

log = get_logger()


def _interpolate_linear(timestamps: list[datetime], values: list[float], 
                        target_freq: str = '5min') -> tuple[list[datetime], list[float]]:
    """
    Интерполирует пропуски и ресемплирует к целевой частоте.
    
    Args:
        timestamps: исходные timestamps
        values: исходные значения
        target_freq: частота ресемплинга ('5min', '15min', '1h', etc.)
    
    Returns:
        (новые timestamps, интерполированные значения)
    """
    if len(timestamps) < 2:
        return timestamps, values
    
    # Создаём DataFrame для удобной работы с временными рядами
    df = pd.DataFrame({
        'timestamp': pd.to_datetime(timestamps),
        'value': values
    })
    df = df.set_index('timestamp').sort_index()
    
    # Ресемплинг к целевой частоте
    df_resampled = df.resample(target_freq).mean()
    
    # Линейная интерполяция пропусков
    df_interpolated = df_resampled.interpolate(method='linear', limit_area='inside')
    
    # Убираем NaN на краях (если интерполяция не смогла заполнить)
    df_interpolated = df_interpolated.dropna()
    
    return (
        df_interpolated.index.to_pydatetime().tolist(),
        df_interpolated['value'].tolist()
    )


def _align_timestamps(tags_data: dict[str, dict], 
                      tolerance: timedelta = timedelta(seconds=30)) -> tuple[dict[str, dict], list[datetime]]:
    """
    Выравнивает несколько временных рядов по общим timestamps.
    
    Args:
        tags_data: {tag_name: {"timestamps": [...], "values": [...], ...}, ...}
        tolerance: допустимое расхождение timestamps (по умолчанию 30 секунд)
    
    Returns:
        (выровненные данные, список общих timestamps)
    """
    if not tags_data:
        return {}, []
    
    # Собираем все timestamps
    all_timestamps = []
    for tag_name, data in tags_data.items():
        all_timestamps.extend(data['timestamps'])
    
    if not all_timestamps:
        return tags_data, []
    
    # Находим общий диапазон
    min_ts = min(all_timestamps)
    max_ts = max(all_timestamps)
    
    # Создаём сетку общих timestamps с шагом 5 минут (или минимальным интервалом)
    # Используем минимальный интервал между точками как базовый шаг
    min_interval = min(
        (t2 - t1 for t1, t2 in zip(all_timestamps[:-1], all_timestamps[1:]) 
         if t2 > t1),
        default=timedelta(minutes=5)
    )
    step = min(min_interval, timedelta(minutes=5))
    
    common_ts = []
    current = min_ts
    while current <= max_ts:
        common_ts.append(current)
        current += step
    
    # Для каждого тега: интерполируем значения к общим timestamps
    aligned_data = {}
    for tag_name, data in tags_data.items():
        if not data['timestamps']:
            aligned_data[tag_name] = {**data, 'aligned_values': [None] * len(common_ts)}
            continue
        
        # Создаём Series для интерполяции
        series = pd.Series(
            data['values'], 
            index=pd.to_datetime(data['timestamps'])
        ).sort_index()
        
        # Интерполируем к общим timestamps
        aligned_values = []
        for ts in common_ts:
            # Находим ближайшую точку в пределах tolerance
            diffs = [abs((pd.Timestamp(t) - pd.Timestamp(ts)).total_seconds()) 
                    for t in data['timestamps']]
            if diffs and min(diffs) <= tolerance.total_seconds():
                idx = diffs.index(min(diffs))
                aligned_values.append(data['values'][idx])
            else:
                # Интерполируем между соседними точками
                aligned_values.append(None)  # пока None, потом можно добавить интерполяцию
        
        aligned_data[tag_name] = {
            **data,
            'aligned_values': aligned_values,
        }
    
    return aligned_data, common_ts


async def fetch_tag_data(
    tag_name: str,
    start_date: datetime,
    end_date: datetime,
    exclude_nulls: bool = True,
    resample_freq: Optional[str] = None,  # '5min', '15min', '1h', etc.
) -> dict:
    """
    Собирает данные по конкретному тегу за период.
    
    Args:
        tag_name: имя тега
        start_date: начало периода
        end_date: конец периода
        exclude_nulls: исключать NULL значения
        resample_freq: частота ресемплинга (опционально)
    
    Returns:
        {
            "tag_name": str,
            "timestamps": list[datetime],
            "values": list[float],
            "total_count": int,
            "valid_count": int,
            "null_count": int,
            "metadata": {...},
            "resampled": bool,  # был ли применён ресемплинг
        }
    """
    log.info(
        "Fetching tag data",
        tag=tag_name,
        start=start_date.isoformat(),
        end=end_date.isoformat(),
        resample=resample_freq
    )
    
    # SQL запрос (упрощённый, без JOIN zones_dict)
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
    
    # Ресемплинг если запрошен
    resampled = False
    if resample_freq and len(timestamps) >= 2:
        timestamps, values = _interpolate_linear(timestamps, values, resample_freq)
        resampled = True
    
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
        "resampled": resampled,
        "resample_freq": resample_freq if resampled else None,
    }
    
    log.info(
        "Tag data fetched",
        tag=tag_name,
        total=len(rows),
        valid=len(values),
        nulls=null_count,
        resampled=resampled
    )
    
    return result


async def fetch_multiple_tags(
    tag_names: list[str],
    start_date: datetime,
    end_date: datetime,
    exclude_nulls: bool = True,
    resample_freq: Optional[str] = '5min',  # по умолчанию 5 минут для корреляций
    align: bool = True,  # выравнивать ли по общим timestamps
) -> dict:
    """
    Собирает данные по группе тегов для кросс-анализа.
    
    Args:
        tag_names: список имён тегов
        start_date: начало периода
        end_date: конец периода
        exclude_nulls: исключать NULL значения
        resample_freq: частота ресемплинга (по умолчанию '5min')
        align: выравнивать ли ряды по общим timestamps
    
    Returns:
        {
            "tags": {
                tag_name: {
                    "timestamps": [...],
                    "values": [...],
                    "aligned_values": [...] if align else None,
                    ...
                },
                ...
            },
            "common_timestamps": list[datetime],  # общие точки для корреляций
            "resample_freq": str,  # применённая частота
            "aligned": bool,  # было ли выравнивание
        }
    """
    log.info(
        "Fetching multiple tags",
        count=len(tag_names),
        resample=resample_freq,
        align=align
    )
    
    # Собираем данные по каждому тегу с ресемплингом
    tags_data = {}
    for tag_name in tag_names:
        tags_data[tag_name] = await fetch_tag_data(
            tag_name, start_date, end_date, exclude_nulls, resample_freq
        )
    
    # Выравнивание по общим timestamps
    common_timestamps = []
    if align and len(tags_data) > 1:
        tags_data, common_timestamps = _align_timestamps(tags_data)
    
    result = {
        "tags": tags_data,
        "common_timestamps": common_timestamps,
        "resample_freq": resample_freq if resample_freq else None,
        "aligned": align,
    }
    
    log.info(
        "Multiple tags fetched",
        tags=list(tags_data.keys()),
        common_count=len(common_timestamps)
    )
    
    return result
'''

fetcher_path.write_text(new_fetcher, encoding='utf-8', newline='\n')

print('✓ backend/modules/deep_analysis/collectors/data_fetcher.py обновлён')
print()
print('Что добавлено:')
print('  • _interpolate_linear() — интерполяция пропусков + ресемплинг')
print('  • _align_timestamps() — выравнивание рядов по общим timestamps')
print('  • fetch_tag_data() — параметр resample_freq')
print('  • fetch_multiple_tags() — параметры resample_freq, align')
print()
print('Зависимости:')
print('  • pandas — для работы с временными рядами')
print()

# Проверяем pandas
try:
    import pandas as pd
    print(f'✓ pandas установлен: версия {pd.__version__}')
except ImportError:
    print('⚠ pandas НЕ установлен!')
    print('  Установи: pip install pandas')
    print()

print()
print('=' * 70)
print('СЛЕДУЮЩИЙ ШАГ: correlations.py')
print('=' * 70)
print()
print('После перезапуска backend проверь:')
print('  curl -X POST http://localhost:8081/api/v1/deep_analysis/run \\')
print('    -H "Content-Type: application/json" \\')
print('    -d \'{"tags": ["R203-Temperature", "R203-CO2"], "period": 30}\'')
print()
print('Ожидай в ответе:')
print('  • "resampled": true')
print('  • "common_timestamps": [...] с выравниванием')
print('  • "aligned_values" для каждого тега')
print()
print('Готов кодить correlations.py? (Pearson, Spearman, Mutual Information)')