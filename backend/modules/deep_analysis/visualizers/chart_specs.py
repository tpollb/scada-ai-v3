"""Генерация JSON-спецификаций для Chart.js"""
from typing import Optional
import numpy as np
from datetime import datetime
from structlog import get_logger

log = get_logger()


def create_time_series_spec(
    timestamps: list[datetime],
    values: list[float],
    tag_name: str,
    anomalies: Optional[dict] = None,
) -> dict:
    """
    Создаёт JSON-спецификацию для time series графика.
    
    Args:
        timestamps: массив timestamps
        values: массив значений
        tag_name: имя тега (для заголовка)
        anomalies: результат от detect_anomalies_isolation_forest
    
    Returns:
        Chart.js конфигурация (dict) для передачи в Line компонент
    """
    # Форматируем timestamps для Chart.js
    labels = [ts.strftime("%Y-%m-%d %H:%M") for ts in timestamps]
    
    # Основной dataset (данные)
    datasets = [
        {
            "label": tag_name,
            "data": values,
            "borderColor": "#3b82f6",  # синий
            "backgroundColor": "#3b82f620",
            "tension": 0.3,
            "fill": False,
            "pointRadius": 0,
            "pointHoverRadius": 4,
        }
    ]
    
    # Если есть аномалии — добавляем scatter dataset
    if anomalies and anomalies['anomaly_indices']:
        # Создаём массив с null для нормальных точек
        anomaly_data = [None] * len(values)
        for idx, val in zip(anomalies['anomaly_indices'], anomalies['anomaly_values']):
            anomaly_data[idx] = val
        
        datasets.append({
            "label": "Аномалии",
            "data": anomaly_data,
            "borderColor": "#ef4444",  # красный
            "backgroundColor": "#ef4444",
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
                },
                "tooltip": {
                    "mode": "index",
                    "intersect": False,
                },
            },
            "scales": {
                "x": {
                    "display": True,
                    "grid": {"display": False},
                    "ticks": {"maxTicksLimit": 10},
                },
                "y": {
                    "display": True,
                    "grid": {"color": "rgba(0, 0, 0, 0.05)"},
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
    """
    Создаёт спецификацию для гистограммы распределения.
    
    Args:
        histogram_data: результат от compute_histogram()
        tag_name: имя тега
    
    Returns:
        Chart.js конфигурация для Bar chart
    """
    spec = {
        "type": "bar",
        "data": {
            "labels": [f"{x:.2f}" for x in histogram_data['bin_centers']],
            "datasets": [
                {
                    "label": f"Распределение {tag_name}",
                    "data": histogram_data['bin_counts'],
                    "backgroundColor": "#3b82f680",
                    "borderColor": "#3b82f6",
                    "borderWidth": 1,
                }
            ],
        },
        "options": {
            "responsive": True,
            "maintainAspectRatio": False,
            "plugins": {
                "legend": {"display": False},
            },
            "scales": {
                "x": {
                    "display": True,
                    "title": {"display": True, "text": "Значение"},
                },
                "y": {
                    "display": True,
                    "title": {"display": True, "text": "Частота"},
                },
            },
        },
    }
    
    return spec


def create_heatmap_spec(
    correlation_matrix: dict,
    title: str = "Матрица корреляций"
) -> dict:
    """
    Создаёт JSON-спецификацию для heatmap (матрица корреляций).
    
    Args:
        correlation_matrix: результат от compute_correlation_matrix()
        title: заголовок графика
    
    Returns:
        Chart.js конфигурация для heatmap
    """
    tags = correlation_matrix['tags']
    matrix = correlation_matrix['matrix']
    
    # Форматируем данные для Chart.js heatmap
    # Chart.js не имеет встроенного heatmap, поэтому используем scatter с цветами
    datasets = []
    
    for i, tag1 in enumerate(tags):
        for j, tag2 in enumerate(tags):
            value = matrix[i][j]
            # Цвет: красный (отрицательная) → белый (ноль) → синий (положительная)
            if value >= 0:
                color = f"rgba(59, 130, 246, {abs(value)})"  # синий
            else:
                color = f"rgba(239, 68, 68, {abs(value)})"  # красный
            
            datasets.append({
                "x": j,
                "y": i,
                "v": value,
                "r": abs(value) * 20 + 5,  # размер точки
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
                "tooltip": {
                    "callbacks": {
                        "label": f"function(context) {{ return '{tags[0]}: ' + context.raw.v.toFixed(2); }}"
                    }
                }
            },
            "scales": {
                "x": {
                    "type": "linear",
                    "min": -0.5,
                    "max": len(tags) - 0.5,
                    "ticks": {
                        "callback": f"function(value) {{ return {tags}[value] || ''; }}",
                        "stepSize": 1,
                    },
                    "title": {"display": False},
                },
                "y": {
                    "type": "linear",
                    "min": -0.5,
                    "max": len(tags) - 0.5,
                    "ticks": {
                        "callback": f"function(value) {{ return {tags}[value] || ''; }}",
                        "stepSize": 1,
                    },
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
    """
    Создаёт JSON-спецификацию для scatter plot (пара тегов).
    
    Returns:
        Chart.js конфигурация для scatter plot с линией регрессии
    """
    # Точки данных
    points = [{"x": x, "y": y} for x, y in zip(x_values, y_values)]
    
    # Линия регрессии (линейная)
    if len(x_values) > 1:
        x_arr = np.array(x_values)
        y_arr = np.array(y_values)
        slope, intercept = np.polyfit(x_arr, y_arr, 1)
        
        # Две точки для линии регрессии
        x_min, x_max = float(np.min(x_arr)), float(np.max(x_arr))
        regression_line = [
            {"x": x_min, "y": slope * x_min + intercept},
            {"x": x_max, "y": slope * x_max + intercept},
        ]
    else:
        regression_line = []
    
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
                }
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
