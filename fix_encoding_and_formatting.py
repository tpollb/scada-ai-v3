#!/usr/bin/env python3
"""
fix_encoding_and_formatting.py - исправляет UTF-8 и форматирование в prompts.py
"""
from pathlib import Path

prompts_path = Path('backend/modules/deep_analysis/prompts.py')

# Пересохраняем с явной UTF-8 кодировкой
content = prompts_path.read_text(encoding='utf-8', errors='replace')

print('【1】Исправляем форматирование в build_dda_prompt()')
print('-' * 80)

# Находим функцию build_dda_prompt и добавляем helper для безопасного форматирования
old_helper = '''def build_dda_prompt(analysis_result: dict) -> str:'''

new_helper = '''def _safe_format(value, fmt: str = ".2f", default: str = "N/A") -> str:
    """Безопасное форматирование чисел с fallback на 'N/A'"""
    if value is None:
        return default
    try:
        # Пробуем конвертировать в float
        num = float(value)
        return f"{num:{fmt}}"
    except (ValueError, TypeError):
        return str(value) if value else default


def _safe_pct(value, default: str = "N/A") -> str:
    """Безопасное форматирование процентов"""
    if value is None:
        return default
    try:
        num = float(value)
        return f"{num:.1%}" if num <= 1.5 else f"{num:.1f}%"
    except (ValueError, TypeError):
        return str(value) if value else default


def build_dda_prompt(analysis_result: dict) -> str:'''

if old_helper in content:
    content = content.replace(old_helper, new_helper)
    print('✅ Добавлены helper функции _safe_format и _safe_pct')
else:
    print('⚠️  Helper marker не найден')

# Теперь заменяем все прямые форматирования на safe версии
# Паттерн 1: {stats.get('mean', 'N/A'):.2f}
import re

# Все вхождения вида {variable:.2f} или {variable:.2%} внутри f-strings
# заменяем на _safe_format(variable, ".2f")

# Статистика
replacements = [
    # Статистика - mean/median/std/min/max/range
    (r"stats\.get\('mean', 'N/A'\):\.2f", "_safe_format(stats.get('mean'), '.2f')"),
    (r"stats\.get\('median', 'N/A'\):\.2f", "_safe_format(stats.get('median'), '.2f')"),
    (r"stats\.get\('std', 'N/A'\):\.2f", "_safe_format(stats.get('std'), '.2f')"),
    (r"stats\.get\('min', 'N/A'\):\.2f", "_safe_format(stats.get('min'), '.2f')"),
    (r"stats\.get\('max', 'N/A'\):\.2f", "_safe_format(stats.get('max'), '.2f')"),
    (r"stats\.get\('range', 'N/A'\):\.2f", "_safe_format(stats.get('range'), '.2f')"),
    
    # Сезонность - confidence, power, trend/seasonal/residual
    (r"dominant\.get\('confidence', 0\):\.2%", "_safe_pct(dominant.get('confidence'))"),
    (r"dominant\.get\('power', 0\):\.2f", "_safe_format(dominant.get('power'), '.2f')"),
    (r"decomp\.get\('trend', 0\):\.1%", "_safe_pct(decomp.get('trend'))"),
    (r"decomp\.get\('seasonal', 0\):\.1%", "_safe_pct(decomp.get('seasonal'))"),
    (r"decomp\.get\('residual', 0\):\.1%", "_safe_pct(decomp.get('residual'))"),
    
    # Паттерн - min/max/amplitude
    (r"pattern\.get\('min', 'N/A'\):\.2f", "_safe_format(pattern.get('min'), '.2f')"),
    (r"pattern\.get\('max', 'N/A'\):\.2f", "_safe_format(pattern.get('max'), '.2f')"),
    (r"pattern\.get\('amplitude', 'N/A'\):\.2f", "_safe_format(pattern.get('amplitude'), '.2f')"),
    
    # Корреляции
    (r"coef:\+\.\3f", "_safe_format(coef, '+.3f')"),
    
    # A/B анализ - delta
    (r"delta\.get\('mean', 0\):\+\.2%", "_safe_pct(delta.get('mean'))"),
    (r"delta\.get\('std', 0\):\+\.2%", "_safe_pct(delta.get('std'))"),
    (r"delta\.get\('min', 0\):\+\.2%", "_safe_pct(delta.get('min'))"),
    (r"delta\.get\('max', 0\):\+\.2%", "_safe_pct(delta.get('max'))"),
    
    # A/B анализ - significance
    (r"sig\.get\('t_stat', 'N/A'\):\.3f", "_safe_format(sig.get('t_stat'), '.3f')"),
    (r"sig\.get\('p_value', 'N/A'\):\.6f", "_safe_format(sig.get('p_value'), '.6f')"),
    
    # A/B анализ - patterns
    (r"patterns\.get\('delta_amplitude_pct', 0\):\+\.2%", "_safe_pct(patterns.get('delta_amplitude_pct', 0) / 100)"),
    (r"patterns\['pattern_correlation'\]:\.3f", "_safe_format(patterns['pattern_correlation'], '.3f')"),
]

fixed_count = 0
for pattern, replacement in replacements:
    # Простая замена (без regex для надёжности)
    old_pattern = '{' + pattern + '}'
    if old_pattern in content:
        content = content.replace(old_pattern, '{' + replacement + '}')
        fixed_count += 1

print(f'✅ Исправлено {fixed_count} форматирований')

# Сохраняем с явной UTF-8
prompts_path.write_text(content, encoding='utf-8', newline='\n')
print()
print('✅ Файл сохранён с UTF-8 кодировкой')

# Проверяем синтаксис
import ast
try:
    ast.parse(content)
    print('✅ Файл синтаксически корректен')
except SyntaxError as e:
    print(f'❌ Синтаксическая ошибка: {e}')