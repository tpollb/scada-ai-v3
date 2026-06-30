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


def compare_snapshots(data_a: list[float], data_b: list[float]) -> dict:
    """
    Сравнивает два набора данных (snapshot A vs snapshot B).

    Args:
        data_a: значения первого периода/тега
        data_b: значения второго периода/тега

    Returns:
        {
            "statistics": {
                "a": {...},  # базовая статистика для A
                "b": {...},  # базовая статистика для B
                "delta": {...}  # разница в процентах
            },
            "significance": {
                "t_stat": float,
                "p_value": float,
                "cohens_d": float,
                "interpretation": str
            }
        }
    """
    # Базовая статистика
    stats_a = compute_basic_stats(data_a)
    stats_b = compute_basic_stats(data_b)

    # Разница в процентах (с защитой от inf/nan)
    delta = {}
    for key in ['mean', 'median', 'std', 'min', 'max', 'range']:
        val_a = stats_a.get(key, 0)
        val_b = stats_b.get(key, 0)
        
        if val_a != 0 and abs(val_a) > 1e-10:
            delta_val = ((val_b - val_a) / abs(val_a)) * 100
            # Защита от inf/nan
            if delta_val != delta_val or abs(delta_val) > 1e6:  # isnan или очень большое
                delta[key] = 9999.0 if delta_val > 0 else -9999.0
            else:
                delta[key] = float(delta_val)
        else:
            delta[key] = 0.0 if val_b == 0 else 9999.0

    # Статистическая значимость (Welch's t-test)
    t_stat, p_value = stats.ttest_ind(data_a, data_b, equal_var=False)

    # Effect size (Cohen's d)
    mean_diff = stats_b['mean'] - stats_a['mean']
    pooled_std = np.sqrt((stats_a['variance'] + stats_b['variance']) / 2)
    cohens_d = mean_diff / pooled_std if pooled_std > 0 else 0

    # Интерпретация
    if p_value < 0.001:
        significance_interp = "highly_significant"
    elif p_value < 0.05:
        significance_interp = "significant"
    else:
        significance_interp = "not_significant"

    # Защита от inf/nan в significance
    def safe_float(v, default=0.0):
        if v is None:
            return default
        v = float(v)
        if v != v or abs(v) > 1e10:  # isnan или слишком большое
            return default
        return v
    
    return {
        "statistics": {
            "a": stats_a,
            "b": stats_b,
            "delta": delta
        },
        "significance": {
            "t_stat": safe_float(t_stat),
            "p_value": safe_float(p_value, 1.0),
            "cohens_d": safe_float(cohens_d),
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

    # Разница амплитуд в процентах
    delta_amp = ((amp_b - amp_a) / amp_a * 100) if amp_a > 0 else 0

    # Корреляция паттернов (если периоды совпадают)
    pattern_corr = None
    if period_a == period_b and len(pattern_a) == len(pattern_b) and len(pattern_a) > 0:
        pattern_corr = float(np.corrcoef(pattern_a, pattern_b)[0, 1])

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
    stats = comparison_result['statistics']
    sig = comparison_result['significance']
    
    delta_mean = stats['delta']['mean']
    delta_std = stats['delta']['std']
    
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
    if sig['interpretation'] == "highly_significant":
        findings.append("Различие статистически высоко значимо (p < 0.001)")
    elif sig['interpretation'] == "significant":
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
