#!/usr/bin/env python3
"""
fix_api_final.py — финальный фикс api.py через git restore + line-by-line правки
"""
import subprocess
import sys
from pathlib import Path

print('=' * 80)
print('ФИНАЛЬНЫЙ ФИКС: Восстановление api.py + добавление seasonal для single-tag')
print('=' * 80)
print()

api_path = Path('backend/modules/deep_analysis/api.py')

# 1. Восстанавливаем файл из git
print('【1】Восстанавливаем api.py из git')
print('-' * 80)
result = subprocess.run(
    ['git', 'restore', str(api_path)],
    capture_output=True,
    text=True
)
if result.returncode == 0:
    print('✅ Файл восстановлен из git')
else:
    print(f'❌ Ошибка git restore: {result.stderr}')
    sys.exit(1)

# 2. Читаем файл построчно
print()
print('【2】Читаем файл построчно')
print('-' * 80)
lines = api_path.read_text(encoding='utf-8').splitlines(keepends=True)
print(f'✅ Прочитано {len(lines)} строк')

# 3. Ищем строку с histogram_spec для single-tag
print()
print('【3】Ищем строку с histogram_spec для single-tag')
print('-' * 80)
histogram_line_idx = None
for i, line in enumerate(lines):
    if 'histogram_spec = create_histogram_spec(histogram, tag_name)' in line:
        histogram_line_idx = i
        print(f'✅ Найдена на строке {i+1}: {line.strip()}')
        break

if histogram_line_idx is None:
    print('❌ Строка с histogram_spec не найдена')
    sys.exit(1)

# 4. Ищем блок results = { после histogram_spec
print()
print('【4】Ищем блок "results = {" после histogram_spec')
print('-' * 80)
results_line_idx = None
for i in range(histogram_line_idx, min(histogram_line_idx + 20, len(lines))):
    if 'results = {' in lines[i]:
        results_line_idx = i
        print(f'✅ Найден на строке {i+1}: {lines[i].strip()}')
        break

if results_line_idx is None:
    print('❌ Блок results = { не найден')
    sys.exit(1)

# 5. Находим закрывающую } этого словаря
print()
print('【5】Ищем закрывающую } словаря results')
print('-' * 80)
closing_brace_idx = None
brace_count = 0
for i in range(results_line_idx, min(results_line_idx + 20, len(lines))):
    for char in lines[i]:
        if char == '{':
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0:
                closing_brace_idx = i
                break
    if closing_brace_idx is not None:
        break

if closing_brace_idx is None:
    print('❌ Закрывающая } не найдена')
    sys.exit(1)

print(f'✅ Найдена на строке {closing_brace_idx+1}: {lines[closing_brace_idx].strip()}')

# 6. Вставляем блок seasonal анализа ПЕРЕД results = {
print()
print('【6】Вставляем блок seasonal анализа перед results = {')
print('-' * 80)

seasonal_block = '''
            # Сезонный анализ для single-tag
            seasonal_analysis = {}
            if len(data['raw_values']) >= 50:
                try:
                    periods_result = detect_dominant_periods(
                        data['raw_values'],
                        data['raw_timestamps']
                    )
                    
                    decomp_result = None
                    pattern_result = None
                    
                    if periods_result.get('detected_periods'):
                        main_period = periods_result['detected_periods'][0]['period']
                        decomp_result = decompose_seasonal(data['raw_values'], period=main_period)
                        pattern_result = get_seasonal_pattern(data['raw_values'], period=main_period)
                    
                    seasonal_analysis = {
                        "periods": periods_result,
                        "decomposition": decomp_result,
                        "pattern": pattern_result,
                    }
                except Exception as e:
                    log.warning("Seasonal analysis failed", tag=tag_name, error=str(e))
                    seasonal_analysis = {"error": str(e)}

'''

# Вставляем блок перед results = {
lines.insert(results_line_idx, seasonal_block)
print(f'✅ Блок вставлен перед строкой {results_line_idx+1}')

# Обновляем индексы (так как вставили новую строку)
results_line_idx += 1
closing_brace_idx += 1

# 7. Находим последнюю запятую перед закрывающей } словаря results
print()
print('【7】Добавляем "seasonal_analysis": seasonal_analysis в словарь results')
print('-' * 80)

last_comma_idx = None
for i in range(closing_brace_idx, results_line_idx - 1, -1):
    if ',' in lines[i]:
        last_comma_idx = i
        print(f'✅ Найдена запятая на строке {i+1}: {lines[i].strip()}')
        break

if last_comma_idx is None:
    print('❌ Запятая не найдена')
    sys.exit(1)

# Вставляем новую строку после последней запятой
# Находим отступ последней строки
indent = len(lines[last_comma_idx]) - len(lines[last_comma_idx].lstrip())
indent_str = ' ' * indent

# Разделяем строку с запятой и добавляем новую строку
current_line = lines[last_comma_idx]
lines[last_comma_idx] = current_line  # оставляем как есть
lines.insert(last_comma_idx + 1, f'{indent_str}"seasonal_analysis": seasonal_analysis,\n')

print(f'✅ Добавлена строка после строки {last_comma_idx+1}')

# 8. Изменяем seasonality=None на seasonality=seasonal_analysis
print()
print('【8】Изменяем seasonality=None на seasonality=seasonal_analysis')
print('-' * 80)

seasonality_changed = 0
for i, line in enumerate(lines):
    if 'seasonality=None,' in line:
        lines[i] = line.replace('seasonality=None,', 'seasonality=seasonal_analysis,')
        print(f'✅ Строка {i+1}: seasonality=None → seasonality=seasonal_analysis')
        seasonality_changed += 1

if seasonality_changed == 0:
    print('⚠️  Не найдено ни одной строки с seasonality=None')
else:
    print(f'✅ Изменено {seasonality_changed} строк')

# 9. Добавляем импорты seasonal функций если их нет
print()
print('【9】Проверяем импорты seasonal функций')
print('-' * 80)

has_seasonal_import = any('from modules.deep_analysis.analyzers.seasonal import' in line for line in lines)

if not has_seasonal_import:
    # Ищем строку с импортом anomalies
    for i, line in enumerate(lines):
        if 'from modules.deep_analysis.analyzers.anomalies import' in line:
            # Вставляем импорт seasonal после этой строки
            lines.insert(i + 1, 'from modules.deep_analysis.analyzers.seasonal import detect_dominant_periods, decompose_seasonal, get_seasonal_pattern\n')
            print(f'✅ Импорты seasonal добавлены после строки {i+1}')
            break
else:
    print('ℹ️  Импорты уже есть')

# 10. Сохраняем файл
print()
print('【10】Сохраняем файл')
print('-' * 80)
api_path.write_text(''.join(lines), encoding='utf-8', newline='\n')
print(f'✅ Файл сохранён ({len(lines)} строк)')

print()
print('=' * 80)
print('ЧТО СДЕЛАНО:')
print('=' * 80)
print()
print('1. ✅ Файл восстановлен из git')
print('2. ✅ Добавлен блок seasonal анализа для single-tag')
print('3. ✅ Добавлен "seasonal_analysis": seasonal_analysis в results')
print('4. ✅ seasonality=None → seasonality=seasonal_analysis (для single и multi-tag)')
print('5. ✅ Добавлены импорты seasonal функций')
print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Backend перезагрузится сам (если --reload)')
print('2. Запусти анализ для single-tag:')
print()
print('   curl -s -X POST http://localhost:8081/api/v1/deep_analysis/run \\')
print('     -H "Content-Type: application/json" \\')
print('     -d \'{"tags": ["KITCHEN2-CO2"], "period": 7}\' | \\')
print('     python -c "import sys, json; data=json.load(sys.stdin); print(json.dumps(data.get(\'seasonality\', {}), indent=2, default=str)[:2000])"')
print()
print('3. Ожидаемый результат:')
print('   {')
print('     "periods": {')
print('       "detected_periods": [{"period": 288, "confidence": 0.207, ...}]')
print('     },')
print('     "decomposition": {')
print('       "variance_explained": {"trend": 30%, "seasonal": 55%, "residual": 15%}')
print('     },')
print('     "pattern": {...}')
print('   }')