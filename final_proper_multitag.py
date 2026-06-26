#!/usr/bin/env python3
"""
final_proper_multitag.py — ОДИН downsampling, одинаковые timestamps для всех тегов
"""
from pathlib import Path

print('=' * 80)
print('ФИНАЛЬНОЕ РЕШЕНИЕ: ОДИН downsampling для всех тегов')
print('=' * 80)
print()

cs_path = Path('backend/modules/deep_analysis/visualizers/chart_specs.py')
content = cs_path.read_text(encoding='utf-8')

import re

old_func_start = 'def create_multitag_time_series_spec('
old_func_end = '\n\n\ndef create_histogram_spec('

start_idx = content.find(old_func_start)
end_idx = content.find(old_func_end)

if start_idx == -1 or end_idx == -1:
    print('❌ Не удалось найти функцию')
    exit(1)

new_func = '''def create_multitag_time_series_spec(
    tags_data: dict,
    common_timestamps: list,
    anomalies_per_tag: dict = None,
    max_points: int = 3000,
) -> dict:
    """
    Multi-tag: ОДИН downsampling для всех тегов.
    Это гарантирует что все графики имеют одинаковые timestamps.
    """
    if not anomalies_per_tag:
        anomalies_per_tag = {}

    # ОДИН downsampling для получения timestamps
    # Используем первый тег (или common_timestamps если нет тегов)
    first_tag = next(iter(tags_data.values()), None)
    if first_tag:
        first_values = first_tag.get('aligned_values', [])
        ds_values_first, ds_timestamps = downsample_time_series(
            first_values, common_timestamps, max_points
        )
    else:
        ds_timestamps = common_timestamps[:max_points]

    # Labels с timezone
    labels = []
    for ts in ds_timestamps:
        if isinstance(ts, datetime):
            labels.append(apply_timezone(ts).strftime("%Y-%m-%d %H:%M"))
        else:
            ts_str = str(ts).replace('T', ' ')
            labels.append(ts_str[:16] if len(ts_str) > 16 else ts_str)

    # Создаём маппинг timestamp → downsampled index
    ts_to_index = {}
    for idx, ts in enumerate(ds_timestamps):
        if isinstance(ts, datetime):
            ts_key = apply_timezone(ts).strftime("%Y-%m-%d %H:%M")
        else:
            ts_str = str(ts).replace('T', ' ')
            ts_key = ts_str[:16] if len(ts_str) > 16 else ts_str
        ts_to_index[ts_key] = idx

    datasets = []
    tag_colors = [
        "#3b82f6", "#10b981", "#f59e0b", "#ef4444",
        "#8b5cf6", "#ec4899", "#14b8a6", "#f97316",
    ]
    type_colors = {
        "spike": {"color": "#ef4444", "label": "Пики"},
        "dip": {"color": "#3b82f6", "label": "Провалы"},
        "drift": {"color": "#f59e0b", "label": "Дрейфы"},
        "noise": {"color": "#9ca3af", "label": "Шум"},
    }

    # Для каждого тега: downsample через те же timestamps
    for i, (tag_name, tag_data) in enumerate(tags_data.items()):
        aligned_values = tag_data.get('aligned_values', [])
        color = tag_colors[i % len(tag_colors)]

        # ВАЖНО: downsample через те же common_timestamps
        # Это гарантирует что получим значения для тех же ds_timestamps
        ds_values, _ = downsample_time_series(aligned_values, common_timestamps, max_points)

        # Проверяем что длины совпадают (должны!)
        if len(ds_values) != len(ds_timestamps):
            # Если не совпадают — обрезаем или дополняем
            if len(ds_values) > len(ds_timestamps):
                ds_values = ds_values[:len(ds_timestamps)]
            else:
                ds_values.extend([None] * (len(ds_timestamps) - len(ds_values)))

        datasets.append({
            "label": tag_name,
            "data": ds_values,
            "borderColor": color,
            "backgroundColor": color,
            "type": "line",
            "borderWidth": 1.5,
            "pointRadius": 0,
            "pointHoverRadius": 4,
            "tension": 0.1,
            "fill": False,
        })

    # Scatter аномалии (точный маппинг через timestamp)
    if anomalies_per_tag:
        for tag_name, tag_anomalies in anomalies_per_tag.items():
            indices = tag_anomalies.get('anomaly_indices', [])
            types = tag_anomalies.get('anomaly_types', [])
            aligned_values = tags_data[tag_name].get('aligned_values', [])

            # Маппим индексы из valid_values в aligned_values
            valid_idx = 0
            idx_map = {}
            for i, v in enumerate(aligned_values):
                if v is not None:
                    idx_map[valid_idx] = i
                    valid_idx += 1

            # Группируем по типам
            by_type = {}
            for anom_idx, anom_type in zip(indices, types):
                actual_idx = idx_map.get(anom_idx)
                if actual_idx is None or actual_idx >= len(common_timestamps):
                    continue

                value = aligned_values[actual_idx]
                orig_ts = common_timestamps[actual_idx]

                # Форматируем timestamp аномалии
                if isinstance(orig_ts, datetime):
                    ts_key = apply_timezone(orig_ts).strftime("%Y-%m-%d %H:%M")
                else:
                    ts_str = str(orig_ts).replace('T', ' ')
                    ts_key = ts_str[:16] if len(ts_str) > 16 else ts_str

                # Точный маппинг через ts_to_index
                ds_idx = ts_to_index.get(ts_key)

                # Fallback: ищем ближайший timestamp
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
                    continue

                if anom_type not in by_type:
                    by_type[anom_type] = []
                by_type[anom_type].append((ds_idx, value))

            # Создаём dataset для каждого типа
            for atype, points in by_type.items():
                color_info = type_colors.get(atype, type_colors["noise"])
                type_data = [None] * len(ds_timestamps)

                for ds_idx, val in points:
                    if 0 <= ds_idx < len(type_data):
                        type_data[ds_idx] = val

                label = f"{color_info['label']} ({tag_name})"

                datasets.append({
                    "label": label,
                    "data": type_data,
                    "borderColor": color_info["color"],
                    "backgroundColor": color_info["color"],
                    "type": "scatter",
                    "pointRadius": 5,
                    "pointHoverRadius": 7,
                    "showLine": False,
                })

    return {
        "type": "line",
        "data": {
            "labels": labels,
            "datasets": datasets,
        },
        "options": {
            "responsive": True,
            "maintainAspectRatio": False,
            "plugins": {
                "legend": {
                    "display": True,
                    "position": "top",
                    "labels": {"font": {"size": 10}, "boxWidth": 10},
                },
                "tooltip": {
                    "mode": "index",
                    "intersect": False,
                },
            },
            "scales": {
                "x": {
                    "type": "category",
                    "display": True,
                    "ticks": {"maxTicksLimit": 10, "font": {"size": 9}},
                },
                "y": {
                    "display": True,
                    "grid": {"color": "rgba(0, 0, 0, 0.05)"},
                    "ticks": {"font": {"size": 9}},
                },
            },
        },
    }

'''

content = content[:start_idx] + new_func + content[end_idx:]
cs_path.write_text(content, encoding='utf-8', newline='\n')

print('✅ create_multitag_time_series_spec переписана')
print()
print('Ключевое изменение:')
print('  1. ОДИН downsampling для получения ds_timestamps')
print('  2. Все теги downsample через те же common_timestamps')
print('  3. Проверка длин: if len(ds_values) != len(ds_timestamps) — обрезаем')
print('  4. ts_to_index для точного маппинга аномалий')
print()
print('Почему это работает:')
print('  • Все теги используют ОДИНАКОВЫЕ timestamps')
print('  • НЕТ "съехавших" графиков')
print('  • НЕТ разного масштаба')
print('  • Точный маппинг аномалий через timestamp')
print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Backend перезагрузится сам')
print('2. Запусти анализ с 2+ тегами')
print('3. Все графики должны иметь одинаковый масштаб')
print('4. НЕТ "съехавших" графиков')