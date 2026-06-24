#!/usr/bin/env python3
"""
fix_chart_specs_syntax.py — полная перезапись chart_specs.py
"""

from pathlib import Path

print('=' * 70)
print('ПОЛНАЯ ПЕРЕЗАПИСЬ chart_specs.py (фикс SyntaxError)')
print('=' * 70)
print()

chart_specs_path = Path('backend/modules/deep_analysis/visualizers/chart_specs.py')

new_content = '''"""Создание JSON-спецификаций для графиков Chart.js"""
from typing import Optional
from datetime import datetime
import numpy as np
from structlog import get_logger

log = get_logger()


def downsample_time_series(values: list, timestamps: list, target_points: int = 800) -> tuple[list, list]:
    """
    Downsample временной ряд до target_points точек через усреднение по bucket'ам.
    
    Алгоритм:
    1. Делим диапазон на N bucket'ов
    2. Для каждого bucket считаем среднее значение
    3. Timestamp берём из середины bucket'а
    
    Args:
        values: значения (с None для пропусков)
        timestamps: соответствующие timestamps
        target_points: целевое количество точек
    
    Returns:
        (downsampled_values, downsampled_timestamps)
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
        
        valid_values = [v for v in bucket_values if v is not None]
        
        if valid_values:
            ds_values.append(sum(valid_values) / len(valid_values))
            mid_idx = start_idx + len(bucket_timestamps) // 2
            if mid_idx < len(bucket_timestamps):
                ds_timestamps.append(bucket_timestamps[mid_idx])
            else:
                ds_timestamps.append(bucket_timestamps[-1] if bucket_timestamps else None)
        else:
            ds_values.append(None)
            ds_timestamps.append(None)
    
    return ds_values, ds_timestamps


def create_time_series_spec(
    timestamps: list[datetime],
    values: list[float],
    tag_name: str,
    anomalies: Optional[dict] = None,
) -> dict:
    """
    Создаёт JSON-спецификацию для time series графика с цветовой кодировкой аномалий.
    
    Цвета аномалий:
    - 🔴 Spike (пик) — красный
    - 🔵 Dip (провал) — синий
    - 🟠 Drift (дрейф) — оранжевый
    - ⚪ Noise (шум) — серый
    """
    # Форматируем labels
    labels = []
    for ts in timestamps:
        if isinstance(ts, datetime):
            labels.append(ts.strftime("%Y-%m-%d %H:%M"))
        else:
            labels.append(str(ts))
    
    datasets = []
    
    # Основной ряд данных
    datasets.append({
        "label": tag_name,
        "data": values,
        "borderColor": "#3b82f6",
        "backgroundColor": "rgba(59, 130, 246, 0.1)",
        "borderWidth": 1.5,
        "pointRadius": 0,
        "pointHoverRadius": 3,
        "tension": 0.1,
        "fill": False,
    })
    
    # Если есть аномалии — добавляем scatter datasets по типам
    if anomalies and anomalies.get('anomaly_indices'):
        anomaly_types = anomalies.get('anomaly_types', [])
        
        type_colors = {
            "spike": {"color": "#ef4444", "label": "Пики (Spike)"},
            "dip": {"color": "#3b82f6", "label": "Провалы (Dip)"},
            "drift": {"color": "#f59e0b", "label": "Дрейфы (Drift)"},
            "noise": {"color": "#6b7280", "label": "Шум (Noise)"},
            "unknown": {"color": "#ef4444", "label": "Аномалии"},
        }
        
        anomalies_by_type = {}
        for idx, val, atype in zip(
            anomalies['anomaly_indices'], 
            anomalies['anomaly_values'], 
            anomaly_types
        ):
            if atype not in anomalies_by_type:
                anomalies_by_type[atype] = []
            anomalies_by_type[atype].append((idx, val))
        
        for atype, points in anomalies_by_type.items():
            color_info = type_colors.get(atype, type_colors["unknown"])
            
            type_data = [None] * len(values)
            for idx, val in points:
                if 0 <= idx < len(type_data):
                    type_data[idx] = val
            
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
                    "labels": {"font": {"size": 11}, "boxWidth": 12},
                },
                "tooltip": {
                    "mode": "index",
                    "intersect": False,
                },
                "zoom": {
                    "pan": {"enabled": True, "mode": "x"},
                    "zoom": {
                        "wheel": {"enabled": True, "speed": 0.05},
                        "pinch": {"enabled": True},
                        "drag": {
                            "enabled": True,
                            "modifierKey": "shift",
                            "backgroundColor": "rgba(59, 130, 246, 0.1)",
                        },
                        "mode": "x",
                    },
                },
            },
            "scales": {
                "x": {
                    "display": True,
                    "grid": {"display": False},
                    "ticks": {"maxTicksLimit": 10, "font": {"size": 10}},
                },
                "y": {
                    "display": True,
                    "grid": {"color": "rgba(0, 0, 0, 0.05)"},
                    "ticks": {"font": {"size": 10}},
                },
            },
            "interaction": {
                "mode": "nearest",
                "axis": "x",
                "intersect": False,
            },
        },
    }
    
    return spec


def create_histogram_spec(
    histogram_data: dict,
    tag_name: str,
) -> dict:
    """Создаёт JSON-спецификацию для гистограммы распределения."""
    spec = {
        "type": "bar",
        "data": {
            "labels": [f"{edge:.2f}" for edge in histogram_data['bin_edges'][:-1]],
            "datasets": [{
                "label": f"Распределение {tag_name}",
                "data": histogram_data['counts'],
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
    max_points: int = 800,
) -> dict:
    """
    Создаёт time series spec для мульти-тег графика с downsampling.
    
    Показывает:
    - Линии для каждого тега (разные цвета, downsampled до max_points)
    - Scatter points для аномалий с цветовой кодировкой по типам
    
    Args:
        tags_data: {tag_name: {"aligned_values": [...], ...}, ...}
        common_timestamps: общие timestamps
        anomalies_per_tag: {tag_name: {"anomaly_indices": [...], "anomaly_types": [...], ...}, ...}
        max_points: максимальное количество точек (по умолчанию 800 для производительности)
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
        "noise": {"color": "#6b7280", "label": "Шум"},
    }
    
    # Downsampling
    need_downsample = len(common_timestamps) > max_points
    
    if need_downsample:
        ds_timestamps, _ = downsample_time_series(
            list(range(len(common_timestamps))),
            common_timestamps,
            max_points
        )
        ds_timestamps = [t for t in ds_timestamps if t is not None]
    else:
        ds_timestamps = common_timestamps
    
    # Форматируем labels
    labels = []
    for ts in ds_timestamps:
        if isinstance(ts, datetime):
            labels.append(ts.strftime("%Y-%m-%d %H:%M"))
        else:
            labels.append(str(ts))
    
    # 1. Добавляем линии для каждого тега (с downsampling)
    for i, (tag_name, tag_data) in enumerate(tags_data.items()):
        aligned_values = tag_data.get('aligned_values', [])
        color = tag_colors[i % len(tag_colors)]
        
        if need_downsample:
            ds_values, _ = downsample_time_series(aligned_values, common_timestamps, max_points)
        else:
            ds_values = aligned_values
        
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
    
    # 2. Добавляем scatter points для аномалий по типам
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
                anomalies_by_type[key]["points"].append((ds_idx, value))
        
        # Создаём dataset для каждого типа аномалий
        for key, info in anomalies_by_type.items():
            atype = info["type"]
            tag_name = info["tag"]
            color_info = type_colors.get(atype, type_colors["noise"])
            
            type_data = [None] * len(ds_timestamps)
            for idx, val in info["points"]:
                if 0 <= idx < len(type_data):
                    type_data[idx] = val
            
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
                "zoom": {
                    "pan": {"enabled": True, "mode": "x"},
                    "zoom": {
                        "wheel": {"enabled": True, "speed": 0.05},
                        "pinch": {"enabled": True},
                        "drag": {
                            "enabled": True,
                            "modifierKey": "shift",
                            "backgroundColor": "rgba(59, 130, 246, 0.1)",
                        },
                        "mode": "x",
                    },
                },
            },
            "scales": {
                "x": {
                    "display": True,
                    "grid": {"display": False},
                    "ticks": {"maxTicksLimit": 10, "font": {"size": 9}},
                },
                "y": {
                    "display": True,
                    "grid": {"color": "rgba(0, 0, 0, 0.05)"},
                    "ticks": {"font": {"size": 9}},
                },
            },
            "interaction": {
                "mode": "nearest",
                "axis": "x",
                "intersect": False,
            },
        },
    }
    
    return spec
'''

chart_specs_path.write_text(new_content, encoding='utf-8', newline='\n')

print('✓ chart_specs.py полностью перезаписан')
print()
print('Содержимое файла:')
print('  • downsample_time_series() — сжатие данных до 800 точек')
print('  • create_time_series_spec() — single-tag с цветовой кодировкой аномалий')
print('  • create_histogram_spec() — гистограмма распределения')
print('  • create_heatmap_spec() — матрица корреляций')
print('  • create_scatter_spec() — scatter plot + регрессия (БЕЗ callbacks)')
print('  • create_multitag_time_series_spec() — мульти-тег с downsampling')
print()
print('Исправлено:')
print('  ✓ Убраны callback функции из tooltip options')
print('  ✓ Правильный синтаксис Python (все скобки закрыты)')
print('  ✓ Downsampling для производительности (8641 → 800 точек)')
print()
print('=' * 70)
print('ПРОВЕРКА:')
print('=' * 70)
print()
print('Backend должен перезапуститься автоматически без SyntaxError.')
print()
print('Затем проверь мульти-тег анализ:')
print('  curl -X POST http://localhost:8081/api/v1/deep_analysis/run \\')
print('    -H "Content-Type: application/json" \\')
print('    -d \'{"tags": ["KITCHEN2-CO2", "KITCHEN2-Temperature"], "period": 30}\'')
print()
print('График должен рендериться БЫСТРО (~800 точек вместо 8641).')