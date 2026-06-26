#!/usr/bin/env python3
"""
fix_multitag_mapping.py — применяем timestamp-based маппинг к multi-tag
"""
from pathlib import Path
import re

print('=' * 80)
print('ФИКС: Timestamp-based маппинг для multi-tag (как в single-tag)')
print('=' * 80)
print()

cs_path = Path('backend/modules/deep_analysis/visualizers/chart_specs.py')
content = cs_path.read_text(encoding='utf-8')

# Находим блок маппинга аномалий в create_multitag_time_series_spec
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

        # Создаём маппинг timestamp -> downsampled index (как в single-tag)
        ts_to_index = {}
        for idx, ts in enumerate(ds_timestamps):
            if isinstance(ts, datetime):
                ts_key = ts.strftime("%Y-%m-%d %H:%M")
            else:
                ts_str = str(ts).replace('T', ' ')
                ts_key = ts_str[:16] if len(ts_str) > 16 else ts_str
            ts_to_index[ts_key] = idx

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

                # Используем timestamp-based маппинг (как в single-tag)
                if actual_idx < len(common_timestamps):
                    orig_ts = common_timestamps[actual_idx]
                    
                    # Форматируем timestamp аномалии
                    if isinstance(orig_ts, datetime):
                        ts_key = orig_ts.strftime("%Y-%m-%d %H:%M")
                    else:
                        ts_str = str(orig_ts).replace('T', ' ')
                        ts_key = ts_str[:16] if len(ts_str) > 16 else ts_str

                    # Ищем в downsampled timestamps
                    ds_idx = None
                    if ts_key in ts_to_index:
                        ds_idx = ts_to_index[ts_key]
                    else:
                        # Если точного совпадения нет — ищем ближайший timestamp
                        try:
                            if isinstance(orig_ts, datetime):
                                orig_ts_dt = orig_ts
                            else:
                                ts_str = str(orig_ts).replace('T', ' ')
                                if len(ts_str) > 16:
                                    ts_str = ts_str[:16]
                                orig_ts_dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M")

                            min_diff = float('inf')
                            closest_idx = None

                            for i, ds_ts in enumerate(ds_timestamps):
                                if isinstance(ds_ts, datetime):
                                    diff = abs((ds_ts - orig_ts_dt).total_seconds())
                                    if diff < min_diff:
                                        min_diff = diff
                                        closest_idx = i

                            # Если разница меньше 30 минут — используем этот индекс
                            if closest_idx is not None and min_diff < 1800:
                                ds_idx = closest_idx
                        except Exception:
                            pass
                    
                    if ds_idx is not None:
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
    cs_path.write_text(content, encoding='utf-8', newline='\n')
    print('✅ Multi-tag теперь использует timestamp-based маппинг')
    print('   Тот же подход что работает в single-tag')
else:
    print('⚠️  Блок маппинга не найден')

print()
print('=' * 80)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 80)
print()
print('Было (multi-tag):')
print('  bucket_size = len(common_timestamps) / max_points')
print('  ds_idx = int(actual_idx / bucket_size)')
print('  • Грубое деление')
print('  • Не учитывает что min-max downsampling создаёт ~2x точек')
print('  • Результат: хаотичное отображение')
print()
print('Стало (multi-tag):')
print('  ts_to_index = {timestamp_string: downsampled_idx}')
print('  ds_idx = ts_to_index[ts_key]')
print('  • Точный маппинг через timestamp (как в single-tag)')
print('  • Учитывает реальное количество downsampled точек')
print('  • Fallback: если точного совпадения нет — ищем ближайший (до 30 мин)')
print('  • Результат: точное позиционирование')
print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Перезапусти backend')
print()
print('2. Запусти анализ с 2+ тегами (KITCHEN2-CO2 + R001-CO2)')
print()
print('3. Проверь multi-tag график:')
print('   • Точки аномалий должны быть на правильных местах')
print('   • НЕ должно быть хаотичного отображения')
print('   • Все типы аномалий (spike/dip/drift/noise) на своих позициях')