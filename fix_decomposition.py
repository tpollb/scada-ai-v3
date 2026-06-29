#!/usr/bin/env python3
"""
fix_decomposition.py — улучшаем алгоритм декомпозиции
"""
from pathlib import Path

print('=' * 80)
print('ФИКС: Улучшаем decompose_seasonal')
print('=' * 80)
print()

seasonal_path = Path('backend/modules/deep_analysis/analyzers/seasonal.py')
content = seasonal_path.read_text(encoding='utf-8')

# Заменяем функцию decompose_seasonal на улучшенную версию
old_decompose = '''def decompose_seasonal(
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
    }'''

new_decompose = '''def decompose_seasonal(
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
            "variance_explained": {"trend": X%, "seasonal": Y%, "residual": Z%}
        }
    """
    clean_values = _prepare_values(values, interpolate=True)
    if len(clean_values) < 2 * period:
        return {"error": "insufficient_data_for_decomposition"}

    # 1. Оценка тренда через скользящее среднее
    # Используем окно = period (один полный цикл) вместо 2*period+1
    # Это даёт более чувствительный тренд без артефактов на краях
    trend_window = min(period, len(clean_values) // 3)  # не больше 1/3 данных
    
    # Используем pandas rolling для лучшей обработки краёв
    import pandas as pd
    series = pd.Series(clean_values)
    trend_series = series.rolling(window=trend_window, center=True, min_periods=1).mean()
    trend = trend_series.values

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
        residual = clean_values / (safe_trend * (seasonal + 1))
    else:  # additive
        residual = clean_values - trend - seasonal

    # 5. Вычисляем объяснённую дисперсию
    total_var = np.var(clean_values)
    trend_var = np.var(trend)
    seasonal_var = np.var(seasonal)
    residual_var = np.var(residual)
    
    if total_var > 0:
        variance_explained = {
            "trend": round(trend_var / total_var * 100, 1),
            "seasonal": round(seasonal_var / total_var * 100, 1),
            "residual": round(residual_var / total_var * 100, 1),
        }
    else:
        variance_explained = {"trend": 0, "seasonal": 0, "residual": 0}

    return {
        "trend": trend.tolist(),
        "seasonal": seasonal.tolist(),
        "residual": residual.tolist(),
        "original": clean_values.tolist(),
        "variance_explained": variance_explained,
    }'''

if old_decompose in content:
    content = content.replace(old_decompose, new_decompose)
    seasonal_path.write_text(content, encoding='utf-8', newline='\n')
    print('✅ decompose_seasonal улучшена')
    print()
    print('Что изменилось:')
    print('  1. trend_window = period (вместо 2*period+1)')
    print('  2. Используется pandas rolling вместо np.convolve')
    print('  3. Добавлен variance_explained в результат')
    print('  4. Лучшая обработка краёв (min_periods=1)')
else:
    print('⚠️  Функция не найдена в ожидаемом виде')

print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Backend перезагрузится сам')
print('2. Запусти анализ:')
print()
print('   curl -s -X POST http://localhost:8081/api/v1/deep_analysis/run \\')
print('     -H "Content-Type: application/json" \\')
print('     -d \'{"tags": ["KITCHEN2-CO2"], "period": 7}\' | \\')
print('     python -c "import sys, json; data=json.load(sys.stdin); print(json.dumps(data.get(\'seasonality\', {}), indent=2, default=str))"')
print()
print('3. Теперь trend должен меняться (не быть плоским)')
print('4. variance_explained покажет распределение дисперсии:')
print('   {"trend": 30%, "seasonal": 55%, "residual": 15%}')