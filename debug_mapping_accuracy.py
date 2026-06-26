#!/usr/bin/env python3
"""
debug_mapping_accuracy.py — точная диагностика маппинга timestamp → index
"""
import requests
from datetime import datetime

print('=' * 80)
print('ДИАГНОСТИКА: Точность маппинга timestamp → downsampled index')
print('=' * 80)
print()

# Запускаем анализ
r = requests.post(
    'http://localhost:8081/api/v1/deep_analysis/run',
    json={"tags": ["KITCHEN2-CO2"], "period": 7},
    timeout=120
)

if r.status_code != 200:
    print(f'❌ Ошибка: {r.status_code}')
    exit(1)

data = r.json()

# Извлекаем данные
anomalies = data.get('anomalies', {})
anomaly_indices = anomalies.get('anomaly_indices', [])
anomaly_timestamps = anomalies.get('anomaly_timestamps', [])
anomaly_values = anomalies.get('anomaly_values', [])
anomaly_types = anomalies.get('anomaly_types', [])

viz = data.get('visualizations', {})
ts_spec = viz.get('time_series', {})
ts_data = ts_spec.get('data', {})
labels = ts_data.get('labels', [])
datasets = ts_data.get('datasets', [])

print(f'Всего аномалий: {len(anomaly_indices)}')
print(f'Labels (downsampled точек): {len(labels)}')
print()

# Проверяем шаг между labels (для понимания downsampling)
print('【1】Шаг между labels')
print('-' * 80)
if len(labels) >= 3:
    try:
        t1 = datetime.strptime(labels[0], "%Y-%m-%d %H:%M")
        t2 = datetime.strptime(labels[1], "%Y-%m-%d %H:%M")
        t3 = datetime.strptime(labels[2], "%Y-%m-%d %H:%M")
        step1 = (t2 - t1).total_seconds() / 60
        step2 = (t3 - t2).total_seconds() / 60
        print(f'  Шаг между label[0] и label[1]: {step1:.1f} мин')
        print(f'  Шаг между label[1] и label[2]: {step2:.1f} мин')
        
        if step1 != step2:
            print(f'  ⚠️  Шаг НЕ равномерный! ({step1:.1f} vs {step2:.1f} мин)')
            print(f'      Это МОЖЕТ вызывать смещение при маппинге')
    except Exception as e:
        print(f'  ⚠️  Не удалось парсить labels: {e}')

print()

# Проверяем конкретный пример смещения
print('【2】Анализ конкретного примера смещения')
print('-' * 80)
print('Ты упоминал: "12.06 в 2.10 а по факту 12.06 в 2.40"')
print('Ищем этот случай в аномалиях...')
print()

target_date = '2026-06-12'
target_hour = '02'

matching_anomalies = []
for idx, ts, val, atype in zip(anomaly_indices, anomaly_timestamps, anomaly_values, anomaly_types):
    ts_str = str(ts)
    if target_date in ts_str and f'T{target_hour}:' in ts_str or f' {target_hour}:' in ts_str:
        matching_anomalies.append((idx, ts_str, val, atype))

if matching_anomalies:
    print(f'Найдено {len(matching_anomalies)} аномалий на 12.06 в 02:xx')
    for idx, ts, val, atype in matching_anomalies[:10]:
        print(f'  anom_idx={idx}, ts={ts}, val={val:.2f}, type={atype}')
    
    print()
    print('Теперь смотрим что в scatter datasets на этих индексах:')
    
    for idx, ts, val, atype in matching_anomalies[:5]:
        # Ищем этот индекс в scatter datasets
        for ds in datasets:
            if ds.get('type') == 'scatter':
                ds_data = ds.get('data', [])
                if idx < len(ds_data):
                    chart_val = ds_data[idx]
                    if chart_val is not None:
                        chart_label = labels[idx] if idx < len(labels) else '???'
                        print(f'    Dataset: {ds.get("label")}')
                        print(f'      scatter_idx={idx}, label={chart_label}, val={chart_val:.2f}')
                        
                        # Проверяем: совпадает ли label с оригинальным timestamp?
                        if ts[:16] != chart_label:
                            print(f'      ⚠️  СМЕЩЕНИЕ!')
                            print(f'         Оригинал: {ts}')
                            print(f'         На графике: {chart_label}')
                            
                            # Считаем разницу
                            try:
                                ts_dt = datetime.strptime(ts[:16], "%Y-%m-%d %H:%M")
                                lbl_dt = datetime.strptime(chart_label, "%Y-%m-%d %H:%M")
                                diff_min = (lbl_dt - ts_dt).total_seconds() / 60
                                print(f'         Разница: {diff_min:.1f} мин')
                            except:
                                pass
else:
    print(f'❌ Аномалий на 12.06 02:xx не найдено')
    print('   Возможно период 7 дней не включает эту дату')

print()

# Проверяем общие характеристики маппинга
print('【3】Общая статистика маппинга')
print('-' * 80)

offsets = []
for idx, ts, val, atype in zip(anomaly_indices[:100], anomaly_timestamps[:100], 
                                anomaly_values[:100], anomaly_types[:100]):
    if idx >= len(labels):
        continue
    
    chart_label = labels[idx]
    ts_str = str(ts)[:16].replace('T', ' ')
    
    try:
        ts_dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M")
        lbl_dt = datetime.strptime(chart_label, "%Y-%m-%d %H:%M")
        diff_min = (lbl_dt - ts_dt).total_seconds() / 60
        offsets.append(diff_min)
    except:
        pass

if offsets:
    import statistics
    print(f'Проверено аномалий: {len(offsets)}')
    print(f'Среднее смещение: {statistics.mean(offsets):.1f} мин')
    print(f'Медиана смещения: {statistics.median(offsets):.1f} мин')
    print(f'Min смещение: {min(offsets):.1f} мин')
    print(f'Max смещение: {max(offsets):.1f} мин')
    print(f'Std deviation: {statistics.stdev(offsets):.1f} мин' if len(offsets) > 1 else '')
    
    if abs(statistics.mean(offsets)) > 5:
        print()
        print('⚠️  Систематическое смещение больше 5 минут!')
        print('   Это указывает на проблему в маппинге timestamp → downsampled index')

print()
print('=' * 80)
print('ВЫВОДЫ:')
print('=' * 80)
print()
print('Если смещение:')
print('  • ~0 мин → маппинг работает правильно, проблема в Chart.js парсинге дат')
print('  • ~30 мин → проблема в downsampling (bucket_size не делится ровно)')
print('  • ~60+ мин → проблема в timezone')
print()
print('Если шаг между labels НЕ равномерный:')
print('  → Min-max downsampling создаёт неравные интервалы')
print('  → Это ПРИЧИНА смещения!')
print()
print('РЕШЕНИЕ:')
print('  Использовать РАВНОМЕРНЫЙ downsampling (по индексам, не по min-max)')
print('  Или хранить оригинальные индексы при downsampling для точного маппинга')