#!/usr/bin/env python3
"""
fix_nameerror.py — исправление NameError: orig_apply_timezone
"""
from pathlib import Path
import re

print('=' * 80)
print('ФИКС: NameError: orig_apply_timezone is not defined')
print('=' * 80)
print()

cs_path = Path('backend/modules/deep_analysis/visualizers/chart_specs.py')
content = cs_path.read_text(encoding='utf-8')

changes = []

# 1. Исправляем битые замены: orig_apply_timezone(ts) → apply_timezone(orig_ts)
print('【1】Исправляем битые замены')
print('-' * 80)

# Находим все битые паттерны
patterns_to_fix = [
    (r'orig_apply_timezone\(([^)]+)\)', r'apply_timezone(orig_\1)'),
    (r'ds_apply_timezone\(([^)]+)\)', r'apply_timezone(ds_\1)'),
    (r'anom_apply_timezone\(([^)]+)\)', r'apply_timezone(anom_\1)'),
]

for pattern, replacement in patterns_to_fix:
    matches = re.findall(pattern, content)
    if matches:
        content = re.sub(pattern, replacement, content)
        changes.append(f'Исправлено {len(matches)} вхождений: {pattern} → {replacement}')
        print(f'  ✅ {changes[-1]}')

# 2. Теперь правильно оборачиваем переменные в apply_timezone
print()
print('【2】Правильно оборачиваем переменные в apply_timezone')
print('-' * 80)

# Используем word boundary (\b) чтобы не заменять внутри других слов
# Но с Python re используем более точный подход — проверяем что перед .strftime стоит просто имя переменной

replacements = [
    # orig_ts.strftime → apply_timezone(orig_ts).strftime
    (r'\borig_ts\.strftime\(', 'apply_timezone(orig_ts).strftime('),
    # ds_ts.strftime → apply_timezone(ds_ts).strftime  
    (r'\bds_ts\.strftime\(', 'apply_timezone(ds_ts).strftime('),
    # ts.strftime (но только если перед ts нет буквы — т.е. не orig_ts, ds_ts)
    # Используем negative lookbehind
    (r'(?<![a-zA-Z_])ts\.strftime\(', 'apply_timezone(ts).strftime('),
]

for pattern, replacement in replacements:
    matches = re.findall(pattern, content)
    if matches:
        content = re.sub(pattern, replacement, content)
        changes.append(f'Обёрнуто {len(matches)} вхождений: {pattern[:30]}...')
        print(f'  ✅ {changes[-1]}')
    else:
        print(f'  ℹ️  Паттерн {pattern[:40]}... не найден')

# 3. Убираем двойные обёртки apply_timezone(apply_timezone(...))
print()
print('【3】Убираем двойные обёртки')
print('-' * 80)

double_wrap_pattern = r'apply_timezone\(apply_timezone\(([^)]+)\)\)'
double_matches = re.findall(double_wrap_pattern, content)
if double_matches:
    content = re.sub(double_wrap_pattern, r'apply_timezone(\1)', content)
    changes.append(f'Убрано {len(double_matches)} двойных обёрток')
    print(f'  ✅ {changes[-1]}')
else:
    print('  ℹ️  Двойных обёрток не найдено')

# Сохраняем
cs_path.write_text(content, encoding='utf-8', newline='\n')

# 4. Проверяем синтаксис
print()
print('【4】Проверка синтаксиса')
print('-' * 80)
try:
    compile(content, str(cs_path), 'exec')
    print('✅ Синтаксис корректен!')
except SyntaxError as e:
    print(f'❌ Синтаксическая ошибка: {e}')
    exit(1)

# 5. Проверяем что apply_timezone определена
print()
print('【5】Проверка наличия apply_timezone')
print('-' * 80)
if 'def apply_timezone' in content:
    print('✅ Функция apply_timezone определена')
else:
    print('❌ Функция apply_timezone НЕ определена!')

print()
print('=' * 80)
print('ИТОГО:')
print('=' * 80)
for c in changes:
    print(f'  • {c}')

print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Перезапусти backend (uvicorn должен автоматически перезагрузить)')
print('2. Запусти анализ KITCHEN2-CO2')
print('3. Ошибка NameError должна исчезнуть')
print('4. Точки аномалий должны быть на правильных датах (без смещения)')