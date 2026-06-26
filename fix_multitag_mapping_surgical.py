#!/usr/bin/env python3
"""
fix_multitag_mapping_surgical.py — точечный фикс ТОЛЬКО маппинга в multi-tag
НЕ трогает single-tag и ничего больше
"""
from pathlib import Path

print('=' * 80)
print('ТОЧЕЧНЫЙ ФИКС: Маппинг аномалий в multi-tag')
print('=' * 80)
print()

cs_path = Path('backend/modules/deep_analysis/visualizers/chart_specs.py')
content = cs_path.read_text(encoding='utf-8')

# 1. Добавляем ts_to_index сразу после создания ds_timestamps в multi-tag
print('【1】Добавляем ts_to_index в multi-tag')
print('-' * 80)

old_ds_timestamps = '''    if need_downsample:
        # ВНИМАНИЕ: downsample_time_series возвращает (values, timestamps)
        _, ds_timestamps = downsample_time_series(
            list(range(len(common_timestamps))),
            common_timestamps,
            max_points
        )
        ds_timestamps = [t for t in ds_timestamps if t is not None]
    else:
        ds_timestamps = common_timestamps'''

new_ds_timestamps = '''    if need_downsample:
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
    # (такой же подход как в single-tag)
    ts_to_index = {}
    for idx, ts in enumerate(ds_timestamps):
        if isinstance(ts, datetime):
            ts_key = apply_timezone(ts).strftime("%Y-%m-%d %H:%M")
        else:
            ts_str = str(ts).replace('T', ' ')
            ts_key = ts_str[:16] if len(ts_str) > 16 else ts_str
        ts_to_index[ts_key] = idx'''

if old_ds_timestamps in content:
    content = content.replace(old_ds_timestamps, new_ds_timestamps)
    print('✅ ts_to_index добавлен в multi-tag')
else:
    print('⚠️  Блок ds_timestamps не найден')

print()

# 2. Заменяем грубое деление на точный поиск по timestamp
print('【2】Заменяем грубое деление на точный маппинг')
print('-' * 80)

old_mapping = '''    # 2. Добавляем scatter points для аномалий по типам
    if anomalies_per_tag:
        anomalies_by_type = {}

        bucket_size = len(common_timestamps) / max_points if need_downsample else 1.0

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
                    ds_idx = actual_idx

                key = f"{tag_name}|{anom_type}"

                if key not in anomalies_by_type:
                    anomalies_by_type[key] = {
                        "tag": tag_name,
                        "type": anom_type,
                        "points": []
                    }
                anomalies_by_type[key]["points"].append((ds_idx, value))'''

new_mapping = '''    # 2. Добавляем scatter points для аномалий по типам
    if anomalies_per_tag:
        anomalies_by_type = {}

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
                if actual_idx >= len(common_timestamps):
                    continue

                value = aligned_values[actual_idx]
                orig_ts = common_timestamps[actual_idx]

                # Форматируем timestamp аномалии (с apply_timezone!)
                if isinstance(orig_ts, datetime):
                    ts_key = apply_timezone(orig_ts).strftime("%Y-%m-%d %H:%M")
                else:
                    ts_str = str(orig_ts).replace('T', ' ')
                    ts_key = ts_str[:16] if len(ts_str) > 16 else ts_str

                # Точный маппинг через ts_to_index (как в single-tag)
                ds_idx = None
                if ts_key in ts_to_index:
                    ds_idx = ts_to_index[ts_key]
                else:
                    # Fallback: ищем ближайший timestamp (до 30 мин)
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
                    continue

                key = f"{tag_name}|{anom_type}"

                if key not in anomalies_by_type:
                    anomalies_by_type[key] = {
                        "tag": tag_name,
                        "type": anom_type,
                        "points": []
                    }
                anomalies_by_type[key]["points"].append((ds_idx, value))'''

if old_mapping in content:
    content = content.replace(old_mapping, new_mapping)
    print('✅ Грубое деление заменено на точный маппинг через timestamp')
else:
    print('⚠️  Блок маппинга не найден')

# Сохраняем
cs_path.write_text(content, encoding='utf-8', newline='\n')

print()

# Проверяем синтаксис
print('【Проверка синтаксиса】')
print('-' * 80)
try:
    compile(content, str(cs_path), 'exec')
    print('✅ Синтаксис корректен!')
except SyntaxError as e:
    print(f'❌ Ошибка: {e}')

print()
print('=' * 80)
print('ЧТО ИСПРАВЛЕНО (МИНИМАЛЬНОЕ ИЗМЕНЕНИЕ):')
print('=' * 80)
print()
print('1. Добавлен ts_to_index словарь в multi-tag')
print('   (такой же как в single-tag)')
print()
print('2. Вместо грубого деления:')
print('   ds_idx = int(actual_idx / bucket_size)')
print()
print('   Теперь точный поиск:')
print('   ts_key = apply_timezone(orig_ts).strftime("%Y-%m-%d %H:%M")')
print('   ds_idx = ts_to_index[ts_key]')
print()
print('3. Применён apply_timezone к аномалиям (было пропущено!)')
print()
print('Single-tag НЕ изменён вообще.')
print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Backend перезагрузится сам (--reload)')
print('2. Запусти анализ с 2+ тегами')
print('3. Multi-tag должен работать точно как single-tag')