#!/usr/bin/env python3
"""
fix_double_comma.py — чистим двойные запятые и пустые импорты в api.py
"""
from pathlib import Path
import re

print('=' * 80)
print('ФИКС: Синтаксические ошибки в api.py')
print('=' * 80)
print()

api_path = Path('backend/modules/deep_analysis/api.py')
content = api_path.read_text(encoding='utf-8')

# Находим все проблемные паттерны
issues_found = []

# 1. Двойные запятые
double_commas = re.findall(r',\s*,', content)
if double_commas:
    content = re.sub(r',\s*,', ',', content)
    issues_found.append(f'Двойные запятые: {len(double_commas)}')

# 2. Запятая перед закрывающей скобкой: ,)
trailing_commas = re.findall(r',\s*\)', content)
if trailing_commas:
    content = re.sub(r',(\s*\))', r'\1', content)
    issues_found.append(f'Висячие запятые перед ): {len(trailing_commas)}')

# 3. Пустые строки в многострочных импортах
empty_imports = re.findall(r'from .* import \(\s*,', content)
if empty_imports:
    content = re.sub(r'(from .* import \()\s*,', r'\1', content)
    issues_found.append(f'Пустые импорты: {len(empty_imports)}')

# 4. Двойные пустые строки подряд (>2)
content = re.sub(r'\n{4,}', '\n\n\n', content)

# 5. Дубликаты импортов в одном блоке (ищем многострочные import и убираем дубли)
def dedupe_import_block(match):
    prefix = match.group(1)
    items_str = match.group(2)
    
    # Парсим элементы
    items = []
    for item in items_str.split(','):
        item = item.strip()
        if item and item not in items:
            items.append(item)
    
    # Формируем заново
    if len(items) <= 3:
        return prefix + ', '.join(items)
    else:
        return prefix + '(\n    ' + ',\n    '.join(items) + ',\n)'

# Ищем многострочные импорты
multiline_pattern = r'(from [^\n]+ import )\(([^)]+)\)'
content = re.sub(multiline_pattern, dedupe_import_block, content, flags=re.DOTALL)

# 6. Конкретно чистим блок импорта из anomalies (часто ломается)
# Находим блок
anomalies_import_pattern = r'from modules\.deep_analysis\.analyzers\.anomalies import \(([^)]+)\)'
match = re.search(anomalies_import_pattern, content, re.DOTALL)

if match:
    imports_str = match.group(1)
    
    # Список всех нужных импортов
    needed = [
        'detect_anomalies_isolation_forest',
        'detect_zero_dips',
        'detect_significant_dips',
        'group_anomaly_events',
        '_is_monotonic',
        '_is_plateau',
        '_compute_linear_trend',
        '_compute_relative_change',
    ]
    
    # Проверяем что есть
    existing = [x.strip() for x in imports_str.split(',') if x.strip()]
    
    # Формируем полный список без дублей
    final = []
    for item in needed:
        if item not in final:
            final.append(item)
    
    # Создаём новый блок
    new_block = 'from modules.deep_analysis.analyzers.anomalies import (\n    ' + ',\n    '.join(final) + ',\n)'
    
    content = content[:match.start()] + new_block + content[match.end():]
    issues_found.append('Импорт из anomalies перестроен')

api_path.write_text(content, encoding='utf-8', newline='\n')

if issues_found:
    print('✅ Найдено и исправлено:')
    for i in issues_found:
        print(f'   • {i}')
else:
    print('ℹ️  Явных проблем не найдено')

# Проверка синтаксиса
print()
print('=' * 80)
print('ПРОВЕРКА СИНТАКСИСА:')
print('=' * 80)
print()

try:
    compile(content, str(api_path), 'exec')
    print('✅ Синтаксис Python корректен!')
except SyntaxError as e:
    print(f'❌ Синтаксическая ошибка: {e}')
    print()
    print('Контекст ошибки:')
    lines = content.split('\n')
    start = max(0, e.lineno - 5)
    end = min(len(lines), e.lineno + 3)
    for i in range(start, end):
        marker = ' >>>' if i == e.lineno - 1 else '    '
        print(f'{marker} {i+1}: {lines[i]}')

print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('Перезапусти backend:')
print('  uvicorn main:app --host 0.0.0.0 --port 8081 --reload')
print()
print('Должно стартовать без SyntaxError.')