#!/usr/bin/env python3
"""
remove_duplicate_function.py — удаляем дублирующуюся функцию
"""
from pathlib import Path
import re

print('=' * 80)
print('УДАЛЕНИЕ: Дублирующаяся функция create_multitag_time_series_spec')
print('=' * 80)
print()

cs_path = Path('backend/modules/deep_analysis/visualizers/chart_specs.py')
content = cs_path.read_text(encoding='utf-8')

# Ищем все вхождения def create_multitag_time_series_spec
pattern = r'^def create_multitag_time_series_spec\('
matches = list(re.finditer(pattern, content, re.MULTILINE))

print(f'Найдено {len(matches)} вхождений функции')
print()

if len(matches) == 1:
    print('✅ Только одна функция — всё ок')
    exit(0)
elif len(matches) == 2:
    print('⚠️  ДВЕ функции с одинаковым именем!')
    print()
    
    # Показываем где они
    for i, match in enumerate(matches, 1):
        line_num = content[:match.start()].count('\n') + 1
        # Берём первые 3 строки функции
        func_start = content[match.start():match.start()+300]
        print(f'Функция {i} (строка {line_num}):')
        print('  ' + func_start.split('\n')[0])
        print('  ' + func_start.split('\n')[1] if len(func_start.split('\n')) > 1 else '')
        print()
    
    # Удаляем ВТОРУЮ функцию (она начинается позже)
    second_match = matches[1]
    
    # Находим где заканчивается вторая функция (начало следующей функции или конец файла)
    next_func_pattern = r'^def create_\w+\('
    next_matches = list(re.finditer(next_func_pattern, content[second_match.end():], re.MULTILINE))
    
    if next_matches:
        # Есть следующая функция — удаляем от second_match до неё
        second_end = second_match.end() + next_matches[0].start()
    else:
        # Это последняя функция — удаляем до конца файла
        second_end = len(content)
    
    # Удаляем вторую функцию
    content = content[:second_match.start()] + content[second_end:]
    
    cs_path.write_text(content, encoding='utf-8', newline='\n')
    
    print('✅ Вторая функция удалена')
    print()
    print('Теперь осталась только первая (правильная) функция:')
    print('  "Multi-tag: просто вызываем create_time_series_spec для каждого тега"')
    print()
    
    # Проверяем что осталась одна функция
    remaining = len(list(re.finditer(pattern, content, re.MULTILINE)))
    print(f'Осталось функций: {remaining}')
    
else:
    print(f'❌ Найдено {len(matches)} функций — что-то не так')
    exit(1)

print()
print('=' * 80)
print('ЧТО ПРОИЗОШЛО:')
print('=' * 80)
print()
print('В файле было ДВЕ функции с одинаковым именем.')
print('Python использовал ВТОРУЮ (которая переопределяет первую).')
print()
print('Вторая функция использовала min-max downsampling,')
print('который давал РАЗНЫЕ timestamps для разных тегов → рассинхрон.')
print()
print('Теперь осталась только ПЕРВАЯ функция,')
print('которая просто вызывает create_time_series_spec N раз.')
print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Backend перезагрузится сам')
print('2. Запусти анализ с 2+ тегами')
print('3. График должен быть на ВЕСЬ экран (как single-tag)')
print('4. Все теги должны иметь одинаковый масштаб')
print('5. Аналитические точки должны быть на своих местах')