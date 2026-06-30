#!/usr/bin/env python3
"""
fix_ab_indentation.py - исправляет отступы в ab_analysis
"""
from pathlib import Path

api_path = Path('backend/modules/deep_analysis/api.py')
content = api_path.read_text(encoding='utf-8')

print('Исправляем отступы в ab_analysis...')
print()

# Проблема 1: pattern_comparison = compare_patterns(values_a, values_b)
old_1 = '''        if len(values_a) >= 288 and len(values_b) >= 288:  # минимум 24 часа данных
        pattern_comparison = compare_patterns(values_a, values_b)'''

new_1 = '''        if len(values_a) >= 288 and len(values_b) >= 288:  # минимум 24 часа данных
            pattern_comparison = compare_patterns(values_a, values_b)'''

if old_1 in content:
    content = content.replace(old_1, new_1)
    print('✅ Исправлен отступ pattern_comparison (if блок)')
else:
    print('⚠️  Проблема 1 не найдена')

# Проблема 2: result["pattern_comparison"] = pattern_comparison
old_2 = '''        if pattern_comparison:
        result["pattern_comparison"] = pattern_comparison'''

new_2 = '''        if pattern_comparison:
            result["pattern_comparison"] = pattern_comparison'''

if old_2 in content:
    content = content.replace(old_2, new_2)
    print('✅ Исправлен отступ result["pattern_comparison"] (if блок)')
else:
    print('⚠️  Проблема 2 не найдена')

# Сохраняем
api_path.write_text(content, encoding='utf-8')

# Проверяем синтаксис
import ast
try:
    ast.parse(content)
    print()
    print('✅ Файл синтаксически корректен!')
except SyntaxError as e:
    print()
    print(f'❌ Синтаксическая ошибка: {e}')
    print(f'   Строка {e.lineno}: {e.text}')