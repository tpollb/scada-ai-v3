#!/usr/bin/env python3
"""
check_multitag_timezone.py — диагностика timezone в multi-tag
"""
from pathlib import Path
import re

print('=' * 80)
print('ДИАГНОСТИКА: Timezone в multi-tag vs single-tag')
print('=' * 80)
print()

cs_path = Path('backend/modules/deep_analysis/visualizers/chart_specs.py')
content = cs_path.read_text(encoding='utf-8')

# 1. Проверяем есть ли apply_timezone в файле
print('【1】Есть ли функция apply_timezone в файле?')
print('-' * 80)

if 'def apply_timezone' in content:
    print('✅ Функция apply_timezone определена')
    
    # Показываем её
    match = re.search(r'def apply_timezone\(.*?\n(?=\ndef |\Z)', content, re.DOTALL)
    if match:
        print()
        print('Код функции:')
        for line in match.group(0).split('\n')[:15]:
            print(f'  {line}')
else:
    print('❌ Функция apply_timezone НЕ определена!')

print()

# 2. Проверяем single-tag — использует ли apply_timezone
print('【2】Single-tag (create_time_series_spec)')
print('-' * 80)

# Ищем функцию
match = re.search(r'def create_time_series_spec\(.*?\n(?=\ndef |\Z)', content, re.DOTALL)
if match:
    func_code = match.group(0)
    
    if 'apply_timezone' in func_code:
        print('✅ Использует apply_timezone')
        # Показываем где
        lines = func_code.split('\n')
        for i, line in enumerate(lines, 1):
            if 'apply_timezone' in line:
                print(f'   Строка {i}: {line.strip()}')
    else:
        print('❌ НЕ использует apply_timezone')

print()

# 3. Проверяем multi-tag — использует ли apply_timezone
print('【3】Multi-tag (create_multitag_time_series_spec)')
print('-' * 80)

match = re.search(r'def create_multitag_time_series_spec\(.*?\n(?=\ndef |\Z)', content, re.DOTALL)
if match:
    func_code = match.group(0)
    
    if 'apply_timezone' in func_code:
        print('✅ Использует apply_timezone')
    else:
        print('❌ НЕ использует apply_timezone')
        print('   Вот корень проблемы!')

print()

# 4. Показываем как форматируются labels в multi-tag
print('【4】Как форматируются labels в multi-tag?')
print('-' * 80)

# Ищем блок форматирования labels
match = re.search(r'# Форматируем labels.*?for ts in ds_timestamps:.*?(?=\n    #|\n    # 1\.)', content, re.DOTALL)
if match:
    print('Код форматирования:')
    for line in match.group(0).split('\n')[:10]:
        print(f'  {line}')
else:
    print('⚠️  Блок форматирования не найден')

print()

# 5. Показываем как форматируются ts_key для маппинга
print('【5】Как форматируются ts_key для маппинга в multi-tag?')
print('-' * 80)

# Ищем блок создания ts_to_index
match = re.search(r'ts_to_index = \{\}.*?for idx, ts in enumerate\(ds_timestamps\):.*?(?=\n        for tag_name)', content, re.DOTALL)
if match:
    print('Код маппинга:')
    for line in match.group(0).split('\n')[:15]:
        print(f'  {line}')

print()
print('=' * 80)
print('ДИАГНОЗ:')
print('=' * 80)
print()
print('Если multi-tag НЕ использует apply_timezone:')
print('  • Timestamps форматируются как "2026-05-28 02:18" (БЕЗ timezone)')
print('  • Chart.js интерпретирует как UTC или в своём часовом поясе')
print('  • Результат: смещение на 11 часов 20 минут')
print()
print('РЕШЕНИЕ:')
print('  Применить apply_timezone() ко всем форматированиям timestamps в multi-tag')