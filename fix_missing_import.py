#!/usr/bin/env python3
"""
fix_missing_import.py — добавляем импорт create_multitag_time_series_spec
"""

from pathlib import Path

print('=' * 70)
print('ФИКС: Добавляем импорт create_multitag_time_series_spec')
print('=' * 70)
print()

api_path = Path('backend/modules/deep_analysis/api.py')
content = api_path.read_text(encoding='utf-8')

# Проверяем есть ли уже импорт
if 'create_multitag_time_series_spec' in content:
    # Импорт есть, но возможно сломанный
    print('ℹ create_multitag_time_series_spec уже упоминается в файле')
    
    # Проверяем строку импорта
    for i, line in enumerate(content.split('\n'), 1):
        if 'from modules.deep_analysis.visualizers.chart_specs import' in line:
            print(f'  Строка {i}: {line.strip()}')
else:
    print('❌ Импорт create_multitag_time_series_spec отсутствует')

# Ищем строку импорта chart_specs и добавляем туда нашу функцию
import_patterns = [
    'from modules.deep_analysis.visualizers.chart_specs import create_time_series_spec, create_histogram_spec, create_heatmap_spec, create_scatter_spec',
    'from modules.deep_analysis.visualizers.chart_specs import create_time_series_spec, create_histogram_spec, create_heatmap_spec, create_scatter_spec, create_multitag_time_series_spec',
]

old_import = import_patterns[0]
new_import = import_patterns[1]

if old_import in content:
    content = content.replace(old_import, new_import)
    api_path.write_text(content, encoding='utf-8', newline='\n')
    print()
    print('✓ Импорт обновлён:')
    print(f'  Было: {old_import}')
    print(f'  Стало: {new_import}')
elif new_import in content:
    print()
    print('✓ Импорт уже правильный')
else:
    print()
    print('⚠ Не удалось найти строку импорта для замены')
    print()
    print('Возможные варианты:')
    for i, line in enumerate(content.split('\n'), 1):
        if 'chart_specs' in line.lower() and 'import' in line:
            print(f'  Строка {i}: {line.strip()}')
    
    # Попробуем альтернативный подход — найти первую строку с импортом chart_specs
    # и заменить её на правильную
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'from modules.deep_analysis.visualizers.chart_specs import' in line:
            print()
            print(f'Найдена строка {i+1}, заменяем на правильный импорт...')
            lines[i] = new_import
            content = '\n'.join(lines)
            api_path.write_text(content, encoding='utf-8', newline='\n')
            print('✓ Импорт обновлён (альтернативный путь)')
            break

# ============================================================================
# Проверка chart_specs.py — есть ли там функция
# ============================================================================
print()
print('=' * 70)
print('ПРОВЕРКА chart_specs.py:')
print('=' * 70)

chart_specs_path = Path('backend/modules/deep_analysis/visualizers/chart_specs.py')
cs_content = chart_specs_path.read_text(encoding='utf-8')

if 'def create_multitag_time_series_spec' in cs_content:
    print('✓ Функция create_multitag_time_series_spec существует в chart_specs.py')
    
    # Показываем сигнатуру
    lines = cs_content.split('\n')
    for i, line in enumerate(lines):
        if 'def create_multitag_time_series_spec' in line:
            print()
            print('Сигнатура функции:')
            # Показываем несколько строк
            for j in range(i, min(i+10, len(lines))):
                print(f'  {lines[j]}')
                if '"""' in lines[j] and j > i:
                    break
            break
else:
    print('❌ Функция create_multitag_time_series_spec НЕ существует!')
    print('   Нужно добавить её в chart_specs.py')

print()
print('=' * 70)
print('ПРОВЕРКА:')
print('=' * 70)
print()
print('Перезапусти backend и проверь:')
print()
print('  curl -X POST http://localhost:8081/api/v1/deep_analysis/run \\')
print('    -H "Content-Type: application/json" \\')
print('    -d \'{"tags": ["KITCHEN2-CO2", "KITCHEN2-Temperature"], "period": 30}\'')
print()
print('Должно вернуться без NameError:')
print('  • visualizations.time_series с графиками обоих тегов')
print('  • visualizations.heatmap с матрицей корреляций')
print('  • visualizations.scatter с scatter plot')
print('  • anomalies.per_tag с деталями по каждому тегу')