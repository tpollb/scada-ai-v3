from pathlib import Path

print('=== fix_analytics_aggregation.py ===')
print()

# ============================================================================
# 1. collectors/history.py — агрегация + строгий validator
# ============================================================================
history_path = Path('modules/analytics/collectors/history.py')
history_content = '''"""Сбор исторических данных за N дней с валидацией и агрегацией"""
from datetime import datetime, timedelta
from typing import Any, Literal
from structlog import get_logger

from core.db import fetch

log = get_logger()


def _auto_aggregation(days: int) -> str:
    """Автовыбор агрегации в зависимости от периода"""
    if days <= 7:
        return "hourly"
    elif days <= 90:
        return "hourly"
    else:
        return "daily"


async def collect_param_history(
    param_key: str,
    include_keywords: list[str],
    exclude_keywords: list[str],
    norms: dict,
    validator: dict,
    days: int = 30,
    aggregation: str = "auto",
) -> dict:
    """
    Собирает данные по параметру за N дней с валидацией и агрегацией.

    Использует norms.crit_min/crit_max (строгие границы) вместо validator
    (физические границы) — чтобы отсеять битые датчики типа 0°C в помещении.

    Args:
        param_key: ключ параметра (temperature, co2, etc)
        include_keywords: паттерны для матчинга тегов
        exclude_keywords: паттерны для исключения
        norms: {"opt_min": 18, "opt_max": 24, "crit_min": 10, "crit_max": 35}
        validator: {"min": -50, "max": 80} — для справки в ответе
        days: период в днях
        aggregation: raw/hourly/daily/auto

    Returns:
        {
            "param": "temperature",
            "aggregation": "hourly",
            "data_points": [...],        # агрегированные (avg/min/max/count per bucket)
            "bucket_count": int,         # количество buckets
            "total_raw_count": int,      # всего сырых точек (валидных)
            "outliers_count": int,       # битые датчики
            "norms": {...},
            "validator": {...},
        }
    """
    # Автовыбор агрегации
    if aggregation == "auto":
        aggregation = _auto_aggregation(days)

    # Формируем WHERE для матчинга тегов
    include_clauses = " OR ".join(
        [f"LOWER(td.tag_name) LIKE \\'%{kw.lower()}%\\'" for kw in include_keywords]
    )
    exclude_clauses = " AND ".join(
        [f"LOWER(td.tag_name) NOT LIKE \\'%{kw.lower()}%\\'" for kw in exclude_keywords]
    )

    since = datetime.now() - timedelta(days=days)

    # Строгие границы для аналитики (из norms, не validator)
    # Если crit_min/crit_max нет — fallback на validator
    val_min = norms.get("crit_min", validator.get("min", -999999))
    val_max = norms.get("crit_max", validator.get("max", 999999))

    # 1. Агрегированные данные (GROUP BY hour/day)
    if aggregation == "hourly":
        bucket_expr = "DATE_TRUNC('hour', tv.date_created)"
        bucket_label = "hour"
    elif aggregation == "daily":
        bucket_expr = "DATE_TRUNC('day', tv.date_created)"
        bucket_label = "day"
    else:
        # raw — без агрегации (но с LIMIT для безопасности)
        bucket_expr = "tv.date_created"
        bucket_label = "raw"

    if aggregation == "raw":
        query_data = f"""
            SELECT tv.date_created, tv.value, td.tag_name
            FROM tags_value tv
            JOIN tags_dict td ON td.tag_id = tv.tag_id
            WHERE tv.date_created >= $1
              AND ({include_clauses})
              AND ({exclude_clauses})
              AND tv.value >= $2
              AND tv.value <= $3
            ORDER BY tv.date_created ASC
            LIMIT 100000
        """
    else:
        query_data = f"""
            SELECT
                {bucket_expr} AS bucket_start,
                AVG(tv.value)::float AS avg_value,
                MIN(tv.value)::float AS min_value,
                MAX(tv.value)::float AS max_value,
                COUNT(*) AS point_count
            FROM tags_value tv
            JOIN tags_dict td ON td.tag_id = tv.tag_id
            WHERE tv.date_created >= $1
              AND ({include_clauses})
              AND ({exclude_clauses})
              AND tv.value >= $2
              AND tv.value <= $3
            GROUP BY bucket_start
            ORDER BY bucket_start ASC
        """

    # 2. Считаем OUTLIERS (битые датчики вне строгих границ)
    query_outliers = f"""
        SELECT COUNT(*) as outlier_count
        FROM tags_value tv
        JOIN tags_dict td ON td.tag_id = tv.tag_id
        WHERE tv.date_created >= $1
          AND ({include_clauses})
          AND ({exclude_clauses})
          AND (tv.value < $2 OR tv.value > $3)
    """

    # 3. Считаем всего валидных сырых точек
    query_total = f"""
        SELECT COUNT(*) as total_count
        FROM tags_value tv
        JOIN tags_dict td ON td.tag_id = tv.tag_id
        WHERE tv.date_created >= $1
          AND ({include_clauses})
          AND ({exclude_clauses})
          AND tv.value >= $2
          AND tv.value <= $3
    """

    try:
        rows_data = await fetch(query_data, since, val_min, val_max)
        outlier_row = await fetch(query_outliers, since, val_min, val_max)
        total_row = await fetch(query_total, since, val_min, val_max)

        outliers_count = outlier_row[0]["outlier_count"] if outlier_row else 0
        total_raw_count = total_row[0]["total_count"] if total_row else 0

        # Формируем data_points в едином формате
        if aggregation == "raw":
            data_points = [
                {
                    "timestamp": row["date_created"].isoformat() if row["date_created"] else None,
                    "value": float(row["value"]) if row["value"] is not None else None,
                }
                for row in rows_data
                if row["value"] is not None
            ]
        else:
            data_points = [
                {
                    "bucket_start": row["bucket_start"].isoformat() if row["bucket_start"] else None,
                    "avg": float(row["avg_value"]) if row["avg_value"] is not None else None,
                    "min": float(row["min_value"]) if row["min_value"] is not None else None,
                    "max": float(row["max_value"]) if row["max_value"] is not None else None,
                    "count": int(row["point_count"]),
                }
                for row in rows_data
            ]

        log.info(
            f"collected history for {param_key}",
            days=days,
            aggregation=aggregation,
            buckets=len(data_points),
            outliers=outliers_count,
        )

        return {
            "param": param_key,
            "aggregation": aggregation,
            "bucket_label": bucket_label,
            "data_points": data_points,
            "bucket_count": len(data_points),
            "total_raw_count": total_raw_count,
            "outliers_count": outliers_count,
            "norms": norms,
            "validator": validator,
        }
    except Exception as e:
        log.error(f"failed to collect history for {param_key}", error=str(e))
        return {
            "param": param_key,
            "aggregation": aggregation,
            "bucket_label": bucket_label if aggregation != "raw" else "raw",
            "data_points": [],
            "bucket_count": 0,
            "total_raw_count": 0,
            "outliers_count": 0,
            "norms": norms,
            "validator": validator,
            "error": str(e),
        }


async def collect_history(
    days: int = 30,
    params: list[str] | None = None,
    aggregation: str = "auto",
) -> dict:
    """
    Собирает историю по всем параметрам за N дней.
    """
    from modules.health.data_collectors import PARAM_GROUPS

    if params is None or params == ["all"]:
        params = list(PARAM_GROUPS.keys())

    results = {}
    for param_key in params:
        if param_key not in PARAM_GROUPS:
            continue
        cfg = PARAM_GROUPS[param_key]
        result = await collect_param_history(
            param_key=param_key,
            include_keywords=cfg["include"],
            exclude_keywords=cfg["exclude"],
            norms=cfg.get("norms", {}),
            validator=cfg["validator"],
            days=days,
            aggregation=aggregation,
        )
        results[param_key] = result

    return {
        "period_days": days,
        "aggregation": aggregation,
        "collected_at": datetime.now().isoformat(),
        "params": results,
    }
'''

history_path.write_text(history_content, encoding='utf-8', newline='\n')
print('✓ collectors/history.py: агрегация + строгий validator (norms.crit_min/max)')

# ============================================================================
# 2. analyzers/trends.py — работает с агрегированными данными
# ============================================================================
trends_path = Path('modules/analytics/analyzers/trends.py')
trends_content = '''"""Анализ трендов — работает с агрегированными данными (hourly/daily)"""
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
            "unit": "°C",
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

trends_path.write_text(trends_content, encoding='utf-8', newline='\n')
print('✓ analyzers/trends.py: работает с агрегированными данными')

# ============================================================================
# 3. api/routes/analytics.py — добавляем параметр aggregation
# ============================================================================
router_path = Path('api/routes/analytics.py')
router_content = '''"""Analytics API — тренды и аналитика"""
from fastapi import APIRouter, Query
from datetime import datetime
from structlog import get_logger

from modules.analytics.collectors.history import collect_history
from modules.analytics.analyzers.trends import analyze_trends

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
):
    """
    Отчёт аналитики: тренды, аномалии, статистика.

    aggregation:
      - raw: все сырые точки (LIMIT 100000) — только для коротких периодов
      - hourly: GROUP BY hour — для 7-90 дней
      - daily: GROUP BY day — для >90 дней
      - auto: автоматически по периоду
    """
    log.info(
        "analytics/report requested",
        period=period,
        params=params,
        aggregation=aggregation,
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

    log.info(
        "analytics/report ready",
        period=period,
        aggregation=history["aggregation"],
        params=list(trends["trends"].keys()),
    )

    return {
        "period_days": period,
        "aggregation": history["aggregation"],
        "collected_at": history["collected_at"],
        "trends": trends["trends"],
    }
'''

router_path.write_text(router_content, encoding='utf-8', newline='\n')
print('✓ api/routes/analytics.py: добавлен параметр aggregation')

print()
print('=' * 60)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 60)
print()
print('1. Строгий validator (для аналитики):')
print('   • Использует norms.crit_min/crit_max (не validator.min/max)')
print('   • Temperature: 10..35°C вместо -50..80°C')
print('   • CO2: 350..2000 ppm (атмосфера ~415 ppm, 0 = битый)')
print('   • Отсекает 0°C в помещении как битый датчик')
print()
print('2. Агрегация в SQL (GROUP BY):')
print('   • hourly: GROUP BY DATE_TRUNC(\'hour\') — для 7-90 дней')
print('   • daily: GROUP BY DATE_TRUNC(\'day\') — для >90 дней')
print('   • raw: без агрегации (LIMIT 100000) — для коротких периодов')
print('   • auto: выбирает автоматически по period')
print()
print('3. Автовыбор агрегации:')
print('   • 7 дней → hourly')
print('   • 30 дней → hourly (720 buckets вместо 488000 точек)')
print('   • 90 дней → hourly')
print('   • 365 дней → daily (365 buckets)')
print()
print('Backend перезагрузится автоматически.')
print()
print('Проверка (все 5 параметров, авто-агрегация):')
print('  curl "http://localhost:8081/analytics/report?period=30&params=all"')
print()
print('Проверка (явная hourly агрегация):')
print('  curl "http://localhost:8081/analytics/report?period=7&aggregation=hourly"')
print()
print('Ожидаемый результат:')
print('  • Все 5 параметров: temperature, humidity, co2, pressure, voc')
print('  • aggregation: "hourly" (для 30 дней)')
print('  • bucket_count: ~720 (часов за 30 дней)')
print('  • min/max в разумных пределах (не 0°C, не 124°C)')