#!/usr/bin/env python3
"""
fix_base_py.py — исправляем синтаксическую ошибку в base.py
"""
from pathlib import Path

print('=' * 80)
print('ФИКС: Синтаксическая ошибка в base.py')
print('=' * 80)
print()

base_path = Path('backend/core/llm/base.py')

if not base_path.exists():
    # Проверяем альтернативный путь
    alt_path = Path('core/llm/base.py')
    if alt_path.exists():
        base_path = alt_path
        print(f'ℹ️  Используем альтернативный путь: {base_path}')
    else:
        print(f'❌ Файл не найден: {base_path}')
        exit(1)

content = base_path.read_text(encoding='utf-8')

# Проблема: строка 80 имеет неправильный отступ
# @abstractmethod должно быть на уровне класса (4 пробела), а не метода (8 пробелов)

print('【1】Исправляем отступ @abstractmethod для health_check')
print('-' * 80)

# Ищем проблемный блок
old_block = '''        ...
        yield ""  # type hint для async generator

        @abstractmethod
    async def health_check(self) -> bool:'''

new_block = '''        ...
        yield ""  # type hint для async generator

    @abstractmethod
    async def health_check(self) -> bool:'''

if old_block in content:
    content = content.replace(old_block, new_block)
    print('✅ Исправлен отступ @abstractmethod (8 пробелов → 4 пробела)')
else:
    print('⚠️  Точный блок не найден, пробуем альтернативный вариант...')
    
    # Альтернативный поиск по строкам
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if '@abstractmethod' in line and i > 0 and 'async def health_check' in lines[i+1]:
            # Проверяем отступ
            indent = len(line) - len(line.lstrip())
            if indent == 8:  # Неправильный отступ
                lines[i] = '    @abstractmethod'  # Исправляем на 4 пробела
                print(f'✅ Исправлена строка {i+1}: отступ 8 → 4')
                break
    
    content = '\n'.join(lines)

# Сохраняем
base_path.write_text(content, encoding='utf-8', newline='\n')
print('✅ Файл сохранён')

print()
print('【2】Проверяем синтаксис')
print('-' * 80)

import ast
try:
    ast.parse(content)
    print('✅ base.py синтаксически корректен')
except SyntaxError as e:
    print(f'❌ Синтаксическая ошибка: {e}')
    print(f'   Строка {e.lineno}: {e.text}')

print()
print('=' * 80)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 80)
print()
print('ПРОБЛЕМА:')
print('  В методе generate_stream (строки 64-78) docstring не был закрыт,')
print('  и следующий @abstractmethod попал внутрь метода с отступом 8 пробелов.')
print()
print('РЕШЕНИЕ:')
print('  Исправлен отступ @abstractmethod с 8 пробелов на 4 пробела')
print('  (уровень класса вместо уровня метода)')
print()
print('=' * 80)