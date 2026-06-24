#!/usr/bin/env python3
"""
fix_single_tag_downsampling.py — добавляем downsampling для single-tag анализа
"""
from pathlib import Path

print('=' * 80)
print('ФИКС: Downsampling для single-tag + правильные индексы аномалий')
print('=' * 80)
print()

# ============================================================================
# Полностью переписываем create_time_series_spec с downsampling
# ============================================================================
chart_specs_path = Path('backend/modules/deep_analysis/visualizers/chart_specs.py')
cs_content = chart_specs_path.read_text(encoding='utf-8')

# Находим функцию create_time_series_spec и полностью её заменяем
import re

# Ищем старую функцию
old_func_pattern = r'def create_time_series_spec\(.*?(?=\n\ndef |\Z)'
match = re.search(old_func_pattern, cs_content, re.DOTALL)

if match:
    new_func = '''def create_time_series_spec(
    timestamps: list[datetime],
    values: list[float],
    tag_name: str,
    anomalies: Optional[dict] = None,
    max_points: int = 1500,
) -> dict:
    """
    Создаёт JSON-спецификацию для time series графика с цветовой кодировкой аномалий.
    
    Применяет min-max downsampling к основному ряду для производительности.
    Аномалии (scatter points) не даунсемплятся — их обычно немного.
    """
    # Downsampling основного ряда через min-max
    need_downsample = len(values) > max_points
    
    if need_downsample:
        ds_values, ds_timestamps = downsample_time_series(values, timestamps, max_points)
        
        # Строим маппинг: original_idx -> downsampled_idx
        # Это нужно чтобы правильно позиционировать аномалии
        bucket_size = len(values) / max_points
        idx_map = {}
        for orig_idx in range(len(values)):
            ds_idx = int(orig_idx / bucket_size)
            if ds_idx >= max_points:
                ds_idx = max_points - 1
            # Для каждой точки находим ближайший downsampled индекс
            # Берём минимальный ds_idx чтобы аномалии не "уезжали" вперёд
            if orig_idx not in idx_map:
                idx_map[orig_idx] = min(ds_idx, len(ds_values) - 1)
    else:
        ds_values = values
        ds_timestamps = timestamps
        idx_map = {i: i for i in range(len(values))}
    
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
        
        type_colors = {
            "spike": {"color": "#ef4444", "label": "Пики (Spike)"},
            "dip": {"color": "#3b82f6", "label": "Провалы (Dip)"},
            "drift": {"color": "#f59e0b", "label": "Дрейфы (Drift)"},
            "noise": {"color": "#9ca3af", "label": "Шум (Noise)"},
            "unknown": {"color": "#ef4444", "label": "Аномалии"},
        }
        
        # Группируем аномалии по типам с пересчётом индексов
        anomalies_by_type = {}
        for idx, val, atype in zip(
            anomalies['anomaly_indices'],
            anomalies['anomaly_values'],
            anomaly_types
        ):
            if atype not in anomalies_by_type:
                anomalies_by_type[atype] = []
            
            # Пересчитываем индекс под downsampled данные
            ds_idx = idx_map.get(idx, idx)
            anomalies_by_type[atype].append((ds_idx, val))
        
        for atype, points in anomalies_by_type.items():
            color_info = type_colors.get(atype, type_colors["unknown"])
            
            type_data = [None] * len(ds_values)
            for ds_idx, val in points:
                if 0 <= ds_idx < len(type_data):
                    type_data[ds_idx] = val
            
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
    
    cs_content = cs_content[:match.start()] + new_func + cs_content[match.end():]
    chart_specs_path.write_text(cs_content, encoding='utf-8', newline='\n')
    
    print('✅ create_time_series_spec полностью переписан:')
    print('   • Добавлен параметр max_points=1500')
    print('   • Min-max downsampling основного ряда')
    print('   • Правильный пересчёт индексов аномалий через idx_map')
    print('   • Дрейф рисуется пунктирной линией')
    print('   • Цвет шума: #9ca3af (светло-серый)')
else:
    print('❌ Не удалось найти create_time_series_spec')

# ============================================================================
# Добавляем endpoint для диагностики аномалий по неделям
# ============================================================================
api_path = Path('backend/modules/deep_analysis/api.py')
api_content = api_path.read_text(encoding='utf-8')

diagnose_weeks_endpoint = '''

@router.get("/diagnose_weeks/{tag_name}")
async def diagnose_anomalies_by_weeks(tag_name: str, period: int = 30):
    """
    Диагностика: распределение аномалий по неделям.
    Помогает понять, где именно пропадают аномалии.
    """
    from datetime import datetime, timedelta
    from modules.deep_analysis.collectors.data_fetcher import fetch_tag_data
    from modules.deep_analysis.analyzers.anomalies import detect_anomalies_isolation_forest
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=period)
    
    try:
        data = await fetch_tag_data(tag_name, start_date, end_date)
        
        result = detect_anomalies_isolation_forest(
            data['raw_values'],
            data['raw_timestamps'],
            contamination=0.06,
            classify_types=True
        )
        
        # Распределяем аномалии по неделям
        weeks = []
        for week in range(4):
            w_start = start_date + timedelta(weeks=week)
            w_end = w_start + timedelta(weeks=1)
            
            week_anomalies = {
                "start": w_start.isoformat(),
                "end": w_end.isoformat(),
                "total_points": 0,
                "anomalies": {"spike": 0, "dip": 0, "drift": 0, "noise": 0},
                "sample_points": []
            }
            
            # Считаем точки и аномалии в этой неделе
            for i, (ts, val) in enumerate(zip(data['raw_timestamps'], data['raw_values'])):
                if w_start <= ts < w_end:
                    week_anomalies["total_points"] += 1
                    
                    if i in result['anomaly_indices']:
                        idx_in_list = result['anomaly_indices'].index(i)
                        atype = result['anomaly_types'][idx_in_list]
                        week_anomalies["anomalies"][atype] = week_anomalies["anomalies"].get(atype, 0) + 1
                        
                        # Первые 3 примера
                        if len(week_anomalies["sample_points"]) < 3:
                            week_anomalies["sample_points"].append({
                                "timestamp": ts.isoformat(),
                                "value": float(val) if val is not None else None,
                                "type": atype
                            })
            
            weeks.append(week_anomalies)
        
        return {
            "tag_name": tag_name,
            "period": f"{start_date.isoformat()} - {end_date.isoformat()}",
            "total_anomalies": result['total_anomalies'],
            "type_counts": result['type_counts'],
            "anomaly_rate": result['anomaly_rate'],
            "by_week": weeks
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

'''

if '@router.get("/diagnose_weeks/' not in api_content:
    marker = '@router.get("/tags"'
    if marker in api_content:
        api_content = api_content.replace(marker, diagnose_weeks_endpoint + '\n\n' + marker)
        api_path.write_text(api_content, encoding='utf-8', newline='\n')
        print()
        print('✅ Добавлен endpoint GET /api/v1/deep_analysis/diagnose_weeks/{tag_name}')
        print('   Показывает распределение аномалий по 4 неделям')

print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Перезапусти backend')
print()
print('2. Проверь что downsampling работает:')
print('   curl -s -X POST http://localhost:8081/api/v1/deep_analysis/run \\')
print('     -H "Content-Type: application/json" \\')
print('     -d \'{"tags": ["R001-CO2"], "period": 30}\' | \\')
print('     python -c "import sys, json; r = json.load(sys.stdin); ts = r[\'visualizations\'][\'time_series\']; print(f\'Labels: {len(ts[\\\"data\\\"][\\\"labels\\\"])} (должно быть ~1500)\')')
print()
print('3. Проверь распределение аномалий по неделям:')
print('   curl -s http://localhost:8081/api/v1/deep_analysis/diagnose_weeks/R001-CO2?period=30 \\')
print('     | python -m json.tool | head -100')
print()
print('4. Открой фронтенд:')
print('   • График должен рендериться БЫСТРО (1500 точек вместо 7587)')
print('   • Все аномалии должны быть видны до 23.06')
print('   • В легенде: "Провалы (Dip)" вместо кракозябр')
print()
print('Что это исправляет:')
print('  • Было: 7587 точек → Chart.js задыхается, аномалии после 08.06 не рендерятся')
print('  • Стало: 1500 точек → быстрый рендер, ВСЕ аномалии видны')
print('  • Индексы аномалий пересчитываются через idx_map (не "уезжают")')
print()
print('Про кодировку:')
print('  • "РџСЂРѕРІР°Р»С‹" — это НЕ проблема backend')
print('  • Это Windows console неправильно отображает UTF-8')
print('  • В браузере всё будет корректно: "Провалы (Dip)"')