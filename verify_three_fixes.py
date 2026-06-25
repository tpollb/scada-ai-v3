#!/usr/bin/env python3
"""
verify_three_fixes.py — проверка что три проблемы решены
"""
import requests
from datetime import datetime

print('=' * 80)
print('ПРОВЕРКА: Три проблемы решены?')
print('=' * 80)
print()

r = requests.post(
    'http://localhost:8081/api/v1/deep_analysis/run',
    json={"tags": ["KITCHEN2-CO2"], "period": 30},
    timeout=120
)

data = r.json()
anomalies = data.get('anomalies', {})
indices = anomalies.get('anomaly_indices', [])
values = anomalies.get('anomaly_values', [])
types = anomalies.get('anomaly_types', [])
timestamps = anomalies.get('anomaly_timestamps', [])

print(f'Всего аномалий: {len(indices)}')
print(f'По типам: {anomalies.get("type_counts", {})}')
print()

# 1. Проверяем провалы 18.06 11:00-13:00
print('【1】Провалы 18.06 11:00-13:00')
print('-' * 80)

dips_on_18 = []
for idx, val, atype, ts in zip(indices, values, types, timestamps):
    if atype == 'dip' and '2026-06-18' in str(ts):
        ts_str = str(ts)
        if '11:' in ts_str or '12:' in ts_str or '13:' in ts_str:
            dips_on_18.append((idx, val, ts))

if dips_on_18:
    print(f'⚠️  Найдено {len(dips_on_18)} провалов 18.06 11:00-13:00:')
    for idx, val, ts in dips_on_18[:10]:
        print(f'  idx={idx}, val={val:.2f}, ts={ts}')
    print()
    print('Это значит что значения действительно низкие (< 187 при mean=505, std=106)')
    print('Или классификатор помечает их через другой механизм (не z-score)')
else:
    print('✅ Провалов 18.06 11:00-13:00 не найдено')

print()

# 2. Проверяем плато 409 (07.06 и 14.06)
print('【2】Плато 409 (07.06 и 14.06)')
print('-' * 80)

plateau_409_anomalies = []
for idx, val, atype, ts in zip(indices, values, types, timestamps):
    if abs(val - 409) < 1:  # значение близко к 409
        plateau_409_anomalies.append((idx, val, atype, ts))

if plateau_409_anomalies:
    print(f'⚠️  Найдено {len(plateau_409_anomalies)} точек со значением ~409 в аномалиях:')
    for idx, val, atype, ts in plateau_409_anomalies[:10]:
        print(f'  idx={idx}, val={val:.2f}, type={atype}, ts={ts}')
    print()
    print('Это значит что stuck sensor detection не сработал для этих точек')
else:
    print('✅ Точек со значением 409 в аномалиях не найдено (stuck sensor detection работает)')

print()

# 3. Проверяем дрейфы
print('【3】Дрейфы')
print('-' * 80)

drifts = [(idx, val, ts) for idx, val, atype, ts in zip(indices, values, types, timestamps) if atype == 'drift']

if drifts:
    print(f'✅ Найдено {len(drifts)} дрейфов:')
    
    # Группируем по датам
    from collections import defaultdict
    drifts_by_date = defaultdict(list)
    for idx, val, ts in drifts:
        date = str(ts)[:10]
        drifts_by_date[date].append((idx, val, ts))
    
    for date, points in sorted(drifts_by_date.items()):
        print(f'  {date}: {len(points)} точек')
        for idx, val, ts in points[:3]:
            print(f'    idx={idx}, val={val:.2f}, ts={ts}')
else:
    print('❌ Дрейфов не найдено (но в type_counts drift=4 — странно)')

print()

# 4. Показываем ВСЕ провалы
print('【4】Все провалы (dip)')
print('-' * 80)

dips = [(idx, val, ts) for idx, val, atype, ts in zip(indices, values, types, timestamps) if atype == 'dip']
print(f'Всего провалов: {len(dips)}')
print()
print('Первые 10:')
for idx, val, ts in dips[:10]:
    print(f'  idx={idx:5d}, val={val:7.2f}, ts={ts}')

print()
print('Последние 10:')
for idx, val, ts in dips[-10:]:
    print(f'  idx={idx:5d}, val={val:7.2f}, ts={ts}')

print()
print('=' * 80)
print('ВЫВОДЫ:')
print('=' * 80)
print()

if len(drifts) > 0:
    print('✅ Дрейфы детектируются правильно')
else:
    print('⚠️  Дрейфы в type_counts есть, но точки не найдены (возможно группировка)')

if len(plateau_409_anomalies) == 0:
    print('✅ Stuck sensor detection работает (плато 409 исключено)')
else:
    print('⚠️  Stuck sensor detection не сработал для некоторых точек')

if len(dips_on_18) == 0:
    print('✅ Провалы 18.06 11:00-13:00 больше не помечаются')
else:
    print('⚠️  Провалы 18.06 11:00-13:00 всё ещё есть')
    print('   Возможные причины:')
    print('   • Значения действительно низкие (< 187)')
    print('   • Классификатор использует другой механизм (detect_significant_dips)')
    print('   • Нужно проверить код classify_anomaly_types')

print()
print('=' * 80)
print('ЧТО ДЕЛАТЬ ДАЛЬШЕ:')
print('=' * 80)
print()
print('1. Открой фронтенд → DDA → KITCHEN2-CO2 → анализ')
print()
print('2. Визуально проверь:')
print('   • 18.06 11:00-13:00 — есть ли синие точки (dip)?')
print('   • 07.06 12:33-16:53 — есть ли серые точки (плато 409)?')
print('   • 14.06 08:52-17:47 — есть ли серые точки (плато 409)?')
print('   • Есть ли оранжевый пунктир (drift)?')
print()
print('3. Если визуально всё правильно — переходим к ChartModal')
print('   (кнопка ⛶ для полноэкранных графиков)')