#!/usr/bin/env python3
"""
debug_timestamp_formats.py — отладка реальных форматов timestamp
"""
import requests
from datetime import datetime

print('=' * 80)
print('ОТЛАДКА: Реальные форматы timestamp')
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
timestamps = anomalies.get('anomaly_timestamps', [])
values = anomalies.get('anomaly_values', [])
types = anomalies.get('anomaly_types', [])

print(f'Всего аномалий: {len(timestamps)}')
print()

# 3. Показываем РЕАЛЬНЫЙ формат timestamp
print('【2】РЕАЛЬНЫЙ формат timestamp из anomalies')
print('-' * 80)

if timestamps:
    print('Первые 10 timestamp (сырые):')
    for i, ts in enumerate(timestamps[:10], 1):
        print(f'  {i}. Тип: {type(ts).__name__}, Значение: {repr(ts)}')
    
    print()
    print('Примеры нормализации:')
    for i, ts in enumerate(timestamps[:5], 1):
        if isinstance(ts, str):
            # Пробуем разные способы нормализации
            normalized1 = ts.replace('T', ' ')[:16]
            normalized2 = ts[:16].replace('T', ' ')
            
            print(f'  {i}. Оригинал: {repr(ts)}')
            print(f'     Способ 1 (replace T, потом срез): {repr(normalized1)}')
            print(f'     Способ 2 (срез, потом replace T): {repr(normalized2)}')
            print()

# 4. Извлекаем данные графика
viz = data.get('visualizations', {})
ts_spec = viz.get('time_series', {})
ts_data = ts_spec.get('data', {})
labels = ts_data.get('labels', [])

print('【3】РЕАЛЬНЫЙ формат labels из графика')
print('-' * 80)

if labels:
    print('Первые 10 labels:')
    for i, label in enumerate(labels[:10], 1):
        print(f'  {i}. {repr(label)}')

print()

# 5. Пробуем найти совпадения
print('【4】Поиск совпадений')
print('-' * 80)

if timestamps and labels:
    # Берём первые 5 аномалий
    print('Пытаемся найти первые 5 аномалий в labels:')
    print()
    
    for i, (ts, val, atype) in enumerate(zip(timestamps[:5], values[:5], types[:5]), 1):
        print(f'{i}. Аномалия: {atype}, val={val:.2f}')
        print(f'   Timestamp (сырой): {repr(ts)}')
        
        # Нормализуем timestamp
        if isinstance(ts, str):
            ts_normalized = ts.replace('T', ' ')[:16]
        elif isinstance(ts, datetime):
            ts_normalized = ts.strftime('%Y-%m-%d %H:%M')
        else:
            ts_normalized = str(ts).replace('T', ' ')[:16]
        
        print(f'   Timestamp (нормализованный): {repr(ts_normalized)}')
        
        # Ищем в labels
        found = False
        for j, label in enumerate(labels):
            if label == ts_normalized:
                print(f'   ✅ НАЙДЕНО! label[{j}] = {repr(label)}')
                found = True
                break
        
        if not found:
            print(f'   ❌ НЕ НАЙДЕНО в labels')
            
            # Пробуем частичное совпадение
            partial_matches = [l for l in labels if ts_normalized[:10] in l]
            if partial_matches:
                print(f'   Частичные совпадения (по дате {ts_normalized[:10]}):')
                for pm in partial_matches[:3]:
                    print(f'     • {repr(pm)}')
        
        print()

# 6. Проверяем scatter datasets
print('【5】Проверка scatter datasets')
print('-' * 80)

datasets = ts_data.get('datasets', [])
for ds in datasets:
    ds_type = ds.get('type', 'line')
    ds_label = ds.get('label', '?')
    ds_data = ds.get('data', [])
    
    if ds_type == 'scatter':
        non_null = sum(1 for v in ds_data if v is not None)
        print(f'{ds_label} (scatter):')
        print(f'  Размер: {len(ds_data)}')
        print(f'  Непустых: {non_null}')
        
        # Показываем первые 5 непустых
        print(f'  Первые 5 непустых точек:')
        count = 0
        for idx, val in enumerate(ds_data):
            if val is not None:
                label = labels[idx] if idx < len(labels) else '???'
                print(f'    idx={idx}, label={label}, val={val}')
                count += 1
                if count >= 5:
                    break
        print()

print('=' * 80)
print('ВЫВОДЫ:')
print('=' * 80)
print()
print('1. Проверь формат timestamp — может быть datetime объект, а не строка')
print('2. Проверь формат labels — может быть другой чем ожидается')
print('3. Если scatter datasets пустые или имеют неправильные индексы — проблема в chart_specs.py')
print()
print('Скинь этот вывод — я увижу РЕАЛЬНЫЕ форматы и дам точечный фикс!')