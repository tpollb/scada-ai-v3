"""Анализ трендов — работает с агрегированными данными (hourly/daily)"""
from typing import Any
from datetime import datetime
import statistics
from structlog import get_logger

log = get_logger()


def analyze_param_trend(param_data: dict) -> dict:
    """
    Анализирует тренд одного параметра на агрегированных данных.

    Args:
        param_data: результат collect_param_history()
            aggregation: "hourly"|"daily"|"raw"
            data_points: [{"bucket_start": ..., "avg": ..., "min": ..., "max": ..., "count": ...}, ...]

    Returns:
        {
            "param": "temperature",
            "aggregation": "hourly",
            "bucket_count": 720,
            "total_raw_count": 488520,
            "outliers_count": 6,
            "avg": 22.5,
            "min": 18.0,
            "max": 26.0,
            "stdev": 2.3,
            "slope_per_day": 0.05,
            "r_squared": 0.78,
            "direction": "rising",
            "anomalies": 12,
            "anomaly_rate": 0.017,
            "raw_data": [{"timestamp": ..., "value": ...}, ...]
        }
    """
    param_key = param_data.get("param", "unknown")
    aggregation = param_data.get("aggregation", "raw")
    data_points = param_data.get("data_points", [])
    total_raw_count = param_data.get("total_raw_count", 0)
    outliers_count = param_data.get("outliers_count", 0)

    if not data_points:
        return {
            "param": param_key,
            "aggregation": aggregation,
            "bucket_count": 0,
            "total_raw_count": total_raw_count,
            "outliers_count": outliers_count,
            "direction": "no_data",
            "raw_data": [],
        }

    # Извлекаем значения (avg для агрегированных, value для raw)
    if aggregation == "raw":
        values = [p["value"] for p in data_points if p.get("value") is not None]
        timestamps_raw = [p["timestamp"] for p in data_points if p.get("timestamp")]
    else:
        values = [p["avg"] for p in data_points if p.get("avg") is not None]
        timestamps_raw = [p["bucket_start"] for p in data_points if p.get("bucket_start")]

    if len(values) < 2:
        return {
            "param": param_key,
            "aggregation": aggregation,
            "bucket_count": len(data_points),
            "total_raw_count": total_raw_count,
            "outliers_count": outliers_count,
            "direction": "insufficient_data",
            "raw_data": [],
        }

    # Базовая статистика
    avg = statistics.mean(values)
    min_val = min(values)
    max_val = max(values)
    stdev = statistics.stdev(values) if len(values) > 1 else 0

    # Парсим timestamps в "дни от начала"
    timestamps_days = []
    valid_values = []
    for ts_str, val in zip(timestamps_raw, values):
        try:
            ts = datetime.fromisoformat(ts_str)
            timestamps_days.append(ts)
            valid_values.append(val)
        except (ValueError, TypeError):
            continue

    if len(valid_values) < 2:
        return {
            "param": param_key,
            "aggregation": aggregation,
            "bucket_count": len(data_points),
            "total_raw_count": total_raw_count,
            "outliers_count": outliers_count,
            "direction": "insufficient_data",
            "raw_data": [],
        }

    # Конвертируем в дни от начала
    start_ts = min(timestamps_days)
    x_days = [(ts - start_ts).total_seconds() / 86400.0 for ts in timestamps_days]

    # Линейная регрессия
    n = len(valid_values)
    x_mean = statistics.mean(x_days)
    y_mean = statistics.mean(valid_values)

    numerator = sum((x_days[i] - x_mean) * (valid_values[i] - y_mean) for i in range(n))
    denominator = sum((x_days[i] - x_mean) ** 2 for i in range(n))

    if denominator == 0:
        slope_per_day = 0
        r_squared = 0
    else:
        slope_per_day = numerator / denominator
        y_pred = [y_mean + slope_per_day * (xi - x_mean) for xi in x_days]
        ss_res = sum((valid_values[i] - y_pred[i]) ** 2 for i in range(n))
        ss_tot = sum((valid_values[i] - y_mean) ** 2 for i in range(n))
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

    # Направление
    if abs(slope_per_day) < 0.01:
        direction = "stable"
    elif slope_per_day > 0:
        direction = "rising"
    else:
        direction = "falling"

    # Аномалии (Z-score > 3 на агрегированных данных)
    anomalies = 0
    if stdev > 0:
        for v in valid_values:
            z = abs((v - avg) / stdev)
            if z > 3:
                anomalies += 1

    anomaly_rate = anomalies / len(valid_values) if valid_values else 0

    # Добавляем raw_data для графиков (адаптивно: все точки если <500, иначе downsampling)
    raw_data_all = []
    for p in data_points:
        ts = p.get("bucket_start") or p.get("timestamp")
        val = p.get("avg") if "avg" in p else p.get("value")
        if ts is not None and val is not None:
            raw_data_all.append({"timestamp": ts, "value": val})

    # Downsampling если точек слишком много (лимит 500 для производительности)
    MAX_POINTS = 500
    if len(raw_data_all) <= MAX_POINTS:
        raw_data = raw_data_all
    else:
        # Берём каждую N-ю точку, но ВСЕГДА включаем последнюю
        step = len(raw_data_all) / MAX_POINTS
        raw_data = []
        i = 0.0
        while int(i) < len(raw_data_all) - 1:
            raw_data.append(raw_data_all[int(i)])
            i += step
        # Гарантированно добавляем последнюю точку
        raw_data.append(raw_data_all[-1])

    return {
        "param": param_key,
        "aggregation": aggregation,
        "bucket_count": len(data_points),
        "total_raw_count": total_raw_count,
        "outliers_count": outliers_count,
        "avg": round(avg, 2),
        "min": round(min_val, 2),
        "max": round(max_val, 2),
        "stdev": round(stdev, 2),
        "slope_per_day": round(slope_per_day, 4),
        "r_squared": round(r_squared, 3),
        "direction": direction,
        "anomalies": anomalies,
        "anomaly_rate": round(anomaly_rate, 4),
        "norms": param_data.get("norms", {}),
        "raw_data": raw_data,
    }


def analyze_trends(history_data: dict) -> dict:
    """
    Анализирует тренды всех параметров.
    """
    trends = {}
    for param_key, param_data in history_data.get("params", {}).items():
        trend = analyze_param_trend(param_data)
        trends[param_key] = trend

    return {
        "period_days": history_data.get("period_days", 0),
        "aggregation": history_data.get("aggregation", "auto"),
        "trends": trends,
    }
