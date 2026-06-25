#!/usr/bin/env python3
"""
diagnose_via_http.py — диагностика аномалий через работающий API
"""
import requests
import json
import sys
from datetime import datetime

BASE_URL = "http://localhost:8081"

print('=' * 80)
print('ДИАГНОСТИКА АНОМАЛИЙ ЧЕРЕЗ HTTP API')
print('=' * 80)
print()

# 1. Проверяем что backend запущен
print('【1】Проверка доступности backend')
print('-' * 80)
try:
    r = requests.get(f'{BASE_URL}/api/v1/deep_analysis/ping', timeout=5)
    if r.status_code == 200:
        print(f'✅ Backend доступен: {r.json()}')
    else:
        print(f'⚠️  Backend вернул статус {r.status_code}')
except Exception as e:
    print(f'❌ Backend недоступен: {e}')
    sys.exit(1)

print()

# 2. Запускаем анализ для KITCHEN2-CO2
print('【2】Запуск анализа KITCHEN2-CO2 (30 дней)')
print('-' * 80)

try:
    r = requests.post(
        f'{BASE_URL}/api/v1/deep_analysis/run',
        json={"tags": ["KITCHEN2-CO2"], "period": 30, "anomalies": True},
        timeout=120
    )
    
    if r.status_code != 200:
        print(f'❌ Ошибка анализа: {r.status_code}')
        print(r.text[:500])
        sys.exit(1)
    
    data = r.json()
    
    # Общая статистика
    stats = data.get('statistics', {})
    anomalies = data.get('anomalies', {})
    viz = data.get('visualizations', {})
    
    print(f'✅ Анализ выполнен за {data.get("execution_time_ms", "?")} мс')
    print()
    
    print('【3】Общая статистика')
    print('-' * 80)
    print(f'  Всего точек:      {stats.get("count", "?")}')
    print(f'  Валидных:         {stats.get("valid_count", "?")}')
    print(f'  None/NaN:         {stats.get("null_count", "?")}')
    print(f'  Среднее:          {stats.get("mean", 0):.2f}')
    print(f'  Std:              {stats.get("std", 0):.2f}')
    print(f'  Min:              {stats.get("min", 0):.2f}')
    print(f'  Max:              {stats.get("max", 0):.2f}')
    print()
    
    print('【4】Аномалии')
    print('-' * 80)
    print(f'  Всего:            {anomalies.get("total_anomalies", 0)}')
    print(f'  Доля:             {anomalies.get("anomaly_rate", 0)*100:.2f}%')
    print(f'  По типам:')
    type_counts = anomalies.get('type_counts', {})
    for t in ['spike', 'dip', 'drift', 'noise']:
        cnt = type_counts.get(t, 0)
        print(f'    {t:10s}: {cnt:5d}')
    print()
    
    # Zero dips и sig dips
    zero_events = anomalies.get('zero_dips_events', [])
    sig_events = anomalies.get('sig_dips_events', [])
    print(f'  Zero dips events: {len(zero_events)}')
    print(f'  Sig dips events:  {len(sig_events)}')
    print()
    
    print('【5】Downsampling анализ')
    print('-' * 80)
    time_series = viz.get('time_series', {})
    if time_series:
        ds_labels = time_series.get('data', {}).get('labels', [])
        ds_datasets = time_series.get('data', {}).get('datasets', [])
        
        print(f'  Точек после downsampling: {len(ds_labels)}')
        print(f'  Количество datasets:      {len(ds_datasets)}')
        print()
        print(f'  Структура datasets:')
        for ds in ds_datasets:
            ds_type = ds.get('type', 'line')
            ds_label = ds.get('label', '?')
            ds_data = ds.get('data', [])
            non_null = sum(1 for v in ds_data if v is not None)
            print(f'    [{ds_type:7s}] {ds_label:30s} — {len(ds_data)} точек, {non_null} валидных')
        print()
        
        # Первая и последняя дата
        if ds_labels:
            print(f'  Первая дата:  {ds_labels[0]}')
            print(f'  Последняя:    {ds_labels[-1]}')
    
    print()
    print('【6】Примеры аномалий по типам (первые 5)')
    print('-' * 80)
    
    indices = anomalies.get('anomaly_indices', [])
    values = anomalies.get('anomaly_values', [])
    types = anomalies.get('anomaly_types', [])
    timestamps = anomalies.get('anomaly_timestamps', [])
    
    for atype in ['spike', 'dip', 'drift', 'noise']:
        type_samples = [
            (i, v, t, ts) for i, v, t, ts in zip(indices, values, types, timestamps)
            if t == atype
        ][:5]
        
        print(f'\n  {atype.upper()} ({len([t for t in types if t == atype])} всего):')
        if type_samples:
            for idx, val, _, ts in type_samples:
                print(f'    #{idx:5d}  {ts}  = {val:.2f}')
        else:
            print(f'    (нет примеров)')
    
    print()
    print('=' * 80)
    print('ДИАГНОСТИКА ЗАВЕРШЕНА')
    print('=' * 80)
    
    # Сохраняем сырой JSON
    with open('diagnosis_raw.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    print()
    print('💾 Сырые данные сохранены: diagnosis_raw.json')
    
except requests.exceptions.RequestException as e:
    print(f'❌ Ошибка запроса: {e}')
    sys.exit(1)
except Exception as e:
    print(f'❌ Ошибка: {e}')
    import traceback
    traceback.print_exc()