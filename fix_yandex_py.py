#!/usr/bin/env python3
"""
fix_yandex_py.py — исправляем синтаксическую ошибку в yandex.py
"""
from pathlib import Path
import ast

print('=' * 80)
print('ФИКС: Синтаксическая ошибка в yandex.py')
print('=' * 80)
print()

yandex_path = Path('backend/core/llm/yandex.py')

if not yandex_path.exists():
    print(f'❌ Файл не найден: {yandex_path}')
    exit(1)

content = yandex_path.read_text(encoding='utf-8')
lines = content.split('\n')

print(f'【1】Прочитано {len(lines)} строк')
print()

# Ищем методы с неправильным отступом (8 пробелов вместо 4)
print('【2】Ищем методы с неправильным отступом')
print('-' * 80)

fixed_lines = []
fixed_count = 0

for i, line in enumerate(lines):
    # Проверяем строки вида "        async def health_check" (8 пробелов)
    # Они должны быть "    async def health_check" (4 пробела)
    if line.startswith('        async def ') and 'self' in line:
        # Это метод класса с неправильным отступом (8 вместо 4)
        fixed_line = '    ' + line.lstrip()
        fixed_lines.append(fixed_line)
        fixed_count += 1
        print(f'   Строка {i+1}: исправлен отступ 8 → 4 для "{line.strip()[:50]}..."')
    # Также исправляем строки с телом метода health_check/close (12 пробелов → 8)
    elif line.startswith('            ') and i > 0 and any(
        'health_check' in lines[j] or 'close' in lines[j] 
        for j in range(max(0, i-5), i) 
        if lines[j].strip().startswith('async def')
    ):
        # Проверяем: если предыдущий метод был health_check или close, то это их тело
        # Тело должно иметь отступ 8 (2 уровня), а не 12 (3 уровня)
        # Находим ближайший метод выше
        for j in range(i-1, max(-1, i-10), -1):
            if j >= 0 and lines[j].strip().startswith('async def'):
                if 'health_check' in lines[j] or 'close' in lines[j]:
                    # Это тело метода health_check/close — нужен отступ 8
                    if line.startswith('            ') and not line.startswith('                '):
                        fixed_line = line[4:]  # Убираем 4 пробела
                        fixed_lines.append(fixed_line)
                        fixed_count += 1
                    else:
                        fixed_lines.append(line)
                else:
                    fixed_lines.append(line)
                break
        else:
            fixed_lines.append(line)
    else:
        fixed_lines.append(line)

print(f'\n✅ Исправлено {fixed_count} строк')

# Сохраняем
new_content = '\n'.join(fixed_lines)
yandex_path.write_text(new_content, encoding='utf-8', newline='\n')
print('✅ Файл сохранён')

print()
print('【3】Проверяем синтаксис')
print('-' * 80)

try:
    ast.parse(new_content)
    print('✅ yandex.py синтаксически корректен')
except SyntaxError as e:
    print(f'❌ Синтаксическая ошибка: {e}')
    print(f'   Строка {e.lineno}: {e.text}')
    # Показываем контекст
    error_lines = new_content.split('\n')
    start = max(0, e.lineno - 3)
    end = min(len(error_lines), e.lineno + 3)
    print(f'\n   Контекст (строки {start+1}-{end}):')
    for i in range(start, end):
        marker = '>>>' if i + 1 == e.lineno else '   '
        print(f'   {marker} {i+1}: {error_lines[i]}')

print()
print('=' * 80)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 80)
print()
print('ПРОБЛЕМА:')
print('  Методы health_check и close попали ВНУТРЬ generate_stream')
print('  с отступом 8 пробелов (уровень вложенной функции).')
print('  Это произошло потому что вчера при вставке generate_stream')
print('  не был правильно обработан конец метода.')
print()
print('РЕШЕНИЕ:')
print('  • async def health_check(self) -> bool:  (8 → 4 пробела)')
print('  • async def close(self):                  (8 → 4 пробела)')
print('  • Тело этих методов:                      (12 → 8 пробелов)')
print()
print('=' * 80)
print('СЛЕДУЮЩИЙ ШАГ:')
print('=' * 80)
print()
print('Запусти backend:')
print('  cd backend')
print('  python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8081')
print()
print('Проверь что "LLM provider failed to initialize" больше нет.')
print('После успешного старта — идём к шагу 2 (модуль ab_analysis.py).')