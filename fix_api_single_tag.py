#!/usr/bin/env python3
"""
fix_api_single_tag.py — адаптируем api.py для новой структуры fetch_tag_data
"""

from pathlib import Path

print('=' * 70)
print('ФИКС: api.py для новой структуры fetch_tag_data')
print('=' * 70)
print()

api_path = Path('backend/modules/deep_analysis/api.py')
content = api_path.read_text(encoding='utf-8')

changes = []

# 1. Обновляем проверку пустых данных
old_check = "if not data['values']:"
new_check = "if not data['raw_values']:"

if old_check in content:
    content = content.replace(old_check, new_check)
    changes.append("Проверка: data['values'] → data['raw_values']")
    print("✓ Проверка пустых данных обновлена")

# 2. Обновляем вызов compute_basic_stats
old_stats = "stats = compute_basic_stats(data['values'])"
new_stats = "stats = compute_basic_stats(data['raw_values'])"

if old_stats in content:
    content = content.replace(old_stats, new_stats)
    changes.append("Статистика: data['values'] → data['raw_values']")
    print("✓ Вызов compute_basic_stats обновлён")

# 3. Обновляем вызов compute_histogram
old_hist = "histogram = compute_histogram(data['values'])"
new_hist = "histogram = compute_histogram(data['raw_values'])"

if old_hist in content:
    content = content.replace(old_hist, new_hist)
    changes.append("Гистограмма: data['values'] → data['raw_values']")
    print("✓ Вызов compute_histogram обновлён")

# 4. Обновляем вызов detect_anomalies_isolation_forest
old_anom = '''anomalies_result = detect_anomalies_isolation_forest(
                    data['values'],
                    data['timestamps']
                )'''

new_anom = '''anomalies_result = detect_anomalies_isolation_forest(
                    data['raw_values'],
                    data['raw_timestamps']
                )'''

if old_anom in content:
    content = content.replace(old_anom, new_anom)
    changes.append("Аномалии: data['values/timestamps'] → data['raw_values/timestamps']")
    print("✓ Вызов detect_anomalies_isolation_forest обновлён")

# 5. Обновляем вызов create_time_series_spec
old_ts_spec = '''time_series_spec = create_time_series_spec(
                data['timestamps'],
                data['values'],
                tag_name,
                anomalies=anomalies_result
            )'''

new_ts_spec = '''time_series_spec = create_time_series_spec(
                data['raw_timestamps'],
                data['raw_values'],
                tag_name,
                anomalies=anomalies_result
            )'''

if old_ts_spec in content:
    content = content.replace(old_ts_spec, new_ts_spec)
    changes.append("Time series: data['timestamps/values'] → data['raw_*']")
    print("✓ Вызов create_time_series_spec обновлён")

# 6. Обновляем summary (использует stats['count'] — это уже обновлено через stats)
# Не нужно менять

# Сохраняем
api_path.write_text(content, encoding='utf-8', newline='\n')

print()
print('=' * 70)
print('ИТОГ:')
print('=' * 70)
for i, c in enumerate(changes, 1):
    print(f'  {i}. ✓ {c}')

print()
print('=' * 70)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 70)
print()
print('fetch_tag_data теперь возвращает СЫРЫЕ данные:')
print('  • raw_timestamps (вместо timestamps)')
print('  • raw_values (вместо values)')
print('  • Без ресемплинга (ресемплинг делается в fetch_multiple_tags)')
print()
print('api.py обновлён чтобы использовать raw_values/raw_timestamps')
print('для single-tag анализа.')
print()
print('=' * 70)
print('ПРОВЕРКА:')
print('=' * 70)
print()
print('Перезапусти backend и проверь:')
print()
print('  curl -X POST http://localhost:8081/api/v1/deep_analysis/run \\')
print('    -H "Content-Type: application/json" \\')
print('    -d \'{"tags": ["R203-CO2"], "period": 30}\'')
print()
print('Должно вернуться:')
print('  • statistics (mean, std, min, max)')
print('  • anomalies с типами (spike, dip, drift, noise)')
print('  • visualizations с цветовой кодировкой аномалий')