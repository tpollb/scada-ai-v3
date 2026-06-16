"""Analytics API — тренды, корреляции, топ проблемы + LLM insights"""
from fastapi import APIRouter, Query
from datetime import datetime
from structlog import get_logger

from modules.analytics.collectors.history import collect_history
from modules.analytics.analyzers.trends import analyze_trends
from modules.analytics.analyzers.correlations import find_correlations
from modules.analytics.analyzers.aggregators import rank_issues
from modules.analytics.llm.analyzer import get_analytics_llm

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
    include_llm: bool = Query(True, description="Включить LLM-анализ (insights, рекомендации, прогнозы)"),
):
    """
    Полный отчёт аналитики: тренды, корреляции, топ проблемы + LLM insights.
    
    Параметры:
      - period: период в днях (7, 30, 90, 365)
      - aggregation: raw/hourly/daily/auto
      - min_correlation: порог для корреляций (default 0.5)
      - top_issues_count: количество топ проблем (default 5)
      - include_llm: вызывать ли LLM (default true)
    
    При include_llm=true возвращает поля:
      - summary: краткое резюме
      - insights: список инсайтов
      - recommendations: список рекомендаций
      - forecast: прогноз на 7/30 дней
    
    При ошибке LLM возвращается fallback с полем llm_error.
    """
    log.info(
        "analytics/report requested",
        period=period,
        params=params,
        aggregation=aggregation,
        min_correlation=min_correlation,
        top_issues_count=top_issues_count,
        include_llm=include_llm,
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

    # Базовый ответ
    response = {
        "period_days": period,
        "aggregation": history["aggregation"],
        "collected_at": history["collected_at"],
        "trends": trends["trends"],
        "correlations": correlations,
        "top_issues": top_issues,
    }

    # 5. LLM insights (если включено)
    if include_llm:
        try:
            llm = get_analytics_llm()
            llm_result = await llm.analyze(
                trends=trends["trends"],
                correlations=correlations,
                top_issues=top_issues,
                period_days=period,
            )
            response["summary"] = llm_result.get("summary", "")
            response["insights"] = llm_result.get("insights", [])
            response["recommendations"] = llm_result.get("recommendations", [])
            response["forecast"] = llm_result.get("forecast", {})
            if "llm_error" in llm_result:
                response["llm_error"] = llm_result["llm_error"]
                log.warning("LLM used fallback", error=llm_result["llm_error"])
        except Exception as e:
            log.error("LLM analysis failed", error=str(e))
            response["llm_error"] = str(e)

    log.info(
        "analytics/report ready",
        period=period,
        aggregation=history["aggregation"],
        params=list(trends["trends"].keys()),
        correlations=len(correlations),
        top_issues=len(top_issues),
        has_llm="summary" in response,
    )

    return response
