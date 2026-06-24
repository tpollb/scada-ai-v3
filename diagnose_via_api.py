#!/usr/bin/env python3
"""
diagnose_via_api.py — диагностика через работающее API приложения
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, 'backend')

async def diagnose():
    print('=' * 80)
    print('ДИАГНОСТИКА ЧЕРЕЗ РАБОТАЮЩЕЕ ПРИЛОЖЕНИЕ')
    print('=' * 80)
    print()
    
    try:
        from modules.deep_analysis.collectors.data_fetcher import fetch_tag_data
        from modules.deep_analysis.analyzers.anomalies import (
            detect_anomalies_isolation_forest,
            detect_zero_dips,
            detect_significant_dips,
            classify_anomaly_types,
        )
        
        # 1. Загружаем данные
        print('【1】ЗАГРУЗКА ДАННЫХ R001-CO2')
        print('-' * 80)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        data = await fetch_tag_data('R001-CO2', start_date, end_date)
        
        print(f'  Период: {start_date.strftime("%Y-%m-%d %H:%M")} → {end_date.strftime("%Y-%m-%d %H:%M")}')
        print(f'  Всего точек: {len(data["raw_values"])}')
        print(f'  Первая точка: {data["raw_timestamps"][0]}')
        print(f'  Последняя точка: {data["raw_timestamps"][-1]}')
        print()
        
        # Проверяем распределение по датам
        print('  Распределение по неделям:')
        for week in range(4):
            week_start = start_date + timedelta(weeks=week)
            week_end = week_start + timedelta(weeks=1)
            
            week_count = sum(
                1 for ts in data['raw_timestamps']
                if week_start <= ts < week_end
            )
            
            print(f'    Неделя {week+1} ({week_start.strftime("%d.%m")} - {week_end.strftime("%d.%m")}): {week_count} точек')
        
        print()
        
        # 2. Проверяем последние точки
        print('【2】ПОСЛЕДНИЕ 20 ТОЧЕК')
        print('-' * 80)
        for i in range(-20, 0):
            ts = data['raw_timestamps'][i]
            val = data['raw_values'][i]
            print(f'  {ts.strftime("%Y-%m-%d %H:%M")} → {val:.2f}')
        print()
        
        # 3. Ищем провалы вручную
        print('【3】ПОИСК ПРОВАЛОВ (значения < 200)')
        print('-' * 80)
        low_values = []
        for i, (ts, val) in enumerate(zip(data['raw_timestamps'], data['raw_values'])):
            if val is not None and val < 200:
                low_values.append((i, ts, val))
        
        if low_values:
            print(f'  Найдено {len(low_values)} точек с значением < 200:')
            for idx, ts, val in low_values[:20]:
                print(f'    #{idx} {ts.strftime("%Y-%m-%d %H:%M")} → {val:.2f}')
            if len(low_values) > 20:
                print(f'    ... и ещё {len(low_values) - 20}')
        else:
            print('  ⚠️  Точек со значением < 200 не найдено!')
        print()
        
        # 4. Детекция аномалий
        print('【4】ДЕТЕКЦИЯ АНОМАЛИЙ')
        print('-' * 80)
        
        # Zero dips
        zd = detect_zero_dips(data['raw_values'], data['raw_timestamps'], zero_threshold_ratio=0.05)
        print(f'  Zero dips (падения < 5% от среднего):')
        print(f'    Событий: {len(zd["events"])}')
        print(f'    Точек: {len(zd["anomaly_indices"])}')
        if zd['events']:
            print(f'    Первые 5 событий:')
            for e in zd['events'][:5]:
                ts_start = data['raw_timestamps'][e['start_idx']]
                ts_end = data['raw_timestamps'][e['end_idx']]
                print(f'      {ts_start.strftime("%d.%m %H:%M")} - {ts_end.strftime("%d.%m %H:%M")} '
                      f'({e["duration"]} точек, min={e["min_value"]:.2f})')
        print()
        
        # Significant dips
        sd = detect_significant_dips(data['raw_values'], data['raw_timestamps'], drop_ratio=0.30)
        print(f'  Significant dips (падения > 30%):')
        print(f'    Событий: {len(sd["events"])}')
        print(f'    Точек: {len(sd["anomaly_indices"])}')
        if sd['events']:
            print(f'    Первые 10 событий:')
            for e in sd['events'][:10]:
                ts_start = data['raw_timestamps'][e['start_idx']]
                ts_end = data['raw_timestamps'][e['end_idx']]
                drop_pct = e.get('drop_percent', 0) * 100
                mean_before = e.get('local_mean_before', 0)
                print(f'      {ts_start.strftime("%d.%m %H:%M")} - {ts_end.strftime("%d.%m %H:%M")} '
                      f'({e["duration"]} точек, drop={drop_pct:.1f}%, mean_before={mean_before:.1f})')
        print()
        
        # Полная детекция
        result = detect_anomalies_isolation_forest(
            data['raw_values'],
            data['raw_timestamps'],
            contamination=0.10,
            classify_types=True
        )
        
        print(f'  Итоговая классификация:')
        print(f'    {result["type_counts"]}')
        print()
        
        # 5. Детали по каждому типу
        print('【5】ДЕТАЛИ ПО ТИПАМ АНОМАЛИЙ')
        print('-' * 80)
        
        for atype in ['spike', 'dip', 'drift', 'noise']:
            indices = [
                i for i, t in zip(result['anomaly_indices'], result['anomaly_types'])
                if t == atype
            ]
            
            print(f'  {atype.upper()} ({len(indices)} точек):')
            
            if indices:
                # Показываем первые 10 точек
                for idx in indices[:10]:
                    ts = data['raw_timestamps'][idx]
                    val = data['raw_values'][idx]
                    print(f'    #{idx} {ts.strftime("%d.%m %H:%M")} → {val:.2f}')
                
                if len(indices) > 10:
                    print(f'    ... и ещё {len(indices) - 10} точек')
            else:
                print(f'    (нет точек)')
            
            print()
        
        # 6. Проверяем плато
        print('【6】ПРОВЕРКА ПЛАТО (повторяющиеся значения)')
        print('-' * 80)
        
        # Ищем последовательности одинаковых значений
        plateaus = []
        current_val = None
        current_count = 0
        current_start = None
        
        for i, val in enumerate(data['raw_values']):
            if val == current_val:
                current_count += 1
            else:
                if current_count >= 5:
                    plateaus.append((current_start, i-1, current_val, current_count))
                current_val = val
                current_count = 1
                current_start = i
        
        if current_count >= 5:
            plateaus.append((current_start, len(data['raw_values'])-1, current_val, current_count))
        
        print(f'  Найдено {len(plateaus)} плато (5+ одинаковых значений подряд):')
        for start, end, val, count in plateaus[:10]:
            ts_start = data['raw_timestamps'][start]
            ts_end = data['raw_timestamps'][end]
            
            # Проверяем тип этих точек
            types_in_plateau = [
                result['anomaly_types'][i]
                for i in range(start, end+1)
                if i in result['anomaly_indices']
            ]
            
            print(f'    {ts_start.strftime("%d.%m %H:%M")} - {ts_end.strftime("%d.%m %H:%M")} '
                  f'({count} точек, значение={val:.2f}, типы: {set(types_in_plateau) if types_in_plateau else "не аномалии"})')
        
        if len(plateaus) > 10:
            print(f'    ... и ещё {len(plateaus) - 10} плато')
        
        print()
        print('=' * 80)
        print('ДИАГНОСТИКА ЗАВЕРШЕНА')
        print('=' * 80)
        
    except Exception as e:
        print(f'❌ Ошибка: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(diagnose())