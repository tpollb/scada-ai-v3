from pathlib import Path

print('=== add_correlations.py ===')
print()

# ============================================================================
# 1. analyzers/correlations.py — Pearson correlation между параметрами
# ============================================================================
corr_path = Path('modules/analytics/analyzers/correlations.py')
corr_content = '''"""Корреляционный анализ — Pearson между парами параметров"""
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
'''

corr_path.write_text(corr_content, encoding='utf-8', newline='\n')
print('✓ analyzers/correlations.py: Pearson correlation между парами параметров')

# ============================================================================
# 2. Обновляем api/routes/analytics.py — добавляем correlations
# ============================================================================
router_path = Path('api/routes/analytics.py')
router_content = '''"""Analytics API — тренды, корреляции и аналитика"""
from fastapi import APIRouter, Query
from datetime import datetime
from structlog import get_logger

from modules.analytics.collectors.history import collect_history
from modules.analytics.analyzers.trends import analyze_trends
from modules.analytics.analyzers.correlations import find_correlations

log = get_logger()
router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/ping")
async def ping():
    """Простой health-check"""
    return {"status": "ok", "time": datetime.now().isoformat()}


@router.get("/report")
async def get_report(
    period: int = Query(30, description="Период в днях (7, 30, 90, 365)"),
    params: str = Query("all", description="Параметры через запятую или 'all'"),
    aggregation: str = Query("auto", description="Агрегация: raw/hourly/daily/auto"),
    min_correlation: float = Query(0.5, description="Минимальный |r| для корреляций"),
):
    """
    Отчёт аналитики: тренды, корреляции, статистика.

    aggregation:
      - raw: все сырые точки (LIMIT 100000) — только для коротких периодов
      - hourly: GROUP BY hour — для 7-90 дней
      - daily: GROUP BY day — для >90 дней
      - auto: автоматически по периоду
    
    min_correlation:
      - Минимальный |коэффициент| для включения в correlations
      - По умолчанию 0.5 (умеренная корреляция)
    """
    log.info(
        "analytics/report requested",
        period=period,
        params=params,
        aggregation=aggregation,
        min_correlation=min_correlation,
    )

    # Парсим params
    if params == "all":
        params_list = None
    else:
        params_list = [p.strip() for p in params.split(",")]

    # 1. Собираем историю (с валидацией + агрегацией)
    history = await collect_history(
        days=period,
        params=params_list,
        aggregation=aggregation,
    )

    # 2. Анализируем тренды
    trends = analyze_trends(history)

    # 3. Находим корреляции
    correlations = find_correlations(
        history,
        min_correlation=min_correlation,
    )

    log.info(
        "analytics/report ready",
        period=period,
        aggregation=history["aggregation"],
        params=list(trends["trends"].keys()),
        correlations=len(correlations),
    )

    return {
        "period_days": period,
        "aggregation": history["aggregation"],
        "collected_at": history["collected_at"],
        "trends": trends["trends"],
        "correlations": correlations,
    }
'''

router_path.write_text(router_content, encoding='utf-8', newline='\n')
print('✓ api/routes/analytics.py: добавлены корреляции в отчёт')

print()
print('=' * 60)
print('ЧТО ДОБАВЛЕНО:')
print('=' * 60)
print()
print('1. analyzers/correlations.py:')
print('   • Pearson correlation между всеми парами параметров')
print('   • Выравнивание временных рядов по timestamp')
print('   • Фильтрация по min_correlation (по умолчанию 0.5)')
print('   • Интерпретация: positive/negative, strong/moderate/weak')
print('   • Сортировка по убыванию |coefficient|')
print()
print('2. api/routes/analytics.py:')
print('   • Новый параметр: min_correlation (float, default=0.5)')
print('   • В ответ добавлено поле "correlations": [...]')
print()
print('Backend перезагрузится автоматически (hot-reload).')
print()
print('Проверка:')
print('  curl "http://localhost:8081/analytics/report?period=30&params=all"')
print()
print('Ожидаемый результат:')
print('  "correlations": [')
print('    {')
print('      "params": ["humidity", "temperature"],')
print('      "coefficient": -0.68,')
print('      "interpretation": "negative",')
print('      "strength": "moderate",')
print('      "sample_size": 450')
print('    },')
print('    ...')
print('  ]')