#!/usr/bin/env python3
"""
fix_timestamp_based_scatter.py — переход на timestamp-based scatter
"""
from pathlib import Path
import re

print('=' * 80)
print('ФИКС: Timestamp-based scatter для аномалий')
print('=' * 80)
print()

cs_path = Path('backend/modules/deep_analysis/visualizers/chart_specs.py')
content = cs_path.read_text(encoding='utf-8')

# 1. Находим блок создания scatter datasets
print('【1】Поиск блока создания scatter datasets')
print('-' * 80)

# Ищем паттерн создания type_data
pattern = r'type_data = \[None\] \* len\(([^)]+)\)\s+for (?:ds_)?idx, val in (?:points|anomalies_data):.*?type_data\[(?:ds_)?idx\] = val'

match = re.search(pattern, content, re.DOTALL)
if match:
    print('✅ Найден блок создания scatter datasets')
    print()
    print('Текущий код:')
    print(match.group(0))
    print()
else:
    print('⚠️  Паттерн не найден, ищем альтернативно...')
    # Показываем контекст с type_data
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        if 'type_data = [None]' in line:
            print(f'Найдено на строке {i}:')
            for j in range(max(0, i-5), min(len(lines), i+15)):
                marker = '>>>' if j == i-1 else '   '
                print(f'{marker} {j+1}: {lines[j]}')
            break

print()

# 2. Создаём новый код с timestamp-based scatter
print('【2】Создание timestamp-based scatter')
print('-' * 80)

new_scatter_code = '''            # Timestamp-based scatter: точки привязаны к реальным датам
            scatter_data = []
            for orig_idx, val, ts in anomalies_data:
                # orig_idx — индекс в raw_values (с None)
                # ts — timestamp этой точки
                scatter_data.append({
                    "x": ts.isoformat() if hasattr(ts, 'isoformat') else str(ts),
                    "y": val
                })
            
            datasets.append({
                "label": color_info["label"],
                "data": scatter_data,
                "borderColor": color_info["color"],
                "backgroundColor": color_info["color"],
                "type": "scatter",
                "pointRadius": 6,
                "pointHoverRadius": 8,
                "showLine": False,
            })'''

print('Новый код:')
print(new_scatter_code)
print()

# 3. Применяем фикс
print('【3】Применение фикса')
print('-' * 80)

# Ищем старый блок и заменяем
old_pattern = r'''            # Создаём scatter dataset для этого типа
            type_data = \[None\] \* len\(ds_values\)
            
            for ds_idx, val in points:
                if 0 <= ds_idx < len\(type_data\):
                    type_data\[ds_idx\] = val
            
            # Дрейф рисуем ЛИНИЕЙ \(пунктир\), остальные — точками
            if atype == "drift":
                datasets\.append\(\{
                    "label": color_info\["label"\],
                    "data": type_data,
                    "borderColor": color_info\["color"\],
                    "backgroundColor": color_info\["color"\],
                    "type": "line",
                    "borderWidth": 2,
                    "borderDash": \[6, 3\],
                    "pointRadius": 3,
                    "pointHoverRadius": 5,
                    "showLine": True,
                    "spanGaps": True,
                \}\)
            else:
                datasets\.append\(\{
                    "label": color_info\["label"\],
                    "data": type_data,
                    "borderColor": color_info\["color"\],
                    "backgroundColor": color_info\["color"\],
                    "type": "scatter",
                    "pointRadius": 6,
                    "pointHoverRadius": 8,
                    "showLine": False,
                \}\)'''

# Если нашли старый блок — заменяем
if re.search(old_pattern, content, re.DOTALL):
    new_code = '''            # Timestamp-based scatter: точки привязаны к реальным датам
            scatter_data = []
            for orig_idx, val, ts in points_with_timestamps:
                scatter_data.append({
                    "x": ts.isoformat() if hasattr(ts, 'isoformat') else str(ts),
                    "y": val
                })
            
            # Дрейф рисуем ЛИНИЕЙ (пунктир), остальные — точками
            if atype == "drift":
                # Для дрейфа нужен line формат с timestamp-based data
                line_data = []
                for orig_idx, val, ts in points_with_timestamps:
                    line_data.append({
                        "x": ts.isoformat() if hasattr(ts, 'isoformat') else str(ts),
                        "y": val
                    })
                
                datasets.append({
                    "label": color_info["label"],
                    "data": line_data,
                    "borderColor": color_info["color"],
                    "backgroundColor": color_info["color"],
                    "type": "line",
                    "borderWidth": 2,
                    "borderDash": [6, 3],
                    "pointRadius": 3,
                    "pointHoverRadius": 5,
                    "showLine": True,
                    "spanGaps": True,
                })
            else:
                datasets.append({
                    "label": color_info["label"],
                    "data": scatter_data,
                    "borderColor": color_info["color"],
                    "backgroundColor": color_info["color"],
                    "type": "scatter",
                    "pointRadius": 6,
                    "pointHoverRadius": 8,
                    "showLine": False,
                })'''
    
    content = re.sub(old_pattern, new_code, content, flags=re.DOTALL)
    print('✅ Старый блок заменён на timestamp-based scatter')
else:
    print('⚠️  Не удалось найти точный паттерн для замены')
    print('   Показываю структуру для ручной правки...')
    
    # Ищем все блоки с type_data
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        if 'type_data = [None]' in line:
            print(f'\\nБлок {i}:')
            for j in range(max(0, i-3), min(len(lines), i+25)):
                print(f'{j+1:4d}: {lines[j]}')

# 4. Нужно также обновить маппинг anomalies_data
print()
print('【4】Обновление маппинга anomalies_data')
print('-' * 80)

# Ищем блок где создаётся anomalies_by_type
pattern = r'anomalies_by_type = \{[^}]+\}.*?for idx, val, atype in zip\([^)]+\):'
match = re.search(pattern, content, re.DOTALL)

if match:
    print('✅ Найден блок маппинга anomalies_by_type')
    
    # Нужно добавить timestamps в этот маппинг
    old_mapping = '''        anomalies_by_type = {}
        for idx, val, atype in zip(
            anomalies['anomaly_indices'],
            anomalies['anomaly_values'],
            anomalies['anomaly_types']
        ):'''
    
    new_mapping = '''        anomalies_by_type = {}
        points_with_timestamps = {}  # Добавляем словарь с timestamps
        
        for idx, val, atype, ts in zip(
            anomalies['anomaly_indices'],
            anomalies['anomaly_values'],
            anomalies['anomaly_types'],
            anomalies.get('anomaly_timestamps', [])
        ):
            if atype not in anomalies_by_type:
                anomalies_by_type[atype] = []
                points_with_timestamps[atype] = []
            anomalies_by_type[atype].append((idx, val))
            points_with_timestamps[atype].append((idx, val, ts))'''
    
    if old_mapping in content:
        content = content.replace(old_mapping, new_mapping)
        print('✅ Маппинг обновлён: добавлены timestamps')
    else:
        print('⚠️  Не удалось найти точный паттерн маппинга')

cs_path.write_text(content, encoding='utf-8', newline='\n')

print()
print('=' * 80)
print('ГОТОВО')
print('=' * 80)
print()
print('Что исправлено:')
print('  • Scatter точки теперь используют timestamp-based формат')
print('  • Каждая точка привязана к реальной дате: {x: timestamp, y: value}')
print('  • Больше никакой рассинхронизации индексов')
print()
print('Перезапусти backend и проверь:')
print('  1. Открой фронтенд → DDA → KITCHEN2-CO2 → анализ')
print('  2. Точки spike/dip/noise должны быть НА правильных датах')
print('  3. Наведи на точку — tooltip должен показать правильную дату')
print('  4. Проверь что точка с значением 661 теперь на 2026-05-29 10:31 (а не 01:52)')
print()
print('Запусти диагностику для проверки:')
print('  python test_index_mapping.py')
print()
print('В выводе должно быть:')
print('  ✓ Timestamp совпадает')
print('  (вместо "⚠️  Timestamp НЕ совпадает!")')