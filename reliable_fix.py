#!/usr/bin/env python3
"""
reliable_fix.py — надёжный фикс через line-by-line обработку
"""
from pathlib import Path

print('=' * 80)
print('НАДЁЖНЫЙ ФИКС: Line-by-line обработка')
print('=' * 80)
print()

results_path = Path('frontend/src/components/DeepAnalysisResults.svelte')
lines = results_path.read_text(encoding='utf-8').splitlines(keepends=True)

print(f'【1】Прочитано {len(lines)} строк')
print()

# ============================================================================
# 2. НАХОДИМ СТРОКИ ДЛЯ УДАЛЕНИЯ (ПЕРВЫЙ multi-tag seasonal блок)
# ============================================================================
print('【2】Ищем строки для удаления (ПЕРВЫЙ multi-tag seasonal блок)')
print('-' * 80)

first_multitag_start = None
for i, line in enumerate(lines):
    if '<!-- Сезонный анализ (multi-tag) -->' in line and 600 < i < 800:
        first_multitag_start = i
        print(f'   Найдено начало ПЕРВОГО блока: строка {i + 1}')
        break

first_multitag_end = None
for i, line in enumerate(lines):
    if '<!-- 2. Scatter plot' in line and i > first_multitag_start:
        for j in range(i - 1, first_multitag_start, -1):
            if lines[j].strip() == '{/if}':
                first_multitag_end = j
                print(f'   Найдено окончание ПЕРВОГО блока: строка {j + 1}')
                break
        break

if first_multitag_start and first_multitag_end:
    delete_start = first_multitag_start
    if delete_start > 0 and lines[delete_start - 1].strip() == '':
        delete_start -= 1
    
    del lines[delete_start:first_multitag_end + 1]
    print(f'   ✅ Удалено строк: {first_multitag_end + 1 - delete_start}')

# ============================================================================
# 3. ИСПРАВЛЯЕМ SINGLE-TAG SEASONAL БЛОК
# ============================================================================
print()
print('【3】Исправляем single-tag seasonal блок')
print('-' * 80)

for i, line in enumerate(lines):
    if '{#each pattern.slice(0, 48)' in line and i < 700:
        print(f'   Найдена строка {i + 1}')
        indent = len(line) - len(line.lstrip())
        lines[i] = ' ' * indent + '{#each sampled as val, i}\n'
        
        for j in range(i - 10, i):
            if '{@const minVal' in lines[j]:
                lines[j] = ' ' * indent + '{@const sampled = samplePattern(pattern, 200)}\n'
                lines[j + 1] = ' ' * indent + '{@const stats = getPatternStats(pattern)}\n'
                if '{@const maxVal' in lines[j + 2]:
                    lines[j + 2] = ''
                if '{@const range' in lines[j + 3]:
                    lines[j + 3] = ''
                print(f'   ✅ Заменены строки {j + 1}-{j + 4}')
                break
        
        for j in range(i, i + 20):
            if 'Мин: {minVal' in lines[j]:
                lines[j] = lines[j].replace('minVal', 'stats.min').replace('maxVal', 'stats.max').replace('range', 'stats.range')
                print(f'   ✅ Заменена строка {j + 1}')
                break
        
        for j in range(i, i + 20):
            if 'height: {((val - minVal)' in lines[j]:
                lines[j] = lines[j].replace('minVal', 'stats.min').replace('range', 'stats.range')
                if '{#if val !== null}' in lines[j - 1]:
                    lines[j - 1] = lines[j - 1].replace('{#if val !== null}', '{#if val !== null && stats.range > 0}')
                print(f'   ✅ Заменена строка {j + 1}')
                break
        
        break

# ============================================================================
# 4. СОХРАНЯЕМ ФАЙЛ
# ============================================================================
print()
print('【4】Сохраняем файл')
print('-' * 80)
results_path.write_text(''.join(lines), encoding='utf-8', newline='\n')
print(f'✅ Файл сохранён')

print()
print('ПРОВЕРКА: Frontend перезагрузится автоматически')