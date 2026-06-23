#!/usr/bin/env python3
"""
day2_correlations.py — мульти-тег анализ + корреляции
"""

from pathlib import Path

print('=' * 70)
print('DAY 2: КОРРЕЛЯЦИИ + МУЛЬТИ-ТЕГ АНАЛИЗ')
print('=' * 70)
print()

# ============================================================================
# 1. Создаём correlations.py
# ============================================================================
correlations_path = Path('backend/modules/deep_analysis/analyzers/correlations.py')

correlations_content = '''"""Корреляционный анализ: Pearson, Spearman, Mutual Information, Cross-correlation"""
from typing import Optional
import numpy as np
from scipy import stats
from sklearn.metrics import mutual_info_score
from structlog import get_logger

log = get_logger()


def compute_pearson(x: list[float], y: list[float]) -> dict:
    """
    Вычисляет коэффициент корреляции Пирсона (линейная зависимость).
    
    Returns:
        {
            "coefficient": float,  # от -1 до 1
            "p_value": float,      # статистическая значимость
            "interpretation": str  # "сильная положительная" / "слабая" / etc.
        }
    """
    if len(x) < 3 or len(y) < 3:
        return {"coefficient": 0.0, "p_value": 1.0, "interpretation": "недостаточно данных"}
    
    try:
        coef, p_val = stats.pearsonr(x, y)
        return {
            "coefficient": float(coef),
            "p_value": float(p_val),
            "interpretation": _interpret_correlation(coef, p_val),
        }
    except Exception as e:
        log.warning("Pearson correlation failed", error=str(e))
        return {"coefficient": 0.0, "p_value": 1.0, "interpretation": "ошибка"}


def compute_spearman(x: list[float], y: list[float]) -> dict:
    """
    Вычисляет коэффициент корреляции Спирмена (монотонная зависимость, ранговая).
    
    Returns:
        {
            "coefficient": float,
            "p_value": float,
            "interpretation": str
        }
    """
    if len(x) < 3 or len(y) < 3:
        return {"coefficient": 0.0, "p_value": 1.0, "interpretation": "недостаточно данных"}
    
    try:
        coef, p_val = stats.spearmanr(x, y)
        return {
            "coefficient": float(coef),
            "p_value": float(p_val),
            "interpretation": _interpret_correlation(coef, p_val),
        }
    except Exception as e:
        log.warning("Spearman correlation failed", error=str(e))
        return {"coefficient": 0.0, "p_value": 1.0, "interpretation": "ошибка"}


def compute_mutual_information(x: list[float], y: list[float], n_bins: int = 20) -> dict:
    """
    Вычисляет Mutual Information (нелинейная зависимость).
    
    Returns:
        {
            "mi": float,  # mutual information score (0 = независимы, >0 = зависимы)
            "normalized": float,  # нормализованное значение [0, 1]
            "interpretation": str
        }
    """
    if len(x) < 10 or len(y) < 10:
        return {"mi": 0.0, "normalized": 0.0, "interpretation": "недостаточно данных"}
    
    try:
        # Дискретизация непрерывных значений
        x_binned = np.digitize(x, np.histogram_bin_edges(x, bins=n_bins))
        y_binned = np.digitize(y, np.histogram_bin_edges(y, bins=n_bins))
        
        mi = mutual_info_score(x_binned, y_binned)
        
        # Нормализация: делим на max(H(X), H(Y)) для получения значения [0, 1]
        h_x = -np.sum([p * np.log(p + 1e-10) for p in np.bincount(x_binned) / len(x_binned)])
        h_y = -np.sum([p * np.log(p + 1e-10) for p in np.bincount(y_binned) / len(y_binned)])
        normalized = mi / max(h_x, h_y) if max(h_x, h_y) > 0 else 0.0
        
        return {
            "mi": float(mi),
            "normalized": float(normalized),
            "interpretation": _interpret_mi(normalized),
        }
    except Exception as e:
        log.warning("Mutual information failed", error=str(e))
        return {"mi": 0.0, "normalized": 0.0, "interpretation": "ошибка"}


def compute_cross_correlation(x: list[float], y: list[float], max_lag: int = 50) -> dict:
    """
    Вычисляет cross-correlation с лагом (что происходит раньше: X или Y?).
    
    Returns:
        {
            "max_correlation": float,  # максимальная корреляция
            "optimal_lag": int,        # оптимальный лаг (положительный = X опережает Y)
            "lags": list[int],         # все проверенные лаги
            "correlations": list[float],  # корреляции для каждого лага
            "interpretation": str
        }
    """
    if len(x) < 10 or len(y) < 10:
        return {
            "max_correlation": 0.0,
            "optimal_lag": 0,
            "lags": [],
            "correlations": [],
            "interpretation": "недостаточно данных"
        }
    
    try:
        x_arr = np.array(x)
        y_arr = np.array(y)
        
        # Нормализация
        x_norm = (x_arr - np.mean(x_arr)) / (np.std(x_arr) + 1e-10)
        y_norm = (y_arr - np.mean(y_arr)) / (np.std(y_arr) + 1e-10)
        
        lags = list(range(-max_lag, max_lag + 1))
        correlations = []
        
        for lag in lags:
            if lag >= 0:
                # X опережает Y на lag шагов
                corr = np.corrcoef(x_norm[:-lag if lag > 0 else None], y_norm[lag:])[0, 1]
            else:
                # Y опережает X на |lag| шагов
                corr = np.corrcoef(x_norm[-lag:], y_norm[:lag])[0, 1]
            correlations.append(float(corr) if not np.isnan(corr) else 0.0)
        
        max_idx = np.argmax(np.abs(correlations))
        max_corr = correlations[max_idx]
        optimal_lag = lags[max_idx]
        
        return {
            "max_correlation": float(max_corr),
            "optimal_lag": int(optimal_lag),
            "lags": lags,
            "correlations": correlations,
            "interpretation": _interpret_lag(max_corr, optimal_lag),
        }
    except Exception as e:
        log.warning("Cross-correlation failed", error=str(e))
        return {
            "max_correlation": 0.0,
            "optimal_lag": 0,
            "lags": [],
            "correlations": [],
            "interpretation": "ошибка"
        }


def compute_correlation_matrix(
    tags_data: dict[str, dict],
    common_timestamps: list,
    method: str = "pearson"
) -> dict:
    """
    Вычисляет матрицу корреляций для всех пар тегов.
    
    Args:
        tags_data: {tag_name: {"aligned_values": [...], ...}, ...}
        common_timestamps: общие timestamps
        method: "pearson", "spearman", "mutual_info"
    
    Returns:
        {
            "tags": list[str],  # порядок тегов
            "matrix": [[r11, r12, ...], [r21, r22, ...], ...],  # матрица корреляций
            "p_values": [[p11, p12, ...], [p21, p22, ...], ...],  # p-values
            "method": str
        }
    """
    tag_names = list(tags_data.keys())
    n_tags = len(tag_names)
    
    # Извлекаем aligned_values
    values_dict = {}
    for tag in tag_names:
        values_dict[tag] = tags_data[tag].get('aligned_values', [])
    
    # Фильтруем строки где все значения не None
    valid_indices = []
    for i in range(len(common_timestamps)):
        all_valid = all(
            values_dict[tag][i] is not None 
            for tag in tag_names 
            if i < len(values_dict[tag])
        )
        if all_valid:
            valid_indices.append(i)
    
    if len(valid_indices) < 3:
        log.warning("Not enough valid data points for correlation matrix", count=len(valid_indices))
        return {
            "tags": tag_names,
            "matrix": [[0.0] * n_tags for _ in range(n_tags)],
            "p_values": [[1.0] * n_tags for _ in range(n_tags)],
            "method": method,
        }
    
    # Формируем массивы для корреляций
    arrays = {}
    for tag in tag_names:
        arrays[tag] = [values_dict[tag][i] for i in valid_indices]
    
    # Вычисляем матрицу
    matrix = []
    p_values = []
    
    for i, tag1 in enumerate(tag_names):
        row_matrix = []
        row_pvalues = []
        for j, tag2 in enumerate(tag_names):
            if i == j:
                # Диагональ: корреляция с самим собой
                row_matrix.append(1.0)
                row_pvalues.append(0.0)
            else:
                if method == "pearson":
                    result = compute_pearson(arrays[tag1], arrays[tag2])
                elif method == "spearman":
                    result = compute_spearman(arrays[tag1], arrays[tag2])
                elif method == "mutual_info":
                    result = compute_mutual_information(arrays[tag1], arrays[tag2])
                    row_matrix.append(result['normalized'])
                    row_pvalues.append(0.0)  # MI не имеет p-value
                    continue
                else:
                    result = compute_pearson(arrays[tag1], arrays[tag2])
                
                row_matrix.append(result['coefficient'])
                row_pvalues.append(result['p_value'])
        
        matrix.append(row_matrix)
        p_values.append(row_pvalues)
    
    return {
        "tags": tag_names,
        "matrix": matrix,
        "p_values": p_values,
        "method": method,
        "valid_points": len(valid_indices),
    }


def compute_pair_correlation(
    x: list[float],
    y: list[float],
    tag_x: str,
    tag_y: str,
) -> dict:
    """
    Детальный анализ корреляции для пары тегов.
    
    Returns:
        {
            "tag_x": str,
            "tag_y": str,
            "pearson": {...},
            "spearman": {...},
            "mutual_info": {...},
            "cross_correlation": {...},
            "scatter_data": {"x": [...], "y": [...]},
        }
    """
    # Фильтруем валидные точки
    valid_pairs = [(xi, yi) for xi, yi in zip(x, y) if xi is not None and yi is not None]
    
    if len(valid_pairs) < 3:
        return {
            "tag_x": tag_x,
            "tag_y": tag_y,
            "pearson": {"coefficient": 0.0, "p_value": 1.0, "interpretation": "недостаточно данных"},
            "spearman": {"coefficient": 0.0, "p_value": 1.0, "interpretation": "недостаточно данных"},
            "mutual_info": {"mi": 0.0, "normalized": 0.0, "interpretation": "недостаточно данных"},
            "cross_correlation": {"max_correlation": 0.0, "optimal_lag": 0, "interpretation": "недостаточно данных"},
            "scatter_data": {"x": [], "y": []},
        }
    
    x_valid = [p[0] for p in valid_pairs]
    y_valid = [p[1] for p in valid_pairs]
    
    return {
        "tag_x": tag_x,
        "tag_y": tag_y,
        "pearson": compute_pearson(x_valid, y_valid),
        "spearman": compute_spearman(x_valid, y_valid),
        "mutual_info": compute_mutual_information(x_valid, y_valid),
        "cross_correlation": compute_cross_correlation(x_valid, y_valid),
        "scatter_data": {"x": x_valid, "y": y_valid},
    }


def _interpret_correlation(coef: float, p_value: float, alpha: float = 0.05) -> str:
    """Интерпретирует коэффициент корреляции"""
    abs_coef = abs(coef)
    
    # Статистическая значимость
    if p_value > alpha:
        return "незначимая (p > 0.05)"
    
    # Сила корреляции
    if abs_coef >= 0.7:
        strength = "сильная"
    elif abs_coef >= 0.5:
        strength = "умеренная"
    elif abs_coef >= 0.3:
        strength = "слабая"
    else:
        strength = "очень слабая"
    
    # Направление
    direction = "положительная" if coef > 0 else "отрицательная"
    
    return f"{strength} {direction} (r={coef:.2f}, p={p_value:.4f})"


def _interpret_mi(normalized: float) -> str:
    """Интерпретирует нормализованную Mutual Information"""
    if normalized >= 0.5:
        return "сильная зависимость"
    elif normalized >= 0.3:
        return "умеренная зависимость"
    elif normalized >= 0.1:
        return "слабая зависимость"
    else:
        return "независимы или очень слабая зависимость"


def _interpret_lag(max_corr: float, optimal_lag: int) -> str:
    """Интерпретирует оптимальный лаг"""
    if abs(max_corr) < 0.3:
        return "слабая корреляция"
    
    if optimal_lag == 0:
        return "синхронная зависимость"
    elif optimal_lag > 0:
        return f"X опережает Y на {optimal_lag} шагов"
    else:
        return f"Y опережает X на {abs(optimal_lag)} шагов"
'''

correlations_path.write_text(correlations_content, encoding='utf-8', newline='\n')
print('✓ Создан: backend/modules/deep_analysis/analyzers/correlations.py')

# ============================================================================
# 2. Обновляем chart_specs.py — добавляем heatmap и scatter plot
# ============================================================================
chart_specs_path = Path('backend/modules/deep_analysis/visualizers/chart_specs.py')
content = chart_specs_path.read_text(encoding='utf-8')

# Добавляем функции для heatmap и scatter
new_functions = '''

def create_heatmap_spec(
    correlation_matrix: dict,
    title: str = "Матрица корреляций"
) -> dict:
    """
    Создаёт JSON-спецификацию для heatmap (матрица корреляций).
    
    Args:
        correlation_matrix: результат от compute_correlation_matrix()
        title: заголовок графика
    
    Returns:
        Chart.js конфигурация для heatmap
    """
    tags = correlation_matrix['tags']
    matrix = correlation_matrix['matrix']
    
    # Форматируем данные для Chart.js heatmap
    # Chart.js не имеет встроенного heatmap, поэтому используем scatter с цветами
    datasets = []
    
    for i, tag1 in enumerate(tags):
        for j, tag2 in enumerate(tags):
            value = matrix[i][j]
            # Цвет: красный (отрицательная) → белый (ноль) → синий (положительная)
            if value >= 0:
                color = f"rgba(59, 130, 246, {abs(value)})"  # синий
            else:
                color = f"rgba(239, 68, 68, {abs(value)})"  # красный
            
            datasets.append({
                "x": j,
                "y": i,
                "v": value,
                "r": abs(value) * 20 + 5,  # размер точки
                "backgroundColor": color,
            })
    
    spec = {
        "type": "bubble",
        "data": {
            "datasets": [{
                "label": title,
                "data": datasets,
                "backgroundColor": [d["backgroundColor"] for d in datasets],
            }]
        },
        "options": {
            "responsive": True,
            "maintainAspectRatio": False,
            "plugins": {
                "legend": {"display": False},
                "tooltip": {
                    "callbacks": {
                        "label": f"function(context) {{ return '{tags[0]}: ' + context.raw.v.toFixed(2); }}"
                    }
                }
            },
            "scales": {
                "x": {
                    "type": "linear",
                    "min": -0.5,
                    "max": len(tags) - 0.5,
                    "ticks": {
                        "callback": f"function(value) {{ return {tags}[value] || ''; }}",
                        "stepSize": 1,
                    },
                    "title": {"display": False},
                },
                "y": {
                    "type": "linear",
                    "min": -0.5,
                    "max": len(tags) - 0.5,
                    "ticks": {
                        "callback": f"function(value) {{ return {tags}[value] || ''; }}",
                        "stepSize": 1,
                    },
                    "title": {"display": False},
                }
            }
        }
    }
    
    return spec


def create_scatter_spec(
    x_values: list[float],
    y_values: list[float],
    tag_x: str,
    tag_y: str,
    correlation_coef: float,
) -> dict:
    """
    Создаёт JSON-спецификацию для scatter plot (пара тегов).
    
    Returns:
        Chart.js конфигурация для scatter plot с линией регрессии
    """
    # Точки данных
    points = [{"x": x, "y": y} for x, y in zip(x_values, y_values)]
    
    # Линия регрессии (линейная)
    if len(x_values) > 1:
        x_arr = np.array(x_values)
        y_arr = np.array(y_values)
        slope, intercept = np.polyfit(x_arr, y_arr, 1)
        
        # Две точки для линии регрессии
        x_min, x_max = float(np.min(x_arr)), float(np.max(x_arr))
        regression_line = [
            {"x": x_min, "y": slope * x_min + intercept},
            {"x": x_max, "y": slope * x_max + intercept},
        ]
    else:
        regression_line = []
    
    spec = {
        "type": "scatter",
        "data": {
            "datasets": [
                {
                    "label": f"{tag_x} vs {tag_y}",
                    "data": points,
                    "backgroundColor": "rgba(59, 130, 246, 0.5)",
                    "borderColor": "rgba(59, 130, 246, 1)",
                    "pointRadius": 3,
                },
                {
                    "label": f"Регрессия (r={correlation_coef:.2f})",
                    "data": regression_line,
                    "type": "line",
                    "borderColor": "rgba(239, 68, 68, 1)",
                    "borderWidth": 2,
                    "borderDash": [5, 5],
                    "pointRadius": 0,
                    "fill": False,
                }
            ]
        },
        "options": {
            "responsive": True,
            "maintainAspectRatio": False,
            "plugins": {
                "legend": {
                    "display": True,
                    "position": "top",
                },
                "tooltip": {
                    "mode": "nearest",
                    "intersect": True,
                }
            },
            "scales": {
                "x": {
                    "type": "linear",
                    "title": {"display": True, "text": tag_x},
                },
                "y": {
                    "type": "linear",
                    "title": {"display": True, "text": tag_y},
                }
            }
        }
    }
    
    return spec
'''

# Добавляем импорт numpy в начало файла
if 'import numpy as np' not in content:
    content = content.replace(
        'from typing import Optional',
        'from typing import Optional\nimport numpy as np'
    )

# Добавляем новые функции в конец
content += new_functions

chart_specs_path.write_text(content, encoding='utf-8', newline='\n')
print('✓ Обновлён: backend/modules/deep_analysis/visualizers/chart_specs.py')
print('  Добавлены: create_heatmap_spec(), create_scatter_spec()')

# ============================================================================
# 3. Обновляем api.py — добавляем поддержку мульти-тега
# ============================================================================
api_path = Path('backend/modules/deep_analysis/api.py')
content = api_path.read_text(encoding='utf-8')

# Импортируем correlations
if 'from modules.deep_analysis.analyzers.correlations import' not in content:
    content = content.replace(
        'from modules.deep_analysis.analyzers.anomalies import detect_anomalies_isolation_forest',
        'from modules.deep_analysis.analyzers.anomalies import detect_anomalies_isolation_forest\nfrom modules.deep_analysis.analyzers.correlations import compute_correlation_matrix, compute_pair_correlation'
    )

# Импортируем новые функции chart_specs
if 'create_heatmap_spec' not in content:
    content = content.replace(
        'from modules.deep_analysis.visualizers.chart_specs import create_time_series_spec, create_histogram_spec',
        'from modules.deep_analysis.visualizers.chart_specs import create_time_series_spec, create_histogram_spec, create_heatmap_spec, create_scatter_spec'
    )

# Находим блок с else: raise HTTPException(501) и заменяем на полную реализацию
old_multi_tag_block = '''        else:
            # Группа тегов — кросс-анализ (упрощённо для Итерации 1)
            # TODO: полная реализация в Итерации 2
            raise HTTPException(
                status_code=501,
                detail="Multi-tag analysis will be implemented in Iteration 2"
            )'''

new_multi_tag_block = '''        else:
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
            
            summary = " ".join(summary_parts)'''

if old_multi_tag_block in content:
    content = content.replace(old_multi_tag_block, new_multi_tag_block)
    print('✓ Обновлён: backend/modules/deep_analysis/api.py')
    print('  Добавлена поддержка мульти-тег анализа')
else:
    print('⚠ Не удалось найти блок для замены в api.py')

# Обновляем формирование ответа для мульти-тега
old_response_block = '''        # Формируем ответ
        response = AnalysisResponse(
            analysis_id=analysis_id,
            status="completed",
            created_at=datetime.now().isoformat(),
            tags=request.tags,
            period=period_str,
            summary=summary,
            statistics=stats,
            anomalies=anomalies_result,
            correlations=None,  # TODO: Итерация 2
            seasonality=None,   # TODO: Итерация 2
            visualizations={
                "time_series": time_series_spec,
                "histogram": histogram_spec,
            },
            history_path=history_path,
        )'''

new_response_block = '''        # Формируем ответ
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
            )'''

if old_response_block in content:
    content = content.replace(old_response_block, new_response_block)
    print('✓ Обновлён блок формирования ответа')

# Сохраняем
api_path.write_text(content, encoding='utf-8', newline='\n')

print()
print('=' * 70)
print('ГОТОВО!')
print('=' * 70)
print()
print('Что сделано:')
print('  1. ✓ Создан correlations.py с математикой:')
print('     • Pearson correlation (линейная зависимость)')
print('     • Spearman correlation (монотонная зависимость)')
print('     • Mutual Information (нелинейная зависимость)')
print('     • Cross-correlation с лагом (что опережает)')
print('     • compute_correlation_matrix() — матрица для всех пар')
print('     • compute_pair_correlation() — детальный анализ пары')
print()
print('  2. ✓ Обновлён chart_specs.py:')
print('     • create_heatmap_spec() — матрица корреляций (bubble chart)')
print('     • create_scatter_spec() — scatter plot с линией регрессии')
print()
print('  3. ✓ Обновлён api.py:')
print('     • Убрана ошибка 501 для мульти-тега')
print('     • Добавлена логика мульти-тег анализа')
print('     • Вызов fetch_multiple_tags с выравниванием')
print('     • Вычисление correlation_matrix')
print('     • Детальный pair_analysis для первой пары')
print('     • Heatmap + scatter визуализации')
print()
print('Перезапусти backend и проверь:')
print()
print('  curl -X POST http://localhost:8081/api/v1/deep_analysis/run \\')
print('    -H "Content-Type: application/json" \\')
print('    -d \'{"tags": ["R203-Temperature", "R203-CO2", "R203-Humidity"], "period": 30}\'')
print()
print('Ожидай в ответе:')
print('  • "correlations": {матрица 3x3 с коэффициентами}')
print('  • "pair_analysis": {детальный анализ первой пары}')
print('  • "visualizations": {"heatmap": {...}, "scatter": {...}}')
print('  • "summary": "Самая сильная корреляция: R203-Temperature ↔ R203-CO2 (r=0.75)"')