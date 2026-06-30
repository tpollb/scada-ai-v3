#!/usr/bin/env python3
"""
fix_indentation.py - исправляет отступы в функции ab_analysis
"""
from pathlib import Path

api_path = Path('backend/modules/deep_analysis/api.py')
content = api_path.read_text(encoding='utf-8')

print('Ищем и исправляем отступы в ab_analysis...')

# Находим функцию ab_analysis
ab_start = content.find('async def ab_analysis(request: Request):')
if ab_start == -1:
    print('❌ Функция ab_analysis не найдена')
    exit(1)

# Находим следующую функцию после ab_analysis
next_func = content.find('\n@router.', ab_start + 100)
if next_func == -1:
    next_func = len(content)

# Извлекаем функцию
func_content = content[ab_start:next_func]

# Разбиваем на строки и исправляем отступы
lines = func_content.split('\n')
new_lines = []

inside_try = False
for i, line in enumerate(lines):
    # Определяем начало try блока
    if line.strip() == 'try:':
        inside_try = True
        new_lines.append(line)
        continue
    
    # Если внутри try блока и строка не пустая
    if inside_try and line.strip():
        # Проверяем отступ
        stripped = line.lstrip()
        current_indent = len(line) - len(stripped)
        
        # Если отступ 4 пробела (неправильно), меняем на 8
        if current_indent == 4 and not line.strip().startswith('except'):
            new_lines.append('    ' + line)
        else:
            new_lines.append(line)
    else:
        new_lines.append(line)

# Собираем обратно
new_func_content = '\n'.join(new_lines)

# Заменяем в контенте
content = content[:ab_start] + new_func_content + content[next_func:]

api_path.write_text(content, encoding='utf-8')
print('✅ Отступы исправлены')

# Проверяем синтаксис
import ast
try:
    ast.parse(content)
    print('✅ Файл синтаксически корректен')
except SyntaxError as e:
    print(f'❌ Синтаксическая ошибка: {e}')
    print(f'   Строка {e.lineno}: {e.text}')