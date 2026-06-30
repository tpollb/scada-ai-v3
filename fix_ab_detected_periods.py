#!/usr/bin/env python3
"""
fix_ab_detected_periods.py - исправляет извлечение периода из detect_dominant_periods
"""
from pathlib import Path

ab_path = Path('backend/modules/deep_analysis/analyzers/ab.py')
content = ab_path.read_text(encoding='utf-8')

# Исправляем первый блок (period_a)
old_block_a = '''    # Автодетект периодов если не указаны
    if period_a is None:
        periods_a = detect_dominant_periods(values_a)
        period_a = periods_a['dominant_period'] if periods_a['dominant_period'] else 288  # fallback: 24h'''

new_block_a = '''    # Автодетект периодов если не указаны
    if period_a is None:
        periods_a = detect_dominant_periods(values_a)
        # Структура возврата: {"detected_periods": [...], "fft_peaks": [...], ...}
        detected = periods_a.get('detected_periods', []) if isinstance(periods_a, dict) else []
        if detected and len(detected) > 0:
            period_a = detected[0].get('period', 288)
        else:
            period_a = 288  # fallback: 24h at 5min resolution'''

if old_block_a in content:
    content = content.replace(old_block_a, new_block_a)
    print('✅ Исправлен period_a')
else:
    print('⚠️  Блок period_a не найден')

# Исправляем второй блок (period_b)
old_block_b = '''    if period_b is None:
        periods_b = detect_dominant_periods(values_b)
        period_b = periods_b['dominant_period'] if periods_b['dominant_period'] else 288'''

new_block_b = '''    if period_b is None:
        periods_b = detect_dominant_periods(values_b)
        detected = periods_b.get('detected_periods', []) if isinstance(periods_b, dict) else []
        if detected and len(detected) > 0:
            period_b = detected[0].get('period', 288)
        else:
            period_b = 288  # fallback: 24h at 5min resolution'''

if old_block_b in content:
    content = content.replace(old_block_b, new_block_b)
    print('✅ Исправлен period_b')
else:
    print('⚠️  Блок period_b не найден')

ab_path.write_text(content, encoding='utf-8')
print('✅ Файл сохранён')