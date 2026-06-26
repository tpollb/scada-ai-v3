#!/usr/bin/env python3
"""
diagnose_multitag_issue.py — диагностика проблемы с multi-tag графиками
"""
from pathlib import Path

print('=' * 80)
print('ДИАГНОСТИКА: Multi-tag графики "едут"')
print('=' * 80)
print()

cs_path = Path('backend/modules/deep_analysis/visualizers/chart_specs.py')
content = cs_path.read_text(encoding='utf-8')

# 1. Проверяем есть ли create_multitag_time_series_spec
print('【1】Поиск create_multitag_time_series_spec')
print('-' * 80)

if 'def create_multitag_time_series_spec' in content:
    print('✅ Функция найдена')
    
    # Извлекаем функцию
    import re
    pattern = r'def create_multitag_time_series_spec\([^)]+\)[^:]*:.*?(?=\n\ndef |\nclass |\Z)'
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        func_code = match.group(0)
        lines = func_code.split('\n')
        
        print(f'   Размер: {len(lines)} строк')
        print()
        
        # Проверяем ключевые элементы
        checks = [
            ('timestamp-based scatter', 'scatter_data.append({"x":'),
            ('index-based scatter', 'type_data = [None]'),
            ('ts_to_index mapping', 'ts_to_index'),
            ('downsample_time_series', 'downsample_time_series'),
            ('anomalies parameter', 'anomalies'),
        ]
        
        print('   Проверка формата данных:')
        for name, pattern in checks:
            if pattern in func_code:
                print(f'     ✅ {name}')
            else:
                print(f'     ❌ {name} НЕ НАЙДЕН')
        
        print()
        print('   Первые 50 строк функции:')
        for i, line in enumerate(lines[:50], 1):
            print(f'   {i:3d}: {line}')
        
        if len(lines) > 50:
            print(f'   ... ({len(lines) - 50} строк ещё)')
else:
    print('❌ Функция НЕ НАЙДЕНА')
    print('   Возможно multi-tag использует ту же функцию что и single-tag')

print()

# 2. Проверяем где вызывается multi-tag функция
print('【2】Где вызывается multi-tag функция')
print('-' * 80)

api_path = Path('backend/modules/deep_analysis/api.py')
api_content = api_path.read_text(encoding='utf-8')

if 'create_multitag_time_series_spec' in api_content:
    lines = api_content.split('\n')
    for i, line in enumerate(lines, 1):
        if 'create_multitag_time_series_spec' in line:
            print(f'   Строка {i}: {line.strip()}')
            # Показываем контекст
            for j in range(max(0, i-3), min(len(lines), i+10)):
                marker = '>>>' if j == i-1 else '   '
                print(f'   {marker} {j+1}: {lines[j]}')
            print()
else:
    print('   ❌ Вызов не найден в api.py')

print()
print('=' * 80)
print('ДИАГНОЗ:')
print('=' * 80)
print()
print('Если в create_multitag_time_series_spec:')
print('  ❌ НЕТ timestamp-based scatter')
print('  ❌ НЕТ ts_to_index mapping')
print('  → Это КОРЕНЬ ПРОБЛЕМЫ!')
print()
print('Multi-tag функция использует старый index-based подход,')
print('а single-tag уже переведён на timestamp-based.')
print()
print('РЕШЕНИЕ: применить тот же timestamp-based маппинг к multi-tag функции')