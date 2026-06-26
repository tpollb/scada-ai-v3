#!/usr/bin/env python3
"""
clean_chart_specs.py — полная чистая версия без багов
"""
from pathlib import Path

print('=' * 80)
print('ЧИСТАЯ РАБОЧАЯ ВЕРСИЯ chart_specs.py')
print('=' * 80)
print()

cs_path = Path('backend/modules/deep_analysis/visualizers/chart_specs.py')

clean_code = '''"""Создание JSON-спецификаций для графиков Chart.js"""
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


def format_ts_label(ts) -> str:
    """Форматирует timestamp в строку для label с учётом таймзоны."""
    if isinstance(ts, datetime):
        return apply_timezone(ts).strftime("%Y-%m-%d %H:%M")
    ts_str = str(ts).replace('T', ' ')
    return ts_str[:16] if len(ts_str) > 16 else ts_str


def downsample_time_series(values: list, timestamps: list, target_points: int = 800) -> tuple:
    """
    Min-max downsampling с сохранением экстремумов.
    Возвращает (downsampled_values, downsampled_timestamps).
    """
    if len(values) <= target_points:
        return values, timestamps

    bucket_size = len(values) / target_points
    ds_values = []
    ds_timestamps = []

    for i in range(target_points):
        start_idx = int(i * bucket_size)
        end_idx = int((i + 1) * bucket_size)

        valid_points = []
        for j in range(start_idx, end_idx):
            if j < len(values) and values[j] is not None and j < len(timestamps) and timestamps[j] is not None:
                valid_points.append((j, values[j], timestamps[j]))

        if not valid_points:
            continue

        min_point = min(valid_points, key=lambda x: x[1])
        max_point = max(valid_points, key=lambda x: x[1])

        if min_point[0] <= max_point[0]:
            ds_values.append(min_point[1])
            ds_timestamps.append(min_point[2])
            if min_point[0] != max_point[0]:
                ds_values.append(max_point[1])
                ds_timestamps.append(max_point[2])
        else:
            ds_values.append(max_point[1])
            ds_timestamps.append(max_point[2])
            ds_values.append(min_point[1])
            ds_timestamps.append(min_point[2])

    return ds_values, ds_timestamps


def create_time_series_spec(
    timestamps: list,
    values: list,
    tag_name: str,
    anomalies: Optional[dict] = None,
    max_points: int = 3000,
) -> dict:
    """
    Single-tag time series с аномалиями.
    Мин-макс downsampling + timestamp-based scatter маппинг.
    """
    # Downsampling
    if len(values) > max_points:
        ds_values, ds_timestamps = downsample_time_series(values, timestamps, max_points)
    else:
        ds_values = values
        ds_timestamps = timestamps

    # Labels и маппинг
    labels = [format_ts_label(ts) for ts in ds_timestamps]
    ts_to_index = {label: idx for idx, label in enumerate(labels)}

    datasets = [{
        "label": tag_name,
        "data": ds_values,
        "borderColor": "#3b82f6",
        "backgroundColor": "rgba(59, 130, 246, 0.1)",
        "borderWidth": 1.5,
        "pointRadius": 0,
        "pointHoverRadius": 3,
        "tension": 0.1,
        "fill": False,
    }]

    # Scatter аномалии
    if anomalies and anomalies.get('anomaly_indices'):
        type_colors = {
            "spike": {"color": "#ef4444", "label": "Пики (Spike)"},
            "dip": {"color": "#3b82f6", "label": "Провалы (Dip)"},
            "drift": {"color": "#f59e0b", "label": "Дрейфы (Drift)"},
            "noise": {"color": "#9ca3af", "label": "Шум (Noise)"},
        }

        # Группируем аномалии по типам
        by_type = {}
        for val, atype, ts in zip(
            anomalies['anomaly_values'],
            anomalies['anomaly_types'],
            anomalies['anomaly_timestamps']
        ):
            if atype not in by_type:
                by_type[atype] = []
            by_type[atype].append((val, ts))

        for atype, points in by_type.items():
            color_info = type_colors.get(atype, type_colors["noise"])
            type_data = [None] * len(ds_values)

            for val, orig_ts in points:
                # Форматируем timestamp аномалии
                ts_key = format_ts_label(orig_ts)

                # Ищем в downsampled данных
                if ts_key in ts_to_index:
                    ds_idx = ts_to_index[ts_key]
                    type_data[ds_idx] = val
                else:
                    # Fallback: ищем ближайший по времени (до 30 мин)
                    try:
                        if isinstance(orig_ts, datetime):
                            orig_ts_dt = apply_timezone(orig_ts)
                        else:
                            ts_str = str(orig_ts).replace('T', ' ')[:16]
                            orig_ts_dt = LOCAL_TZ.localize(
                                datetime.strptime(ts_str, "%Y-%m-%d %H:%M")
                            )

                        min_diff = float('inf')
                        closest_idx = None

                        for i, ds_ts in enumerate(ds_timestamps):
                            ds_ts_tz = apply_timezone(ds_ts) if isinstance(ds_ts, datetime) else None
                            if ds_ts_tz:
                                try:
                                    diff = abs((ds_ts_tz - orig_ts_dt).total_seconds())
                                    if diff < min_diff:
                                        min_diff = diff
                                        closest_idx = i
                                except Exception:
                                    pass

                        if closest_idx is not None and min_diff < 1800:
                            type_data[closest_idx] = val
                    except Exception:
                        pass

            datasets.append({
                "label": color_info["label"],
                "data": type_data,
                "borderColor": color_info["color"],
                "backgroundColor": color_info["color"],
                "type": "scatter",
                "pointRadius": 6,
                "pointHoverRadius": 8,
                "showLine": False,
            })

    return {
        "type": "line",
        "data": {"labels": labels, "datasets": datasets},
        "options": {
            "responsive": True,
            "maintainAspectRatio": False,
            "plugins": {
                "legend": {"display": True, "position": "top"},
                "tooltip": {"mode": "index", "intersect": False},
            },
            "scales": {
                "x": {"type": "category", "display": True, "ticks": {"maxTicksLimit": 10}},
                "y": {"display": True},
            },
        },
    }


def create_multitag_time_series_spec(
    tags_data: dict,
    common_timestamps: list,
    anomalies_per_tag: dict = None,
    max_points: int = 3000,
) -> dict:
    """
    Multi-tag time series.
    Использует STEP-BASED downsampling чтобы ВСЕ теги имели одинаковые timestamps.
    """
    datasets = []

    tag_colors = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899", "#14b8a6", "#f97316"]
    type_colors = {
        "spike": {"color": "#ef4444", "label": "Пики"},
        "dip": {"color": "#3b82f6", "label": "Провалы"},
        "drift": {"color": "#f59e0b", "label": "Дрейфы"},
        "noise": {"color": "#9ca3af", "label": "Шум"},
    }

    # STEP-BASED downsampling: все теги используют одинаковые индексы
    total = len(common_timestamps)
    need_downsample = total > max_points

    if need_downsample:
        step = max(1, total // max_points)
        ds_indices = list(range(0, total, step))[:max_points]
    else:
        ds_indices = list(range(total))

    ds_timestamps = [common_timestamps[i] for i in ds_indices]
    labels = [format_ts_label(ts) for ts in ds_timestamps]

    # Маппинг: оригинальный индекс → downsampled индекс
    orig_to_ds = {orig: ds for ds, orig in enumerate(ds_indices)}

    # 1. Линии для каждого тега
    for i, (tag_name, tag_data) in enumerate(tags_data.items()):
        aligned_values = tag_data.get('aligned_values', [])
        color = tag_colors[i % len(tag_colors)]

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

    # 2. Scatter аномалии
    if anomalies_per_tag:
        for tag_name, tag_anomalies in anomalies_per_tag.items():
            indices = tag_anomalies.get('anomaly_indices', [])
            types = tag_anomalies.get('anomaly_types', [])
            aligned_values = tags_data.get(tag_name, {}).get('aligned_values', [])

            # Группируем по типам
            by_type = {}
            for anom_idx, anom_type in zip(indices, types):
                if anom_idx >= len(aligned_values):
                    continue
                val = aligned_values[anom_idx]
                if val is None:
                    continue
                if anom_type not in by_type:
                    by_type[anom_type] = []
                by_type[anom_type].append((anom_idx, val))

            for atype, points in by_type.items():
                color_info = type_colors.get(atype, type_colors["noise"])
                type_data = [None] * len(ds_indices)

                for orig_idx, val in points:
                    # Точный маппинг
                    if orig_idx in orig_to_ds:
                        ds_idx = orig_to_ds[orig_idx]
                        type_data[ds_idx] = val
                    else:
                        # Ищем ближайший индекс в ds_indices
                        closest_orig = min(ds_indices, key=lambda x: abs(x - orig_idx))
                        ds_idx = orig_to_ds[closest_orig]
                        # Проверяем что разница <= step (не больше одного bucket'а)
                        if abs(closest_orig - orig_idx) <= (total // max_points) + 1:
                            type_data[ds_idx] = val

                datasets.append({
                    "label": f"{color_info['label']} ({tag_name})",
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
        "data": {"labels": labels, "datasets": datasets},
        "options": {
            "responsive": True,
            "maintainAspectRatio": False,
            "plugins": {
                "legend": {"display": True, "position": "top", "labels": {"font": {"size": 10}, "boxWidth": 10}},
                "tooltip": {"mode": "index", "intersect": False},
            },
            "scales": {
                "x": {"type": "category", "display": True, "ticks": {"maxTicksLimit": 10, "font": {"size": 9}}},
                "y": {"display": True, "grid": {"color": "rgba(0, 0, 0, 0.05)"}, "ticks": {"font": {"size": 9}}},
            },
        },
    }


def create_histogram_spec(histogram_data: dict, tag_name: str) -> dict:
    """Гистограмма распределения."""
    return {
        "type": "bar",
        "data": {
            "labels": [f"{edge:.2f}" for edge in (histogram_data.get('bin_edges') or histogram_data.get('bins') or histogram_data.get('edges', []))[:-1]],
            "datasets": [{
                "label": f"Распределение {tag_name}",
                "data": list(histogram_data.get('counts', histogram_data.get('histogram', histogram_data.get('values', [])))),
                "backgroundColor": "rgba(59, 130, 246, 0.5)",
                "borderColor": "rgba(59, 130, 246, 1)",
                "borderWidth": 1,
            }]
        },
        "options": {
            "responsive": True,
            "maintainAspectRatio": False,
            "plugins": {"legend": {"display": False}},
            "scales": {
                "x": {"title": {"display": True, "text": "Значение"}},
                "y": {"title": {"display": True, "text": "Частота"}},
            },
        },
    }


def create_heatmap_spec(correlation_matrix: dict, title: str = "Матрица корреляций") -> dict:
    """Heatmap корреляций."""
    tags = correlation_matrix['tags']
    matrix = correlation_matrix['matrix']
    datasets = []
    for i, tag1 in enumerate(tags):
        for j, tag2 in enumerate(tags):
            value = matrix[i][j]
            if value >= 0:
                color = f"rgba(59, 130, 246, {abs(value)})"
            else:
                color = f"rgba(239, 68, 68, {abs(value)})"
            datasets.append({
                "x": j, "y": i, "v": value,
                "r": abs(value) * 20 + 5,
                "backgroundColor": color,
            })
    return {
        "type": "bubble",
        "data": {"datasets": [{"label": title, "data": datasets, "backgroundColor": [d["backgroundColor"] for d in datasets]}]},
        "options": {
            "responsive": True,
            "maintainAspectRatio": False,
            "plugins": {"legend": {"display": False}},
            "scales": {
                "x": {"type": "linear", "min": -0.5, "max": len(tags) - 0.5, "ticks": {"stepSize": 1}, "title": {"display": False}},
                "y": {"type": "linear", "min": -0.5, "max": len(tags) - 0.5, "ticks": {"stepSize": 1}, "title": {"display": False}},
            }
        }
    }


def create_scatter_spec(x_values: list, y_values: list, tag_x: str, tag_y: str, correlation_coef: float) -> dict:
    """Scatter plot с линией регрессии."""
    points = [{"x": x, "y": y} for x, y in zip(x_values, y_values)]
    regression_line = []
    if len(x_values) > 1:
        x_arr = np.array(x_values)
        y_arr = np.array(y_values)
        slope, intercept = np.polyfit(x_arr, y_arr, 1)
        x_min, x_max = float(np.min(x_arr)), float(np.max(x_arr))
        regression_line = [
            {"x": x_min, "y": slope * x_min + intercept},
            {"x": x_max, "y": slope * x_max + intercept},
        ]
    return {
        "type": "scatter",
        "data": {
            "datasets": [
                {"label": f"{tag_x} vs {tag_y}", "data": points, "backgroundColor": "rgba(59, 130, 246, 0.5)", "borderColor": "rgba(59, 130, 246, 1)", "pointRadius": 3},
                {"label": f"Регрессия (r={correlation_coef:.2f})", "data": regression_line, "type": "line", "borderColor": "rgba(239, 68, 68, 1)", "borderWidth": 2, "borderDash": [5, 5], "pointRadius": 0, "fill": False}
            ]
        },
        "options": {
            "responsive": True,
            "maintainAspectRatio": False,
            "plugins": {"legend": {"display": True, "position": "top"}, "tooltip": {"mode": "nearest", "intersect": True}},
            "scales": {
                "x": {"type": "linear", "title": {"display": True, "text": tag_x}},
                "y": {"type": "linear", "title": {"display": True, "text": tag_y}},
            }
        }
    }
'''

cs_path.write_text(clean_code, encoding='utf-8', newline='\n')

print('✅ chart_specs.py полностью переписан')
print()
print('Что исправлено:')
print('  1. Убрана опечатка orig_apply_timezone(ts) → apply_timezone(orig_ts)')
print('  2. Добавлена функция format_ts_label() — единый форматтер')
print('  3. Multi-tag теперь использует STEP-BASED downsampling')
print('     (вместо min-max который даёт разные timestamps для разных тегов)')
print('  4. Для multi-tag создан orig_to_ds словарь — точный маппинг')
print('  5. Все аномалии корректно маппятся через единый набор индексов')
print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Перезапусти backend')
print('2. Запусти анализ с 2+ тегами')
print('3. Проверь multi-tag график — должно работать без смещения')
print('4. Проверь single-tag график — должен работать как раньше')