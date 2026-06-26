#!/usr/bin/env python3
"""
fix_multitag_final.py — index-based формат с правильным маппингом для multi-tag
"""
from pathlib import Path
import re

print('=' * 80)
print('ФИНАЛЬНЫЙ ФИКС: Index-based формат с правильным маппингом')
print('=' * 80)
print()

cs_path = Path('backend/modules/deep_analysis/visualizers/chart_specs.py')
content = cs_path.read_text(encoding='utf-8')

new_func = '''def create_multitag_time_series_spec(
    tags_data: dict,
    common_timestamps: list,
    anomalies_per_tag: dict = None,
    max_points: int = 3000,
) -> dict:
    """
    Создаёт time series spec для мульти-тег графика.

    ВСЕ датасеты (линии и scatter) используют index-based формат для корректной
    работы с Chart.js tooltip mode: 'index'.

    Ключевое: правильный маппинг timestamp → downsampled index.

    Args:
        tags_data: {tag_name: {"aligned_values": [...], ...}, ...}
        common_timestamps: общие timestamps
        anomalies_per_tag: {tag_name: {"anomaly_indices": [...], "anomaly_types": [...], ...}, ...}
        max_points: максимальное количество точек
    """
    from datetime import datetime

    datasets = []

    tag_colors = [
        "#3b82f6", "#10b981", "#f59e0b", "#ef4444",
        "#8b5cf6", "#ec4899", "#14b8a6", "#f97316",
    ]

    type_colors = {
        "spike": {"color": "#ef4444", "label": "Пики"},
        "dip": {"color": "#3b82f6", "label": "Провалы"},
        "drift": {"color": "#f59e0b", "label": "Дрейфы"},
        "noise": {"color": "#9ca3af", "label": "Шум"},
    }

    # Downsampling через равномерную выборку по индексам
    total_points = len(common_timestamps)
    need_downsample = total_points > max_points

    if need_downsample:
        step = max(1, total_points // max_points)
        ds_indices = list(range(0, total_points, step))[:max_points]
        ds_timestamps = [common_timestamps[i] for i in ds_indices]
    else:
        ds_indices = list(range(total_points))
        ds_timestamps = common_timestamps

    # Форматируем labels
    def format_ts(ts):
        if isinstance(ts, datetime):
            return ts.strftime("%Y-%m-%d %H:%M")
        ts_str = str(ts).replace('T', ' ')
        return ts_str[:16] if len(ts_str) > 16 else ts_str

    labels = [format_ts(ts) for ts in ds_timestamps]

    # Создаём маппинг: оригинальный timestamp → downsampled index
    # Это КЛЮЧЕВОЙ момент для правильного позиционирования точек
    orig_ts_to_ds_idx = {}
    for ds_idx, ds_ts in enumerate(ds_timestamps):
        orig_ts_to_ds_idx[ds_ts] = ds_idx

    # 1. Добавляем линии для каждого тега (index-based формат)
    for i, (tag_name, tag_data) in enumerate(tags_data.items()):
        aligned_values = tag_data.get('aligned_values', [])
        color = tag_colors[i % len(tag_colors)]

        # Downsample values для этого тега
        ds_values = [
            aligned_values[idx] if idx < len(aligned_values) else None
            for idx in ds_indices
        ]

        datasets.append({
            "label": tag_name,
            "data": ds_values,
            "borderColor": color,
            "backgroundColor": color,
            "type": "line",
            "borderWidth": 1.5,
            "pointRadius": 0,
            "pointHoverRadius": 4,
            "tension": 0.1,
            "fill": False,
        })

    # 2. Добавляем scatter points для аномалий (index-based формат)
    if anomalies_per_tag:
        # Группируем аномалии по (tag, type)
        anomalies_by_key = {}

        for tag_name, tag_anomalies in anomalies_per_tag.items():
            indices = tag_anomalies.get('anomaly_indices', [])
            types = tag_anomalies.get('anomaly_types', [])
            aligned_values = tags_data.get(tag_name, {}).get('aligned_values', [])

            for anom_idx, anom_type in zip(indices, types):
                if anom_idx >= len(common_timestamps) or anom_idx >= len(aligned_values):
                    continue

                value = aligned_values[anom_idx]
                if value is None:
                    continue

                anom_ts = common_timestamps[anom_idx]
                key = f"{tag_name}|{anom_type}"

                if key not in anomalies_by_key:
                    anomalies_by_key[key] = {
                        "tag": tag_name,
                        "type": anom_type,
                        "points": []
                    }
                anomalies_by_key[key]["points"].append((anom_ts, value))

        # Создаём scatter dataset для каждой группы (tag, type)
        for key, info in anomalies_by_key.items():
            atype = info["type"]
            tag_name = info["tag"]
            color_info = type_colors.get(atype, type_colors["noise"])

            # Index-based scatter: массив с None, значения только на нужных индексах
            type_data = [None] * len(ds_timestamps)

            for orig_ts, val in info["points"]:
                # Ищем downsampled index для этого timestamp
                if orig_ts in orig_ts_to_ds_idx:
                    ds_idx = orig_ts_to_ds_idx[orig_ts]
                    type_data[ds_idx] = val
                else:
                    # Fallback: ищем ближайший downsampled timestamp
                    try:
                        if isinstance(orig_ts, datetime):
                            orig_ts_dt = orig_ts
                        else:
                            ts_str = str(orig_ts).replace('T', ' ')[:16]
                            orig_ts_dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M")

                        min_diff = float('inf')
                        closest_idx = None

                        for ds_idx, ds_ts in enumerate(ds_timestamps):
                            if isinstance(ds_ts, datetime):
                                diff = abs((ds_ts - orig_ts_dt).total_seconds())
                                if diff < min_diff:
                                    min_diff = diff
                                    closest_idx = ds_idx

                        # Если разница меньше 30 минут — используем этот индекс
                        if closest_idx is not None and min_diff < 1800:
                            type_data[closest_idx] = val
                    except Exception:
                        pass

            label = f"{color_info['label']} ({tag_name})"

            # Все типы рисуем как scatter (точки)
            datasets.append({
                "label": label,
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
pattern = r'def create_multitag_time_series_spec\([^)]+\)[^:]*:.*?(?=\n\ndef |\nclass |\Z)'
match = re.search(pattern, content, re.DOTALL)

if match:
    old_func = match.group(0)
    print(f'✅ Старая функция найдена ({len(old_func.split(chr(10)))} строк)')
    content = content.replace(old_func, new_func)
    cs_path.write_text(content, encoding='utf-8', newline='\n')
    print('✅ Функция переписана на index-based формат')
else:
    print('❌ Функция create_multitag_time_series_spec не найдена')
    exit(1)

# Проверяем синтаксис
print()
print('【Проверка синтаксиса】')
print('-' * 80)
try:
    compile(content, str(cs_path), 'exec')
    print('✅ Синтаксис корректен!')
except SyntaxError as e:
    print(f'❌ Синтаксическая ошибка: {e}')
    exit(1)

print()
print('=' * 80)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 80)
print()
print('1. Index-based формат (не timestamp-based):')
print('   • Линии: [val1, val2, val3, ...]')
print('   • Scatter: [None, None, val, None, ...]')
print('   • Правильно работает с tooltip mode: "index"')
print()
print('2. Правильный маппинг timestamp → downsampled index:')
print('   • Создаём словарь: {оригинальный_ts: downsampled_idx}')
print('   • Для каждой аномалии находим ПРАВИЛЬНЫЙ downsampled index')
print('   • НЕТ "смещения на 5 единиц"')
print()
print('3. Fallback для пропущенных timestamps:')
print('   • Если точного совпадения нет — ищем ближайший (до 30 мин)')
print('   • Это покрывает случаи когда downsampling "съедает" точку')
print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Перезапусти backend')
print()
print('2. Запусти анализ с 2+ тегами')
print()
print('3. Проверь multi-tag график:')
print('   • Точки аномалий должны быть НА правильных местах (без смещения)')
print('   • При наведении мыши tooltip показывает только точки на этой X-координате')
print('   • НЕТ "случайных" точек в пустых местах')
print('   • Все типы аномалий — точки (не линии)')