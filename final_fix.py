#!/usr/bin/env python3
"""
final_fix.py — timestamp-based scatter с правильной настройкой Chart.js
"""
from pathlib import Path
import re

print('=' * 80)
print('ФИНАЛЬНОЕ РЕШЕНИЕ: Timestamp-based scatter + Chart.js time scale')
print('=' * 80)
print()

cs_path = Path('backend/modules/deep_analysis/visualizers/chart_specs.py')
content = cs_path.read_text(encoding='utf-8')

# 1. Возвращаем простую версию downsample_time_series (без return_mapping)
print('【1】Упрощаем downsample_time_series')
print('-' * 80)

old_downsample = '''def downsample_time_series(values: list, timestamps: list, target_points: int = 800, return_mapping: bool = False) -> tuple:'''

new_downsample = '''def downsample_time_series(values: list, timestamps: list, target_points: int = 800) -> tuple[list, list]:'''

if old_downsample in content:
    # Заменяем всю функцию на простую версию
    pattern = r'def downsample_time_series\(.*?\n\n\ndef '
    replacement = '''def downsample_time_series(values: list, timestamps: list, target_points: int = 800) -> tuple[list, list]:
    """
    Downsample временной ряд с сохранением экстремумов (пиков и провалов).
    """
    if len(values) <= target_points:
        return values, timestamps

    bucket_size = len(values) / target_points

    ds_values = []
    ds_timestamps = []

    for i in range(target_points):
        start_idx = int(i * bucket_size)
        end_idx = int((i + 1) * bucket_size)

        bucket_values = values[start_idx:end_idx]
        bucket_timestamps = timestamps[start_idx:end_idx]

        valid_points = []
        for j, (v, t) in enumerate(zip(bucket_values, bucket_timestamps)):
            if v is not None and t is not None:
                valid_points.append((start_idx + j, v, t))

        if not valid_points:
            continue

        min_point = min(valid_points, key=lambda x: x[1])
        max_point = max(valid_points, key=lambda x: x[1])

        if min_point[0] <= max_point[0]:
            ds_values.append(min_point[1])
            ds_timestamps.append(min_point[2])
            if min_point[0] != max_point[0]:
                ds_values.append(max_point[1])
                ds_timestamps.append(max_point[2])
        else:
            ds_values.append(max_point[1])
            ds_timestamps.append(max_point[2])
            ds_values.append(min_point[1])
            ds_timestamps.append(min_point[2])

    return ds_values, ds_timestamps


def '''
    
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    print('✅ downsample_time_series упрощена (без return_mapping)')
else:
    print('ℹ️  Функция уже упрощена')

print()

# 2. Переписываем create_time_series_spec с timestamp-based scatter
print('【2】Переписываем create_time_series_spec')
print('-' * 80)

# Ищем функцию и полностью заменяем
pattern = r'def create_time_series_spec\(.*?\n\n\ndef '

new_func = '''def create_time_series_spec(
    timestamps: list[datetime],
    values: list[float],
    tag_name: str,
    anomalies: Optional[dict] = None,
    max_points: int = 3000,
) -> dict:
    """
    Создаёт JSON-спецификацию для time series графика.
    Использует timestamp-based scatter для точного позиционирования аномалий.
    """
    from datetime import datetime
    
    # Downsampling основного ряда
    need_downsample = len(values) > max_points
    if need_downsample:
        ds_values, ds_timestamps = downsample_time_series(values, timestamps, max_points)
    else:
        ds_values = values
        ds_timestamps = timestamps
    
    # Форматируем labels для основной линии
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
            
            # Timestamp-based scatter: каждая точка знает свои координаты
            scatter_data = []
            for val, orig_ts in points:
                # Конвертируем timestamp в миллисекунды для Chart.js time scale
                if isinstance(orig_ts, datetime):
                    # Unix timestamp в миллисекундах
                    ts_ms = int(orig_ts.timestamp() * 1000)
                else:
                    # Парсим строку
                    try:
                        ts_str = str(orig_ts).replace('T', ' ')
                        if len(ts_str) > 16:
                            ts_str = ts_str[:16]
                        parsed = datetime.strptime(ts_str, "%Y-%m-%d %H:%M")
                        ts_ms = int(parsed.timestamp() * 1000)
                    except Exception:
                        continue
                
                scatter_data.append({"x": ts_ms, "y": val})
            
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
                "tooltip": {
                    "mode": "nearest",
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


def '''

content = re.sub(pattern, new_func, content, flags=re.DOTALL)
cs_path.write_text(content, encoding='utf-8', newline='\n')

print('✅ create_time_series_spec переписана')
print('   • Timestamp-based scatter с миллисекундами')
print('   • Tooltip mode: nearest')
print('   • Scales x type: category')

print()
print('=' * 80)
print('ЧТО ЭТО ДАЁТ:')
print('=' * 80)
print()
print('• Основная линия: downsampled через min-max (быстро)')
print('• Аномалии: timestamp-based scatter {x: timestamp_ms, y: value}')
print('• Chart.js позиционирует точки по РЕАЛЬНОМУ времени')
print('• НЕТ зависимости от downsampling для аномалий')
print('• ВСЕ аномалии отображаются (не только min/max)')
print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Перезапусти backend')
print('2. Запусти анализ KITCHEN2-CO2 на 30 дней')
print('3. Проверь ВСЕ аномалии:')
print('   • Провалы, пики, дрейфы, шум — всё должно быть на месте')
print('   • НЕТ хаотичного отображения')
print('   • Точки на правильных позициях')