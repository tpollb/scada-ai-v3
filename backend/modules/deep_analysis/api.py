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
from modules.deep_analysis.analyzers.seasonal import detect_dominant_periods, decompose_seasonal, get_seasonal_pattern
from modules.deep_analysis.analyzers.correlations import compute_correlation_matrix, compute_pair_correlation
from modules.deep_analysis.visualizers.chart_specs import create_time_series_spec, create_histogram_spec, create_heatmap_spec, create_scatter_spec, create_multitag_time_series_spec
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
            
            if not data['raw_values']:
                raise HTTPException(
                    status_code=404,
                    detail=f"No data found for tag '{tag_name}' in the specified period"
                )
            
            # Базовая статистика
            stats = compute_basic_stats(data['raw_values'])
            histogram = compute_histogram(data['raw_values'])
            
            # Детекция аномалий
            anomalies_result = None
            if request.anomalies:
                anomalies_result = detect_anomalies_isolation_forest(
                    data['raw_values'],
                    data['raw_timestamps']
                )
            
            # Визуализации
            time_series_spec = create_time_series_spec(
                data['raw_timestamps'],
                data['raw_values'],
                tag_name,
                anomalies=anomalies_result
            )
            histogram_spec = create_histogram_spec(histogram, tag_name)
            
            # Формируем результат

            # Сезонный анализ для single-tag
            seasonal_analysis = {}
            if len(data['raw_values']) >= 50:
                try:
                    periods_result = detect_dominant_periods(
                        data['raw_values'],
                        data['raw_timestamps']
                    )
                    
                    decomp_result = None
                    pattern_result = None
                    
                    if periods_result.get('detected_periods'):
                        main_period = periods_result['detected_periods'][0]['period']
                        decomp_result = decompose_seasonal(data['raw_values'], period=main_period)
                        pattern_result = get_seasonal_pattern(data['raw_values'], period=main_period)
                    
                    seasonal_analysis = {
                        "periods": periods_result,
                        "decomposition": decomp_result,
                        "pattern": pattern_result,
                    }
                except Exception as e:
                    log.warning("Seasonal analysis failed", tag=tag_name, error=str(e))
                    seasonal_analysis = {"error": str(e)}

            results = {
                "statistics": stats,
                "histogram": histogram,
                "anomalies": anomalies_result,
                "seasonal_analysis": seasonal_analysis,
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
            # Группа тегов — кросс-анализ (корреляции) + аномалии для каждого тега
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
            
            # Детальный анализ для первой пары
            if len(request.tags) >= 2:
                tag1, tag2 = request.tags[0], request.tags[1]
                pair_analysis = compute_pair_correlation(
                    data['tags'][tag1].get('aligned_values', []),
                    data['tags'][tag2].get('aligned_values', []),
                    tag1, tag2
                )
            else:
                pair_analysis = None
            
            # НОВОЕ: Детекция аномалий для каждого тега (с классификацией по типам)
            anomalies_per_tag = {}
            total_type_counts = {}
            total_anomalies = 0
            
            for tag_name in request.tags:
                tag_data = data['tags'].get(tag_name, {})
                aligned_values = tag_data.get('aligned_values', [])
                
                # Фильтруем None значения
                valid_values = [v for v in aligned_values if v is not None]
                
                if len(valid_values) >= 10:
                    adaptive_contamination = min(0.15, max(0.08, 200 / max(len(valid_values), 1)))
                    tag_anomalies = detect_anomalies_isolation_forest(
                        valid_values,
                        [data["common_timestamps"][j] for j in range(len(aligned_values)) if j < len(aligned_values) and aligned_values[j] is not None],
                        contamination=adaptive_contamination,  # псевдо-timestamps (индексы)
                        classify_types=True
                    )
                    anomalies_per_tag[tag_name] = tag_anomalies
                    total_anomalies += tag_anomalies['total_anomalies']
                    
                    # Агрегируем type_counts
                    for atype, count in tag_anomalies.get('type_counts', {}).items():
                        total_type_counts[atype] = total_type_counts.get(atype, 0) + count
            
            # Формируем общий anomalies объект (для совместимости с UI)
            combined_anomalies = {
                "per_tag": anomalies_per_tag,
                "total_anomalies": total_anomalies,
                "type_counts": total_type_counts,
            } if total_anomalies > 0 else None
            
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
            
            # НОВОЕ: time series spec с аномалиями для мульти-тег
            # Создаём график со всеми тегами + цветовая кодировка аномалий
            time_series_spec = create_multitag_time_series_spec(
                data['tags'],
                data['common_timestamps'],
                anomalies_per_tag
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
            
            # Добавляем информацию об аномалиях
            if combined_anomalies and combined_anomalies['total_anomalies'] > 0:
                tc = combined_anomalies['type_counts']
                type_parts = []
                if tc.get('spike', 0): type_parts.append(f"пиков: {tc['spike']}")
                if tc.get('dip', 0): type_parts.append(f"провалов: {tc['dip']}")
                if tc.get('drift', 0): type_parts.append(f"дрейфов: {tc['drift']}")
                if tc.get('noise', 0): type_parts.append(f"шумов: {tc['noise']}")
                summary_parts.append(
                    f"Обнаружено аномалий: {combined_anomalies['total_anomalies']} ({', '.join(type_parts)})"
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
                seasonality=seasonal_analysis,
                visualizations={
                    "time_series": time_series_spec,
                    "histogram": histogram_spec,
                },
                history_path=history_path
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
                statistics=None,
                anomalies=combined_anomalies,  # НОВОЕ: аномалии для мульти-тег
                correlations=correlation_matrix,
                seasonality=seasonal_analysis,
                visualizations={
                    "heatmap": heatmap_spec,
                    "scatter": scatter_spec,
                    "time_series": time_series_spec,  # НОВОЕ: график с аномалиями
                },
                history_path=history_path
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
            scatter_spec=scatter_spec
        )
    
    except HTTPException:
        raise
    except Exception as e:
        log.error("Pair analysis failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/diagnose/{tag_name}")
async def diagnose_tag(tag_name: str, period: int = 30):
    """
    Диагностический endpoint — показывает детальную информацию о теге.
    
    Возвращает:
    - Количество точек в БД по диапазонам
    - Последние 20 точек с датами
    - Все аномалии с датами и значениями
    - Плато (повторяющиеся значения)
    """
    from datetime import datetime, timedelta
    from core.db import fetch
    
    log.info("Running diagnostics", tag=tag_name, period=period)
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=period)
    
    try:
        # 1. Диапазон данных
        range_query = """
            SELECT 
                MIN(tv.date_created) as first_ts,
                MAX(tv.date_created) as last_ts,
                COUNT(*) as total
            FROM tags_value tv
            JOIN tags_dict td ON td.tag_id = tv.tag_id
            WHERE td.tag_name = $1
              AND tv.date_created >= $2
              AND tv.date_created <= $3
        """
        range_result = await fetch(range_query, tag_name, start_date, end_date)
        
        # 2. Распределение по неделям
        weeks = []
        for week in range(4):
            w_start = start_date + timedelta(weeks=week)
            w_end = w_start + timedelta(weeks=1)
            
            week_query = """
                SELECT COUNT(*) as cnt
                FROM tags_value tv
                JOIN tags_dict td ON td.tag_id = tv.tag_id
                WHERE td.tag_name = $1
                  AND tv.date_created >= $2
                  AND tv.date_created < $3
            """
            week_result = await fetch(week_query, tag_name, w_start, w_end)
            weeks.append({
                "start": w_start.isoformat(),
                "end": w_end.isoformat(),
                "count": week_result[0]['cnt'] if week_result else 0
            })
        
        # 3. Последние 20 точек
        last_query = """
            SELECT tv.date_created, tv.value
            FROM tags_value tv
            JOIN tags_dict td ON td.tag_id = tv.tag_id
            WHERE td.tag_name = $1
            ORDER BY tv.date_created DESC
            LIMIT 20
        """
        last_result = await fetch(last_query, tag_name)
        last_points = [
            {
                "timestamp": r['date_created'].isoformat(),
                "value": float(r['value']) if r['value'] is not None else None
            }
            for r in last_result
        ]
        
        # 4. Низкие значения (< 200)
        low_query = """
            SELECT tv.date_created, tv.value
            FROM tags_value tv
            JOIN tags_dict td ON td.tag_id = tv.tag_id
            WHERE td.tag_name = $1
              AND tv.date_created >= $2
              AND tv.date_created <= $3
              AND tv.value < 200
            ORDER BY tv.date_created ASC
            LIMIT 50
        """
        low_result = await fetch(low_query, tag_name, start_date, end_date)
        low_points = [
            {
                "timestamp": r['date_created'].isoformat(),
                "value": float(r['value'])
            }
            for r in low_result
        ]
        
        # 5. Запускаем анализ аномалий
        from modules.deep_analysis.collectors.data_fetcher import fetch_tag_data
        from modules.deep_analysis.analyzers.anomalies import (
    detect_anomalies_isolation_forest,
    detect_zero_dips,
    detect_significant_dips,
    group_anomaly_events,
    _is_monotonic,
    _is_plateau,
    _compute_linear_trend,
    _compute_relative_change,
)
        
        data = await fetch_tag_data(tag_name, start_date, end_date)
        
        # Zero dips
        zd = detect_zero_dips(data['raw_values'], data['raw_timestamps'])
        zero_dips_events = []
        for e in zd['events'][:10]:
            ts_start = data['raw_timestamps'][e['start_idx']] if e['start_idx'] < len(data['raw_timestamps']) else None
            ts_end = data['raw_timestamps'][e['end_idx']] if e['end_idx'] < len(data['raw_timestamps']) else None
            zero_dips_events.append({
                "start": ts_start.isoformat() if ts_start else None,
                "end": ts_end.isoformat() if ts_end else None,
                "duration": e['duration'],
                "min_value": e['min_value']
            })
        
        # Significant dips
        sd = detect_significant_dips(data['raw_values'], data['raw_timestamps'])
        sig_dips_events = []
        for e in sd['events'][:10]:
            ts_start = data['raw_timestamps'][e['start_idx']] if e['start_idx'] < len(data['raw_timestamps']) else None
            ts_end = data['raw_timestamps'][e['end_idx']] if e['end_idx'] < len(data['raw_timestamps']) else None
            sig_dips_events.append({
                "start": ts_start.isoformat() if ts_start else None,
                "end": ts_end.isoformat() if ts_end else None,
                "duration": e['duration'],
                "drop_percent": e.get('drop_percent', 0),
                "min_value": e['min_value'],
                "mean_before": e.get('local_mean_before', 0)
            })
        
        # Полная детекция
        result = detect_anomalies_isolation_forest(
            data['raw_values'],
            data['raw_timestamps'],
            contamination=0.10,
            classify_types=True
        )
        
        # Детали по типам
        type_details = {}
        for atype in ['spike', 'dip', 'drift', 'noise']:
            indices = [
                i for i, t in zip(result['anomaly_indices'], result['anomaly_types'])
                if t == atype
            ]
            
            points = []
            for idx in indices[:10]:
                if idx < len(data['raw_timestamps']) and idx < len(data['raw_values']):
                    points.append({
                        "idx": idx,
                        "timestamp": data['raw_timestamps'][idx].isoformat(),
                        "value": float(data['raw_values'][idx]) if data['raw_values'][idx] is not None else None
                    })
            
            type_details[atype] = {
                "count": len(indices),
                "sample": points
            }
        
        # Плато
        plateaus = []
        current_val = None
        current_count = 0
        current_start = None
        
        for i, val in enumerate(data['raw_values']):
            if val == current_val:
                current_count += 1
            else:
                if current_count >= 5:
                    ts_start = data['raw_timestamps'][current_start] if current_start < len(data['raw_timestamps']) else None
                    ts_end = data['raw_timestamps'][i-1] if i-1 < len(data['raw_timestamps']) else None
                    
                    # Типы в этом плато
                    types_in_plateau = set()
                    for j in range(current_start, i):
                        if j in result['anomaly_indices']:
                            idx_in_list = result['anomaly_indices'].index(j)
                            types_in_plateau.add(result['anomaly_types'][idx_in_list])
                    
                    plateaus.append({
                        "start": ts_start.isoformat() if ts_start else None,
                        "end": ts_end.isoformat() if ts_end else None,
                        "count": current_count,
                        "value": float(current_val) if current_val is not None else None,
                        "types": list(types_in_plateau)
                    })
                current_val = val
                current_count = 1
                current_start = i
        
        return {
            "tag_name": tag_name,
            "period": f"{start_date.isoformat()} - {end_date.isoformat()}",
            "db_range": {
                "first_ts": range_result[0]['first_ts'].isoformat() if range_result and range_result[0]['first_ts'] else None,
                "last_ts": range_result[0]['last_ts'].isoformat() if range_result and range_result[0]['last_ts'] else None,
                "total_in_period": range_result[0]['total'] if range_result else 0
            },
            "distribution_by_weeks": weeks,
            "last_20_points": last_points,
            "low_values_under_200": {
                "count": len(low_points),
                "sample": low_points
            },
            "anomalies": {
                "total": result['total_anomalies'],
                "type_counts": result['type_counts'],
                "zero_dips_events": zero_dips_events,
                "sig_dips_events": sig_dips_events,
                "by_type": type_details
            },
            "plateaus_5plus": plateaus[:10]
        }
    
    except Exception as e:
        log.error("Diagnostics failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/diagnose_weeks/{tag_name}")
async def diagnose_anomalies_by_weeks(tag_name: str, period: int = 30):
    """
    Диагностика: распределение аномалий по неделям.
    Помогает понять, где именно пропадают аномалии.
    """
    from datetime import datetime, timedelta
    from modules.deep_analysis.collectors.data_fetcher import fetch_tag_data
    from modules.deep_analysis.analyzers.anomalies import detect_anomalies_isolation_forest
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=period)
    
    try:
        data = await fetch_tag_data(tag_name, start_date, end_date)
        
        result = detect_anomalies_isolation_forest(
            data['raw_values'],
            data['raw_timestamps'],
            classify_types=True
        )
        
        # Распределяем аномалии по неделям
        weeks = []
        for week in range(4):
            w_start = start_date + timedelta(weeks=week)
            w_end = w_start + timedelta(weeks=1)
            
            week_anomalies = {
                "start": w_start.isoformat(),
                "end": w_end.isoformat(),
                "total_points": 0,
                "anomalies": {"spike": 0, "dip": 0, "drift": 0, "noise": 0},
                "sample_points": []
            }
            
            # Считаем точки и аномалии в этой неделе
            for i, (ts, val) in enumerate(zip(data['raw_timestamps'], data['raw_values'])):
                if w_start <= ts < w_end:
                    week_anomalies["total_points"] += 1
                    
                    if i in result['anomaly_indices']:
                        idx_in_list = result['anomaly_indices'].index(i)
                        atype = result['anomaly_types'][idx_in_list]
                        week_anomalies["anomalies"][atype] = week_anomalies["anomalies"].get(atype, 0) + 1
                        
                        # Первые 3 примера
                        if len(week_anomalies["sample_points"]) < 3:
                            week_anomalies["sample_points"].append({
                                "timestamp": ts.isoformat(),
                                "value": float(val) if val is not None else None,
                                "type": atype
                            })
            
            weeks.append(week_anomalies)
        
        return {
            "tag_name": tag_name,
            "period": f"{start_date.isoformat()} - {end_date.isoformat()}",
            "total_anomalies": result['total_anomalies'],
            "type_counts": result['type_counts'],
            "anomaly_rate": result['anomaly_rate'],
            "by_week": weeks,
            "near_drift_events": near_drift[:20],  # топ-20 кандидатов в дрейфы
        }
    
    except Exception as e:
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


# ============================================================================
# Расширенная диагностика downsampling и аномалий
# ============================================================================

@router.get("/diagnose/downsampling/{tag_name}")
async def diagnose_downsampling(tag_name: str, period: int = 30, max_points: int = 1500):
    """
    Показывает как downsampling влияет на аномалии:
    1. Сырые данные (с None)
    2. Отфильтрованные данные (без None) — на них работает Isolation Forest
    3. Downsampled данные — на них отображается график
    4. Сравнение аномалий в каждом из представлений
    """
    from datetime import datetime, timedelta
    from modules.deep_analysis.collectors.data_fetcher import fetch_tag_data
    from modules.deep_analysis.analyzers.anomalies import detect_anomalies_isolation_forest
    from modules.deep_analysis.visualizers.chart_specs import downsample_time_series
    import numpy as np
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=period)
    
    try:
        data = await fetch_tag_data(tag_name, start_date, end_date)
        raw_values = data['raw_values']
        raw_timestamps = data['raw_timestamps']
        
        # 1. Сырые данные
        total = len(raw_values)
        none_count = sum(1 for v in raw_values if v is None or (isinstance(v, float) and np.isnan(v)))
        valid_count = total - none_count
        
        # 2. Отфильтрованные данные
        valid_indices = [i for i, v in enumerate(raw_values) 
                        if v is not None and not (isinstance(v, float) and np.isnan(v))]
        valid_values = [raw_values[i] for i in valid_indices]
        valid_timestamps = [raw_timestamps[i] for i in valid_indices]
        
        # 3. Детекция аномалий на отфильтрованных данных
        if len(valid_values) >= 10:
            result = detect_anomalies_isolation_forest(
                valid_values, valid_timestamps, classify_types=True
            )
        else:
            result = {'anomaly_indices': [], 'anomaly_types': [], 'anomaly_values': [], 'type_counts': {}}
        
        # 4. Downsampling
        ds_values, ds_timestamps = downsample_time_series(raw_values, raw_timestamps, max_points)
        
        # 5. Маппинг аномалий на downsampled данные
        # ЭТО КРИТИЧЕСКАЯ ЧАСТЬ — смотрим как индексы маппятся
        anomaly_mapping = []
        bucket_size = total / max_points if total > max_points else 1.0
        
        for orig_idx, val, atype in zip(
            result['anomaly_indices'][:20],
            result['anomaly_values'][:20],
            result['anomaly_types'][:20]
        ):
            # Находим оригинальный индекс в raw_values
            raw_idx = valid_indices[orig_idx]
            
            # Приблизительный индекс в downsampled
            ds_idx_approx = int(raw_idx / bucket_size) if bucket_size > 0 else raw_idx
            ds_idx_approx = min(ds_idx_approx, len(ds_values) - 1)
            
            ds_val = ds_values[ds_idx_approx]
            ds_ts = ds_timestamps[ds_idx_approx] if ds_idx_approx < len(ds_timestamps) else None
            
            # Ищем реальное значение в bucket
            bucket_start = int(raw_idx / bucket_size) * int(bucket_size) if bucket_size > 1 else raw_idx
            bucket_end = min(bucket_start + int(bucket_size) + 1, total) if bucket_size > 1 else raw_idx + 1
            
            anomaly_mapping.append({
                'type': atype,
                'orig_idx': raw_idx,
                'orig_value': val,
                'orig_timestamp': raw_timestamps[raw_idx].isoformat() if raw_idx < len(raw_timestamps) else None,
                'ds_idx_approx': ds_idx_approx,
                'ds_value': float(ds_val) if ds_val is not None else None,
                'ds_timestamp': ds_ts.isoformat() if hasattr(ds_ts, 'isoformat') else str(ds_ts),
                'value_diff': abs(val - ds_val) if ds_val is not None else None,
                'bucket_range': [bucket_start, bucket_end],
            })
        
        # 6. Анализ дрейфов — ищем потенциальные дрейфы в данных
        potential_drifts = []
        window_size = 30
        for i in range(0, len(valid_values) - window_size, window_size // 2):
            window = valid_values[i:i+window_size]
            
            if None in window:
                continue
            
            try:
                x = np.arange(len(window))
                y = np.array(window)
                slope, intercept = np.polyfit(x, y, 1)
                y_pred = slope * x + intercept
                ss_res = np.sum((y - y_pred) ** 2)
                ss_tot = np.sum((y - np.mean(y)) ** 2)
                r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0
                
                # Монотонность
                increases = sum(1 for j in range(len(window)-1) if window[j+1] > window[j])
                decreases = sum(1 for j in range(len(window)-1) if window[j+1] < window[j])
                monotonic_ratio = max(increases, decreases) / (len(window) - 1)
                
                # Изменение
                change = abs(window[-1] - window[0]) / (abs(window[0]) + 1e-10)
                
                if r_squared > 0.5 and monotonic_ratio > 0.6 and change > 0.03:
                    potential_drifts.append({
                        'start_idx': i,
                        'end_idx': i + window_size,
                        'start_timestamp': valid_timestamps[i].isoformat(),
                        'end_timestamp': valid_timestamps[i + window_size - 1].isoformat(),
                        'start_value': float(window[0]),
                        'end_value': float(window[-1]),
                        'r_squared': float(r_squared),
                        'monotonic_ratio': float(monotonic_ratio),
                        'change_percent': float(change * 100),
                    })
            except Exception:
                continue
        
        # Сортируем по r_squared
        potential_drifts.sort(key=lambda x: x['r_squared'], reverse=True)
        
        return {
            'tag_name': tag_name,
            'period_days': period,
            'raw_data': {
                'total_points': total,
                'valid_points': valid_count,
                'null_points': none_count,
                'null_percent': round(none_count / total * 100, 2) if total > 0 else 0,
                'first_timestamp': raw_timestamps[0].isoformat() if raw_timestamps else None,
                'last_timestamp': raw_timestamps[-1].isoformat() if raw_timestamps else None,
            },
            'anomalies_detected': {
                'total': result.get('total_anomalies', 0),
                'type_counts': result.get('type_counts', {}),
                'rate': result.get('anomaly_rate', 0),
            },
            'downsampling': {
                'original_points': total,
                'downsampled_points': len(ds_values),
                'compression_ratio': round(total / len(ds_values), 2) if ds_values else 0,
                'bucket_size': round(bucket_size, 2),
            },
            'anomaly_mapping_sample': anomaly_mapping,
            'potential_drifts': potential_drifts[:20],
            'summary': {
                'null_affects_analysis': none_count > valid_count * 0.1,
                'downsampling_loses_anomalies': any(
                    m['value_diff'] is not None and m['value_diff'] > 50
                    for m in anomaly_mapping
                ),
                'drifts_found_but_not_classified': len(potential_drifts) > 0 and result.get('type_counts', {}).get('drift', 0) == 0,
            },
        }
    
    except Exception as e:
        log.error("Downsampling diagnosis failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

