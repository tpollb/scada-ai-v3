#!/usr/bin/env python3
"""
fix_dangling_else.py — удаляем висячий блок else
"""
from pathlib import Path

print('=' * 80)
print('ФИКС: Удаление висячего блока else')
print('=' * 80)
print()

cs_path = Path('backend/modules/deep_analysis/visualizers/chart_specs.py')
lines = cs_path.read_text(encoding='utf-8').split('\n')

# Находим строку с одиноким else: (после корректного datasets.append)
problem_start = None
for i, line in enumerate(lines):
    if line.strip() == 'else:' and i > 0:
        # Проверяем что перед этим был datasets.append({...})
        prev_lines = '\n'.join(lines[max(0, i-15):i])
        if 'datasets.append(' in prev_lines and '"type": "scatter"' in prev_lines:
            problem_start = i
            break

if problem_start is None:
    print('ℹ️  Висячий else не найден')
    exit(0)

print(f'Найден висячий else на строке {problem_start + 1}')
print()

# Находим конец этого else блока (следующая строка с тем же отступом что у else, или меньше)
else_indent = len(lines[problem_start]) - len(lines[problem_start].lstrip())
problem_end = problem_start + 1

for i in range(problem_start + 1, len(lines)):
    line = lines[i]
    if not line.strip():  # пустая строка — пропускаем
        continue
    line_indent = len(line) - len(line.lstrip())
    if line_indent <= else_indent:
        problem_end = i
        break
else:
    problem_end = len(lines)

print(f'Удаляю строки {problem_start + 1} - {problem_end}:')
print('-' * 80)
for i in range(problem_start, min(problem_end, problem_start + 15)):
    print(f'  {i+1:3d}: {lines[i]}')
if problem_end - problem_start > 15:
    print(f'  ... ({problem_end - problem_start - 15} строк ещё)')
print('-' * 80)
print()

# Удаляем
del lines[problem_start:problem_end]

# Сохраняем
cs_path.write_text('\n'.join(lines), encoding='utf-8', newline='\n')

print('✅ Висячий else блок удалён')
print()

# Проверяем синтаксис
print('【Проверка синтаксиса】')
print('-' * 80)
try:
    compile('\n'.join(lines), str(cs_path), 'exec')
    print('✅ Синтаксис корректен!')
except SyntaxError as e:
    print(f'❌ Синтаксическая ошибка: {e}')
    print(f'   Строка {e.lineno}: {e.text}')

print()
print('=' * 80)
print('Перезапусти backend:')
print('  uvicorn main:app --host 0.0.0.0 --port 8081 --reload')
print('=' * 80)