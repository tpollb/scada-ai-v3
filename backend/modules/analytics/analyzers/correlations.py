"""Корреляционный анализ — Pearson между парами параметров"""
from typing import Any
from datetime import datetime
import statistics
import math
from structlog import get_logger

log = get_logger()


def _pearson_correlation(x: list[float], y: list[float]) -> tuple[float, int]:
    """
    Вычисляет коэффициент корреляции Пирсона между двумя списками.
    
    Returns:
        (r, n) — коэффициент корреляции и размер выборки
    """
    n = len(x)
    if n < 3:
        return 0.0, n
    
    x_mean = statistics.mean(x)
    y_mean = statistics.mean(y)
    
    numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
    denom_x = sum((x[i] - x_mean) ** 2 for i in range(n))
    denom_y = sum((y[i] - y_mean) ** 2 for i in range(n))
    
    denominator = math.sqrt(denom_x * denom_y)
    
    if denominator == 0:
        return 0.0, n
    
    r = numerator / denominator
    return r, n


def _align_timeseries(
    param_a_data: dict,
    param_b_data: dict,
) -> tuple[list[float], list[float]]:
    """
    Выравнивает два временных ряда по timestamp (только совпадающие buckets).
    
    Args:
        param_a_data, param_b_data: результаты collect_param_history()
            data_points: [{"bucket_start": "2026-06-16T10:00:00", "avg": 22.5}, ...]
    
    Returns:
        (values_a, values_b) — выровненные значения
    """
    # Строим словари {timestamp: avg_value}
    map_a = {}
    for p in param_a_data.get("data_points", []):
        ts = p.get("bucket_start") or p.get("timestamp")
        val = p.get("avg") if "avg" in p else p.get("value")
        if ts and val is not None:
            map_a[ts] = val
    
    map_b = {}
    for p in param_b_data.get("data_points", []):
        ts = p.get("bucket_start") or p.get("timestamp")
        val = p.get("avg") if "avg" in p else p.get("value")
        if ts and val is not None:
            map_b[ts] = val
    
    # Находим пересечение timestamp'ов
    common_timestamps = sorted(set(map_a.keys()) & set(map_b.keys()))
    
    values_a = [map_a[ts] for ts in common_timestamps]
    values_b = [map_b[ts] for ts in common_timestamps]
    
    return values_a, values_b


def find_correlations(
    history_data: dict,
    min_correlation: float = 0.5,
    min_sample_size: int = 10,
) -> list[dict]:
    """
    Находит корреляции между всеми парами параметров.
    
    Args:
        history_data: результат collect_history()
        min_correlation: минимальный |r| для включения в результат
        min_sample_size: минимальный размер выборки
    
    Returns:
        [
            {
                "params": ["co2", "temperature"],
                "coefficient": 0.68,
                "abs_coefficient": 0.68,
                "interpretation": "positive" | "negative" | "weak",
                "sample_size": 450,
                "strength": "strong" | "moderate" | "weak",
            },
            ...
        ]
        Отсортировано по убыванию |coefficient|.
    """
    params_data = history_data.get("params", {})
    param_keys = list(params_data.keys())
    
    if len(param_keys) < 2:
        return []
    
    correlations = []
    
    # Перебираем все пары (i, j) где i < j
    for i in range(len(param_keys)):
        for j in range(i + 1, len(param_keys)):
            param_a = param_keys[i]
            param_b = param_keys[j]
            
            data_a = params_data[param_a]
            data_b = params_data[param_b]
            
            # Выравниваем временные ряды
            values_a, values_b = _align_timeseries(data_a, data_b)
            
            if len(values_a) < min_sample_size:
                continue
            
            # Считаем корреляцию
            r, n = _pearson_correlation(values_a, values_b)
            
            # Фильтруем по минимальному порогу
            if abs(r) < min_correlation:
                continue
            
            # Интерпретация
            abs_r = abs(r)
            if abs_r >= 0.7:
                strength = "strong"
            elif abs_r >= 0.5:
                strength = "moderate"
            else:
                strength = "weak"
            
            if r > 0:
                interpretation = "positive"
            elif r < 0:
                interpretation = "negative"
            else:
                interpretation = "none"
            
            correlations.append({
                "params": [param_a, param_b],
                "coefficient": round(r, 3),
                "abs_coefficient": round(abs_r, 3),
                "interpretation": interpretation,
                "strength": strength,
                "sample_size": n,
            })
    
    # Сортируем по убыванию |coefficient|
    correlations.sort(key=lambda c: c["abs_coefficient"], reverse=True)
    
    log.info(
        "correlations found",
        total=len(correlations),
        strong=sum(1 for c in correlations if c["strength"] == "strong"),
    )
    
    return correlations
