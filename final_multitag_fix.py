#!/usr/bin/env python3
"""
final_multitag_fix.py — полная переделка multi-tag с step-based downsampling
"""
from pathlib import Path

print('=' * 80)
print('ФИНАЛЬНЫЙ ФИКС: Step-based downsampling + точный timestamp маппинг')
print('=' * 80)
print()

cs_path = Path('backend/modules/deep_analysis/visualizers/chart_specs.py')
content = cs_path.read_text(encoding='utf-8')

# Находим и полностью заменяем функцию create_multitag_time_series_spec
import re

old_func_start = 'def create_multitag_time_series_spec('
old_func_end = '\n\n\ndef create_histogram_spec('

start_idx = content.find(old_func_start)
end_idx = content.find(old_func_end)

if start_idx == -1 or end_idx == -1:
    print('❌ Не удалось найти функцию create_multitag_time_series_spec')
    exit(1)

old_func = content[start_idx:end_idx]

new_func = '''def create_multitag_time_series_spec(
    tags_data: dict,
    common_timestamps: list,
    anomalies_per_tag: dict = None,
    max_points: int = 3000,
) -> dict:
    """
    Multi-tag time series с STEP-BASED downsampling.
    Все теги используют одинаковые индексы для гарантии синхронизации.
    """
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

    # STEP-BASED downsampling: равномерный по индексам
    total_points = len(common_timestamps)
    need_downsample = total_points > max_points

    if need_downsample:
        # Равномерная выборка: берём каждые N-ные точки
        step = max(1, total_points // max_points)
        ds_indices = list(range(0, total_points, step))[:max_points]
    else:
        ds_indices = list(range(total_points))

    # Downsampled timestamps (одинаковые для всех тегов)
    ds_timestamps = [common_timestamps[i] for i in ds_indices]

    # Labels с apply_timezone
    labels = [
        apply_timezone(ts).strftime("%Y-%m-%d %H:%M") if isinstance(ts, datetime) else str(ts)[:16]
        for ts in ds_timestamps
    ]

    # Создаём маппинг: оригинальный индекс → downsampled индекс
    orig_to_ds = {orig_idx: ds_idx for ds_idx, orig_idx in enumerate(ds_indices)}

    # 1. Линии для каждого тега (используют одинаковые индексы)
    for i, (tag_name, tag_data) in enumerate(tags_data.items()):
        aligned_values = tag_data.get('aligned_values', [])
        color = tag_colors[i % len(tag_colors)]

        # Downsample через те же индексы (НЕ min-max!)
        ds_values = [
            aligned_values[idx] if idx < len(aligned_values) else None
            for idx in ds_indices
        ]

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

    # 2. Scatter аномалии (точный маппинг через timestamp)
    if anomalies_per_tag:
        # Создаём маппинг timestamp → downsampled index
        ts_to_index = {}
        for idx, ts in enumerate(ds_timestamps):
            if isinstance(ts, datetime):
                ts_key = apply_timezone(ts).strftime("%Y-%m-%d %H:%M")
            else:
                ts_str = str(ts).replace('T', ' ')
                ts_key = ts_str[:16] if len(ts_str) > 16 else ts_str
            ts_to_index[ts_key] = idx

        for tag_name, tag_anomalies in anomalies_per_tag.items():
            indices = tag_anomalies.get('anomaly_indices', [])
            types = tag_anomalies.get('anomaly_types', [])
            aligned_values = tags_data[tag_name].get('aligned_values', [])

            # Маппим индексы из valid_values обратно в aligned_values
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

                # Точный маппинг через timestamp (как в single-tag)
                ds_idx = ts_to_index.get(ts_key)

                # Fallback: если точного совпадения нет — используем orig_to_ds
                if ds_idx is None:
                    ds_idx = orig_to_ds.get(actual_idx)

                # Fallback 2: ищем ближайший downsampled индекс
                if ds_idx is None:
                    closest_orig = min(ds_indices, key=lambda x: abs(x - actual_idx))
                    # Проверяем что разница <= 2 * step
                    if abs(closest_orig - actual_idx) <= 2 * (total_points // max_points if need_downsample else 1):
                        ds_idx = orig_to_ds[closest_orig]

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

    spec = {
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

    return spec

'''

content = content[:start_idx] + new_func + content[end_idx:]
cs_path.write_text(content, encoding='utf-8', newline='\n')

print('✅ create_multitag_time_series_spec полностью переписана')
print()
print('Что исправлено:')
print('  1. STEP-BASED downsampling вместо min-max')
print('     • ds_indices = [0, step, 2*step, ...]')
print('     • Все теги используют одинаковые индексы')
print('     • НЕТ рассинхрона между ds_timestamps и ds_values')
print()
print('  2. Точный маппинг аномалий через timestamp')
print('     • ts_to_index словарь (как в single-tag)')
print('     • ds_idx = ts_to_index[ts_key]')
print('     • Fallback через orig_to_ds и ближайший индекс')
print()
print('  3. Применён apply_timezone ко всем timestamps')
print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Backend перезагрузится сам (--reload)')
print('2. Запусти анализ с 2+ тегами')
print('3. Multi-tag должен работать точно как single-tag')
print('4. НЕТ рассинхрона, НЕТ смещения')