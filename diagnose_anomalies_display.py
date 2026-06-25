#!/usr/bin/env python3
"""
diagnose_anomalies_display.py — диагностика отображения аномалий
"""
from pathlib import Path
import json
import sys

print('=' * 80)
print('ДИАГНОСТИКА: Отображение аномалий на графике')
print('=' * 80)
print()

# 1. Проверяем как работает downsampling в chart_specs.py
print('【1】Проверка downsampling логики')
print('-' * 80)

chart_specs_path = Path('backend/modules/deep_analysis/visualizers/chart_specs.py')
if chart_specs_path.exists():
    content = chart_specs_path.read_text(encoding='utf-8')
    
    # Ищем функцию downsample_time_series
    if 'def downsample_time_series' in content:
        print('✅ Функция downsample_time_series найдена')
        
        # Показываем ключевые части
        lines = content.split('\n')
        in_function = False
        function_lines = []
        
        for i, line in enumerate(lines):
            if 'def downsample_time_series' in line:
                in_function = True
            if in_function:
                function_lines.append(line)
                if line.strip() and not line.startswith(' ') and not line.startswith('\t') and 'def ' not in line:
                    break
                if len(function_lines) > 50:  # Ограничиваем вывод
                    break
        
        print('   Код функции (первые 30 строк):')
        for line in function_lines[:30]:
            print(f'   {line}')
    else:
        print('❌ Функция downsample_time_series НЕ найдена')
else:
    print('❌ chart_specs.py не найден')

print()

# 2. Проверяем как обрабатываются None/NaN в anomalies.py
print('【2】Проверка обработки None/NaN значений')
print('-' * 80)

anomalies_path = Path('backend/modules/deep_analysis/analyzers/anomalies.py')
if anomalies_path.exists():
    content = anomalies_path.read_text(encoding='utf-8')
    
    # Проверяем detect_anomalies_isolation_forest
    if 'def detect_anomalies_isolation_forest' in content:
        print('✅ Функция detect_anomalies_isolation_forest найдена')
        
        # Ищем обработку None
        if 'None' in content or 'np.nan' in content:
            print('✅ Упоминания None/NaN найдены')
            
            # Показываем контекст
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                if 'None' in line or 'np.nan' in line:
                    if 'valid_values' in line or 'values' in line:
                        print(f'   Строка {i}: {line.strip()}')
        else:
            print('⚠️  Обработка None/NaN не найдена')
    
    # Проверяем classify_anomaly_types
    if 'def classify_anomaly_types' in content:
        print('✅ Функция classify_anomaly_types найдена')
        
        # Ищем условия для drift
        if 'drift' in content:
            drift_lines = []
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                if 'drift' in line.lower() and ('duration' in line or 'r_squared' in line or 'monotonic' in line):
                    drift_lines.append((i, line.strip()))
            
            print(f'   Условия для drift ({len(drift_lines)} строк):')
            for line_no, line in drift_lines[:10]:
                print(f'   Строка {line_no}: {line}')
else:
    print('❌ anomalies.py не найден')

print()

# 3. Создаём тестовый скрипт для проверки downsampling
print('【3】Создание тестового скрипта')
print('-' * 80)

test_script = '''#!/usr/bin/env python3
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
'''

test_script_path = Path('test_downsampling.py')
test_script_path.write_text(test_script, encoding='utf-8', newline='\n')

print('✅ Создан test_downsampling.py')
print()

# 4. Создаём визуальный отчёт
print('【4】Создание визуального отчёта')
print('-' * 80)

report_script = '''#!/usr/bin/env python3
"""
generate_anomalies_report.py — генерация отчёта по аномалиям
"""
import sys
sys.path.insert(0, 'backend')

from modules.deep_analysis.analyzers.anomalies import detect_anomalies_isolation_forest
from modules.deep_analysis.collectors.data_fetcher import fetch_tag_data
from datetime import datetime, timedelta
import json

async def generate():
    print("Генерация отчёта по аномалиям...")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    data = await fetch_tag_data('KITCHEN2-CO2', start_date, end_date)
    raw_values = data['raw_values']
    raw_timestamps = data['raw_timestamps']
    
    # Фильтруем None
    valid_indices = [i for i, v in enumerate(raw_values) if v is not None]
    valid_values = [raw_values[i] for i in valid_indices]
    
    result = detect_anomalies_isolation_forest(
        valid_values,
        [raw_timestamps[i] for i in valid_indices],
        classify_types=True
    )
    
    # Формируем отчёт
    report = {
        'tag': 'KITCHEN2-CO2',
        'period': f"{start_date.isoformat()} - {end_date.isoformat()}",
        'total_points': len(raw_values),
        'valid_points': len(valid_values),
        'none_points': len(raw_values) - len(valid_values),
        'anomalies': {
            'total': result['total_anomalies'],
            'by_type': result['type_counts'],
            'rate': result['anomaly_rate']
        },
        'samples': {
            'spike': [],
            'dip': [],
            'drift': [],
            'noise': []
        }
    }
    
    # Берём примеры каждого типа
    for idx, val, atype, ts in zip(
        result['anomaly_indices'],
        result['anomaly_values'],
        result['anomaly_types'],
        result['anomaly_timestamps']
    ):
        if len(report['samples'][atype]) < 5:
            report['samples'][atype].append({
                'index': idx,
                'value': val,
                'timestamp': ts.isoformat(),
                'original_index': valid_indices[idx]
            })
    
    # Сохраняем
    with open('anomalies_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Отчёт сохранён: anomalies_report.json")
    print()
    print("Сводка:")
    print(f"  Всего точек: {report['total_points']}")
    print(f"  Валидных: {report['valid_points']}")
    print(f"  None: {report['none_points']}")
    print(f"  Аномалий: {report['anomalies']['total']} ({report['anomalies']['rate']:.2%})")
    print(f"  По типам: {report['anomalies']['by_type']}")

import asyncio
asyncio.run(generate())
'''

report_script_path = Path('generate_anomalies_report.py')
report_script_path.write_text(report_script, encoding='utf-8', newline='\n')

print('✅ Создан generate_anomalies_report.py')
print()

print('=' * 80)
print('СЛЕДУЮЩИЕ ШАГИ:')
print('=' * 80)
print()
print('1. Запусти тест downsampling:')
print('   python test_downsampling.py')
print()
print('2. Сгенерируй отчёт по аномалиям:')
print('   python generate_anomalies_report.py')
print()
print('3. Скинь вывод обоих скриптов — я увижу:')
print('   • Сколько None/NaN в данных')
print('   • Как downsampling влияет на значения')
print('   • Почему не детектируются дрейфы')
print('   • Примеры точек каждого типа')
print()
print('После этого создам фикс который:')
print('  • Правильно обрабатывает None/NaN')
print('  • Сохраняет аномалии при downsampling')
print('  • Улучшает детекцию дрейфов')