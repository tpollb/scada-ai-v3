"""Ранжирование проблем по влиянию на health score"""
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
            "impact": -12.5,
            "reason": "Rising +0.74%/day, R²=0.591, reaches CRITICAL in 25 days",
            "severity": "high",
            "weight": 0.15,
            "components": {...}
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
        deviation_penalty = -(excess / crit_range) * weight * 30

    # 2. Тренд (усиленная логика)
    trend_penalty = 0
    days_to_crit = 999
    
    if abs(slope) > 0.01 and r_squared > 0.1:
        # Сколько дней до достижения критической границы
        if slope > 0:
            distance_to_crit = crit_max - avg
            days_to_crit = distance_to_crit / slope if slope > 0 else 999
        else:
            distance_to_crit = avg - crit_min
            days_to_crit = distance_to_crit / abs(slope) if slope < 0 else 999

        # Если достигнем критической границы в разумные сроки
        if days_to_crit < 180:  # 6 месяцев
            # Urgency: 1.0 если через 1 день, 0.0 если через 180 дней
            urgency = max(0, 1 - (days_to_crit / 180))
            
            # Усиливаем если R² высокий (тренд надёжный)
            reliability = min(r_squared * 2, 1.0)  # R²=0.5 → 1.0, R²=1.0 → 1.0
            
            # Базовый penalty с учётом веса
            trend_penalty = -urgency * reliability * weight * 40
            
            # Дополнительный penalty если скоро достигнем критической границы
            if days_to_crit < 30:
                trend_penalty *= 1.5  # Умножаем на 1.5 если меньше месяца

    # 3. Аномалии (выбросы в данных)
    anomaly_penalty = -anomaly_rate * 100 * weight * 10

    # 4. Битые датчики (outliers) — ИСПРАВЛЕННАЯ ФОРМУЛА
    total_points = outliers_count + total_raw_count
    outlier_rate = outliers_count / total_points if total_points > 0 else 0
    outlier_penalty = -outlier_rate * weight * 20

    # Суммарный impact
    total_impact = deviation_penalty + trend_penalty + anomaly_penalty + outlier_penalty

    # Формируем reason
    reasons = []
    if abs(deviation_penalty) > 0.5:
        reasons.append(f"Avg {avg:.1f} outside optimal range")
    if abs(trend_penalty) > 0.5:
        if days_to_crit < 180:
            reasons.append(f"{direction.capitalize()} {abs(slope):.2f}/day (R²={r_squared:.2f}), reaches CRITICAL in {int(days_to_crit)} days")
        else:
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
        "days_to_critical": int(days_to_crit) if days_to_crit < 999 else None,
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
                "reason": "Rising +0.74%/day, R²=0.591, reaches CRITICAL in 25 days",
                "severity": "high",
                "weight": 0.15,
                "days_to_critical": 25,
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
