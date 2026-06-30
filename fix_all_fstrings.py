#!/usr/bin/env python3
"""
fix_all_fstrings.py - исправляет ВСЕ сломанные f-strings в api.py
"""
from pathlib import Path
import re

api_path = Path('backend/modules/deep_analysis/api.py')
content = api_path.read_text(encoding='utf-8')

print('Ищем ВСЕ сломанные f-strings с json.dumps...')
print()

# Паттерн для поиска: yield f"data: {json.dumps({...})}
# с возможным переносом строки и незакрытыми кавычками

# Находим все проблемные блоки
lines = content.split('\n')
new_lines = []
i = 0

fixed_count = 0

while i < len(lines):
    line = lines[i]
    
    # Проверяем паттерн: yield f"data: {json.dumps(
    if 'yield f"data: {json.dumps(' in line and not line.rstrip().endswith(')\\n\\n"'):
        print(f'Найдена проблема на строке {i+1}: {line[:80]}...')
        
        # Извлекаем JSON content из строки
        # Паттерн: yield f"data: {json.dumps({'key': 'value'})}
        match = re.search(r"json\.dumps\((\{[^}]+\})\)", line)
        
        if match:
            json_content = match.group(1)
            print(f'  JSON content: {json_content}')
            
            # Заменяем одинарные кавычки на двойные в JSON
            json_content_fixed = json_content.replace("'", '"')
            
            # Создаём временную переменную
            var_name = 'temp_data'
            if 'error' in json_content:
                var_name = 'error_data'
            elif 'chunk' in json_content:
                var_name = 'chunk_data'
            elif 'done' in json_content:
                var_name = 'done_data'
            
            # Получаем отступ текущей строки
            indent = len(line) - len(line.lstrip())
            indent_str = ' ' * indent
            
            # Заменяем на две строки
            new_lines.append(f'{indent_str}{var_name} = json.dumps({json_content_fixed})')
            new_lines.append(f'{indent_str}yield f"data: {{{var_name}}}\\n\\n"')
            
            fixed_count += 1
            print(f'  ✅ Исправлено')
            
            # Пропускаем следующие строки если они пустые или содержат только закрывающую кавычку
            i += 1
            while i < len(lines) and (lines[i].strip() == '' or lines[i].strip() == '"'):
                i += 1
            continue
    
    new_lines.append(line)
    i += 1

# Сохраняем
new_content = '\n'.join(new_lines)
api_path.write_text(new_content, encoding='utf-8')

print()
print(f'✅ Исправлено {fixed_count} f-strings')
print()

# Проверяем синтаксис
import ast
try:
    ast.parse(new_content)
    print('✅ Файл синтаксически корректен!')
except SyntaxError as e:
    print(f'❌ Синтаксическая ошибка: {e}')
    print(f'   Строка {e.lineno}: {e.text}')