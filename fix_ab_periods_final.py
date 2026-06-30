#!/usr/bin/env python3
"""
fix_ab_periods_final.py - исправляет структуру возврата detect_dominant_periods
"""
from pathlib import Path

ab_path = Path('backend/modules/deep_analysis/analyzers/ab.py')
content = ab_path.read_text(encoding='utf-8')

# Находим проблемный блок
old_block = '''    # Автодетект периодов если не указаны
    if period_a is None:
        periods_a = detect_dominant_periods(values_a)
        # Безопасно извлекаем доминирующий период
        detected = periods_a.get('periods', []) if isinstance(periods_a, dict) else []
        if detected and len(detected) > 0:
            period_a = detected[0].get('period', 288)
        else:
            period_a = 288  # fallback: 24h at 5min resolution

    if period_b is None:
        periods_b = detect_dominant_periods(values_b)
        detected = periods_b.get('periods', []) if isinstance(periods_b, dict) else []
        if detected and len(detected) > 0:
            period_b = detected[0].get('period', 288)
        else:
            period_b = 288  # fallback: 24h at 5min resolution'''

new_block = '''    # Автодетект периодов если не указаны
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
            period_b = 288  # fallback: 24h at 5min resolution'''

if old_block in content:
    content = content.replace(old_block, new_block)
    ab_path.write_text(content, encoding='utf-8')
    print('✅ compare_patterns исправлен для структуры detected_periods')
else:
    print('⚠️  Блок не найден в ожидаемом виде')