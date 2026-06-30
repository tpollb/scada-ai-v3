#!/usr/bin/env python3
"""
fix_imports.py - добавляет недостающие импорты в api.py
"""
from pathlib import Path

api_path = Path('backend/modules/deep_analysis/api.py')
content = api_path.read_text(encoding='utf-8')

print('Добавляем недостающие импорты...')

# 1. Добавляем Request в импорт fastapi
if 'from fastapi import' in content and 'Request' not in content:
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if line.startswith('from fastapi import'):
            # Добавляем Request
            if line.rstrip().endswith(','):
                lines[i] = line.rstrip() + ' Request'
            else:
                lines[i] = line.rstrip() + ', Request'
            print(f'✅ Добавлен Request в строку {i+1}')
            break
    content = '\n'.join(lines)

# 2. Добавляем datetime если нет
if 'from datetime import datetime' not in content:
    # Ищем место для вставки (после других импортов)
    lines = content.split('\n')
    insert_pos = 0
    for i, line in enumerate(lines):
        if line.startswith('from ') or line.startswith('import '):
            insert_pos = i + 1
    lines.insert(insert_pos, 'from datetime import datetime')
    content = '\n'.join(lines)
    print(f'✅ Добавлен импорт datetime')

# 3. Проверяем fetch_multiple_tags
if 'fetch_multiple_tags' not in content:
    # Ищем строку с импортом из data_fetcher
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'from modules.deep_analysis.collectors' in line or 'data_fetcher' in line:
            if 'fetch_multiple_tags' not in line:
                lines[i] = line.rstrip() + ', fetch_multiple_tags'
                print(f'✅ Добавлен fetch_multiple_tags в строку {i+1}')
            break
    content = '\n'.join(lines)

api_path.write_text(content, encoding='utf-8')
print('✅ Файл сохранён')