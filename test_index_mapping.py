#!/usr/bin/env python3
"""
test_index_mapping.py — демонстрация рассинхронизации
"""
import sys
sys.path.insert(0, 'backend')

import asyncio
import json
from datetime import datetime, timedelta
import numpy as np

async def test():
    print("=" * 80)
    print("ТЕСТ: Маппинг индексов аномалий")
    print("=" * 80)
    print()
    
    # 1. Загружаем данные через работающий API
    import requests
    
    print("【1】Загружаем результат анализа KITCHEN2-CO2")
    print("-" * 80)
    
    r = requests.post(
        'http://localhost:8081/api/v1/deep_analysis/run',
        json={"tags": ["KITCHEN2-CO2"], "period": 30},
        timeout=120
    )
    
    if r.status_code != 200:
        print(f"❌ Ошибка: {r.status_code}")
        return
    
    data = r.json()
    
    # 2. Извлекаем аномалии
    anomalies = data.get('anomalies', {})
    indices = anomalies.get('anomaly_indices', [])
    values = anomalies.get('anomaly_values', [])
    types = anomalies.get('anomaly_types', [])
    timestamps = anomalies.get('anomaly_timestamps', [])
    
    print(f"Всего аномалий: {len(indices)}")
    print(f"Типы: {anomalies.get('type_counts', {})}")
    print()
    
    # 3. Извлекаем данные графика
    viz = data.get('visualizations', {})
    ts_spec = viz.get('time_series', {})
    ts_data = ts_spec.get('data', {})
    labels = ts_data.get('labels', [])
    datasets = ts_data.get('datasets', [])
    
    print(f"【2】Данные графика")
    print("-" * 80)
    print(f"Labels (дат): {len(labels)}")
    print(f"Datasets: {len(datasets)}")
    for ds in datasets:
        ds_data = ds.get('data', [])
        non_null = sum(1 for v in ds_data if v is not None)
        print(f"  {ds.get('label'):30s}: {len(ds_data)} точек, {non_null} непустых")
    print()
    
    # 4. Основная проверка — где лежат scatter точки
    print(f"【3】Проверка scatter datasets")
    print("-" * 80)
    
    for ds in datasets:
        ds_type = ds.get('type', 'line')
        ds_label = ds.get('label', '?')
        ds_data = ds.get('data', [])
        
        if ds_type == 'scatter':
            print(f"\n📍 {ds_label} (scatter, {len(ds_data)} точек)")
            
            # Находим непустые точки
            non_null_indices = [i for i, v in enumerate(ds_data) if v is not None]
            print(f"   Непустых точек: {len(non_null_indices)}")
            
            if non_null_indices:
                # Показываем первые 10 точек
                print(f"   Первые 10 точек:")
                for idx in non_null_indices[:10]:
                    val = ds_data[idx]
                    label = labels[idx] if idx < len(labels) else '???'
                    print(f"     index={idx:5d}, label={label}, value={val}")
                
                # КРИТИЧЕСКАЯ ПРОВЕРКА: индекс scatter точки должен совпадать с label
                print(f"\n   🔍 Проверка соответствия index ↔ label:")
                mismatches = []
                for idx in non_null_indices[:20]:
                    val = ds_data[idx]
                    label = labels[idx] if idx < len(labels) else '???'
                    
                    # Ищем этот timestamp в оригинальных аномалиях
                    matching_anomalies = []
                    for a_idx, a_val, a_type, a_ts in zip(indices, values, types, timestamps):
                        if isinstance(a_ts, str) and label in a_ts:
                            matching_anomalies.append((a_idx, a_val, a_type))
                        elif str(a_ts) == label:
                            matching_anomalies.append((a_idx, a_val, a_type))
                    
                    if matching_anomalies:
                        a_idx, a_val, a_type = matching_anomalies[0]
                        match = "✓" if abs(val - a_val) < 0.01 else f"✗ (diff={abs(val-a_val):.2f})"
                        print(f"     idx={idx:5d}, label={label}, scatter_val={val:.2f}, anom_val={a_val:.2f} {match}")
                    else:
                        print(f"     idx={idx:5d}, label={label}, scatter_val={val:.2f}, anom=NOT_FOUND")
                
                # Проверяем: выходят ли индексы за пределы labels?
                max_idx = max(non_null_indices)
                if max_idx >= len(labels):
                    print(f"\n   ⚠️  БАГ! Max scatter index ({max_idx}) >= len(labels) ({len(labels)})")
                    print(f"       Scatter точки выходят за границы графика!")
                else:
                    print(f"\n   ✓ Все scatter индексы в пределах labels (max={max_idx}, labels={len(labels)})")
    
    # 5. Проверка конкретного примера
    print(f"\n【4】Конкретный пример: точка шума с значением ~658")
    print("-" * 80)
    
    # Ищем в аномалиях значение близкое к 658
    target_value = 658
    tolerance = 5
    
    matching = []
    for i, (idx, val, atype, ts) in enumerate(zip(indices, values, types, timestamps)):
        if abs(val - target_value) < tolerance:
            matching.append((i, idx, val, atype, ts))
    
    if matching:
        print(f"Найдено {len(matching)} аномалий со значением ~{target_value}:")
        for i, idx, val, atype, ts in matching[:5]:
            print(f"  • anom_idx={idx}, value={val:.2f}, type={atype}, timestamp={ts}")
        
        # Проверяем где это отображается на графике
        if matching:
            sample = matching[0]
            anom_idx = sample[1]
            anom_val = sample[2]
            anom_ts = sample[4]
            
            print(f"\n  Где это отображается на графике?")
            print(f"  Ищем в scatter datasets точку со значением {anom_val:.2f}...")
            
            for ds in datasets:
                if ds.get('type') == 'scatter':
                    ds_data = ds.get('data', [])
                    for chart_idx, chart_val in enumerate(ds_data):
                        if chart_val is not None and abs(chart_val - anom_val) < 0.01:
                            chart_label = labels[chart_idx] if chart_idx < len(labels) else '???'
                            print(f"    ✓ Найдено в {ds.get('label')}: chart_idx={chart_idx}, label={chart_label}")
                            print(f"      Значение на графике в этом label: {anom_val:.2f}")
                            
                            # Проверяем: это тот же timestamp?
                            if str(anom_ts) == chart_label or (isinstance(anom_ts, str) and chart_label in anom_ts):
                                print(f"      ✓ Timestamp совпадает")
                            else:
                                print(f"      ⚠️  Timestamp НЕ совпадает!")
                                print(f"         Аномалия: {anom_ts}")
                                print(f"         График:   {chart_label}")
    else:
        print(f"Не найдено аномалий со значением ~{target_value}")

asyncio.run(test())
