#!/usr/bin/env python3
"""
fix_scales_type.py — добавляем type: 'category' в опции графика
"""
from pathlib import Path
import re

print('=' * 80)
print('ФИКС: Добавление type: "category" в scales.x')
print('=' * 80)
print()

# 1. Frontend — DeepAnalysisResults.svelte
print('【1】Frontend: добавляем type: "category" в timeSeriesOptions')
print('-' * 80)

dar_path = Path('frontend/src/components/DeepAnalysisResults.svelte')
dar_content = dar_path.read_text(encoding='utf-8')

# Ищем строку 209: x: { display: true, grid: ...
old_line = "x: { display: true, grid: { display: false }, ticks: { maxTicksLimit: 10, font: { size: 10 } } }"
new_line = "x: { type: 'category' as const, display: true, grid: { display: false }, ticks: { maxTicksLimit: 10, font: { size: 10 } } }"

if old_line in dar_content:
    dar_content = dar_content.replace(old_line, new_line)
    dar_path.write_text(dar_content, encoding='utf-8', newline='\n')
    print(f'  ✅ Добавлено type: "category" в timeSeriesOptions')
else:
    print(f'  ℹ️  Строка уже изменена или не найдена')

print()

# 2. Backend — chart_specs.py
print('【2】Backend: проверяем chart_specs.py')
print('-' * 80)

cs_path = Path('backend/modules/deep_analysis/visualizers/chart_specs.py')
cs_content = cs_path.read_text(encoding='utf-8')

# Ищем блок "scales" в create_time_series_spec
if '"x": {' in cs_content and '"type": "category"' in cs_content:
    print('  ✅ В chart_specs.py уже стоит type: "category"')
elif '"x": {' in cs_content:
    print('  ⚠️  Найден блок "x": { но нет type')
    
    # Добавляем type: "category" после "x": {
    pattern = r'("x":\s*\{)'
    replacement = r'\1\n                    "type": "category",'
    
    if '"type": "category"' not in cs_content:
        cs_content = re.sub(pattern, replacement, cs_content, count=1)
        cs_path.write_text(cs_content, encoding='utf-8', newline='\n')
        print('  ✅ Добавлено "type": "category" в chart_specs.py')
else:
    print('  ℹ️  Блок "x": { не найден')

print()

# 3. Проверяем другие опции графиков
print('【3】Проверяем scatterOptions')
print('-' * 80)

if 'const scatterOptions' in dar_content:
    # Ищем блок scales в scatterOptions
    scatter_match = re.search(r'const scatterOptions[^}]+scales:\s*\{[^}]+x:\s*\{([^}]+)\}', dar_content, re.DOTALL)
    if scatter_match:
        x_block = scatter_match.group(1)
        if 'type:' in x_block:
            print('  ✅ scatterOptions уже имеет type для x')
        else:
            print('  ℹ️  scatterOptions не имеет type (это scatter plot, может быть линейный)')
else:
    print('  ℹ️  scatterOptions не найден')

print()
print('=' * 80)
print('ЧТО ЭТО ДАЁТ:')
print('=' * 80)
print()
print('Было:')
print('  scales: { x: { display: true, ... } }')
print('  Chart.js автоопределяет тип → может парсить даты')
print('  Результат: смещение из-за парсинга')
print()
print('Стало:')
print('  scales: { x: { type: "category", display: true, ... } }')
print('  Chart.js использует labels КАК ЕСТЬ (без парсинга)')
print('  Результат: НЕТ смещения')
print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Vite автоматически перезагрузит фронтенд')
print()
print('2. Запусти анализ с периодом 30 дней:')
print('   • Выбери KITCHEN2-CO2')
print('   • Период: 30 дней')
print('   • Запусти анализ')
print()
print('3. Проверь точки аномалий:')
print('   • Просадка 12.06 02:40 должна быть НА 12.06 02:40')
print('   • НЕ должно быть смещения на 02:10 или другое время')
print('   • Все точки точно на своих позициях')
print()
print('4. Проверь tooltip:')
print('   • Наведи на точку аномалии')
print('   • Tooltip должен показать правильную дату/время')
print('   • Значение должно совпадать с линией графика')