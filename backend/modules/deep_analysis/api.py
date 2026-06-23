"""Deep Analysis API endpoints"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime, timedelta
from structlog import get_logger
import traceback

from modules.deep_analysis.collectors.data_fetcher import fetch_tag_data, fetch_multiple_tags
from modules.deep_analysis.collectors.tag_resolver import get_available_tags
from modules.deep_analysis.analyzers.stats import compute_basic_stats, compute_histogram
from modules.deep_analysis.analyzers.anomalies import detect_anomalies_isolation_forest
from modules.deep_analysis.analyzers.correlations import compute_correlation_matrix, compute_pair_correlation
from modules.deep_analysis.visualizers.chart_specs import create_time_series_spec, create_histogram_spec, create_heatmap_spec, create_scatter_spec
from modules.deep_analysis.history.storage import save_analysis, load_analysis, list_analyses, generate_analysis_id

log = get_logger()
router = APIRouter(prefix="/deep_analysis", tags=["deep_analysis"])


# ============================================================================
# Pydantic Models
# ============================================================================

class AnalysisRequest(BaseModel):
    """Запрос на запуск анализа"""
    tags: list[str] = Field(..., description="Список тегов для анализа", min_length=1)
    period: Optional[int] = Field(None, description="Период в днях (7/30/120/365)", ge=1, le=365)
    start_date: Optional[datetime] = Field(None, description="Начало периода (для custom)")
    end_date: Optional[datetime] = Field(None, description="Конец периода (для custom)")
    anomalies: bool = Field(True, description="Детекция аномалий")
    correlations: bool = Field(True, description="Корреляции (для группы тегов)")
    seasonality: bool = Field(True, description="Сезонность (FFT)")
    compare_periods: bool = Field(False, description="Сравнение с предыдущим периодом")




class PairAnalysisRequest(BaseModel):
    """Запрос анализа конкретной пары тегов"""
    tag1: str = Field(..., description="Первый тег")
    tag2: str = Field(..., description="Второй тег")
    period: int = Field(30, description="Период в днях", ge=1, le=365)


class PairAnalysisResponse(BaseModel):
    """Ответ с детальным анализом пары"""
    tag1: str
    tag2: str
    period: str
    pearson: dict
    spearman: dict
    mutual_info: dict
    cross_correlation: dict
    scatter_data: dict
    scatter_spec: dict


class AnalysisResponse(BaseModel):
    """Ответ с результатами анализа"""
    analysis_id: str
    status: Literal["completed", "failed"]
    created_at: str
    tags: list[str]
    period: str
    summary: str
    statistics: Optional[dict] = None  # None для мульти-тег анализа
    anomalies: Optional[dict] = None   # None для мульти-тег анализа
    correlations: Optional[dict] = None
    seasonality: Optional[dict] = None
    visualizations: dict
    history_path: str

class TagInfo(BaseModel):
    """Информация о теге"""
    tag_id: int
    tag_name: str
    zone_name: Optional[str]
    unit: Optional[str]
    last_value: Optional[float]
    last_update: Optional[datetime]


class HistoryItem(BaseModel):
    """Элемент списка истории"""
    analysis_id: str
    created_at: str
    tags: list[str]
    period: str


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/run", response_model=AnalysisResponse)
async def run_analysis(request: AnalysisRequest):
    """
    Запускает глубокий анализ тега или группы тегов.
    
    Выполняет:
    - Сбор данных из tags_value
    - Базовую статистику
    - Детекцию аномалий (Isolation Forest)
    - Корреляции (для группы тегов)
    - Сезонность (FFT)
    - Сохранение в историю
    """
    log.info(
        "Starting deep analysis",
        tags=request.tags,
        period=request.period,
        anomalies=request.anomalies
    )
    
    try:
        # Определяем период
        if request.period:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=request.period)
            period_str = f"{request.period} days"
        elif request.start_date and request.end_date:
            start_date = request.start_date
            end_date = request.end_date
            period_str = f"{start_date.date()} to {end_date.date()}"
        else:
            raise HTTPException(
                status_code=400,
                detail="Either 'period' or both 'start_date' and 'end_date' must be provided"
            )
        
        # Если один тег — простой анализ
        if len(request.tags) == 1:
            tag_name = request.tags[0]
            
            # Сбор данных
            data = await fetch_tag_data(tag_name, start_date, end_date)
            
            if not data['values']:
                raise HTTPException(
                    status_code=404,
                    detail=f"No data found for tag '{tag_name}' in the specified period"
                )
            
            # Базовая статистика
            stats = compute_basic_stats(data['values'])
            histogram = compute_histogram(data['values'])
            
            # Детекция аномалий
            anomalies_result = None
            if request.anomalies:
                anomalies_result = detect_anomalies_isolation_forest(
                    data['values'],
                    data['timestamps']
                )
            
            # Визуализации
            time_series_spec = create_time_series_spec(
                data['timestamps'],
                data['values'],
                tag_name,
                anomalies=anomalies_result
            )
            histogram_spec = create_histogram_spec(histogram, tag_name)
            
            # Формируем результат
            results = {
                "statistics": stats,
                "histogram": histogram,
                "anomalies": anomalies_result,
            }
            
            # Краткое summary
            summary_parts = [
                f"Анализ тега '{tag_name}' за период {period_str}.",
                f"Всего точек: {stats['count']}, среднее: {stats['mean']:.2f}, std: {stats['std']:.2f}."
            ]
            if anomalies_result and anomalies_result['total_anomalies'] > 0:
                summary_parts.append(
                    f"Обнаружено {anomalies_result['total_anomalies']} аномалий ({anomalies_result['anomaly_rate']:.1%})."
                )
            summary = " ".join(summary_parts)
        
        else:
            # Группа тегов — кросс-анализ (корреляции)
            log.info("Multi-tag analysis", tags=request.tags)
            
            # Сбор данных с выравниванием
            data = await fetch_multiple_tags(
                request.tags, start_date, end_date,
                resample_freq='5min',
                align=True
            )
            
            if not data['common_timestamps']:
                raise HTTPException(
                    status_code=400,
                    detail="No common timestamps found for correlation analysis. "
                           "Tags may have insufficient data or non-overlapping time ranges."
                )
            
            # Матрица корреляций
            correlation_matrix = compute_correlation_matrix(
                data['tags'],
                data['common_timestamps'],
                method='pearson'
            )
            
            # Детальный анализ для первой пары (как пример)
            if len(request.tags) >= 2:
                tag1, tag2 = request.tags[0], request.tags[1]
                pair_analysis = compute_pair_correlation(
                    data['tags'][tag1].get('aligned_values', []),
                    data['tags'][tag2].get('aligned_values', []),
                    tag1, tag2
                )
            else:
                pair_analysis = None
            
            # Визуализации
            heatmap_spec = create_heatmap_spec(correlation_matrix)
            scatter_spec = None
            if pair_analysis and pair_analysis['scatter_data']['x']:
                scatter_spec = create_scatter_spec(
                    pair_analysis['scatter_data']['x'],
                    pair_analysis['scatter_data']['y'],
                    pair_analysis['tag_x'],
                    pair_analysis['tag_y'],
                    pair_analysis['pearson']['coefficient']
                )
            
            # Формируем результаты
            results = {
                "correlation_matrix": correlation_matrix,
                "pair_analysis": pair_analysis,
            }
            
            # Summary
            summary_parts = [
                f"Анализ {len(request.tags)} тегов за период {period_str}.",
                f"Общих точек: {len(data['common_timestamps'])}.",
            ]
            
            # Находим самую сильную корреляцию
            max_corr = 0.0
            max_pair = None
            for i in range(len(correlation_matrix['tags'])):
                for j in range(i + 1, len(correlation_matrix['tags'])):
                    corr = correlation_matrix['matrix'][i][j]
                    if abs(corr) > abs(max_corr):
                        max_corr = corr
                        max_pair = (correlation_matrix['tags'][i], correlation_matrix['tags'][j])
            
            if max_pair:
                summary_parts.append(
                    f"Самая сильная корреляция: {max_pair[0]} ↔ {max_pair[1]} (r={max_corr:.2f})"
                )
            
            summary = " ".join(summary_parts)
        
        # Генерируем ID и сохраняем
        analysis_id = generate_analysis_id(request.tags, period_str)
        params = {
            "tags": request.tags,
            "period": period_str,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "options": {
                "anomalies": request.anomalies,
                "correlations": request.correlations,
                "seasonality": request.seasonality,
                "compare_periods": request.compare_periods,
            }
        }
        
        history_path = save_analysis(analysis_id, params, results)
        
        # Формируем ответ
        if len(request.tags) == 1:
            # Один тег
            response = AnalysisResponse(
                analysis_id=analysis_id,
                status="completed",
                created_at=datetime.now().isoformat(),
                tags=request.tags,
                period=period_str,
                summary=summary,
                statistics=stats,
                anomalies=anomalies_result,
                correlations=None,
                seasonality=None,
                visualizations={
                    "time_series": time_series_spec,
                    "histogram": histogram_spec,
                },
                history_path=history_path,
            )
        else:
            # Мульти-тег
            response = AnalysisResponse(
                analysis_id=analysis_id,
                status="completed",
                created_at=datetime.now().isoformat(),
                tags=request.tags,
                period=period_str,
                summary=summary,
                statistics=None,  # для мульти-тега статистика по каждому тегу отдельно
                anomalies=None,
                correlations=results.get('correlation_matrix'),
                seasonality=None,
                visualizations={
                    "heatmap": heatmap_spec,
                    "scatter": scatter_spec,
                },
                history_path=history_path,
            )
        
        log.info("Analysis completed", id=analysis_id, summary=summary[:100])
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        tb = traceback.format_exc()
        log.error("Analysis failed", error=str(e), tags=request.tags, traceback=tb)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {type(e).__name__}: {str(e)}")




@router.post("/pair", response_model=PairAnalysisResponse)
async def analyze_pair(request: PairAnalysisRequest):
    """
    Детальный анализ конкретной пары тегов.
    Используется при клике на ячейку в heatmap.
    """
    log.info(
        "Analyzing pair",
        tag1=request.tag1,
        tag2=request.tag2,
        period=request.period
    )
    
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=request.period)
        period_str = f"{request.period} days"
        
        # Собираем данные с выравниванием
        data = await fetch_multiple_tags(
            [request.tag1, request.tag2],
            start_date, end_date,
            resample_freq='5min',
            align=True
        )
        
        if not data['common_timestamps']:
            raise HTTPException(
                status_code=400,
                detail="No common data for pair analysis"
            )
        
        # Детальный анализ пары
        pair_analysis = compute_pair_correlation(
            data['tags'][request.tag1].get('aligned_values', []),
            data['tags'][request.tag2].get('aligned_values', []),
            request.tag1, request.tag2
        )
        
        # Scatter spec
        scatter_spec = create_scatter_spec(
            pair_analysis['scatter_data']['x'],
            pair_analysis['scatter_data']['y'],
            request.tag1, request.tag2,
            pair_analysis['pearson']['coefficient']
        )
        
        return PairAnalysisResponse(
            tag1=request.tag1,
            tag2=request.tag2,
            period=period_str,
            pearson=pair_analysis['pearson'],
            spearman=pair_analysis['spearman'],
            mutual_info=pair_analysis['mutual_info'],
            cross_correlation=pair_analysis['cross_correlation'],
            scatter_data=pair_analysis['scatter_data'],
            scatter_spec=scatter_spec,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        log.error("Pair analysis failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tags", response_model=list[TagInfo])
async def get_tags():
    """
    Возвращает список всех доступных тегов для UI dropdown.
    """
    try:
        tags = await get_available_tags()
        return [TagInfo(**tag) for tag in tags]
    except Exception as e:
        log.error("Failed to fetch tags", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch tags: {str(e)}")


@router.get("/history", response_model=list[HistoryItem])
async def get_history(limit: int = Query(50, ge=1, le=200)):
    """
    Возвращает список сохранённых анализов.
    """
    try:
        analyses = list_analyses(limit=limit)
        return [HistoryItem(**item) for item in analyses]
    except Exception as e:
        log.error("Failed to fetch history", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch history: {str(e)}")


@router.get("/history/{analysis_id}")
async def get_analysis(analysis_id: str):
    """
    Загружает сохранённый анализ по ID.
    """
    try:
        data = load_analysis(analysis_id)
        if not data:
            raise HTTPException(status_code=404, detail="Analysis not found")
        return data
    except HTTPException:
        raise
    except Exception as e:
        log.error("Failed to load analysis", id=analysis_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to load analysis: {str(e)}")


@router.delete("/history/{analysis_id}")
async def delete_analysis(analysis_id: str):
    """
    Удаляет анализ из истории.
    """
    from modules.deep_analysis.history.storage import delete_analysis as delete_from_storage
    
    try:
        deleted = delete_from_storage(analysis_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Analysis not found")
        return {"status": "deleted", "analysis_id": analysis_id}
    except HTTPException:
        raise
    except Exception as e:
        log.error("Failed to delete analysis", id=analysis_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to delete analysis: {str(e)}")


@router.get("/ping")
async def ping():
    """
    Health check для deep_analysis модуля.
    """
    return {
        "status": "ok",
        "module": "deep_analysis",
        "version": "0.1.0",
        "time": datetime.now().isoformat()
    }
