#!/usr/bin/env python3
"""
diagnose_anomalies_coverage.py — полная диагностика покрытия аномалий
"""
from pathlib import Path
import json
import sys

print('=' * 80)
print('ДИАГНОСТИКА: Покрытие аномалий и пропуски')
print('=' * 80)
print()

# 1. Проверяем anomalies.py на скрытые лимиты
print('【1】Проверка anomalies.py на скрытые лимиты')
print('-' * 80)

anomalies_path = Path('backend/modules/deep_analysis/analyzers/anomalies.py')
if anomalies_path.exists():
    content = anomalies_path.read_text(encoding='utf-8')
    
    # Ищем возможные лимиты
    limits_found = []
    
    # Проверка на slice [:N]
    import re
    slices = re.findall(r'anomaly_indices\[:\d+\]|anomaly_values\[:\d+\]|anomaly_types\[:\d+\]', content)
    if slices:
        limits_found.append(f'Срезы массивов: {slices}')
    
    # Проверка на max/limit параметры
    if 'max_anomalies' in content or 'limit=' in content:
        limits_found.append('Найдены параметры max_anomalies или limit')
    
    # Проверка contamination
    contam_matches = re.findall(r'contamination[=:]\s*([\d.]+)', content)
    if contam_matches:
        print(f'  Contamination значения: {set(contam_matches)}')
    
    if limits_found:
        print('  ⚠️  Найдены возможные лимиты:')
        for lim in limits_found:
            print(f'     • {lim}')
    else:
        print('  ✅ Явных лимитов не найдено')
else:
    print('  ❌ anomalies.py не найден')

print()

# 2. Создаём расширенный диагностический скрипт
print('【2】Создание расширенной диагностики')
print('-' * 80)

diag_script = '''#!/usr/bin/env python3
"""
diagnose_anomalies_detailed.py — детальная диагностика пропусков
"""
import sys
sys.path.insert(0, 'backend')

import asyncio
import requests
import json
from datetime import datetime
from collections import defaultdict
import numpy as np

BASE_URL = "http://localhost:8081"

async def diagnose():
    print("=" * 80)
    print("ДЕТАЛЬНАЯ ДИАГНОСТИКА АНОМАЛИЙ")
    print("=" * 80)
    print()
    
    # 1. Запускаем анализ
    print("【1】Запуск анализа KITCHEN2-CO2 (30 дней)")
    print("-" * 80)
    
    r = requests.post(
        f'{BASE_URL}/api/v1/deep_analysis/run',
        json={"tags": ["KITCHEN2-CO2"], "period": 30, "anomalies": True},
        timeout=120
    )
    
    if r.status_code != 200:
        print(f"❌ Ошибка: {r.status_code}")
        return
    
    data = r.json()
    anomalies = data.get('anomalies', {})
    
    total = anomalies.get('total_anomalies', 0)
    type_counts = anomalies.get('type_counts', {})
    indices = anomalies.get('anomaly_indices', [])
    values = anomalies.get('anomaly_values', [])
    types = anomalies.get('anomaly_types', [])
    timestamps = anomalies.get('anomaly_timestamps', [])
    
    print(f"Всего аномалий: {total}")
    print(f"По типам: {type_counts}")
    print()
    
    # 2. Распределение по датам
    print("【2】Распределение аномалий по датам")
    print("-" * 80)
    
    date_counts = defaultdict(lambda: {"spike": 0, "dip": 0, "drift": 0, "noise": 0, "total": 0})
    
    for ts, atype in zip(timestamps, types):
        date_str = ts.split('T')[0] if 'T' in ts else str(ts)[:10]
        date_counts[date_str][atype] += 1
        date_counts[date_str]["total"] += 1
    
    # Сортируем по датам
    sorted_dates = sorted(date_counts.keys())
    
    print(f"Дней с аномалиями: {len(sorted_dates)}")
    print(f"Период: {sorted_dates[0] if sorted_dates else 'N/A'} - {sorted_dates[-1] if sorted_dates else 'N/A'}")
    print()
    
    # Показываем последние 10 дней
    print("Последние 10 дней:")
    for date in sorted_dates[-10:]:
        counts = date_counts[date]
        total_day = counts["total"]
        print(f"  {date}: {total_day:3d} аномалий (spike:{counts['spike']}, dip:{counts['dip']}, drift:{counts['drift']}, noise:{counts['noise']})")
    
    print()
    
    # 3. Ищем пропуски — дни без аномалий
    print("【3】Поиск пропусков (дни без аномалий)")
    print("-" * 80)
    
    if sorted_dates:
        from datetime import timedelta
        
        first_date = datetime.strptime(sorted_dates[0], '%Y-%m-%d')
        last_date = datetime.strptime(sorted_dates[-1], '%Y-%m-%d')
        
        missing_days = []
        current = first_date
        while current <= last_date:
            date_str = current.strftime('%Y-%m-%d')
            if date_str not in date_counts:
                missing_days.append(date_str)
            current += timedelta(days=1)
        
        print(f"Дней без аномалий: {len(missing_days)}")
        if missing_days:
            print("Пропущенные дни:")
            for day in missing_days[:10]:
                print(f"  • {day}")
            if len(missing_days) > 10:
                print(f"  ... и ещё {len(missing_days) - 10}")
        print()
    
    # 4. Проверяем маппинг индексов
    print("【4】Проверка маппинга индексов")
    print("-" * 80)
    
    # Загружаем сырые данные
    from modules.deep_analysis.collectors.data_fetcher import fetch_tag_data
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    data = await fetch_tag_data('KITCHEN2-CO2', start_date, end_date)
    raw_values = data['raw_values']
    raw_timestamps = data['raw_timestamps']
    
    print(f"Сырых точек: {len(raw_values)}")
    print(f"Аномалий найдено: {len(indices)}")
    print(f"Максимальный индекс аномалии: {max(indices) if indices else 0}")
    print()
    
    # 5. Ищем явные пики которые не помечены
    print("【5】Поиск пропущенных пиков")
    print("-" * 80)
    
    # Вычисляем среднее и std
    valid_values = [v for v in raw_values if v is not None]
    mean_val = np.mean(valid_values)
    std_val = np.std(valid_values)
    
    print(f"Среднее: {mean_val:.2f}")
    print(f"Std: {std_val:.2f}")
    print(f"Порог пика (2 std): {mean_val + 2*std_val:.2f}")
    print(f"Порог провала (-2 std): {mean_val - 2*std_val:.2f}")
    print()
    
    # Ищем точки которые выглядят как аномалии, но не помечены
    anomaly_set = set(indices)
    missed_peaks = []
    missed_dips = []
    
    for i, (val, ts) in enumerate(zip(raw_values, raw_timestamps)):
        if val is None:
            continue
        
        # Проверяем пик
        if val > mean_val + 2.5 * std_val and i not in anomaly_set:
            missed_peaks.append((i, val, ts))
        
        # Проверяем провал
        if val < mean_val - 2.5 * std_val and i not in anomaly_set:
            missed_dips.append((i, val, ts))
    
    print(f"Пропущенных пиков (> 2.5 std): {len(missed_peaks)}")
    if missed_peaks:
        print("Примеры:")
        for idx, val, ts in missed_peaks[:5]:
            print(f"  #{idx} {ts} = {val:.2f}")
    print()
    
    print(f"Пропущенных провалов (< -2.5 std): {len(missed_dips)}")
    if missed_dips:
        print("Примеры:")
        for idx, val, ts in missed_dips[:5]:
            print(f"  #{idx} {ts} = {val:.2f}")
    print()
    
    # 6. Проверяем valid_indices маппинг
    print("【6】Проверка valid_indices маппинга")
    print("-" * 80)
    
    # Воспроизводим логику из anomalies.py
    valid_indices = [i for i, v in enumerate(raw_values) if v is not None]
    
    print(f"Всего точек: {len(raw_values)}")
    print(f"Валидных точек: {len(valid_indices)}")
    print(f"None/NaN точек: {len(raw_values) - len(valid_indices)}")
    print()
    
    # Проверяем последние 10 аномалий
    if indices:
        print("Последние 10 аномалий (проверка маппинга):")
        for anom_idx, val, atype, ts in zip(indices[-10:], values[-10:], types[-10:], timestamps[-10:]):
            # anom_idx — это индекс в valid_values
            # Проверяем что он в пределах
            if anom_idx < len(valid_indices):
                raw_idx = valid_indices[anom_idx]
                raw_val = raw_values[raw_idx]
                raw_ts = raw_timestamps[raw_idx]
                
                match = "✓" if abs(raw_val - val) < 0.01 else "✗"
                print(f"  {match} anom_idx={anom_idx}, raw_idx={raw_idx}, type={atype}, val={val:.2f}, raw_val={raw_val:.2f}")
            else:
                print(f"  ✗ anom_idx={anom_idx} ВНЕ ПРЕДЕЛОВ valid_indices (len={len(valid_indices)})")
        print()
    
    # 7. Итоговый отчёт
    print("=" * 80)
    print("ИТОГОВЫЙ ОТЧЁТ")
    print("=" * 80)
    print()
    
    issues = []
    
    if len(missing_days) > len(sorted_dates) * 0.3:
        issues.append(f"Много пропущенных дней: {len(missing_days)} из {len(sorted_dates) + len(missing_days)}")
    
    if len(missed_peaks) > 10:
        issues.append(f"Пропущено {len(missed_peaks)} явных пиков")
    
    if len(missed_dips) > 10:
        issues.append(f"Пропущено {len(missed_dips)} явных провалов")
    
    if indices and max(indices) >= len(valid_indices):
        issues.append(f"Индексы аномалий выходят за пределы valid_indices (max={max(indices)}, len={len(valid_indices)})")
    
    if issues:
        print("❌ НАЙДЕНЫ ПРОБЛЕМЫ:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
    else:
        print("✅ Явных проблем не найдено")
    
    print()
    print("=" * 80)

asyncio.run(diagnose())
'''

diag_path = Path('diagnose_anomalies_detailed.py')
diag_path.write_text(diag_script, encoding='utf-8', newline='\n')

print('✅ Создан diagnose_anomalies_detailed.py')
print()

print('=' * 80)
print('СЛЕДУЮЩИЕ ШАГИ:')
print('=' * 80)
print()
print('Запусти диагностику:')
print('  python diagnose_anomalies_detailed.py')
print()
print('Что покажет скрипт:')
print('  1. Скрытые лимиты в anomalies.py')
print('  2. Распределение аномалий по датам (где обрывается)')
print('  3. Дни без аномалий (пропуски)')
print('  4. Пропущенные пики/провалы (явные аномалии которые не помечены)')
print('  5. Проверка маппинга valid_indices → raw_indices')
print()
print('После этого я увижу КОРЕНЬ проблемы:')
print('  • Если много пропущенных дней → проблема с фильтрацией или downsampling')
print('  • Если пропущены явные пики → проблема с contamination или порогами')
print('  • Если индексы выходят за пределы → баг в маппинге valid_indices')
print()
print('Скинь вывод скрипта — дам точечный фикс!')