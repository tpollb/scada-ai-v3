"""Сбор исторических данных за N дней с валидацией и агрегацией"""
from datetime import datetime, timedelta
from typing import Any, Literal
from structlog import get_logger

import asyncio
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
        [f"LOWER(td.tag_name) LIKE \'%{kw.lower()}%\'" for kw in include_keywords]
    )
    exclude_clauses = " AND ".join(
        [f"LOWER(td.tag_name) NOT LIKE \'%{kw.lower()}%\'" for kw in exclude_keywords]
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

    # Параллельный сбор всех параметров (ускоряет в 3-5 раз)
    tasks = []
    param_keys = []
    for param_key in params:
        if param_key not in PARAM_GROUPS:
            continue
        cfg = PARAM_GROUPS[param_key]
        tasks.append(
            collect_param_history(
                param_key=param_key,
                include_keywords=cfg["include"],
                exclude_keywords=cfg["exclude"],
                norms=cfg.get("norms", {}),
                validator=cfg["validator"],
                days=days,
                aggregation=aggregation,
            )
        )
        param_keys.append(param_key)
    
    # Выполняем все запросы параллельно
    results_list = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Собираем результаты, обрабатывая ошибки
    results = {}
    for param_key, result in zip(param_keys, results_list):
        if isinstance(result, Exception):
            log.error(f"failed to collect {param_key}", error=str(result))
            results[param_key] = {
                "param": param_key,
                "aggregation": aggregation,
                "data_points": [],
                "bucket_count": 0,
                "total_raw_count": 0,
                "outliers_count": 0,
                "error": str(result),
            }
        else:
            results[param_key] = result

    return {
        "period_days": days,
        "aggregation": aggregation,
        "collected_at": datetime.now().isoformat(),
        "params": results,
    }
