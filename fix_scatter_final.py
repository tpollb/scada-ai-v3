#!/usr/bin/env python3
"""
fix_scatter_final.py — полная перезапись функции создания scatter datasets
"""
from pathlib import Path
import re

print('=' * 80)
print('ФИНАЛЬНЫЙ ФИКС: Правильный маппинг scatter точек')
print('=' * 80)
print()

cs_path = Path('backend/modules/deep_analysis/visualizers/chart_specs.py')
content = cs_path.read_text(encoding='utf-8')

# 1. Проверяем текущее состояние
print('【1】Текущее состояние chart_specs.py')
print('-' * 80)

if 'type_data = [None] * len(' in content:
    print('  ❌ Найден старый паттерн type_data = [None] * len(...)')
    print('     Это БАГ — создаётся массив размером с labels, а не с аномалиями')
else:
    print('  ✓ Старый паттерн не найден')

print()

# 2. Находим функцию create_time_series_spec
print('【2】Поиск функции create_time_series_spec')
print('-' * 80)

# Ищем сигнатуру и тело функции
pattern = r'def create_time_series_spec\([^)]+\)[^:]*:.*?(?=\n\ndef |\nclass |\Z)'
match = re.search(pattern, content, re.DOTALL)

if match:
    old_func = match.group(0)
    print(f'  ✅ Функция найдена ({len(old_func.split(chr(10)))} строк)')
    
    # Показываем первые 50 строк
    lines = old_func.split('\n')[:50]
    print()
    print('  Первые 50 строк:')
    for i, line in enumerate(lines, 1):
        print(f'  {i:3d}: {line}')
else:
    print('  ❌ Функция не найдена')
    exit(1)

print()
print('【3】Создание новой функции с правильным маппингом')
print('-' * 80)

# Новая функция
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
    Аномалии (scatter points) правильно маппятся на downsampled данные по timestamp.
    """
    # Downsampling основного ряда через min-max
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
            labels.append(str(ts))
    
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
        
        # Создаём timestamp → index маппинг для downsampled данных
        ts_to_ds_idx = {}
        for i, ts in enumerate(ds_timestamps):
            if isinstance(ts, datetime):
                ts_key = ts.strftime("%Y-%m-%d %H:%M")
            else:
                ts_key = str(ts)
            ts_to_ds_idx[ts_key] = i
        
        for atype, points in anomalies_by_type.items():
            color_info = type_colors.get(atype, type_colors["unknown"])
            
            type_data = [None] * len(ds_values)
            
            # Для каждой аномалии находим соответствующий индекс в downsampled данных
            for orig_idx, val, orig_ts in points:
                # Форматируем timestamp аномалии
                if isinstance(orig_ts, datetime):
                    ts_key = orig_ts.strftime("%Y-%m-%d %H:%M")
                else:
                    ts_key = str(orig_ts)
                
                # Ищем этот timestamp в downsampled данных
                if ts_key in ts_to_ds_idx:
                    ds_idx = ts_to_ds_idx[ts_key]
                    type_data[ds_idx] = val
                else:
                    # Если точного совпадения нет — ищем ближайший timestamp
                    # (это может быть из-за downsampling)
                    try:
                        orig_ts_dt = datetime.fromisoformat(ts_key) if isinstance(ts_key, str) else orig_ts
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

# 3. Заменяем старую функцию на новую
print('Заменяю функцию...')
content = content.replace(old_func, new_func)

# 4. Сохраняем
cs_path.write_text(content, encoding='utf-8', newline='\n')
print('✅ Функция полностью перезаписана')

print()
print('=' * 80)
print('ЧТО ИЗМЕНИЛОСЬ:')
print('=' * 80)
print()
print('1. Правильный маппинг по timestamp:')
print('   • Создаётся словарь ts_to_ds_idx: {timestamp: downsampled_index}')
print('   • Для каждой аномалии находится соответствующий индекс в downsampled данных')
print()
print('2. Fallback для пропущенных точек:')
print('   • Если точного совпадения timestamp нет — ищем ближайший (до 30 минут)')
print('   • Это решает проблему когда downsampling "съедает" точку аномалии')
print()
print('3. Scatter точки теперь правильно позиционируются:')
print('   • Размер type_data = len(ds_values) (downsampled)')
print('   • Но индексы заполняются по timestamp, а не по orig_idx')
print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Перезапусти backend')
print()
print('2. Запусти диагностику:')
print('   python test_index_mapping.py')
print()
print('3. В выводе должно быть:')
print('   ✓ Timestamp совпадает')
print('   (вместо "⚠️  Timestamp НЕ совпадает!")')
print()
print('4. Открой фронтенд → DDA → KITCHEN2-CO2 → анализ')
print('   • Точки spike/dip/noise должны быть НА правильных датах')
print('   • Наведи на точку — tooltip должен показать правильную дату')
print('   • Проверь что точка с значением 661 теперь на 2026-05-29 10:31')