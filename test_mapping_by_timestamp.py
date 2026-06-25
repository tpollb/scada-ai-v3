#!/usr/bin/env python3
"""
test_mapping_by_timestamp.py — проверка маппинга по timestamp (не по значению)
"""
import requests
from datetime import datetime

print('=' * 80)
print('ТЕСТ: Маппинг аномалий по timestamp')
print('=' * 80)
print()

# 1. Загружаем результат анализа
print('【1】Загрузка результата анализа')
print('-' * 80)

r = requests.post(
    'http://localhost:8081/api/v1/deep_analysis/run',
    json={"tags": ["KITCHEN2-CO2"], "period": 30},
    timeout=120
)

if r.status_code != 200:
    print(f'❌ Ошибка: {r.status_code}')
    exit(1)

data = r.json()

# 2. Извлекаем данные
anomalies = data.get('anomalies', {})
indices = anomalies.get('anomaly_indices', [])
values = anomalies.get('anomaly_values', [])
types = anomalies.get('anomaly_types', [])
timestamps = anomalies.get('anomaly_timestamps', [])

print(f'Всего аномалий: {len(indices)}')
print(f'По типам: {anomalies.get("type_counts", {})}')
print()

# 3. Извлекаем данные графика
viz = data.get('visualizations', {})
ts_spec = viz.get('time_series', {})
ts_data = ts_spec.get('data', {})
labels = ts_data.get('labels', [])
datasets = ts_data.get('datasets', [])

print(f'Labels (дат): {len(labels)}')
print(f'Datasets: {len(datasets)}')
print()

# 4. Проверяем маппинг по timestamp
print('【2】Проверка маппинга по timestamp')
print('-' * 80)

total_checked = 0
correctly_mapped = 0
missed = 0

for atype in ['spike', 'dip', 'noise']:
    print(f'\n📍 {atype.upper()}:')
    
    # Фильтруем аномалии этого типа
    type_anomalies = [
        (idx, val, ts) for idx, val, t, ts in zip(indices, values, types, timestamps)
        if t == atype
    ]
    
    if not type_anomalies:
        print(f'   Нет аномалий типа {atype}')
        continue
    
    # Находим scatter dataset для этого типа
    scatter_ds = None
    for ds in datasets:
        if atype in ds.get('label', '').lower():
            scatter_ds = ds
            break
    
    if not scatter_ds:
        print(f'   ⚠️  Scatter dataset для {atype} не найден')
        continue
    
    scatter_data = scatter_ds.get('data', [])
    
    # Проверяем первые 20 аномалий
    checked = 0
    correct = 0
    
    for orig_idx, val, ts in type_anomalies[:20]:
        total_checked += 1
        checked += 1
        
        # Форматируем timestamp аномалии (убираем секунды)
        if isinstance(ts, str):
            ts_normalized = ts[:16]  # "2026-05-29T10:31"
        else:
            ts_normalized = ts.strftime('%Y-%m-%d %H:%M')
        
        # Ищем этот timestamp в labels
        found = False
        for chart_idx, label in enumerate(labels):
            if label == ts_normalized:
                # Нашли! Проверяем значение
                chart_val = scatter_data[chart_idx] if chart_idx < len(scatter_data) else None
                
                if chart_val is not None and abs(chart_val - val) < 0.01:
                    correct += 1
                    correctly_mapped += 1
                    print(f'   ✓ idx={orig_idx:5d}, ts={ts_normalized}, val={val:.2f} → chart_idx={chart_idx}')
                else:
                    print(f'   ✗ idx={orig_idx:5d}, ts={ts_normalized}, val={val:.2f} → НАЙДЕНО, НО ЗНАЧЕНИЕ НЕ СОВПАДАЕТ (chart_val={chart_val})')
                
                found = True
                break
        
        if not found:
            missed += 1
            print(f'   ✗ idx={orig_idx:5d}, ts={ts_normalized}, val={val:.2f} → НЕ НАЙДЕНО В LABELS')
    
    print(f'   Проверено: {checked}, правильно: {correct}')

print()
print('=' * 80)
print('ИТОГОВАЯ ОЦЕНКА:')
print('=' * 80)
print()

if total_checked > 0:
    accuracy = correctly_mapped / total_checked * 100
    print(f'Всего проверено: {total_checked}')
    print(f'Правильно маппировано: {correctly_mapped} ({accuracy:.1f}%)')
    print(f'Пропущено: {missed}')
    print()
    
    if accuracy >= 95:
        print('✅ ОТЛИЧНО! Маппинг работает правильно')
        print()
        print('Точки аномалий теперь правильно позиционируются на графике:')
        print('  • Каждая точка привязана к правильной дате')
        print('  • Значения совпадают с оригинальными')
        print('  • Нет "висящих в воздухе" точек')
    elif accuracy >= 80:
        print('⚠️  ХОРОШО, но есть небольшие проблемы')
        print()
        print('Большинство точек маппируется правильно, но некоторые теряются.')
        print('Это может быть из-за:')
        print('  • Downsampling "съедает" некоторые точки')
        print('  • Fallback логика не находит ближайший timestamp')
    else:
        print('❌ ПЛОХО! Много точек теряется или маппируется неправильно')
        print()
        print('Нужно пересмотреть логику маппинга.')
else:
    print('⚠️  Не удалось проверить ни одной аномалии')

print()
print('=' * 80)
print('ЧТО ДЕЛАТЬ ДАЛЬШЕ:')
print('=' * 80)
print()
print('1. Открой фронтенд → DDA → KITCHEN2-CO2 → анализ')
print()
print('2. Проверь визуально:')
print('   • Наведи на точку аномалии — tooltip должен показать правильную дату')
print('   • Точка должна быть НА линии графика (не висеть в воздухе)')
print('   • Значение в tooltip должно совпадать с значением на оси Y')
print()
print('3. Если всё выглядит правильно — переходим к следующей задаче:')
print('   • ChartModal (кнопка ⛶ для полноэкранных графиков)')
print('   • Или FFT сезонность (Итерация A Day 3-4)')