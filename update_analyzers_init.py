#!/usr/bin/env python3
"""
update_analyzers_init.py — добавляем seasonal в __init__.py
"""
from pathlib import Path

print('=' * 80)
print('ОБНОВЛЕНИЕ: analyzers/__init__.py')
print('=' * 80)
print()

init_path = Path('backend/modules/deep_analysis/analyzers/__init__.py')
content = init_path.read_text(encoding='utf-8')

print('Текущее содержимое:')
print('-' * 80)
print(content)
print('-' * 80)
print()

# Добавляем импорты seasonal
new_imports = '''from .seasonal import (
    detect_dominant_periods,
    decompose_seasonal,
    get_seasonal_pattern,
)
'''

if 'from .seasonal import' not in content:
    content = content.rstrip() + '\n\n' + new_imports
    init_path.write_text(content, encoding='utf-8', newline='\n')
    print('✅ Добавлены импорты seasonal модуля')
else:
    print('ℹ️  Импорты уже есть')

print()
print('Проверяем что модуль импортируется:')