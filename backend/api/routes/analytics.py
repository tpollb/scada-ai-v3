"""Analytics API — тренды, корреляции, топ проблем"""
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
