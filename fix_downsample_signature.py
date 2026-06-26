#!/usr/bin/env python3
"""
fix_downsample_signature.py — добавляем параметр return_mapping в downsample_time_series
"""
from pathlib import Path

print('=' * 80)
print('ФИКС: Добавляем return_mapping в downsample_time_series')
print('=' * 80)
print()

cs_path = Path('backend/modules/deep_analysis/visualizers/chart_specs.py')
content = cs_path.read_text(encoding='utf-8')

# Проверяем сигнатуру
if 'return_mapping: bool = False' in content:
    print('✅ Функция downsample_time_series уже имеет параметр return_mapping')
    exit(0)

print('❌ Параметр return_mapping отсутствует — добавляю...')
print()

# Заменяем старую функцию на новую
old_func = '''def downsample_time_series(values: list, timestamps: list, target_points: int = 800) -> tuple[list, list]:
    """
    Downsample временной ряд с сохранением экстремумов (пиков и провалов).

    Алгоритм min-max downsampling:
    1. Делим диапазон на N bucket'ов
    2. Для каждого bucket находим min и max значения с их timestamps
    3. Добавляем обе точки в порядке их следования во времени
    4. Это сохраняет пики/провалы, которые теряются при обычном усреднении

    Результат: ~2× больше точек чем target_points, но все экстремумы сохранены.

    Args:
        values: значения (с None для пропусков)
        timestamps: соответствующие timestamps
        target_points: целевое количество bucket'ов

    Returns:
        (downsampled_values, downsampled_timestamps) — может быть до 2×target_points
    """
    if len(values) <= target_points:
        return values, timestamps

    bucket_size = len(values) / target_points

    ds_values = []
    ds_timestamps = []

    for i in range(target_points):
        start_idx = int(i * bucket_size)
        end_idx = int((i + 1) * bucket_size)

        bucket_values = values[start_idx:end_idx]
        bucket_timestamps = timestamps[start_idx:end_idx]

        # Находим все валидные точки в bucket'е
        valid_points = []
        for j, (v, t) in enumerate(zip(bucket_values, bucket_timestamps)):
            if v is not None and t is not None:
                valid_points.append((start_idx + j, v, t))

        if not valid_points:
            continue

        # Находим min и max в bucket'е
        min_point = min(valid_points, key=lambda x: x[1])
        max_point = max(valid_points, key=lambda x: x[1])

        # Добавляем в хронологическом порядке (по индексу)
        if min_point[0] <= max_point[0]:
            ds_values.append(min_point[1])
            ds_timestamps.append(min_point[2])
            if min_point[0] != max_point[0]:  # если это не одна и та же точка
                ds_values.append(max_point[1])
                ds_timestamps.append(max_point[2])
        else:
            ds_values.append(max_point[1])
            ds_timestamps.append(max_point[2])
            ds_values.append(min_point[1])
            ds_timestamps.append(min_point[2])

    return ds_values, ds_timestamps'''

new_func = '''def downsample_time_series(values: list, timestamps: list, target_points: int = 800, return_mapping: bool = False) -> tuple:
    """
    Downsample временной ряд с сохранением экстремумов (пиков и провалов).

    Алгоритм min-max downsampling:
    1. Делим диапазон на N bucket'ов
    2. Для каждого bucket находим min и max значения с их timestamps
    3. Добавляем обе точки в порядке их следования во времени
    4. Это сохраняет пики/провалы, которые теряются при обычном усреднении

    Результат: ~2× больше точек чем target_points, но все экстремумы сохранены.

    Args:
        values: значения (с None для пропусков)
        timestamps: соответствующие timestamps
        target_points: целевое количество bucket'ов
        return_mapping: если True, возвращает также маппинг {orig_idx: ds_idx}

    Returns:
        Если return_mapping=False:
            (downsampled_values, downsampled_timestamps)
        Если return_mapping=True:
            (downsampled_values, downsampled_timestamps, orig_to_ds_idx)
    """
    if len(values) <= target_points:
        if return_mapping:
            mapping = {i: i for i in range(len(values))}
            return values, timestamps, mapping
        return values, timestamps

    bucket_size = len(values) / target_points

    ds_values = []
    ds_timestamps = []
    orig_to_ds_idx = {}

    for i in range(target_points):
        start_idx = int(i * bucket_size)
        end_idx = int((i + 1) * bucket_size)

        bucket_values = values[start_idx:end_idx]
        bucket_timestamps = timestamps[start_idx:end_idx]

        # Находим все валидные точки в bucket'е
        valid_points = []
        for j, (v, t) in enumerate(zip(bucket_values, bucket_timestamps)):
            if v is not None and t is not None:
                valid_points.append((start_idx + j, v, t))

        if not valid_points:
            continue

        # Находим min и max в bucket'е
        min_point = min(valid_points, key=lambda x: x[1])
        max_point = max(valid_points, key=lambda x: x[1])

        # Добавляем в хронологическом порядке (по индексу)
        if min_point[0] <= max_point[0]:
            ds_idx = len(ds_values)
            ds_values.append(min_point[1])
            ds_timestamps.append(min_point[2])
            orig_to_ds_idx[min_point[0]] = ds_idx
            
            if min_point[0] != max_point[0]:
                ds_idx += 1
                ds_values.append(max_point[1])
                ds_timestamps.append(max_point[2])
                orig_to_ds_idx[max_point[0]] = ds_idx
        else:
            ds_idx = len(ds_values)
            ds_values.append(max_point[1])
            ds_timestamps.append(max_point[2])
            orig_to_ds_idx[max_point[0]] = ds_idx
            
            ds_idx += 1
            ds_values.append(min_point[1])
            ds_timestamps.append(min_point[2])
            orig_to_ds_idx[min_point[0]] = ds_idx

    if return_mapping:
        return ds_values, ds_timestamps, orig_to_ds_idx
    return ds_values, ds_timestamps'''

if old_func in content:
    content = content.replace(old_func, new_func)
    cs_path.write_text(content, encoding='utf-8', newline='\n')
    print('✅ Функция downsample_time_series обновлена')
    print('   Добавлен параметр return_mapping')
    print('   Теперь возвращает маппинг {orig_idx: ds_idx}')
else:
    print('❌ Не удалось найти старую функцию')
    print('   Возможно она уже частично изменена')
    
    # Показываем текущую сигнатуру
    import re
    match = re.search(r'def downsample_time_series\([^)]+\)', content)
    if match:
        print(f'   Текущая сигнатура: {match.group(0)}')

print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Перезапусти backend')
print('2. Запусти анализ — ошибка TypeError должна исчезнуть')