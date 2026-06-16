from pathlib import Path

print('=== fix_analytics_validation.py ===')
print()

# ============================================================================
# 1. collectors/history.py — добавляем валидацию и outliers
# ============================================================================
history_path = Path('modules/analytics/collectors/history.py')
history_content = '''"""Сбор исторических данных за N дней с валидацией"""
from datetime import datetime, timedelta
from typing import Any
from structlog import get_logger

from core.db import fetch

log = get_logger()


async def collect_param_history(
    param_key: str,
    include_keywords: list[str],
    exclude_keywords: list[str],
    validator: dict,
    days: int = 30,
) -> dict:
    """
    Собирает данные по параметру за N дней с валидацией.
    
    Args:
        param_key: ключ параметра (temperature, co2, etc)
        include_keywords: паттерны для матчинга тегов
        exclude_keywords: паттерны для исключения
        validator: {"min": -50, "max": 80} — физические границы
        days: период в днях
    
    Returns:
        {
            "param": "temperature",
            "valid_data_points": [...],  # валидные данные
            "valid_count": int,
            "outliers_count": int,       # битые датчики (вне validator)
            "total_count": int,
        }
    """
    # Формируем WHERE для матчинга тегов
    include_clauses = " OR ".join([f"LOWER(td.tag_name) LIKE \\'%{kw.lower()}%\\'" for kw in include_keywords])
    exclude_clauses = " AND ".join([f"LOWER(td.tag_name) NOT LIKE \\'%{kw.lower()}%\\'" for kw in exclude_keywords])
    
    since = datetime.now() - timedelta(days=days)
    val_min = validator.get("min", -999999)
    val_max = validator.get("max", 999999)
    
    # 1. Получаем ВАЛИДНЫЕ данные (в пределах validator)
    query_valid = f"""
        SELECT tv.date_created, tv.value, td.tag_name
        FROM tags_value tv
        JOIN tags_dict td ON td.tag_id = tv.tag_id
        WHERE tv.date_created >= $1
          AND ({include_clauses})
          AND ({exclude_clauses})
          AND tv.value >= $2
          AND tv.value <= $3
        ORDER BY tv.date_created ASC
    """
    
    # 2. Считаем OUTLIERS (битые датчики вне validator)
    query_outliers = f"""
        SELECT COUNT(*) as outlier_count
        FROM tags_value tv
        JOIN tags_dict td ON td.tag_id = tv.tag_id
        WHERE tv.date_created >= $1
          AND ({include_clauses})
          AND ({exclude_clauses})
          AND (tv.value < $2 OR tv.value > $3)
    """
    
    try:
        # Валидные данные
        valid_rows = await fetch(query_valid, since, val_min, val_max)
        valid_data_points = [
            {
                "timestamp": row["date_created"].isoformat() if row["date_created"] else None,
                "value": float(row["value"]) if row["value"] is not None else None,
                "tag_name": row["tag_name"],
            }
            for row in valid_rows
            if row["value"] is not None
        ]
        
        # Outliers
        outlier_row = await fetch(query_outliers, since, val_min, val_max)
        outliers_count = outlier_row[0]["outlier_count"] if outlier_row else 0
        
        total_count = len(valid_data_points) + outliers_count
        
        log.info(
            f"collected history for {param_key}",
            days=days,
            valid=len(valid_data_points),
            outliers=outliers_count,
        )
        
        return {
            "param": param_key,
            "valid_data_points": valid_data_points,
            "valid_count": len(valid_data_points),
            "outliers_count": outliers_count,
            "total_count": total_count,
        }
    except Exception as e:
        log.error(f"failed to collect history for {param_key}", error=str(e))
        return {
            "param": param_key,
            "valid_data_points": [],
            "valid_count": 0,
            "outliers_count": 0,
            "total_count": 0,
            "error": str(e),
        }


async def collect_history(
    days: int = 30,
    params: list[str] | None = None,
) -> dict:
    """
    Собирает историю по всем параметрам за N дней.
    """
    # Используем PARAM_GROUPS из health чтобы не дублировать
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
            validator=cfg["validator"],
            days=days,
        )
        results[param_key] = result
    
    return {
        "period_days": days,
        "collected_at": datetime.now().isoformat(),
        "params": results,
    }
'''

history_path.write_text(history_content, encoding='utf-8', newline='\n')
print('✓ collectors/history.py: добавлена валидация и outliers')

# ============================================================================
# 2. analyzers/trends.py — правильный slope по timestamps
# ============================================================================
trends_path = Path('modules/analytics/analyzers/trends.py')
trends_content = '''"""Анализ трендов — детерминированные формулы с правильным slope"""
from typing import Any
from datetime import datetime
import statistics
from structlog import get_logger

log = get_logger()


def analyze_param_trend(data_points: list[dict], param_key: str) -> dict:
    """
    Анализирует тренд одного параметра.
    
    Args:
        data_points: список {"timestamp": "2026-06-16T...", "value": 22.5, ...}
        param_key: ключ параметра
    
    Returns:
        {
            "param": "temperature",
            "valid_count": 48000,
            "avg": 22.5,
            "min": 18.0,
            "max": 26.0,
            "stdev": 2.3,
            "slope_per_day": 0.05,     # единиц в день
            "r_squared": 0.78,
            "direction": "rising",      # rising/falling/stable
            "anomalies": 12,
            "anomaly_rate": 0.00025
        }
    """
    if not data_points:
        return {
            "param": param_key,
            "valid_count": 0,
            "direction": "no_data",
        }
    
    # Извлекаем values
    values = [p["value"] for p in data_points if p["value"] is not None]
    
    if len(values) < 2:
        return {
            "param": param_key,
            "valid_count": len(values),
            "direction": "insufficient_data",
        }
    
    # Базовая статистика
    avg = statistics.mean(values)
    min_val = min(values)
    max_val = max(values)
    stdev = statistics.stdev(values) if len(values) > 1 else 0
    
    # Парсим timestamps и конвертируем в "дни от начала"
    timestamps_days = []
    valid_values = []
    
    for p in data_points:
        if p["value"] is None or not p.get("timestamp"):
            continue
        try:
            ts = datetime.fromisoformat(p["timestamp"])
            valid_values.append(p["value"])
            timestamps_days.append(ts)
        except (ValueError, TypeError):
            continue
    
    if len(valid_values) < 2:
        return {
            "param": param_key,
            "valid_count": len(values),
            "direction": "insufficient_data",
        }
    
    # Конвертируем timestamps в дни от начала периода
    start_ts = min(timestamps_days)
    x_days = [(ts - start_ts).total_seconds() / 86400.0 for ts in timestamps_days]
    
    # Линейная регрессия по (день, значение)
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
        # R²
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
    
    # Аномалии (Z-score > 3)
    anomalies = 0
    if stdev > 0:
        for v in valid_values:
            z = abs((v - avg) / stdev)
            if z > 3:
                anomalies += 1
    
    return {
        "param": param_key,
        "valid_count": len(valid_values),
        "avg": round(avg, 2),
        "min": round(min_val, 2),
        "max": round(max_val, 2),
        "stdev": round(stdev, 2),
        "slope_per_day": round(slope_per_day, 4),
        "r_squared": round(r_squared, 3),
        "direction": direction,
        "anomalies": anomalies,
        "anomaly_rate": round(anomalies / len(valid_values), 4) if valid_values else 0,
    }


def analyze_trends(history_data: dict) -> dict:
    """
    Анализирует тренды всех параметров.
    """
    trends = {}
    for param_key, param_data in history_data.get("params", {}).items():
        valid_data_points = param_data.get("valid_data_points", [])
        outliers_count = param_data.get("outliers_count", 0)
        
        trend = analyze_param_trend(valid_data_points, param_key)
        trend["outliers_count"] = outliers_count
        trend["total_count"] = param_data.get("total_count", 0)
        
        trends[param_key] = trend
    
    return {
        "period_days": history_data.get("period_days", 0),
        "trends": trends,
    }
'''

trends_path.write_text(trends_content, encoding='utf-8', newline='\n')
print('✓ analyzers/trends.py: правильный slope по timestamps')

# ============================================================================
# 3. api/routes/analytics.py — обновляем структуру ответа
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
):
    """
    Отчёт аналитики: тренды, аномалии, статистика.
    
    Returns:
        {
            "period_days": 30,
            "collected_at": "2026-06-16T...",
            "trends": {
                "temperature": {
                    "valid_count": 48000,
                    "outliers_count": 500,
                    "total_count": 48500,
                    "avg": 22.5,
                    "min": 18.0,
                    "max": 26.0,
                    "slope_per_day": 0.05,
                    "r_squared": 0.78,
                    "direction": "rising",
                    "anomalies": 12
                }
            }
        }
    """
    log.info("analytics/report requested", period=period, params=params)
    
    # Парсим params
    if params == "all":
        params_list = None
    else:
        params_list = [p.strip() for p in params.split(",")]
    
    # 1. Собираем историю (с валидацией)
    history = await collect_history(days=period, params=params_list)
    
    # 2. Анализируем тренды
    trends = analyze_trends(history)
    
    log.info(
        "analytics/report ready",
        period=period,
        params=list(trends["trends"].keys()),
    )
    
    return {
        "period_days": period,
        "collected_at": history["collected_at"],
        "trends": trends["trends"],
    }
'''

router_path.write_text(router_content, encoding='utf-8', newline='\n')
print('✓ api/routes/analytics.py: обновлена структура ответа')

print()
print('=' * 60)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 60)
print()
print('1. Валидация данных (collectors/history.py):')
print('   • SQL WHERE clause: value BETWEEN validator.min AND validator.max')
print('   • Отдельный query для outliers (битые датчики)')
print('   • Возвращает valid_count + outliers_count')
print()
print('2. Правильный slope (analyzers/trends.py):')
print('   • Использует реальные timestamps (не индексы)')
print('   • Конвертирует в "дни от начала периода"')
print('   • slope_per_day в интерпретируемых единицах')
print()
print('3. Обновлённая структура ответа:')
print('   • valid_count: количество валидных точек')
print('   • outliers_count: количество битых датчиков')
print('   • total_count: сумма')
print('   • slope_per_day: тренд в единицах/день')
print()
print('Backend перезагрузится автоматически (hot-reload).')
print()
print('Проверка:')
print('  curl "http://localhost:8081/analytics/report?period=30&params=temperature,co2"')
print()
print('Ожидаемый результат:')
print('  • outliers_count > 0 (битые датчики отфильтрованы)')
print('  • min/max в разумных пределах (не 0°C и не 124°C)')
print('  • slope_per_day в интерпретируемых единицах')