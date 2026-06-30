#!/usr/bin/env python3
"""
fix_pattern_extraction.py - исправляет извлечение pattern из dict
"""
from pathlib import Path

ab_path = Path('backend/modules/deep_analysis/analyzers/ab.py')
content = ab_path.read_text(encoding='utf-8')

# Находим проблемный блок с вычислением паттернов
old_block = '''    # Вычисляем паттерны
    pattern_a = get_seasonal_pattern(values_a, period_a)
    pattern_b = get_seasonal_pattern(values_b, period_b)

    # Амплитуды
    amp_a = max(pattern_a) - min(pattern_a)
    amp_b = max(pattern_b) - min(pattern_b)'''

new_block = '''    # Вычисляем паттерны (возвращает dict: {"pattern": [...], "std": [...], "n_samples": [...]})
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
        amp_b = 0.0'''

if old_block in content:
    content = content.replace(old_block, new_block)
    print('✅ Исправлено извлечение pattern из dict')
else:
    print('⚠️  Блок не найден')

# Также исправляем использование pattern_a и pattern_b дальше (для корреляции)
old_corr = '''    # Корреляция паттернов (если периоды совпадают)
    pattern_corr = None
    if period_a == period_b and len(pattern_a) == len(pattern_b):
        pattern_corr = float(np.corrcoef(pattern_a, pattern_b)[0, 1])'''

new_corr = '''    # Корреляция паттернов (если периоды совпадают)
    pattern_corr = None
    if period_a == period_b and len(pattern_a) == len(pattern_b) and len(pattern_a) > 0:
        pattern_corr = float(np.corrcoef(pattern_a, pattern_b)[0, 1])'''

if old_corr in content:
    content = content.replace(old_corr, new_corr)
    print('✅ Исправлена проверка для корреляции')
else:
    print('⚠️  Блок корреляции не найден')

# И в return statement
old_return = '''    return {
        "a": {
            "period": period_a,
            "pattern": pattern_a,
            "amplitude": amp_a
        },
        "b": {
            "period": period_b,
            "pattern": pattern_b,
            "amplitude": amp_b
        },'''

new_return = '''    return {
        "a": {
            "period": period_a,
            "pattern": pattern_a,
            "amplitude": float(amp_a)
        },
        "b": {
            "period": period_b,
            "pattern": pattern_b,
            "amplitude": float(amp_b)
        },'''

if old_return in content:
    content = content.replace(old_return, new_return)
    print('✅ Исправлен return statement')
else:
    print('⚠️  Return statement не найден')

ab_path.write_text(content, encoding='utf-8')
print('✅ Файл сохранён')