"""Создание JSON-спецификаций для графиков Chart.js"""
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


def downsample_time_series(values: list, timestamps: list, target_points: int = 800) -> tuple[list, list]:
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
    
    return ds_values, ds_timestamps


def create_time_series_spec(
    timestamps: list[datetime],
    values: list[float],
    tag_name: str,
    anomalies: Optional[dict] = None,
    max_points: int = 3000,
) -> dict:
    """
    Создаёт JSON-спецификацию для time series графика.
    
    ВСЕ датасеты используют единый index-based формат для корректной работы
    с Chart.js category шкалой и tooltip mode: 'index'.
    """
    from datetime import datetime
    
    # Downsampling основного ряда
    need_downsample = len(values) > max_points
    if need_downsample:
        ds_values, ds_timestamps = downsample_time_series(values, timestamps, max_points)
    else:
        ds_values = values
        ds_timestamps = timestamps
    
    # Форматируем labels
    labels = []
    for ts in ds_timestamps:
        if isinstance(ts, datetime):
            labels.append(ts.strftime("%Y-%m-%d %H:%M"))
        else:
            ts_str = str(ts).replace('T', ' ')
            labels.append(ts_str[:16] if len(ts_str) > 16 else ts_str)
    
    # Создаём маппинг: timestamp → index в downsampled массиве
    ts_to_index = {}
    for idx, ts in enumerate(ds_timestamps):
        if isinstance(ts, datetime):
            ts_key = ts.strftime("%Y-%m-%d %H:%M")
        else:
            ts_str = str(ts).replace('T', ' ')
            ts_key = ts_str[:16] if len(ts_str) > 16 else ts_str
        ts_to_index[ts_key] = idx
    
    datasets = []
    
    # Основной ряд данных (index-based)
    datasets.append({
        "label": tag_name,
        "data": ds_values,
        "borderColor": "#3b82f6",
        "backgroundColor": "rgba(59, 130, 246, 0.1)",
        "borderWidth": 1.5,
        "pointRadius": 0,
        "pointHoverRadius": 3,
        "tension": 0.1,
        "fill": False,
    })
    
    # Index-based scatter для аномалий
    if anomalies and anomalies.get('anomaly_indices'):
        anomaly_types_list = anomalies.get('anomaly_types', [])
        anomaly_timestamps = anomalies.get('anomaly_timestamps', [])
        anomaly_values = anomalies.get('anomaly_values', [])
        
        type_colors = {
            "spike": {"color": "#ef4444", "label": "Пики (Spike)"},
            "dip": {"color": "#3b82f6", "label": "Провалы (Dip)"},
            "drift": {"color": "#f59e0b", "label": "Дрейфы (Drift)"},
            "noise": {"color": "#9ca3af", "label": "Шум (Noise)"},
        }
        
        # Группируем аномалии по типам
        anomalies_by_type = {}
        for val, atype, ts in zip(anomaly_values, anomaly_types_list, anomaly_timestamps):
            if atype not in anomalies_by_type:
                anomalies_by_type[atype] = []
            anomalies_by_type[atype].append((val, ts))
        
        for atype, points in anomalies_by_type.items():
            color_info = type_colors.get(atype, type_colors.get("noise"))
            
            # Index-based scatter: массив с None, значения только на нужных индексах
            type_data = [None] * len(ds_values)
            
            for val, orig_ts in points:
                # Форматируем timestamp аномалии
                if isinstance(orig_ts, datetime):
                    ts_key = orig_ts.strftime("%Y-%m-%d %H:%M")
                else:
                    ts_str = str(orig_ts).replace('T', ' ')
                    ts_key = ts_str[:16] if len(ts_str) > 16 else ts_str
                
                # Ищем индекс в downsampled массиве
                if ts_key in ts_to_index:
                    ds_idx = ts_to_index[ts_key]
                    type_data[ds_idx] = val
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
                            type_data[closest_idx] = val
                    except Exception:
                        pass
            
            # Все типы рисуем как scatter (точки)
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
        "data": {
            "labels": labels,
            "datasets": datasets,
        },
        "options": {
            "responsive": True,
            "maintainAspectRatio": False,
            "plugins": {
                "legend": {"display": True, "position": "top"},
                "tooltip": {
                    "mode": "index",
                    "intersect": False,
                },
            },
            "scales": {
                "x": {
                    "type": "category",
                    "display": True,
                    "ticks": {"maxTicksLimit": 10},
                },
                "y": {
                    "display": True,
                },
            },
        },
    }



def create_histogram_spec(
    histogram_data: dict,
    tag_name: str,
) -> dict:
    """Создаёт JSON-спецификацию для гистограммы распределения."""
    spec = {
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
            "plugins": {
                "legend": {"display": False},
            },
            "scales": {
                "x": {"title": {"display": True, "text": "Значение"}},
                "y": {"title": {"display": True, "text": "Частота"}},
            },
        },
    }
    
    return spec


def create_heatmap_spec(
    correlation_matrix: dict,
    title: str = "Матрица корреляций"
) -> dict:
    """Создаёт JSON-спецификацию для heatmap (матрица корреляций)."""
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
                "x": j,
                "y": i,
                "v": value,
                "r": abs(value) * 20 + 5,
                "backgroundColor": color,
            })
    
    spec = {
        "type": "bubble",
        "data": {
            "datasets": [{
                "label": title,
                "data": datasets,
                "backgroundColor": [d["backgroundColor"] for d in datasets],
            }]
        },
        "options": {
            "responsive": True,
            "maintainAspectRatio": False,
            "plugins": {
                "legend": {"display": False},
            },
            "scales": {
                "x": {
                    "type": "linear",
                    "min": -0.5,
                    "max": len(tags) - 0.5,
                    "ticks": {"stepSize": 1},
                    "title": {"display": False},
                },
                "y": {
                    "type": "linear",
                    "min": -0.5,
                    "max": len(tags) - 0.5,
                    "ticks": {"stepSize": 1},
                    "title": {"display": False},
                }
            }
        }
    }
    
    return spec


def create_scatter_spec(
    x_values: list[float],
    y_values: list[float],
    tag_x: str,
    tag_y: str,
    correlation_coef: float,
) -> dict:
    """Создаёт JSON-спецификацию для scatter plot с линией регрессии."""
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
    
    spec = {
        "type": "scatter",
        "data": {
            "datasets": [
                {
                    "label": f"{tag_x} vs {tag_y}",
                    "data": points,
                    "backgroundColor": "rgba(59, 130, 246, 0.5)",
                    "borderColor": "rgba(59, 130, 246, 1)",
                    "pointRadius": 3,
                },
                {
                    "label": f"Регрессия (r={correlation_coef:.2f})",
                    "data": regression_line,
                    "type": "line",
                    "borderColor": "rgba(239, 68, 68, 1)",
                    "borderWidth": 2,
                    "borderDash": [5, 5],
                    "pointRadius": 0,
                    "fill": False,
                }
            ]
        },
        "options": {
            "responsive": True,
            "maintainAspectRatio": False,
            "plugins": {
                "legend": {
                    "display": True,
                    "position": "top",
                },
                "tooltip": {
                    "mode": "nearest",
                    "intersect": True,
                },
                "zoom": {
                    "pan": {"enabled": True, "mode": "xy"},
                    "zoom": {
                        "wheel": {"enabled": True, "speed": 0.05},
                        "pinch": {"enabled": True},
                        "mode": "xy",
                    },
                },
            },
            "scales": {
                "x": {
                    "type": "linear",
                    "title": {"display": True, "text": tag_x},
                },
                "y": {
                    "type": "linear",
                    "title": {"display": True, "text": tag_y},
                }
            }
        }
    }
    
    return spec


def create_multitag_time_series_spec(
    tags_data: dict,
    common_timestamps: list,
    anomalies_per_tag: dict = None,
    max_points: int = 3000,
) -> dict:
    """
    Multi-tag: просто вызываем create_time_series_spec для каждого тега.
    Если single-tag работает — повторяем его механизм.
    """
    if not anomalies_per_tag:
        anomalies_per_tag = {}

    all_datasets = []
    first_labels = None

    # Цвета для линий тегов
    tag_line_colors = [
        "#3b82f6", "#10b981", "#f59e0b", "#ef4444",
        "#8b5cf6", "#ec4899", "#14b8a6", "#f97316",
    ]

    # Цвета для аномалий (ОДИНАКОВЫЕ для всех тегов)
    anomaly_colors = {
        "spike": {"color": "#ef4444", "label": "Пики (Spike)"},
        "dip": {"color": "#3b82f6", "label": "Провалы (Dip)"},
        "drift": {"color": "#f59e0b", "label": "Дрейфы (Drift)"},
        "noise": {"color": "#9ca3af", "label": "Шум (Noise)"},
    }

    # Для каждого тега вызываем create_time_series_spec
    for i, (tag_name, tag_data) in enumerate(tags_data.items()):
        aligned_values = tag_data.get('aligned_values', [])
        tag_anomalies_raw = anomalies_per_tag.get(tag_name)

        # ВАЖНО: преобразуем индексы аномалий из valid_values в aligned_values
        # Потому что в API детекция идёт на отфильтрованных значениях
        tag_anomalies = None
        if tag_anomalies_raw and tag_anomalies_raw.get('anomaly_indices'):
            # Создаём маппинг: valid_idx → aligned_idx
            valid_idx = 0
            idx_map = {}
            for aligned_idx, v in enumerate(aligned_values):
                if v is not None:
                    idx_map[valid_idx] = aligned_idx
                    valid_idx += 1

            # Преобразуем индексы
            converted_indices = []
            converted_timestamps = []
            converted_values = []
            converted_types = []

            for anom_idx, anom_ts, anom_val, anom_type in zip(
                tag_anomalies_raw.get('anomaly_indices', []),
                tag_anomalies_raw.get('anomaly_timestamps', []),
                tag_anomalies_raw.get('anomaly_values', []),
                tag_anomalies_raw.get('anomaly_types', [])
            ):
                # Преобразуем индекс из valid_values в aligned_values
                aligned_idx = idx_map.get(anom_idx)
                if aligned_idx is not None and aligned_idx < len(aligned_values):
                    converted_indices.append(aligned_idx)
                    converted_timestamps.append(anom_ts)
                    converted_values.append(aligned_values[aligned_idx])
                    converted_types.append(anom_type)

            if converted_indices:
                tag_anomalies = {
                    'anomaly_indices': converted_indices,
                    'anomaly_timestamps': converted_timestamps,
                    'anomaly_values': converted_values,
                    'anomaly_types': converted_types,
                    'total_anomalies': len(converted_indices),
                }

        # Вызываем РАБОЧИЙ single-tag механизм
        tag_spec = create_time_series_spec(
            timestamps=common_timestamps,
            values=aligned_values,
            tag_name=tag_name,
            anomalies=tag_anomalies,
            max_points=max_points,
        )

        # Берём labels из первого тега
        if first_labels is None:
            first_labels = tag_spec['data']['labels']

        # Обрабатываем datasets
        for j, dataset in enumerate(tag_spec['data']['datasets']):
            if j == 0:
                # Первый dataset — основная линия тега: меняем цвет
                dataset['borderColor'] = tag_line_colors[i % len(tag_line_colors)]
                dataset['backgroundColor'] = tag_line_colors[i % len(tag_line_colors)]
                all_datasets.append(dataset)
            else:
                # Остальные — аномалии: используем общие цвета
                label = dataset.get('label', '')
                for atype, color_info in anomaly_colors.items():
                    if atype in label.lower() or color_info['label'] in label:
                        dataset['borderColor'] = color_info['color']
                        dataset['backgroundColor'] = color_info['color']
                        # Убираем имя тега из label аномалии чтобы не дублировать
                        if f"({tag_name})" in label:
                            dataset['label'] = color_info['label']
                        break
                all_datasets.append(dataset)

    if first_labels is None:
        first_labels = []

    return {
        "type": "line",
        "data": {
            "labels": first_labels,
            "datasets": all_datasets,
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

