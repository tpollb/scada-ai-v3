#!/usr/bin/env python3
"""
create_seasonal_analyzer.py — создаём модуль сезонного анализа
"""
from pathlib import Path

print('=' * 80)
print('СОЗДАНИЕ: seasonal.py — циклический анализ')
print('=' * 80)
print()

seasonal_path = Path('backend/modules/deep_analysis/analyzers/seasonal.py')

seasonal_code = '''"""Циклический (сезонный) анализ временных рядов

Модуль для автоматического выявления периодических паттернов:
- FFT (Fast Fourier Transform) — поиск доминирующих частот
- Автокорреляция — подтверждение периодичности
- STL декомпозиция — разделение на trend + seasonal + residual
"""
from typing import Optional, Union
import numpy as np
from scipy import signal, stats
from scipy.fft import fft, fftfreq
from structlog import get_logger

log = get_logger()


def detect_dominant_periods(
    values: list[float],
    timestamps: Optional[list] = None,
    min_period: int = 4,
    max_period: Optional[int] = None,
    significance_threshold: float = 0.05,
) -> dict:
    """
    Автоматическое выявление доминирующих периодов через FFT + автокорреляцию.

    Args:
        values: значения временного ряда
        timestamps: соответствующие timestamps (для расчёта частоты дискретизации)
        min_period: минимальный период для поиска (в точках)
        max_period: максимальный период (по умолчанию len(values) // 4)
        significance_threshold: порог значимости для автокорреляции

    Returns:
        {
            "detected_periods": [
                {"period": 24, "frequency": 0.0417, "power": 0.85, "confidence": 0.92},
                ...
            ],
            "fft_peaks": [...],  # сырые пики FFT
            "autocorr_peaks": [...],  # пики автокорреляции
            "sampling_rate": 12.0,  # точек в час (для 5-мин интервала)
        }
    """
    if len(values) < 2 * min_period:
        log.warning("Недостаточно данных для анализа периодов", 
                   n_points=len(values), min_required=2 * min_period)
        return {"detected_periods": [], "error": "insufficient_data"}

    # Подготовка данных: убираем None, интерполируем если нужно
    clean_values = _prepare_values(values)
    if len(clean_values) < 2 * min_period:
        return {"detected_periods": [], "error": "insufficient_valid_data"}

    # Удаляем тренд (detrend) чтобы FFT не ловил низкочастотный дрейф
    detrended = signal.detrend(clean_values, type='linear')

    # Расчёт частоты дискретизации (если есть timestamps)
    sampling_rate = _estimate_sampling_rate(timestamps) if timestamps else 1.0

    # 1. FFT для поиска доминирующих частот
    fft_result = _compute_fft(detrended, sampling_rate)

    # 2. Автокорреляция для подтверждения периодичности
    autocorr_result = _compute_autocorrelation(detrended, max_period or len(detrended) // 4)

    # 3. Объединяем результаты: периоды которые есть и в FFT, и в автокорреляции
    detected = _merge_period_candidates(
        fft_result['peaks'],
        autocorr_result['peaks'],
        significance_threshold
    )

    log.info("Detected periodic patterns", 
            n_periods=len(detected),
            periods=[p['period'] for p in detected])

    return {
        "detected_periods": detected,
        "fft_peaks": fft_result['peaks'],
        "autocorr_peaks": autocorr_result['peaks'],
        "sampling_rate": sampling_rate,
        "n_points": len(clean_values),
    }


def _prepare_values(values: list[float], interpolate: bool = True) -> np.ndarray:
    """Подготовка данных: фильтрация None и опциональная интерполяция."""
    # Фильтруем None
    valid = [(i, v) for i, v in enumerate(values) if v is not None]
    if not valid:
        return np.array([])

    indices, clean = zip(*valid)
    clean = np.array(clean, dtype=float)

    # Если есть пропуски и нужна интерполяция
    if interpolate and len(indices) < len(values):
        # Линейная интерполяция пропущенных точек
        full_indices = np.arange(len(values))
        clean = np.interp(full_indices, indices, clean)

    return clean


def _estimate_sampling_rate(timestamps: list) -> float:
    """Оценивает частоту дискретизации в точках/час."""
    if len(timestamps) < 2:
        return 1.0

    # Берём первые 100 timestamps для оценки
    sample = timestamps[:min(100, len(timestamps))]
    
    # Считаем средние интервалы в секундах
    intervals = []
    for i in range(1, len(sample)):
        try:
            if hasattr(sample[i], 'timestamp') and hasattr(sample[i-1], 'timestamp'):
                diff = (sample[i].timestamp() - sample[i-1].timestamp())
                if diff > 0:
                    intervals.append(diff)
        except Exception:
            continue

    if not intervals:
        return 1.0  # fallback: 1 точка в час

    avg_interval_sec = np.mean(intervals)
    points_per_hour = 3600 / avg_interval_sec

    return round(points_per_hour, 2)


def _compute_fft(values: np.ndarray, sampling_rate: float) -> dict:
    """Вычисляет FFT и находит значимые пики."""
    n = len(values)
    
    # FFT
    yf = fft(values)
    xf = fftfreq(n, 1 / sampling_rate)  # частоты в Гц

    # Мощность спектра (только положительная частота)
    positive_mask = xf > 0
    xf_pos = xf[positive_mask]
    power = np.abs(yf[positive_mask]) ** 2
    power_norm = power / np.max(power) if np.max(power) > 0 else power

    # Находим пики в спектре мощности
    # Порог: пики должны быть > 10% от максимума
    peak_threshold = 0.1
    peak_indices = np.where(power_norm > peak_threshold)[0]

    peaks = []
    for idx in peak_indices:
        if idx == 0 or idx >= len(xf_pos) - 1:
            continue
        
        # Проверяем что это локальный максимум
        if power_norm[idx] > power_norm[idx-1] and power_norm[idx] > power_norm[idx+1]:
            frequency = xf_pos[idx]
            period = 1 / frequency if frequency > 0 else float('inf')
            
            peaks.append({
                "frequency": float(frequency),
                "period": float(period),
                "power": float(power_norm[idx]),
            })

    # Сортируем по мощности (убывание)
    peaks.sort(key=lambda x: x['power'], reverse=True)

    return {
        "frequencies": xf_pos.tolist(),
        "power": power_norm.tolist(),
        "peaks": peaks[:10],  # топ-10 пиков
    }


def _compute_autocorrelation(values: np.ndarray, max_lag: int) -> dict:
    """Вычисляет автокорреляцию и находит значимые лаги."""
    n = len(values)
    
    # Нормализуем данные
    values_norm = (values - np.mean(values)) / (np.std(values) + 1e-10)
    
    # Автокорреляция через correlate
    autocorr = signal.correlate(values_norm, values_norm, mode='full')
    autocorr = autocorr[n-1:]  # берём только положительную часть
    autocorr = autocorr / autocorr[0]  # нормализуем к 1.0 при лаге 0

    # Ищем пики автокорреляции (исключая лаг 0)
    peaks = []
    for lag in range(1, min(max_lag, len(autocorr) - 1)):
        # Проверяем локальный максимум
        if autocorr[lag] > autocorr[lag-1] and autocorr[lag] > autocorr[lag+1]:
            # Проверяем значимость (p-value через Bartlett формулу)
            # Приблизительная оценка: autocorr > 2/sqrt(n) значим на 5% уровне
            significance = 2 / np.sqrt(n)
            if autocorr[lag] > significance:
                peaks.append({
                    "lag": int(lag),
                    "correlation": float(autocorr[lag]),
                    "significant": autocorr[lag] > 2 * significance,
                })

    # Сортируем по корреляции (убывание)
    peaks.sort(key=lambda x: x['correlation'], reverse=True)

    return {
        "autocorr": autocorr[:max_lag].tolist(),
        "peaks": peaks[:10],  # топ-10 пиков
    }


def _merge_period_candidates(
    fft_peaks: list,
    autocorr_peaks: list,
    significance_threshold: float,
) -> list:
    """Объединяет кандидаты периодов из FFT и автокорреляции."""
    candidates = {}

    # Добавляем периоды из FFT
    for peak in fft_peaks:
        period = round(peak['period'])
        if period < 2:
            continue
        candidates[period] = {
            "period": period,
            "frequency": peak['frequency'],
            "fft_power": peak['power'],
            "autocorr": None,
            "confidence": 0.0,
        }

    # Добавляем/обновляем из автокорреляции
    for peak in autocorr_peaks:
        period = peak['lag']
        if period < 2:
            continue
        
        if period in candidates:
            # Уже есть из FFT — обновляем confidence
            candidates[period]['autocorr'] = peak['correlation']
            # Confidence = комбинация FFT power и autocorr
            candidates[period]['confidence'] = (
                0.5 * candidates[period]['fft_power'] + 
                0.5 * peak['correlation']
            )
        else:
            # Новый кандидат только из автокорреляции
            candidates[period] = {
                "period": period,
                "frequency": 1 / period if period > 0 else 0,
                "fft_power": 0.0,
                "autocorr": peak['correlation'],
                "confidence": 0.5 * peak['correlation'],  # только autocorr
            }

    # Фильтруем по confidence и significance
    result = []
    for period, data in candidates.items():
        if data['confidence'] >= significance_threshold:
            result.append({
                "period": data['period'],
                "frequency": data['frequency'],
                "power": data['fft_power'],
                "autocorrelation": data['autocorr'],
                "confidence": round(data['confidence'], 3),
            })

    # Сортируем по confidence (убывание)
    result.sort(key=lambda x: x['confidence'], reverse=True)

    return result


def decompose_seasonal(
    values: list[float],
    period: int,
    seasonal_type: str = 'additive',
) -> dict:
    """
    STL-подобная декомпозиция: trend + seasonal + residual.

    Args:
        values: временной ряд
        period: период сезонности (в точках)
        seasonal_type: 'additive' или 'multiplicative'

    Returns:
        {
            "trend": [...],
            "seasonal": [...],
            "residual": [...],
        }
    """
    clean_values = _prepare_values(values, interpolate=True)
    if len(clean_values) < 2 * period:
        return {"error": "insufficient_data_for_decomposition"}

    # Простая STL-подобная декомпозиция
    # 1. Оценка тренда через скользящее среднее
    trend_window = 2 * period + 1
    trend = np.convolve(
        clean_values, 
        np.ones(trend_window) / trend_window, 
        mode='same'
    )

    # 2. Detrended = values - trend
    detrended = clean_values - trend

    # 3. Сезонная компонента: усреднение по фазам периода
    seasonal = np.zeros_like(detrended)
    for phase in range(period):
        # Все точки с этой фазой
        phase_values = detrended[phase::period]
        phase_mean = np.mean(phase_values)
        # Заполняем сезонность для этой фазы
        seasonal[phase::period] = phase_mean

    # 4. Остаток
    if seasonal_type == 'multiplicative':
        # Избегаем деления на ноль
        safe_trend = np.where(np.abs(trend) < 1e-10, 1.0, trend)
        residual = clean_values / (safe_trend + seasonal + 1e-10)
    else:  # additive
        residual = clean_values - trend - seasonal

    return {
        "trend": trend.tolist(),
        "seasonal": seasonal.tolist(),
        "residual": residual.tolist(),
        "original": clean_values.tolist(),
    }


def get_seasonal_pattern(
    values: list[float],
    period: int,
) -> dict:
    """
    Возвращает типичный сезонный паттерн для заданного периода.

    Args:
        values: временной ряд
        period: период (в точках)

    Returns:
        {
            "pattern": [mean_value_for_phase_0, mean_for_phase_1, ...],
            "std": [std_for_phase_0, ...],
            "n_samples": [count_for_phase_0, ...],
        }
    """
    clean_values = _prepare_values(values, interpolate=False)
    
    pattern = []
    stds = []
    counts = []

    for phase in range(period):
        phase_values = clean_values[phase::period]
        if len(phase_values) > 0:
            pattern.append(float(np.mean(phase_values)))
            stds.append(float(np.std(phase_values)))
            counts.append(len(phase_values))
        else:
            pattern.append(None)
            stds.append(None)
            counts.append(0)

    return {
        "pattern": pattern,
        "std": stds,
        "n_samples": counts,
        "period": period,
    }
'''

seasonal_path.write_text(seasonal_code, encoding='utf-8', newline='\n')

print('✅ seasonal.py создан')
print()
print('Что внутри:')
print('  • detect_dominant_periods() — автодетект периодов через FFT + autocorr')
print('  • decompose_seasonal() — STL-подобная декомпозиция trend+seasonal+residual')
print('  • get_seasonal_pattern() — типичный паттерн для заданного периода')
print()
print('Следующий шаг: добавить в __init__.py и протестировать')