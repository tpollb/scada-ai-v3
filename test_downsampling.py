#!/usr/bin/env python3
"""
test_downsampling.py — тестирование downsampling на реальных данных
"""
import sys
sys.path.insert(0, 'backend')

from modules.deep_analysis.analyzers.anomalies import detect_anomalies_isolation_forest
from modules.deep_analysis.visualizers.chart_specs import downsample_time_series
from modules.deep_analysis.collectors.data_fetcher import fetch_tag_data
from datetime import datetime, timedelta
import numpy as np

async def test():
    print("=" * 80)
    print("ТЕСТ: Downsampling и детекция аномалий")
    print("=" * 80)
    print()
    
    # 1. Загружаем данные для KITCHEN2-CO2
    print("【1】Загрузка данных KITCHEN2-CO2 (30 дней)")
    print("-" * 80)
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    try:
        data = await fetch_tag_data('KITCHEN2-CO2', start_date, end_date)
        raw_values = data['raw_values']
        raw_timestamps = data['raw_timestamps']
        
        print(f"Всего точек: {len(raw_values)}")
        print(f"Период: {raw_timestamps[0]} - {raw_timestamps[-1]}")
        
        # Подсчёт None/NaN
        none_count = sum(1 for v in raw_values if v is None or (isinstance(v, float) and np.isnan(v)))
        valid_count = len(raw_values) - none_count
        
        print(f"Валидных значений: {valid_count} ({valid_count/len(raw_values)*100:.1f}%)")
        print(f"None/NaN значений: {none_count} ({none_count/len(raw_values)*100:.1f}%)")
        print()
        
        # 2. Детекция аномалий на оригинальных данных
        print("【2】Детекция аномалий на ОРИГИНАЛЬНЫХ данных")
        print("-" * 80)
        
        # Фильтруем None для Isolation Forest
        valid_indices = [i for i, v in enumerate(raw_values) if v is not None and not (isinstance(v, float) and np.isnan(v))]
        valid_values = [raw_values[i] for i in valid_indices]
        
        print(f"Точек для анализа: {len(valid_values)}")
        
        result = detect_anomalies_isolation_forest(
            valid_values,
            [raw_timestamps[i] for i in valid_indices],
            classify_types=True
        )
        
        print(f"Всего аномалий: {result['total_anomalies']}")
        print(f"Типы: {result['type_counts']}")
        print()
        
        # 3. Downsampling
        print("【3】Downsampling данных")
        print("-" * 80)
        
        max_points = 1500
        ds_values, ds_timestamps = downsample_time_series(raw_values, raw_timestamps, max_points)
        
        print(f"Оригинал: {len(raw_values)} точек")
        print(f"После downsampling: {len(ds_values)} точек")
        print(f"Сжатие: {len(raw_values)/len(ds_values):.2f}x")
        print()
        
        # 4. Сравнение значений
        print("【4】Сравнение значений до/после downsampling")
        print("-" * 80)
        
        # Берём первые 10 аномалий и проверяем их значения
        if result['anomaly_indices']:
            print("Первые 10 аномалий:")
            for i, (idx, val, atype) in enumerate(zip(
                result['anomaly_indices'][:10],
                result['anomaly_values'][:10],
                result['anomaly_types'][:10]
            )):
                orig_idx = valid_indices[idx]
                orig_val = raw_values[orig_idx]
                orig_ts = raw_timestamps[orig_idx]
                
                # Ищем эту точку в downsampled данных
                # (упрощённо — берём ближайшую по индексу)
                ds_idx_approx = int(orig_idx * len(ds_values) / len(raw_values))
                ds_val = ds_values[ds_idx_approx] if ds_idx_approx < len(ds_values) else None
                
                print(f"  {i+1}. {atype}:")
                print(f"     Оригинал: #{orig_idx} {orig_ts.strftime('%Y-%m-%d %H:%M')} = {orig_val:.2f}")
                print(f"     Downsampled: #{ds_idx_approx} = {ds_val:.2f if ds_val else 'N/A'}")
                print(f"     Разница: {abs(orig_val - ds_val):.2f}" if ds_val else "     Разница: N/A")
                print()
        
        # 5. Проверка дрейфов
        print("【5】Анализ дрейфов")
        print("-" * 80)
        
        drift_count = result['type_counts'].get('drift', 0)
        print(f"Дрейфов найдено: {drift_count}")
        
        if drift_count == 0:
            print()
            print("⚠️  Дрейфов не найдено! Проверяем почему...")
            print()
            
            # Ищем длинные последовательности с трендом
            print("Поиск потенциальных дрейфов (последовательности > 10 точек с трендом):")
            
            # Упрощённый поиск: берём окна по 20 точек и проверяем монотонность
            window_size = 20
            potential_drifts = []
            
            for i in range(0, len(valid_values) - window_size, window_size // 2):
                window = valid_values[i:i+window_size]
                
                # Проверяем монотонность
                increases = sum(1 for j in range(len(window)-1) if window[j+1] > window[j])
                decreases = sum(1 for j in range(len(window)-1) if window[j+1] < window[j])
                
                monotonic_ratio = max(increases, decreases) / (len(window) - 1)
                
                if monotonic_ratio > 0.7:  # >70% монотонность
                    # Проверяем изменение
                    change = abs(window[-1] - window[0]) / (abs(window[0]) + 1e-10)
                    
                    if change > 0.05:  # >5% изменение
                        potential_drifts.append({
                            'start_idx': i,
                            'end_idx': i + window_size,
                            'monotonic_ratio': monotonic_ratio,
                            'change': change,
                            'start_val': window[0],
                            'end_val': window[-1]
                        })
            
            print(f"Найдено {len(potential_drifts)} потенциальных дрейфов:")
            for i, drift in enumerate(potential_drifts[:5]):
                print(f"  {i+1}. Индексы {drift['start_idx']}-{drift['end_idx']}")
                print(f"     Монотонность: {drift['monotonic_ratio']:.2%}")
                print(f"     Изменение: {drift['change']:.2%}")
                print(f"     Значения: {drift['start_val']:.2f} → {drift['end_val']:.2f}")
                print()
        
        print("=" * 80)
        print("ДИАГНОСТИКА ЗАВЕРШЕНА")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

import asyncio
asyncio.run(test())
