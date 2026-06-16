from pathlib import Path

print('=== create_analytics_module.py ===')
print()

BASE = Path('modules/analytics')
BASE.mkdir(parents=True, exist_ok=True)
(BASE / 'collectors').mkdir(exist_ok=True)
(BASE / 'analyzers').mkdir(exist_ok=True)

# ============================================================================
# 1. __init__.py
# ============================================================================
(BASE / '__init__.py').write_text('''"""Analytics module — тренды, корреляции, рекомендации"""
from structlog import get_logger

__version__ = "1.0.0"
log = get_logger()


def on_load():
    """Вызывается при загрузке модуля"""
    log.info("Analytics module loaded", version=__version__)
''', encoding='utf-8')
print('✓ __init__.py')

# ============================================================================
# 2. config.yaml
# ============================================================================
(BASE / 'config.yaml').write_text('''name: analytics
version: 1.0.0
description: Аналитика, тренды, корреляции и рекомендации
enabled: true

# Горизонты анализа по умолчанию
default_periods:
  days: 30

# Доступные периоды для UI
available_periods: [7, 30, 90, 365]

# Параметры для анализа (те же что в health)
params:
  - temperature
  - humidity
  - co2
  - pressure
  - voc
''', encoding='utf-8')
print('✓ config.yaml')

# ============================================================================
# 3. tools.py (пустой, как в health)
# ============================================================================
(BASE / 'tools.py').write_text('''"""Tools больше не нужны — данные собираются детерминированно"""
TOOLS = []
''', encoding='utf-8')
print('✓ tools.py')

# ============================================================================
# 4. prompts.py (заглушка)
# ============================================================================
(BASE / 'prompts.py').write_text('''"""Промпты для analytics-модуля"""

ANALYTICS_SYSTEM_PROMPT = """Ты — инженер-аналитик SCADA-системы.
На основе предоставленных трендов и аномалий сгенерируй:
1. Главную проблему (что критично)
2. 3 конкретных действия (что сделать)
3. Прогноз (что будет если не починить)
4. Ожидаемый эффект (на сколько баллов улучшится здоровье)
"""
''', encoding='utf-8')
print('✓ prompts.py')

# ============================================================================
# 5. collectors/__init__.py
# ============================================================================
(BASE / 'collectors' / '__init__.py').write_text('', encoding='utf-8')
print('✓ collectors/__init__.py')

# ============================================================================
# 6. collectors/history.py — сбор данных за N дней
# ============================================================================
(BASE / 'collectors' / 'history.py').write_text('''"""Сбор исторических данных за N дней"""
from datetime import datetime, timedelta
from typing import Any
from structlog import get_logger

from core.db import fetch

log = get_logger()


async def collect_param_history(
    param_key: str,
    include_keywords: list[str],
    exclude_keywords: list[str],
    days: int = 30,
) -> dict:
    """
    Собирает данные по параметру за N дней.
    
    Returns:
        {
            "param": "temperature",
            "data_points": [{"timestamp": ..., "value": ...}, ...],
            "count": int
        }
    """
    # Формируем WHERE для матчинга тегов
    include_clauses = " OR ".join([f"LOWER(td.tag_name) LIKE \\'%{kw.lower()}%\\'" for kw in include_keywords])
    exclude_clauses = " AND ".join([f"LOWER(td.tag_name) NOT LIKE \\'%{kw.lower()}%\\'" for kw in exclude_keywords])
    
    since = datetime.now() - timedelta(days=days)
    
    query = f"""
        SELECT tv.date_created, tv.value, td.tag_name
        FROM tags_value tv
        JOIN tags_dict td ON td.tag_id = tv.tag_id
        WHERE tv.date_created >= $1
          AND ({include_clauses})
          AND ({exclude_clauses})
        ORDER BY tv.date_created ASC
        LIMIT 50000
    """
    
    try:
        rows = await fetch(query, since)
        data_points = [
            {
                "timestamp": row["date_created"].isoformat() if row["date_created"] else None,
                "value": float(row["value"]) if row["value"] is not None else None,
                "tag_name": row["tag_name"],
            }
            for row in rows
            if row["value"] is not None
        ]
        
        log.info(f"collected history for {param_key}", days=days, points=len(data_points))
        
        return {
            "param": param_key,
            "data_points": data_points,
            "count": len(data_points),
        }
    except Exception as e:
        log.error(f"failed to collect history for {param_key}", error=str(e))
        return {
            "param": param_key,
            "data_points": [],
            "count": 0,
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
            days=days,
        )
        results[param_key] = result
    
    return {
        "period_days": days,
        "collected_at": datetime.now().isoformat(),
        "params": results,
    }
''', encoding='utf-8')
print('✓ collectors/history.py')

# ============================================================================
# 7. analyzers/__init__.py
# ============================================================================
(BASE / 'analyzers' / '__init__.py').write_text('', encoding='utf-8')
print('✓ analyzers/__init__.py')

# ============================================================================
# 8. analyzers/trends.py — линейная регрессия, аномалии
# ============================================================================
(BASE / 'analyzers' / 'trends.py').write_text('''"""Анализ трендов — детерминированные формулы"""
from typing import Any
import statistics
from structlog import get_logger

log = get_logger()


def analyze_param_trend(data_points: list[dict], param_key: str) -> dict:
    """
    Анализирует тренд одного параметра.
    
    Returns:
        {
            "param": "temperature",
            "count": 1000,
            "avg": 22.5,
            "min": 18.0,
            "max": 26.0,
            "slope": 0.15,         # единиц в день
            "r_squared": 0.78,
            "direction": "rising", # rising/falling/stable
            "anomalies": 12,
            "anomaly_rate": 0.012
        }
    """
    if not data_points:
        return {
            "param": param_key,
            "count": 0,
            "direction": "no_data",
        }
    
    values = [p["value"] for p in data_points if p["value"] is not None]
    
    if len(values) < 2:
        return {
            "param": param_key,
            "count": len(values),
            "direction": "insufficient_data",
        }
    
    avg = statistics.mean(values)
    min_val = min(values)
    max_val = max(values)
    stdev = statistics.stdev(values) if len(values) > 1 else 0
    
    # Линейная регрессия (простой вариант без numpy)
    n = len(values)
    x = list(range(n))
    x_mean = statistics.mean(x)
    y_mean = avg
    
    numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
    denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
    
    if denominator == 0:
        slope = 0
        r_squared = 0
    else:
        slope = numerator / denominator
        # R²
        y_pred = [y_mean + slope * (xi - x_mean) for xi in x]
        ss_res = sum((values[i] - y_pred[i]) ** 2 for i in range(n))
        ss_tot = sum((values[i] - y_mean) ** 2 for i in range(n))
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
    
    # Конвертируем slope в "единиц в день" (примерно, т.к. x — это индекс)
    # Точнее можно будет когда будем парсить timestamp
    slope_per_day = slope
    
    # Направление
    if abs(slope) < 0.01:
        direction = "stable"
    elif slope > 0:
        direction = "rising"
    else:
        direction = "falling"
    
    # Аномалии (Z-score > 3)
    anomalies = 0
    if stdev > 0:
        for v in values:
            z = abs((v - avg) / stdev)
            if z > 3:
                anomalies += 1
    
    return {
        "param": param_key,
        "count": len(values),
        "avg": round(avg, 2),
        "min": round(min_val, 2),
        "max": round(max_val, 2),
        "stdev": round(stdev, 2),
        "slope": round(slope_per_day, 4),
        "r_squared": round(r_squared, 3),
        "direction": direction,
        "anomalies": anomalies,
        "anomaly_rate": round(anomalies / len(values), 4) if values else 0,
    }


def analyze_trends(history_data: dict) -> dict:
    """
    Анализирует тренды всех параметров.
    """
    trends = {}
    for param_key, param_data in history_data.get("params", {}).items():
        data_points = param_data.get("data_points", [])
        trend = analyze_param_trend(data_points, param_key)
        trends[param_key] = trend
    
    return {
        "period_days": history_data.get("period_days", 0),
        "trends": trends,
    }
''', encoding='utf-8')
print('✓ analyzers/trends.py')

# ============================================================================
# 9. renderers.py (заглушка)
# ============================================================================
(BASE / 'renderers.py').write_text('''"""Рендеринг аналитики — narrative + visual"""
from structlog import get_logger

log = get_logger()


def render_analytics(analytics_data: dict) -> dict:
    """Рендерит отчёт аналитики (заглушка)"""
    return {
        "narrative": "Аналитика в разработке",
        "visual": {"widgets": []},
    }
''', encoding='utf-8')
print('✓ renderers.py')

# ============================================================================
# 10. api/routes/analytics.py
# ============================================================================
analytics_router = Path('api/routes/analytics.py')
analytics_router.write_text('''"""Analytics API — тренды и аналитика"""
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
    """
    log.info("analytics/report requested", period=period, params=params)
    
    # Парсим params
    if params == "all":
        params_list = None
    else:
        params_list = [p.strip() for p in params.split(",")]
    
    # 1. Собираем историю
    history = await collect_history(days=period, params=params_list)
    
    # 2. Анализируем тренды
    trends = analyze_trends(history)
    
    log.info("analytics/report ready", period=period, params=list(trends["trends"].keys()))
    
    return {
        "period_days": period,
        "collected_at": history["collected_at"],
        "trends": trends["trends"],
    }
''', encoding='utf-8')
print('✓ api/routes/analytics.py')

# ============================================================================
# 11. Подключаем роутер в main.py
# ============================================================================
main_path = Path('main.py')
main_content = main_path.read_text(encoding='utf-8')

# Добавляем analytics в импорт
if 'from api.routes import chat, config, health, system, docs, energy' in main_content:
    main_content = main_content.replace(
        'from api.routes import chat, config, health, system, docs, energy',
        'from api.routes import chat, config, health, system, docs, energy, analytics'
    )
    print('✓ main.py: добавлен импорт analytics')
else:
    print('⚠ Не нашёл точный паттерн импорта в main.py')

# Добавляем include_router
if 'app.include_router(energy.router)' in main_content and 'analytics.router' not in main_content:
    main_content = main_content.replace(
        'app.include_router(energy.router)',
        'app.include_router(energy.router)\napp.include_router(analytics.router)'
    )
    print('✓ main.py: добавлен include_router(analytics.router)')
elif 'analytics.router' in main_content:
    print('ℹ analytics.router уже подключён')
else:
    print('⚠ Не нашёл точный паттерн include_router в main.py')

main_path.write_text(main_content, encoding='utf-8', newline='\\n')

print()
print('=' * 60)
print('СОЗДАНО:')
print('=' * 60)
print()
print('Модуль: modules/analytics/')
print('  ├── __init__.py')
print('  ├── config.yaml')
print('  ├── tools.py (пустой)')
print('  ├── prompts.py (заглушка)')
print('  ├── collectors/')
print('  │   ├── __init__.py')
print('  │   └── history.py (SQL за N дней)')
print('  ├── analyzers/')
print('  │   ├── __init__.py')
print('  │   └── trends.py (линейная регрессия)')
print('  └── renderers.py (заглушка)')
print()
print('Роутер: api/routes/analytics.py')
print('  ├── GET /analytics/ping')
print('  └── GET /analytics/report?period=30&params=all')
print()
print('Подключено в main.py:')
print('  • import analytics')
print('  • include_router(analytics.router)')
print()
print('Backend перезагрузится автоматически (hot-reload).')
print()
print('ПРОВЕРКА:')
print('  curl http://localhost:8081/analytics/ping')
print('  curl "http://localhost:8081/analytics/report?period=30&params=temperature,co2"')
print()
print('В конфигураторе модуль появится автоматически')
print('(ModuleRegistry.discover_modules() найдёт __init__.py)')