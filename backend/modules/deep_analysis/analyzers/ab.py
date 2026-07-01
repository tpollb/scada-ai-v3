"""A/B анализ: сравнение двух временных периодов или двух тегов

Модуль для сравнительного анализа:
- Before/After: один тег в разные периоды
- Equipment Comparison: два тега в один период
"""
from typing import Optional
from datetime import datetime
import numpy as np
from scipy import stats
from structlog import get_logger

from .stats import compute_basic_stats
from .seasonal import detect_dominant_periods, get_seasonal_pattern

log = get_logger()

def _safe_float(v, default=0.0):
    if v is None:
        return default
    try:
        v = float(v)
    except (TypeError, ValueError):
        return default
    if v != v or abs(v) > 1e10:
        return default
    return v


def _safe_pct_change(val_a, val_b):
    if val_a is None or val_b is None:
        return 0.0
    if abs(val_a) < 1e-10:
        return 0.0 if abs(val_b) < 1e-10 else (9999.0 if val_b > 0 else -9999.0)
    delta = ((val_b - val_a) / abs(val_a)) * 100
    if delta != delta or abs(delta) > 1e6:
        return 0.0
    return float(delta)


MIN_SAMPLE_SIZE = 10



def compare_snapshots(data_a: list[float], data_b: list[float]) -> dict:
    """
    Сравнивает два набора данных (snapshot A vs snapshot B).
    Полная защита от NaN, малых выборок, KeyError, ZeroDivisionError.
    """
    # Валидация размера выборки
    if len(data_a) < MIN_SAMPLE_SIZE or len(data_b) < MIN_SAMPLE_SIZE:
        return {
            "statistics": {"a": {}, "b": {}, "delta": {}},
            "significance": {
                "t_stat": 0.0, "p_value": 1.0, "cohens_d": 0.0,
                "interpretation": "insufficient_data",
                "reason": f"Sample too small: {len(data_a)}/{len(data_b)} (min {MIN_SAMPLE_SIZE})"
            }
        }

    # Фильтрация NaN/Inf из данных
    def is_valid(x):
        if x is None:
            return False
        try:
            return x == x and abs(x) < 1e15
        except (TypeError, ValueError):
            return False
    
    clean_a = [x for x in data_a if is_valid(x)]
    clean_b = [x for x in data_b if is_valid(x)]

    if len(clean_a) < MIN_SAMPLE_SIZE or len(clean_b) < MIN_SAMPLE_SIZE:
        return {
            "statistics": {"a": {}, "b": {}, "delta": {}},
            "significance": {
                "t_stat": 0.0, "p_value": 1.0, "cohens_d": 0.0,
                "interpretation": "insufficient_data",
                "reason": f"Too many NaN: {len(clean_a)}/{len(clean_b)}"
            }
        }

    # Базовая статистика с защитой
    try:
        stats_a = compute_basic_stats(clean_a) or {}
        stats_b = compute_basic_stats(clean_b) or {}
    except Exception as e:
        log.error("compute_basic_stats failed", error=str(e))
        stats_a, stats_b = {}, {}

    if not isinstance(stats_a, dict):
        stats_a = {}
    if not isinstance(stats_b, dict):
        stats_b = {}

    # Разница в процентах через безопасный доступ
    delta = {}
    for key in ['mean', 'median', 'std', 'min', 'max', 'range']:
        val_a = stats_a.get(key)
        val_b = stats_b.get(key)
        delta[key] = _safe_pct_change(val_a, val_b)

    # t-test с try/except и проверкой variance
    t_stat, p_value = 0.0, 1.0
    try:
        if len(clean_a) >= 2 and len(clean_b) >= 2:
            var_a = stats_a.get('variance', 0)
            var_b = stats_b.get('variance', 0)
            if (var_a is not None and var_a > 0) or (var_b is not None and var_b > 0):
                result = stats.ttest_ind(clean_a, clean_b, equal_var=False)
                t_stat = float(result.statistic)
                p_value = float(result.pvalue)
    except Exception as e:
        log.warning("ttest_ind failed", error=str(e))

    # Cohen's d — через безопасные .get()
    mean_a = _safe_float(stats_a.get('mean'), 0.0)
    mean_b = _safe_float(stats_b.get('mean'), 0.0)
    var_a = _safe_float(stats_a.get('variance'), 0.0)
    var_b = _safe_float(stats_b.get('variance'), 0.0)

    mean_diff = mean_b - mean_a
    pooled_var = (var_a + var_b) / 2
    try:
        pooled_std = float(np.sqrt(pooled_var)) if pooled_var > 0 else 0.0
    except Exception:
        pooled_std = 0.0
    cohens_d = mean_diff / pooled_std if pooled_std > 1e-10 else 0.0

    # Интерпретация значимости
    p_value = _safe_float(p_value, 1.0)
    if p_value < 0.001:
        significance_interp = "highly_significant"
    elif p_value < 0.05:
        significance_interp = "significant"
    else:
        significance_interp = "not_significant"

    # Санитизация stats
    def sanitize_dict(d):
        if not isinstance(d, dict):
            return {}
        result = {}
        for k, v in d.items():
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                result[k] = _safe_float(v, 0.0)
            else:
                result[k] = v
        return result

    return {
        "statistics": {
            "a": sanitize_dict(stats_a),
            "b": sanitize_dict(stats_b),
            "delta": delta
        },
        "significance": {
            "t_stat": _safe_float(t_stat),
            "p_value": p_value,
            "cohens_d": _safe_float(cohens_d),
            "interpretation": significance_interp
        }
    }


def compare_patterns(
    values_a: list[float],
    values_b: list[float],
    period_a: Optional[int] = None,
    period_b: Optional[int] = None
) -> dict:
    """
    Сравнивает сезонные паттерны двух наборов данных.

    Args:
        values_a: значения первого периода/тега
        values_b: значения второго периода/тега
        period_a: доминирующий период для A (если None - автодетект)
        period_b: доминирующий период для B (если None - автодетект)

    Returns:
        {
            "a": {"period": int, "pattern": [...], "amplitude": float},
            "b": {"period": int, "pattern": [...], "amplitude": float},
            "comparison": {
                "period_match": bool,
                "delta_amplitude_pct": float,
                "pattern_correlation": float
            }
        }
    """
    # Автодетект периодов если не указаны
    if period_a is None:
        periods_a = detect_dominant_periods(values_a)
        # Структура возврата: {"detected_periods": [...], "fft_peaks": [...], ...}
        detected = periods_a.get('detected_periods', []) if isinstance(periods_a, dict) else []
        if detected and len(detected) > 0:
            period_a = detected[0].get('period', 288)
        else:
            period_a = 288  # fallback: 24h at 5min resolution

    if period_b is None:
        periods_b = detect_dominant_periods(values_b)
        detected = periods_b.get('detected_periods', []) if isinstance(periods_b, dict) else []
        if detected and len(detected) > 0:
            period_b = detected[0].get('period', 288)
        else:
            period_b = 288  # fallback: 24h at 5min resolution

    # Вычисляем паттерны (возвращает dict: {"pattern": [...], "std": [...], "n_samples": [...]})
    result_a = get_seasonal_pattern(values_a, period_a)
    result_b = get_seasonal_pattern(values_b, period_b)
    
    # Извлекаем массивы значений
    pattern_a = result_a.get('pattern', []) if isinstance(result_a, dict) else result_a
    pattern_b = result_b.get('pattern', []) if isinstance(result_b, dict) else result_b

    # Амплитуды (с защитой от пустых списков)
    if pattern_a and len(pattern_a) > 0:
        amp_a = max(pattern_a) - min(pattern_a)
    else:
        amp_a = 0.0
    
    if pattern_b and len(pattern_b) > 0:
        amp_b = max(pattern_b) - min(pattern_b)
    else:
        amp_b = 0.0

    # Разница амплитуд в процентах (с защитой от NaN)
    delta_amp = _safe_pct_change(amp_a, amp_b) if amp_a > 0 else 0.0

    # Корреляция паттернов (если периоды совпадают)
    pattern_corr = None
    if period_a == period_b and len(pattern_a) == len(pattern_b) and len(pattern_a) > 2:
        try:
            corr_matrix = np.corrcoef(pattern_a, pattern_b)
            corr_val = corr_matrix[0, 1]
            if corr_val is not None and corr_val == corr_val and abs(corr_val) <= 1.0:
                pattern_corr = float(corr_val)
            else:
                pattern_corr = None
        except Exception as e:
            log.debug("pattern correlation failed", error=str(e))
            pattern_corr = None

    return {
        "a": {
            "period": period_a,
            "pattern": pattern_a,
            "amplitude": float(amp_a)
        },
        "b": {
            "period": period_b,
            "pattern": pattern_b,
            "amplitude": float(amp_b)
        },
        "comparison": {
            "period_match": period_a == period_b,
            "delta_amplitude_pct": float(delta_amp),
            "pattern_correlation": pattern_corr
        }
    }


def generate_verdict(
    comparison_result: dict,
    pattern_result: Optional[dict] = None,
    mode: str = "before_after"
) -> dict:
    """
    Генерирует автоматический вердикт на основе результатов анализа.

    Args:
        comparison_result: результат compare_snapshots
        pattern_result: результат compare_patterns (опционально)
        mode: "before_after" или "equipment_comparison"

    Returns:
        {
            "summary": str,
            "key_findings": list[str],
            "recommendations": list[str],
            "severity": str  # "low" | "medium" | "high"
        }
    """
    stats = comparison_result.get('statistics', {})
    sig = comparison_result.get('significance', {})
    
    delta = stats.get('delta', {}) if isinstance(stats, dict) else {}
    delta_mean = _safe_float(delta.get('mean'), 0.0)
    delta_std = _safe_float(delta.get('std'), 0.0)
    
    findings = []
    recommendations = []
    severity = "low"

    # 1. Анализ разницы средних
    if abs(delta_mean) > 20:
        direction = "увеличилось" if delta_mean > 0 else "уменьшилось"
        findings.append(f"Среднее значение {direction} на {abs(delta_mean):.1f}%")
        severity = "high" if abs(delta_mean) > 50 else "medium"
    elif abs(delta_mean) > 5:
        direction = "увеличилось" if delta_mean > 0 else "уменьшилось"
        findings.append(f"Среднее значение {direction} на {abs(delta_mean):.1f}%")

    # 2. Анализ изменчивости
    if abs(delta_std) > 50:
        direction = "увеличилась" if delta_std > 0 else "уменьшилась"
        findings.append(f"Изменчивость (std) {direction} на {abs(delta_std):.1f}%")
        severity = "high" if abs(delta_std) > 100 else max(severity, "medium")

    # 3. Статистическая значимость
    sig_interp = sig.get('interpretation', '') if isinstance(sig, dict) else ''
    if sig_interp == "highly_significant":
        findings.append("Различие статистически высоко значимо (p < 0.001)")
    elif sig_interp == "significant":
        findings.append("Различие статистически значимо (p < 0.05)")
    else:
        findings.append("Различие статистически не значимо")

    # 4. Анализ сезонных паттернов
    if pattern_result:
        comp = pattern_result['comparison']
        
        if not comp['period_match']:
            findings.append(f"Доминирующие периоды различаются: {pattern_result['a']['period']} vs {pattern_result['b']['period']}")
            severity = "medium"
        
        delta_amp = comp['delta_amplitude_pct']
        if abs(delta_amp) > 30:
            direction = "увеличилась" if delta_amp > 0 else "уменьшилась"
            findings.append(f"Сезонная амплитуда {direction} на {abs(delta_amp):.1f}%")
            severity = max(severity, "medium")

    # 5. Рекомендации
    if mode == "before_after":
        if severity == "high":
            recommendations.append("⚠️ Обнаружены значительные изменения. Требуется детальный анализ причин.")
            recommendations.append("Проверить условия эксплуатации и внешние факторы.")
        elif severity == "medium":
            recommendations.append("Заметные изменения. Рекомендуется мониторинг.")
        else:
            recommendations.append("Существенных изменений не обнаружено.")
    else:  # equipment_comparison
        if severity == "high":
            recommendations.append("⚠️ Оборудование работает по-разному. Проверить настройки и состояние.")
        elif severity == "medium":
            recommendations.append("Есть различия в работе. Стоит обратить внимание.")
        else:
            recommendations.append("Оборудование работает схожим образом.")

    # Формируем summary
    if severity == "high":
        summary = "Обнаружены критические различия"
    elif severity == "medium":
        summary = "Обнаружены заметные различия"
    else:
        summary = "Существенных различий не обнаружено"

    return {
        "summary": summary,
        "key_findings": findings,
        "recommendations": recommendations,
        "severity": severity
    }
