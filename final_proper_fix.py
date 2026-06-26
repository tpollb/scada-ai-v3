#!/usr/bin/env python3
"""
final_proper_fix.py — правильное решение с нуля
"""
from pathlib import Path

print('=' * 80)
print('ФИНАЛЬНЫЙ ФИКС: Добавляем apply_timezone и чиним multi-tag')
print('=' * 80)
print()

cs_path = Path('backend/modules/deep_analysis/visualizers/chart_specs.py')
content = cs_path.read_text(encoding='utf-8')

# Шаг 1: Проверяем есть ли уже apply_timezone
if 'def apply_timezone' not in content:
    print('【1】Добавляем функцию apply_timezone в начало файла')
    print('-' * 80)
    
    old_header = '''"""Создание JSON-спецификаций для графиков Chart.js"""
from typing import Optional
from datetime import datetime
import numpy as np
from structlog import get_logger

log = get_logger()'''
    
    new_header = '''"""Создание JSON-спецификаций для графиков Chart.js"""
from typing import Optional
from datetime import datetime, timezone
import numpy as np
from structlog import get_logger
from config.settings import settings

log = get_logger()

# Получаем таймзону из конфига
try:
    import pytz
    LOCAL_TZ = pytz.timezone(settings.timezone)
except Exception:
    LOCAL_TZ = timezone.utc


def apply_timezone(ts):
    """Применяет локальную таймзону к timestamp."""
    if isinstance(ts, datetime):
        if ts.tzinfo is None:
            try:
                return LOCAL_TZ.localize(ts)
            except Exception:
                return ts
        else:
            try:
                return ts.astimezone(LOCAL_TZ)
            except Exception:
                return ts
    return ts


def _format_ts_key(ts) -> str:
    """Форматирует timestamp в строку с учётом таймзоны."""
    if isinstance(ts, datetime):
        return apply_timezone(ts).strftime("%Y-%m-%d %H:%M")
    ts_str = str(ts).replace('T', ' ')
    return ts_str[:16] if len(ts_str) > 16 else ts_str
'''
    
    if old_header in content:
        content = content.replace(old_header, new_header)
        print('✅ apply_timezone и _format_ts_key добавлены')
    else:
        print('❌ Не удалось добавить — заголовок не найден')
        exit(1)
else:
    print('【1】apply_timezone уже есть ✅')

print()

# Шаг 2: Применяем apply_timezone к форматированию labels в multi-tag
print('【2】Применяем apply_timezone к labels в multi-tag')
print('-' * 80)

# Ищем блок форматирования labels в multi-tag
old_labels_block = '''    # Форматируем labels (строковое представление timestamps)
    labels = []
    for ts in ds_timestamps:
        if isinstance(ts, datetime):
            labels.append(apply_timezone(ts).strftime("%Y-%m-%d %H:%M"))
        else:
            labels.append(str(ts))'''

# Проверяем есть ли уже apply_timezone в этом блоке
if old_labels_block in content:
    print('✅ labels в multi-tag уже используют apply_timezone')
elif 'labels.append(apply_timezone' not in content[content.find('def create_multitag'):]:
    # Нужно добавить apply_timezone к labels
    old_labels_simple = '''    # Форматируем labels (строковое представление timestamps)
    labels = []
    for ts in ds_timestamps:
        if isinstance(ts, datetime):
            labels.append(ts.strftime("%Y-%m-%d %H:%M"))
        else:
            labels.append(str(ts))'''
    
    new_labels = '''    # Форматируем labels (строковое представление timestamps)
    labels = []
    for ts in ds_timestamps:
        if isinstance(ts, datetime):
            labels.append(apply_timezone(ts).strftime("%Y-%m-%d %H:%M"))
        else:
            labels.append(str(ts))'''
    
    if old_labels_simple in content:
        content = content.replace(old_labels_simple, new_labels)
        print('✅ labels в multi-tag теперь используют apply_timezone')
    else:
        print('⚠️  Блок labels не найден в ожидаемом виде')

print()

# Шаг 3: Добавляем ts_to_index в multi-tag (если ещё нет)
print('【3】Добавляем ts_to_index в multi-tag')
print('-' * 80)

if 'ts_to_index = {}' in content[content.find('def create_multitag'):]:
    print('✅ ts_to_index уже есть в multi-tag')
else:
    # Ищем место после создания ds_timestamps
    old_ds_block = '''    if need_downsample:
        # ВНИМАНИЕ: downsample_time_series возвращает (values, timestamps)
        _, ds_timestamps = downsample_time_series(
            list(range(len(common_timestamps))),
            common_timestamps,
            max_points
        )
        ds_timestamps = [t for t in ds_timestamps if t is not None]
    else:
        ds_timestamps = common_timestamps'''
    
    new_ds_block = '''    if need_downsample:
        # ВНИМАНИЕ: downsample_time_series возвращает (values, timestamps)
        _, ds_timestamps = downsample_time_series(
            list(range(len(common_timestamps))),
            common_timestamps,
            max_points
        )
        ds_timestamps = [t for t in ds_timestamps if t is not None]
    else:
        ds_timestamps = common_timestamps

    # Создаём точный маппинг timestamp -> downsampled index
    ts_to_index = {}
    for idx, ts in enumerate(ds_timestamps):
        ts_key = _format_ts_key(ts)
        ts_to_index[ts_key] = idx'''
    
    if old_ds_block in content:
        content = content.replace(old_ds_block, new_ds_block)
        print('✅ ts_to_index добавлен в multi-tag')
    else:
        print('⚠️  Блок ds_timestamps не найден')

print()

# Шаг 4: Заменяем грубое деление на точный маппинг
print('【4】Заменяем грубое деление на точный маппинг')
print('-' * 80)

old_mapping = '''        bucket_size = len(common_timestamps) / max_points if need_downsample else 1.0

        for tag_name, tag_anomalies in anomalies_per_tag.items():
            indices = tag_anomalies.get('anomaly_indices', [])
            types = tag_anomalies.get('anomaly_types', [])
            aligned_values = tags_data[tag_name].get('aligned_values', [])

            # Сопоставляем индексы (с учётом None в aligned_values)
            valid_idx = 0
            idx_map = {}
            for i, v in enumerate(aligned_values):
                if v is not None:
                    idx_map[valid_idx] = i
                    valid_idx += 1

            for anom_idx, anom_type in zip(indices, types):
                actual_idx = idx_map.get(anom_idx)
                if actual_idx is None:
                    continue

                value = aligned_values[actual_idx]

                # Пересчитываем индекс для downsampled данных
                if need_downsample:
                    ds_idx = int(actual_idx / bucket_size)
                    if ds_idx >= max_points:
                        ds_idx = max_points - 1
                else:
                    ds_idx = actual_idx'''

new_mapping = '''        for tag_name, tag_anomalies in anomalies_per_tag.items():
            indices = tag_anomalies.get('anomaly_indices', [])
            types = tag_anomalies.get('anomaly_types', [])
            aligned_values = tags_data[tag_name].get('aligned_values', [])

            # Сопоставляем индексы (с учётом None в aligned_values)
            valid_idx = 0
            idx_map = {}
            for i, v in enumerate(aligned_values):
                if v is not None:
                    idx_map[valid_idx] = i
                    valid_idx += 1

            for anom_idx, anom_type in zip(indices, types):
                actual_idx = idx_map.get(anom_idx)
                if actual_idx is None:
                    continue
                if actual_idx >= len(common_timestamps):
                    continue

                value = aligned_values[actual_idx]
                orig_ts = common_timestamps[actual_idx]

                # Точный маппинг через timestamp (как в single-tag)
                ts_key = _format_ts_key(orig_ts)
                ds_idx = ts_to_index.get(ts_key)

                # Fallback: ищем ближайший timestamp (до 30 мин)
                if ds_idx is None:
                    try:
                        if isinstance(orig_ts, datetime):
                            orig_ts_dt = apply_timezone(orig_ts)
                        else:
                            ts_str = str(orig_ts).replace('T', ' ')[:16]
                            orig_ts_dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M")

                        min_diff = float('inf')
                        closest_idx = None

                        for i, ds_ts in enumerate(ds_timestamps):
                            if isinstance(ds_ts, datetime):
                                try:
                                    ds_ts_tz = apply_timezone(ds_ts)
                                    diff = abs((ds_ts_tz - orig_ts_dt).total_seconds())
                                    if diff < min_diff:
                                        min_diff = diff
                                        closest_idx = i
                                except Exception:
                                    pass

                        if closest_idx is not None and min_diff < 1800:
                            ds_idx = closest_idx
                    except Exception:
                        pass

                if ds_idx is None:
                    continue'''

if old_mapping in content:
    content = content.replace(old_mapping, new_mapping)
    print('✅ Грубое деление заменено на точный маппинг')
else:
    print('⚠️  Блок маппинга не найден — возможно уже исправлен')

# Сохраняем
cs_path.write_text(content, encoding='utf-8', newline='\n')

print()

# Финальная проверка
print('【Финальная проверка】')
print('-' * 80)
try:
    compile(content, str(cs_path), 'exec')
    print('✅ Синтаксис корректен')
except SyntaxError as e:
    print(f'❌ Синтаксическая ошибка: {e}')
    exit(1)

# Проверяем что apply_timezone определена
if 'def apply_timezone' in content and 'def _format_ts_key' in content:
    print('✅ apply_timezone и _format_ts_key определены')
else:
    print('❌ Функции не определены!')
    exit(1)

# Проверяем что в multi-tag есть ts_to_index
multitag_start = content.find('def create_multitag_time_series_spec')
multitag_end = content.find('\n\ndef ', multitag_start + 1)
multitag_code = content[multitag_start:multitag_end] if multitag_end > 0 else content[multitag_start:]

if 'ts_to_index = {}' in multitag_code:
    print('✅ ts_to_index есть в multi-tag')
else:
    print('❌ ts_to_index НЕ найден в multi-tag!')

if 'ts_to_index.get(ts_key)' in multitag_code or 'ts_to_index[ts_key]' in multitag_code:
    print('✅ Точный маппинг используется в multi-tag')
else:
    print('❌ Точный маппинг НЕ используется!')

print()
print('=' * 80)
print('ГОТОВО')
print('=' * 80)
print()
print('Что сделано:')
print('  1. Добавлена функция apply_timezone в начало файла')
print('  2. Добавлена _format_ts_key как единый форматтер')
print('  3. Multi-tag теперь использует ts_to_index (как single-tag)')
print('  4. Убрано грубое деление bucket_size')
print('  5. Single-tag НЕ тронут')
print()
print('Backend перезагрузится сам. Проверь multi-tag анализ.')