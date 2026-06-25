#!/usr/bin/env python3
"""
fix_scatter_timestamp_based.py — полная переработка на timestamp-based scatter
"""
from pathlib import Path
import re

print('=' * 80)
print('ФИНАЛЬНЫЙ ФИКС: Timestamp-based scatter (полная переработка)')
print('=' * 80)
print()

cs_path = Path('backend/modules/deep_analysis/visualizers/chart_specs.py')
content = cs_path.read_text(encoding='utf-8')

# Находим функцию create_time_series_spec и полностью переписываем её
pattern = r'def create_time_series_spec\([^)]+\)[^:]*:.*?(?=\n\ndef |\nclass |\Z)'
match = re.search(pattern, content, re.DOTALL)

if not match:
    print('❌ Функция create_time_series_spec не найдена')
    exit(1)

print('✅ Функция найдена, полностью переписываю...')
print()

new_func = '''def create_time_series_spec(
    timestamps: list[datetime],
    values: list[float],
    tag_name: str,
    anomalies: Optional[dict] = None,
    max_points: int = 3000,
) -> dict:
    """
    Создаёт JSON-спецификацию для time series графика.
    
    Основной ряд: downsampled массив (min-max) для производительности.
    Аномалии: timestamp-based scatter {x: timestamp, y: value} для точного позиционирования.
    
    Это решает проблему рассинхронизации значений между scatter точками
    и downsampled линией графика.
    """
    from datetime import datetime
    
    # Downsampling основного ряда
    need_downsample = len(values) > max_points
    if need_downsample:
        ds_values, ds_timestamps = downsample_time_series(values, timestamps, max_points)
    else:
        ds_values = values
        ds_timestamps = timestamps
    
    # Форматируем labels в формате "YYYY-MM-DD HH:MM"
    labels = []
    for ts in ds_timestamps:
        if isinstance(ts, datetime):
            labels.append(ts.strftime("%Y-%m-%d %H:%M"))
        else:
            ts_str = str(ts).replace('T', ' ')
            labels.append(ts_str[:16] if len(ts_str) > 16 else ts_str)
    
    datasets = []
    
    # Основной ряд данных (downsampled)
    datasets.append({
        "label": tag_name,
        "data": ds_values,
        "borderColor": "#3b82f6",
        "backgroundColor": "rgba(59, 130, 246, 0.1)",
        "borderWidth": 1.5,
        "pointRadius": 0,
        "pointHoverRadius": 3,
        "tension": 0.1,
        "fill": False,
    })
    
    # Timestamp-based scatter для аномалий
    if anomalies and anomalies.get('anomaly_indices'):
        anomaly_types_list = anomalies.get('anomaly_types', [])
        anomaly_timestamps = anomalies.get('anomaly_timestamps', [])
        anomaly_values = anomalies.get('anomaly_values', [])
        
        type_colors = {
            "spike": {"color": "#ef4444", "label": "Пики (Spike)"},
            "dip": {"color": "#3b82f6", "label": "Провалы (Dip)"},
            "drift": {"color": "#f59e0b", "label": "Дрейфы (Drift)"},
            "noise": {"color": "#9ca3af", "label": "Шум (Noise)"},
        }
        
        # Группируем аномалии по типам
        anomalies_by_type = {}
        for val, atype, ts in zip(anomaly_values, anomaly_types_list, anomaly_timestamps):
            if atype not in anomalies_by_type:
                anomalies_by_type[atype] = []
            anomalies_by_type[atype].append((val, ts))
        
        for atype, points in anomalies_by_type.items():
            color_info = type_colors.get(atype, type_colors.get("noise"))
            
            # Timestamp-based scatter: каждая точка сама знает свои координаты
            # Формат: [{x: "timestamp", y: value}, ...]
            scatter_data = []
            for val, orig_ts in points:
                # Форматируем timestamp в формат меток графика
                if isinstance(orig_ts, datetime):
                    ts_key = orig_ts.strftime("%Y-%m-%d %H:%M")
                else:
                    ts_str = str(orig_ts).replace('T', ' ')
                    ts_key = ts_str[:16] if len(ts_str) > 16 else ts_str
                
                scatter_data.append({"x": ts_key, "y": val})
            
            # Все типы рисуем как scatter (точки)
            datasets.append({
                "label": color_info["label"],
                "data": scatter_data,
                "borderColor": color_info["color"],
                "backgroundColor": color_info["color"],
                "type": "scatter",
                "pointRadius": 6,
                "pointHoverRadius": 8,
                "showLine": False,
            })
    
    return {
        "type": "line",
        "data": {
            "labels": labels,
            "datasets": datasets,
        },
        "options": {
            "responsive": True,
            "maintainAspectRatio": False,
            "plugins": {
                "legend": {"display": True, "position": "top"},
                "tooltip": {"mode": "index", "intersect": False},
            },
            "scales": {
                "x": {
                    "display": True,
                    "ticks": {"maxTicksLimit": 10},
                },
                "y": {
                    "display": True,
                },
            },
        },
    }

'''

# Заменяем старую функцию
content = content.replace(match.group(0), new_func)
cs_path.write_text(content, encoding='utf-8', newline='\n')

print('✅ Функция полностью переписана с timestamp-based scatter')
print()

# Проверяем синтаксис
print('【Проверка синтаксиса】')
print('-' * 80)
try:
    compile(content, str(cs_path), 'exec')
    print('✅ Синтаксис корректен!')
except SyntaxError as e:
    print(f'❌ Синтаксическая ошибка: {e}')
    print(f'   Строка {e.lineno}: {e.text}')
    exit(1)

print()
print('=' * 80)
print('ЧТО ЭТО РЕШАЕТ:')
print('=' * 80)
print()
print('Проблема:')
print('  • Min-max downsampling создаёт массив [min, max] для каждого bucket')
print('  • Scatter точка аномалии позиционировалась по timestamp правильно')
print('  • НО значение аномалии не совпадало со значением линии на том же индексе')
print('  • Пример: spike=723, но линия на этой позиции = 782 (max из bucket)')
print()
print('Решение:')
print('  • Timestamp-based scatter: [{x: "timestamp", y: value}, ...]')
print('  • Каждая точка САМА знает свои координаты X и Y')
print('  • Chart.js рисует точки в правильных местах независимо от downsampling')
print('  • Значения spike/dip/drift/noise теперь совпадают с оригинальными')
print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Перезапусти backend')
print()
print('2. Открой фронтенд → DDA → KITCHEN2-CO2 → анализ')
print()
print('3. Проверь визуально:')
print('   • Spike точки (красные) — на РЕАЛЬНЫХ пиках графика')
print('   • Dip точки (синие) — в РЕАЛЬНЫХ провалах графика')
print('   • Наведи на точку — tooltip покажет правильное значение')
print('   • Значение точки = значению на графике в этой точке')
print()
print('4. Конкретные примеры:')
print('   • 10.06 10:32 — spike точка должна быть на 782 (а не 723)')
print('   • Провалы — должны быть на минимальных значениях (а не выше)')