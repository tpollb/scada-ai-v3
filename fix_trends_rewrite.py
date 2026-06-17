from pathlib import Path

print('=== fix_trends_rewrite.py ===')
print()

PROJECT_ROOT = Path('.')
trends_path = PROJECT_ROOT / 'backend/modules/analytics/analyzers/trends.py'

# ============================================================================
# Полностью переписываем файл с правильным raw_data
# ============================================================================
file_content = '''"""Анализ трендов — работает с агрегированными данными (hourly/daily)"""
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

    # Добавляем raw_data для графиков (первые 200 точек)
    raw_data = []
    for p in data_points[:200]:
        ts = p.get("bucket_start") or p.get("timestamp")
        val = p.get("avg") if "avg" in p else p.get("value")
        if ts is not None and val is not None:
            raw_data.append({"timestamp": ts, "value": val})

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
'''

# Проверяем синтаксис ПЕРЕД записью
try:
    compile(file_content, 'trends.py', 'exec')
    print('✓ Python syntax check passed')
except SyntaxError as e:
    print(f'⚠ Syntax error в самом скрипте: {e}')
    exit(1)

# Записываем файл
trends_path.write_text(file_content, encoding='utf-8', newline='\n')
print(f'✓ Файл перезаписан: {trends_path}')
print(f'  Размер: {len(file_content)} байт')

print()
print('=' * 60)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 60)
print()
print('Файл переписан полностью с правильной структурой:')
print()
print('  def analyze_param_trend(...):')
print('      ... вычисления ...')
print('      ')
print('      # Добавляем raw_data для графиков (первые 200 точек)')
print('      raw_data = []')
print('      for p in data_points[:200]:')
print('          ts = p.get("bucket_start") or p.get("timestamp")')
print('          val = p.get("avg") if "avg" in p else p.get("value")')
print('          if ts is not None and val is not None:')
print('              raw_data.append({"timestamp": ts, "value": val})')
print('      ')
print('      return {')
print('          "param": param_key,')
print('          ...')
print('          "anomaly_rate": round(anomaly_rate, 4),')
print('          "raw_data": raw_data,')
print('      }')
print()
print('Ключевое отличие от предыдущих версий:')
print('  • raw_data = [] ПЕРЕД return (не внутри dict)')
print('  • "raw_data": raw_data ВНУТРИ return dict')
print()
print('Backend перезагрузится автоматически (hot-reload).')
print()
print('Проверка:')
print('  curl "http://localhost:8081/analytics/report?period=7&params=temperature"')
print('  → Должен вернуть JSON с полем "raw_data" в trends.temperature')