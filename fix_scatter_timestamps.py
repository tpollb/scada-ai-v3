#!/usr/bin/env python3
"""
fix_scatter_timestamps.py — финальный фикс с правильной нормализацией дат
"""
from pathlib import Path
import re

print('=' * 80)
print('ФИНАЛЬНЫЙ ФИКС: Правильная нормализация timestamp')
print('=' * 80)
print()

cs_path = Path('backend/modules/deep_analysis/visualizers/chart_specs.py')
content = cs_path.read_text(encoding='utf-8')

# 1. Проверяем текущее состояние
print('【1】Проверка использования timestamp-based маппинга')
print('-' * 80)

if 'ts_to_ds_idx' in content:
    print('✅ Найден ts_to_ds_idx — timestamp-based маппинг используется')
else:
    print('❌ ts_to_ds_idx НЕ НАЙДЕН — старый index-based маппинг!')
    
    # Показываем что там сейчас
    if 'idx_map' in content:
        print('   Найден idx_map — это старый bucket-based подход')
    if 'type_data = [None] * len(' in content:
        print('   Найден type_data = [None] * len(...) — старый подход')

print()

# 2. Показываем примеры форматов
print('【2】Примеры форматов дат')
print('-' * 80)

# Извлекаем примеры из тестового вывода
print('Формат timestamps (из anomalies):')
print('  2026-05-29T10:31:15  (ISO формат с T и секундами)')
print()
print('Формат labels (из графика):')
print('  2026-05-29 10:31     (пробел вместо T, без секунд)')
print()
print('Проблема: код искал точное совпадение строк, но форматы разные!')

print()

# 3. Полностью переписываем функцию create_time_series_spec
print('【3】Полная перезапись функции create_time_series_spec')
print('-' * 80)

new_func = '''def create_time_series_spec(
    timestamps: list[datetime],
    values: list[float],
    tag_name: str,
    anomalies: Optional[dict] = None,
    max_points: int = 3000,
) -> dict:
    """
    Создаёт JSON-спецификацию для time series графика с цветовой кодировкой аномалий.
    
    Применяет min-max downsampling к основному ряду для производительности.
    Аномалии (scatter points) правильно маппятся на downsampled данные через нормализованные timestamps.
    """
    from datetime import datetime
    
    # Downsampling основного ряда через min-max
    need_downsample = len(values) > max_points
    
    if need_downsample:
        ds_values, ds_timestamps = downsample_time_series(values, timestamps, max_points)
    else:
        ds_values = values
        ds_timestamps = timestamps
    
    # Форматируем labels в единый формат: "YYYY-MM-DD HH:MM"
    labels = []
    for ts in ds_timestamps:
        if isinstance(ts, datetime):
            labels.append(ts.strftime("%Y-%m-%d %H:%M"))
        else:
            # Если это строка — нормализуем формат
            ts_str = str(ts)
            # Заменяем T на пробел и обрезаем секунды
            ts_str = ts_str.replace('T', ' ')
            if len(ts_str) > 16:
                ts_str = ts_str[:16]
            labels.append(ts_str)
    
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
    
    # Если есть аномалии — добавляем scatter datasets по типам
    if anomalies and anomalies.get('anomaly_indices'):
        anomaly_types = anomalies.get('anomaly_types', [])
        anomaly_timestamps = anomalies.get('anomaly_timestamps', [])
        
        type_colors = {
            "spike": {"color": "#ef4444", "label": "Пики (Spike)"},
            "dip": {"color": "#3b82f6", "label": "Провалы (Dip)"},
            "drift": {"color": "#f59e0b", "label": "Дрейфы (Drift)"},
            "noise": {"color": "#9ca3af", "label": "Шум (Noise)"},
            "unknown": {"color": "#ef4444", "label": "Аномалии"},
        }
        
        # Группируем аномалии по типам
        anomalies_by_type = {}
        for idx, val, atype, ts in zip(
            anomalies['anomaly_indices'],
            anomalies['anomaly_values'],
            anomaly_types,
            anomaly_timestamps
        ):
            if atype not in anomalies_by_type:
                anomalies_by_type[atype] = []
            anomalies_by_type[atype].append((idx, val, ts))
        
        # Создаём маппинг: нормализованный timestamp → индекс в downsampled данных
        ts_to_ds_idx = {}
        for i, label in enumerate(labels):
            ts_to_ds_idx[label] = i
        
        for atype, points in anomalies_by_type.items():
            color_info = type_colors.get(atype, type_colors["unknown"])
            
            type_data = [None] * len(ds_values)
            
            # Для каждой аномалии нормализуем timestamp и находим индекс
            for orig_idx, val, orig_ts in points:
                # Нормализуем timestamp аномалии в формат "YYYY-MM-DD HH:MM"
                if isinstance(orig_ts, datetime):
                    ts_key = orig_ts.strftime("%Y-%m-%d %H:%M")
                else:
                    ts_str = str(orig_ts)
                    # Заменяем T на пробел
                    ts_str = ts_str.replace('T', ' ')
                    # Обрезаем секунды
                    if len(ts_str) > 16:
                        ts_str = ts_str[:16]
                    ts_key = ts_str
                
                # Ищем этот timestamp в downsampled данных
                if ts_key in ts_to_ds_idx:
                    ds_idx = ts_to_ds_idx[ts_key]
                    type_data[ds_idx] = val
                else:
                    # Если точного совпадения нет — ищем ближайший timestamp
                    # Это может быть из-за downsampling (точка попала в конец bucket'а)
                    try:
                        # Парсим timestamp аномалии
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
                        
                        # Если разница меньше 30 минут (1800 секунд) — используем этот индекс
                        if closest_idx is not None and min_diff < 1800:
                            type_data[closest_idx] = val
                    except Exception as e:
                        # Если парсинг не удался — пропускаем эту точку
                        pass
            
            # Дрейф рисуем ЛИНИЕЙ (пунктир), остальные — точками
            if atype == "drift":
                datasets.append({
                    "label": color_info["label"],
                    "data": type_data,
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
                    "data": type_data,
                    "borderColor": color_info["color"],
                    "backgroundColor": color_info["color"],
                    "type": "scatter",
                    "pointRadius": 6,
                    "pointHoverRadius": 8,
                    "showLine": False,
                })
    
    spec = {
        "type": "line",
        "data": {
            "labels": labels,
            "datasets": datasets,
        },
        "options": {
            "responsive": True,
            "maintainAspectRatio": False,
            "plugins": {
                "legend": {
                    "display": True,
                    "position": "top",
                    "labels": {"font": {"size": 11}, "boxWidth": 12},
                },
                "tooltip": {
                    "mode": "index",
                    "intersect": False,
                },
                "zoom": {
                    "pan": {"enabled": True, "mode": "x"},
                    "zoom": {
                        "wheel": {"enabled": True, "speed": 0.05},
                        "pinch": {"enabled": True},
                        "drag": {
                            "enabled": True,
                            "modifierKey": "shift",
                            "backgroundColor": "rgba(59, 130, 246, 0.1)",
                        },
                        "mode": "x",
                    },
                },
            },
            "scales": {
                "x": {
                    "display": True,
                    "grid": {"display": False},
                    "ticks": {"maxTicksLimit": 10, "font": {"size": 10}},
                },
                "y": {
                    "display": True,
                    "grid": {"color": "rgba(0, 0, 0, 0.05)"},
                    "ticks": {"font": {"size": 10}},
                },
            },
            "interaction": {
                "mode": "nearest",
                "axis": "x",
                "intersect": False,
            },
        },
    }
    
    return spec

'''

# Находим старую функцию
pattern = r'def create_time_series_spec\([^)]+\)[^:]*:.*?(?=\n\ndef |\nclass |\Z)'
match = re.search(pattern, content, re.DOTALL)

if match:
    old_func = match.group(0)
    content = content.replace(old_func, new_func)
    cs_path.write_text(content, encoding='utf-8', newline='\n')
    print('✅ Функция полностью перезаписана с правильной нормализацией дат')
else:
    print('❌ Не удалось найти функцию create_time_series_spec')
    exit(1)

print()
print('=' * 80)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 80)
print()
print('1. Нормализация форматов дат:')
print('   • Labels: "2026-05-29 10:31" (пробел, без секунд)')
print('   • Timestamps: "2026-05-29T10:31:15" → "2026-05-29 10:31"')
print('   • Код заменяет T на пробел и обрезает секунды')
print()
print('2. Правильный маппинг:')
print('   • ts_to_ds_idx = {"2026-05-29 10:31": 212, ...}')
print('   • Для каждой аномалии нормализуется timestamp')
print('   • Ищется в словаре → находится правильный индекс')
print()
print('3. Fallback логика:')
print('   • Если точного совпадения нет — ищет ближайший timestamp')
print('   • Допуск: 30 минут (1800 секунд)')
print('   • Это покрывает случаи когда downsampling "съедает" точку')
print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Перезапусти backend')
print()
print('2. Запусти диагностику:')
print('   python test_mapping_by_timestamp.py')
print()
print('3. Ожидаемый результат:')
print('   ✓ idx=  212, ts=2026-05-29 10:31, val=661.00 → chart_idx=212')
print('   (вместо "НЕ НАЙДЕНО В LABELS")')
print()
print('4. Точность должна быть ≥ 90%')
print()
print('5. Открой фронтенд → DDA → KITCHEN2-CO2 → анализ')
print('   • Точки аномалий должны быть НА правильных датах')
print('   • Наведи на точку — tooltip покажет правильную дату')