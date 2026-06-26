#!/usr/bin/env python3
"""
fix_chart_modal_buttons.py — чиним кнопки в ChartModal
"""
from pathlib import Path

print('=' * 80)
print('ФИКС: Кнопки zoom/download в ChartModal')
print('=' * 80)
print()

modal_path = Path('frontend/src/components/ChartModal.svelte')
content = modal_path.read_text(encoding='utf-8')

# 1. Заменяем переменную chartInstance на chart
print('【1】Переименовываем chartInstance → chart')
print('-' * 80)

old_var = 'let chartInstance = $state<any>(null)'
new_var = 'let chart = $state<any>(null)'

if old_var in content:
    content = content.replace(old_var, new_var)
    # Заменяем все использования chartInstance на chart
    content = content.replace('chartInstance', 'chart')
    print('✅ chartInstance → chart')
else:
    print('ℹ️  Переменная уже переименована или не найдена')

print()

# 2. Заменяем bind:chartInstance на bind:chart в разметке
print('【2】Заменяем bind:chartInstance на bind:chart')
print('-' * 80)

if 'bind:chartInstance' in content:
    content = content.replace('bind:chartInstance', 'bind:chart')
    print('✅ bind:chartInstance → bind:chart')
else:
    print('ℹ️  bind:chart уже используется')

print()

# 3. Проверяем функции zoom/download
print('【3】Проверяем функции zoom/download')
print('-' * 80)

functions_to_check = [
    ('zoomIn', 'chart?.zoom(1.2)'),
    ('zoomOut', 'chart?.zoom(0.8)'),
    ('resetZoom', 'chart?.resetZoom()'),
    ('downloadPNG', 'chart?.toBase64Image()'),
]

for func_name, expected_usage in functions_to_check:
    if f'function {func_name}' in content:
        print(f'  ✅ Функция {func_name} найдена')
    else:
        print(f'  ⚠️  Функция {func_name} не найдена')

# Сохраняем
modal_path.write_text(content, encoding='utf-8', newline='\n')

print()
print('=' * 80)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 80)
print()
print('В svelte-chartjs v4 для Svelte 5 правильный bind это:')
print('  <Line bind:chart={chart} ... />')
print()
print('А не:')
print('  <Line bind:chartInstance={chartInstance} ... />')
print()
print('Теперь chart будет содержать инстанс Chart.js,')
print('и кнопки zoom/download смогут его использовать.')
print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Vite автоматически перезагрузит страницу')
print('2. Открой модалку (кнопка ⛶ на графике)')
print('3. Проверь кнопки:')
print('   • 🔍+ (Zoom In) — должен приближать график')
print('   • 🔍- (Zoom Out) — должен отдалять график')
print('   • ↻ (Reset Zoom) — должен сбросить zoom')
print('   • ⬇ (Download PNG) — должен скачать PNG')