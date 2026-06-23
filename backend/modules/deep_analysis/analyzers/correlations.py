"""Корреляционный анализ: Pearson, Spearman, Mutual Information, Cross-correlation"""
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
