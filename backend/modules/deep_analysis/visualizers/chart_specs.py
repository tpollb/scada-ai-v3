"""Генерация JSON-спецификаций для Chart.js"""
from typing import Optional
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
