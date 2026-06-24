#!/usr/bin/env python3
"""
diagnose_anomaly_types.py — диагностика почему не видна цветовая кодировка
"""

from pathlib import Path
import re

print('=' * 70)
print('ДИАГНОСТИКА ЦВЕТОВОЙ КОДИРОВКИ АНОМАЛИЙ')
print('=' * 70)
print()

# ============================================================================
# 1. Проверяем что возвращает detect_anomalies_isolation_forest
# ============================================================================
print('1. Проверка anomalies.py')
print('-' * 70)
anomalies_path = Path('backend/modules/deep_analysis/analyzers/anomalies.py')
anomalies_content = anomalies_path.read_text(encoding='utf-8')

if 'anomaly_types' in anomalies_content and 'classify_anomaly_types' in anomalies_content:
    print('✓ anomalies.py содержит anomaly_types и classify_anomaly_types')
else:
    print('❌ anomalies.py НЕ содержит новые поля!')

# ============================================================================
# 2. Проверяем Pydantic модель AnalysisResponse
# ============================================================================
print()
print('2. Проверка Pydantic модели AnalysisResponse')
print('-' * 70)
api_path = Path('backend/modules/deep_analysis/api.py')
api_content = api_path.read_text(encoding='utf-8')

# Ищем модель
model_match = re.search(r'class AnalysisResponse\(BaseModel\):.*?(?=\n\nclass|\n\n\n)', api_content, re.DOTALL)
if model_match:
    model_text = model_match.group(0)
    print('Текущая модель:')
    print(model_text[:500])
    print()
    
    # Проверяем тип поля anomalies
    if 'anomalies: Optional[dict]' in model_text or 'anomalies: dict' in model_text:
        print('✓ Поле anomalies объявлено как dict — структура передаётся как есть')
    else:
        print('⚠ Проверь поле anomalies в модели')

# ============================================================================
# 3. Проверяем chart_specs.py — цветовая кодировка
# ============================================================================
print()
print('3. Проверка chart_specs.py')
print('-' * 70)
chart_specs_path = Path('backend/modules/deep_analysis/visualizers/chart_specs.py')
chart_specs_content = chart_specs_path.read_text(encoding='utf-8')

# Ищем функцию create_time_series_spec
ts_match = re.search(r'def create_time_series_spec\([^)]+\)[^:]*:.*?(?=\n\ndef|\Z)', chart_specs_content, re.DOTALL)
if ts_match:
    ts_func = ts_match.group(0)
    
    # Проверяем наличие цветовой кодировки
    if 'anomalies_by_type' in ts_func and 'type_colors' in ts_func:
        print('✓ chart_specs.py содержит цветовую кодировку по типам')
        print()
        print('Фрагмент с цветовой логикой:')
        # Находим блок с type_colors
        colors_match = re.search(r'type_colors = \{[^}]+\}', ts_func, re.DOTALL)
        if colors_match:
            print(colors_match.group(0))
    else:
        print('❌ chart_specs.py НЕ содержит цветовую кодировку!')
        print()
        print('Текущая реализация:')
        print(ts_func[:1500])
        print('...')

# ============================================================================
# 4. Проверяем вызов в api.py
# ============================================================================
print()
print('4. Проверка вызова create_time_series_spec в api.py')
print('-' * 70)

if 'anomalies=anomalies_result' in api_content:
    print('✓ Передаём anomalies_result в create_time_series_spec')
else:
    print('⚠ Проверь как передаются аномалии в визуализатор')

print()
print('=' * 70)
print('ДИАГНОСТИКА ЗАВЕРШЕНА')
print('=' * 70)
print()
print('Теперь проверь через curl что возвращает backend:')
print()
print('  curl -s -X POST http://localhost:8081/api/v1/deep_analysis/run \\')
print('    -H "Content-Type: application/json" \\')
print('    -d \'{"tags": ["R203-CO2"], "period": 30}\' \\')
print('    | python -m json.tool | grep -A 5 "anomaly_types"')
print()
print('Скинь:')
print('  1. Вывод этого скрипта')
print('  2. Вывод curl (первые 50 строк ответа)')
print('  3. Есть ли в ответе поле anomaly_types и type_counts')