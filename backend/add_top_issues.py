from pathlib import Path

print('=== add_top_issues.py ===')
print()

# ============================================================================
# 1. analyzers/aggregators.py — ранжирование проблем по влиянию
# ============================================================================
agg_path = Path('modules/analytics/analyzers/aggregators.py')
agg_content = '''"""Ранжирование проблем по влиянию на health score"""
from typing import Any
from structlog import get_logger

log = get_logger()


# Веса параметров в environmental index (из health/analysis.py)
PARAM_WEIGHTS = {
    "co2": 0.30,
    "temperature": 0.25,
    "voc": 0.20,
    "humidity": 0.15,
    "pressure": 0.10,
}


def _calculate_param_impact(
    param_key: str,
    trend_data: dict,
    norms: dict,
    period_days: int,
) -> dict:
    """
    Вычисляет влияние одного параметра на health score.

    Args:
        param_key: ключ параметра
        trend_data: результат analyze_param_trend()
        norms: {"opt_min": 18, "opt_max": 24, "crit_min": 10, "crit_max": 35}
        period_days: период анализа в днях

    Returns:
        {
            "param": "humidity",
            "impact": -12.5,              # баллы (отрицательное = проблема)
            "reason": "Rising +0.74%/day, R²=0.591",
            "severity": "high",
            "weight": 0.15,
            "components": {
                "deviation": -2.1,
                "trend": -8.5,
                "anomalies": -1.2,
                "outliers": -0.7,
            }
        }
    """
    weight = PARAM_WEIGHTS.get(param_key, 0.10)
    opt_min = norms.get("opt_min", 0)
    opt_max = norms.get("opt_max", 100)
    crit_min = norms.get("crit_min", opt_min - 10)
    crit_max = norms.get("crit_max", opt_max + 10)

    avg = trend_data.get("avg", (opt_min + opt_max) / 2)
    slope = trend_data.get("slope_per_day", 0)
    r_squared = trend_data.get("r_squared", 0)
    direction = trend_data.get("direction", "stable")
    anomaly_rate = trend_data.get("anomaly_rate", 0)
    outliers_count = trend_data.get("outliers_count", 0)
    total_raw_count = trend_data.get("total_raw_count", 1)

    # 1. Отклонение от нормы
    opt_center = (opt_min + opt_max) / 2
    opt_range = opt_max - opt_min
    crit_range = crit_max - crit_min

    deviation = abs(avg - opt_center)
    if deviation <= opt_range / 2:
        deviation_penalty = 0
    else:
        excess = deviation - opt_range / 2
        deviation_penalty = -(excess / crit_range) * weight * 20

    # 2. Тренд (если slope большой и direction плохой)
    trend_penalty = 0
    if abs(slope) > 0.01 and r_squared > 0.1:
        # Сколько дней до достижения критической границы
        if slope > 0:
            days_to_crit = (crit_max - avg) / slope if slope > 0 else 999
        else:
            days_to_crit = (avg - crit_min) / abs(slope) if slope < 0 else 999

        # Если достигнем критической границы в разумные сроки
        if days_to_crit < 90:
            urgency = 1 - (days_to_crit / 90)  # 0..1
            trend_penalty = -urgency * r_squared * weight * 30

    # 3. Аномалии (выбросы в данных)
    anomaly_penalty = -anomaly_rate * 100 * weight * 10

    # 4. Битые датчики (outliers)
    outlier_rate = outliers_count / total_raw_count if total_raw_count > 0 else 0
    outlier_penalty = -outlier_rate * weight * 15

    # Суммарный impact
    total_impact = deviation_penalty + trend_penalty + anomaly_penalty + outlier_penalty

    # Формируем reason
    reasons = []
    if abs(deviation_penalty) > 0.5:
        reasons.append(f"Avg {avg:.1f} outside optimal range")
    if abs(trend_penalty) > 0.5:
        reasons.append(f"{direction.capitalize()} {abs(slope):.2f}/day (R²={r_squared:.2f})")
    if abs(anomaly_penalty) > 0.5:
        reasons.append(f"{anomaly_rate:.1%} anomalies")
    if abs(outlier_penalty) > 0.5:
        reasons.append(f"{outlier_rate:.1%} broken sensors")

    reason = ", ".join(reasons) if reasons else "Within normal range"

    # Severity
    if total_impact > -5:
        severity = "low"
    elif total_impact > -15:
        severity = "medium"
    elif total_impact > -30:
        severity = "high"
    else:
        severity = "critical"

    return {
        "param": param_key,
        "impact": round(total_impact, 2),
        "reason": reason,
        "severity": severity,
        "weight": weight,
        "components": {
            "deviation": round(deviation_penalty, 2),
            "trend": round(trend_penalty, 2),
            "anomalies": round(anomaly_penalty, 2),
            "outliers": round(outlier_penalty, 2),
        },
    }


def rank_issues(
    history_data: dict,
    trends_data: dict,
    top_n: int = 5,
) -> list[dict]:
    """
    Ранжирует проблемы по влиянию на health score.

    Args:
        history_data: результат collect_history() (содержит norms)
        trends_data: результат analyze_trends()
        top_n: сколько топ проблем вернуть

    Returns:
        [
            {
                "param": "humidity",
                "impact": -12.5,
                "reason": "Rising +0.74%/day, R²=0.591",
                "severity": "high",
                "weight": 0.15,
                "components": {...}
            },
            ...
        ]
        Отсортировано по возрастанию impact (самые негативные первые).
    """
    from modules.health.data_collectors import PARAM_GROUPS

    params_history = history_data.get("params", {})
    trends = trends_data.get("trends", {})
    period_days = history_data.get("period_days", 30)

    issues = []

    for param_key, trend_data in trends.items():
        if param_key not in params_history:
            continue

        param_history = params_history[param_key]
        norms = param_history.get("norms", {})

        # Пропускаем если нет данных
        if trend_data.get("bucket_count", 0) == 0:
            continue

        issue = _calculate_param_impact(
            param_key=param_key,
            trend_data=trend_data,
            norms=norms,
            period_days=period_days,
        )

        # Включаем только если есть реальная проблема (impact < -1)
        if issue["impact"] < -1:
            issues.append(issue)

    # Сортируем по возрастанию impact (самые негативные первые)
    issues.sort(key=lambda x: x["impact"])

    # Берём топ-N
    top_issues = issues[:top_n]

    log.info(
        "issues ranked",
        total=len(issues),
        returned=len(top_issues),
        worst=top_issues[0]["param"] if top_issues else "none",
    )

    return top_issues
'''

agg_path.write_text(agg_content, encoding='utf-8', newline='\n')
print('✓ analyzers/aggregators.py: ранжирование проблем по влиянию на health score')

# ============================================================================
# 2. Обновляем api/routes/analytics.py — добавляем top_issues
# ============================================================================
router_path = Path('api/routes/analytics.py')
router_content = '''"""Analytics API — тренды, корреляции, топ проблем"""
from fastapi import APIRouter, Query
from datetime import datetime
from structlog import get_logger

from modules.analytics.collectors.history import collect_history
from modules.analytics.analyzers.trends import analyze_trends
from modules.analytics.analyzers.correlations import find_correlations
from modules.analytics.analyzers.aggregators import rank_issues

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
    top_issues_count: int = Query(5, description="Количество топ проблем"),
):
    """
    Отчёт аналитики: тренды, корреляции, топ проблем.

    aggregation:
      - raw: все сырые точки (LIMIT 100000) — только для коротких периодов
      - hourly: GROUP BY hour — для 7-90 дней
      - daily: GROUP BY day — для >90 дней
      - auto: автоматически по периоду

    min_correlation:
      - Минимальный |коэффициент| для включения в correlations
      - По умолчанию 0.5 (умеренная корреляция)
    
    top_issues_count:
      - Количество топ проблем в ответе
      - По умолчанию 5
    """
    log.info(
        "analytics/report requested",
        period=period,
        params=params,
        aggregation=aggregation,
        min_correlation=min_correlation,
        top_issues_count=top_issues_count,
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

    # 4. Ранжируем проблемы
    top_issues = rank_issues(
        history_data=history,
        trends_data=trends,
        top_n=top_issues_count,
    )

    log.info(
        "analytics/report ready",
        period=period,
        aggregation=history["aggregation"],
        params=list(trends["trends"].keys()),
        correlations=len(correlations),
        top_issues=len(top_issues),
    )

    return {
        "period_days": period,
        "aggregation": history["aggregation"],
        "collected_at": history["collected_at"],
        "trends": trends["trends"],
        "correlations": correlations,
        "top_issues": top_issues,
    }
'''

router_path.write_text(router_content, encoding='utf-8', newline='\n')
print('✓ api/routes/analytics.py: добавлены top_issues в отчёт')

print()
print('=' * 60)
print('ЧТО ДОБАВЛЕНО:')
print('=' * 60)
print()
print('1. analyzers/aggregators.py:')
print('   • _calculate_param_impact() — расчёт влияния одного параметра')
print('   • rank_issues() — ранжирование всех проблем')
print('   • Учитывает 4 компонента:')
print('     - deviation: отклонение от оптимального диапазона')
print('     - trend: сила и направление тренда (slope + R²)')
print('     - anomalies: доля аномальных значений')
print('     - outliers: доля битых датчиков')
print('   • Веса параметров (из health/analysis.py):')
print('     - CO2: 30%')
print('     - Temperature: 25%')
print('     - VOC: 20%')
print('     - Humidity: 15%')
print('     - Pressure: 10%')
print()
print('2. api/routes/analytics.py:')
print('   • Новый параметр: top_issues_count (int, default=5)')
print('   • В ответ добавлено поле "top_issues": [...]')
print()
print('Backend перезагрузится автоматически (hot-reload).')
print()
print('Проверка:')
print('  curl "http://localhost:8081/analytics/report?period=30&params=all"')
print()
print('Ожидаемый результат:')
print('  "top_issues": [')
print('    {')
print('      "param": "humidity",')
print('      "impact": -12.5,')
print('      "reason": "Rising +0.74/day (R²=0.59)",')
print('      "severity": "high",')
print('      "weight": 0.15,')
print('      "components": {')
print('        "deviation": -2.1,')
print('        "trend": -8.5,')
print('        "anomalies": -1.2,')
print('        "outliers": -0.7')
print('      }')
print('    },')
print('    ...')
print('  ]')