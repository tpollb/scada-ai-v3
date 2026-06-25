#!/usr/bin/env python3
"""
fix_chart_final.py — финальный фикс визуализации: единый index-based формат
"""
from pathlib import Path

print('=' * 80)
print('ФИНАЛЬНЫЙ ФИКС: Единый index-based формат для всех датасетов')
print('=' * 80)
print()

cs_path = Path('backend/modules/deep_analysis/visualizers/chart_specs.py')
content = cs_path.read_text(encoding='utf-8')

# Находим функцию create_time_series_spec и полностью переписываем её
new_func = '''def create_time_series_spec(
    timestamps: list[datetime],
    values: list[float],
    tag_name: str,
    anomalies: Optional[dict] = None,
    max_points: int = 3000,
) -> dict:
    """
    Создаёт JSON-спецификацию для time series графика.
    
    ВСЕ датасеты используют единый index-based формат для корректной работы
    с Chart.js category шкалой и tooltip mode: 'index'.
    """
    from datetime import datetime
    
    # Downsampling основного ряда
    need_downsample = len(values) > max_points
    if need_downsample:
        ds_values, ds_timestamps = downsample_time_series(values, timestamps, max_points)
    else:
        ds_values = values
        ds_timestamps = timestamps
    
    # Форматируем labels
    labels = []
    for ts in ds_timestamps:
        if isinstance(ts, datetime):
            labels.append(ts.strftime("%Y-%m-%d %H:%M"))
        else:
            ts_str = str(ts).replace('T', ' ')
            labels.append(ts_str[:16] if len(ts_str) > 16 else ts_str)
    
    # Создаём маппинг: timestamp → index в downsampled массиве
    ts_to_index = {}
    for idx, ts in enumerate(ds_timestamps):
        if isinstance(ts, datetime):
            ts_key = ts.strftime("%Y-%m-%d %H:%M")
        else:
            ts_str = str(ts).replace('T', ' ')
            ts_key = ts_str[:16] if len(ts_str) > 16 else ts_str
        ts_to_index[ts_key] = idx
    
    datasets = []
    
    # Основной ряд данных (index-based)
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
    
    # Index-based scatter для аномалий
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
            
            # Index-based scatter: массив с None, значения только на нужных индексах
            type_data = [None] * len(ds_values)
            
            for val, orig_ts in points:
                # Форматируем timestamp аномалии
                if isinstance(orig_ts, datetime):
                    ts_key = orig_ts.strftime("%Y-%m-%d %H:%M")
                else:
                    ts_str = str(orig_ts).replace('T', ' ')
                    ts_key = ts_str[:16] if len(ts_str) > 16 else ts_str
                
                # Ищем индекс в downsampled массиве
                if ts_key in ts_to_index:
                    ds_idx = ts_to_index[ts_key]
                    type_data[ds_idx] = val
                else:
                    # Если точного совпадения нет — ищем ближайший timestamp
                    try:
                        if isinstance(orig_ts, datetime):
                            orig_ts_dt = orig_ts
                        else:
                            ts_str = str(orig_ts).replace('T', ' ')
                            if len(ts_str) > 16:
                                ts_str = ts_str[:16]
                            orig_ts_dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M")
                        
                        min_diff = float('inf')
                        closest_idx = None
                        
                        for i, ds_ts in enumerate(ds_timestamps):
                            if isinstance(ds_ts, datetime):
                                diff = abs((ds_ts - orig_ts_dt).total_seconds())
                                if diff < min_diff:
                                    min_diff = diff
                                    closest_idx = i
                        
                        # Если разница меньше 30 минут — используем этот индекс
                        if closest_idx is not None and min_diff < 1800:
                            type_data[closest_idx] = val
                    except Exception:
                        pass
            
            # Все типы рисуем как scatter (точки)
            datasets.append({
                "label": color_info["label"],
                "data": type_data,
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
                "tooltip": {
                    "mode": "index",
                    "intersect": False,
                },
            },
            "scales": {
                "x": {
                    "type": "category",
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

# Находим старую функцию
import re
pattern = r'def create_time_series_spec\([^)]+\)[^:]*:.*?(?=\n\ndef |\nclass |\Z)'
match = re.search(pattern, content, re.DOTALL)

if match:
    old_func = match.group(0)
    content = content.replace(old_func, new_func)
    cs_path.write_text(content, encoding='utf-8', newline='\n')
    print('✅ Функция create_time_series_spec полностью переписана')
    print()
    print('Что изменилось:')
    print('  • ВСЕ датасеты используют index-based формат')
    print('  • Scatter точки: [None, None, val, None, ...] вместо [{x, y}, ...]')
    print('  • Правильный маппинг timestamp → index в downsampled массиве')
    print('  • Tooltip mode: "index" теперь работает корректно')
    print('  • Category шкала X правильно отображает все точки')
else:
    print('❌ Не удалось найти функцию create_time_series_spec')
    exit(1)

print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Перезапусти backend')
print()
print('2. Открой фронтенд → DDA → KITCHEN2-CO2 → анализ')
print()
print('3. Проверь:')
print('   • Точки аномалий должны быть НА правильных местах')
print('   • При наведении мыши tooltip показывает правильные значения')
print('   • НЕТ "случайных" точек в пустых местах графика')
print('   • Значения в tooltip совпадают со значениями на графике')
print()
print('4. Конкретные тесты:')
print('   • 18.06 11:00-13:00 — не должно быть синих точек (провалов)')
print('   • Пики (красные) — только на реальных пиках графика')
print('   • Дрейфы (оранжевые) — должны быть видны')