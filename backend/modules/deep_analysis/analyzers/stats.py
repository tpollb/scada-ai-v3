"""Базовая статистика: mean, median, std, quartiles, IQR, KDE"""
from typing import Optional
import numpy as np
from structlog import get_logger

log = get_logger()


def compute_basic_stats(values: list[float]) -> dict:
    """
    Вычисляет базовую статистику по массиву значений.
    
    Args:
        values: список числовых значений (без NaN)
    
    Returns:
        {
            "count": int,
            "mean": float,
            "median": float,
            "std": float,
            "variance": float,
            "min": float,
            "max": float,
            "range": float,
            "q1": float,  # 25-й перцентиль
            "q3": float,  # 75-й перцентиль
            "iqr": float, # межквартильный размах
            "skewness": float,  # асимметрия
            "kurtosis": float,  # эксцесс
        }
    """
    if not values:
        return {"count": 0}
    
    arr = np.array(values, dtype=np.float64)
    
    q1 = np.percentile(arr, 25)
    q3 = np.percentile(arr, 75)
    
    stats = {
        "count": len(arr),
        "mean": float(np.mean(arr)),
        "median": float(np.median(arr)),
        "std": float(np.std(arr, ddof=1)),  # sample std
        "variance": float(np.var(arr, ddof=1)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "range": float(np.max(arr) - np.min(arr)),
        "q1": float(q1),
        "q3": float(q3),
        "iqr": float(q3 - q1),
        "skewness": float(_skewness(arr)),
        "kurtosis": float(_kurtosis(arr)),
    }
    
    log.debug("Basic stats computed", count=len(arr), mean=stats['mean'], std=stats['std'])
    return stats


def _skewness(arr: np.ndarray) -> float:
    """Вычисляет коэффициент асимметрии"""
    n = len(arr)
    if n < 3:
        return 0.0
    
    mean = np.mean(arr)
    std = np.std(arr, ddof=1)
    if std == 0:
        return 0.0
    
    return float(np.sum(((arr - mean) / std) ** 3) * n / ((n - 1) * (n - 2)))


def _kurtosis(arr: np.ndarray) -> float:
    """Вычисляет коэффициент эксцесса (избыточный)"""
    n = len(arr)
    if n < 4:
        return 0.0
    
    mean = np.mean(arr)
    std = np.std(arr, ddof=1)
    if std == 0:
        return 0.0
    
    m4 = np.mean((arr - mean) ** 4)
    m2 = np.var(arr, ddof=1)
    
    # Избыточный эксцесс (нормальное распределение = 0)
    return float(m4 / (m2 ** 2) - 3)


def compute_histogram(
    values: list[float],
    bins: int = 50
) -> dict:
    """
    Вычисляет гистограмму распределения.
    
    Returns:
        {
            "bin_edges": list[float],
            "bin_counts": list[int],
            "bin_centers": list[float],
        }
    """
    if not values:
        return {"bin_edges": [], "bin_counts": [], "bin_centers": []}
    
    arr = np.array(values, dtype=np.float64)
    counts, bin_edges = np.histogram(arr, bins=bins)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    
    return {
        "bin_edges": bin_edges.tolist(),
        "bin_counts": counts.tolist(),
        "bin_centers": bin_centers.tolist(),
    }
