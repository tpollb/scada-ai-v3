#!/usr/bin/env python3
"""
fix_multitag_chart.py — применяет timestamp-based маппинг к multi-tag графику
"""
from pathlib import Path
import re

print('=' * 80)
print('ФИКС: Timestamp-based маппинг для multi-tag графика')
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
    Создаёт time series spec для мульти-тег графика с downsampling.

    Все датасеты (линии и scatter) используют timestamp-based формат {x: ts, y: val}
    для корректной работы с Chart.js tooltip mode: 'index'.

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

    # Downsampling через равномерную выборку по индексам (сохраняем маппинг)
    total_points = len(common_timestamps)
    need_downsample = total_points > max_points

    if need_downsample:
        step = max(1, total_points // max_points)
        ds_indices = list(range(0, total_points, step))[:max_points]
        ds_timestamps = [common_timestamps[i] for i in ds_indices]
    else:
        ds_indices = list(range(total_points))
        ds_timestamps = common_timestamps

    # Форматируем labels и создаём маппинг timestamp -> index
    def format_ts(ts):
        if isinstance(ts, datetime):
            return ts.strftime("%Y-%m-%d %H:%M")
        ts_str = str(ts).replace('T', ' ')
        return ts_str[:16] if len(ts_str) > 16 else ts_str

    labels = [format_ts(ts) for ts in ds_timestamps]
    ts_to_index = {label: i for i, label in enumerate(labels)}

    # 1. Добавляем линии для каждого тега (timestamp-based формат)
    for i, (tag_name, tag_data) in enumerate(tags_data.items()):
        aligned_values = tag_data.get('aligned_values', [])
        color = tag_colors[i % len(tag_colors)]

        # Downsample values для этого тега
        ds_values = [
            aligned_values[idx] if idx < len(aligned_values) else None
            for idx in ds_indices
        ]

        # Timestamp-based формат: [{x: ts, y: val}, ...]
        line_data = []
        for ts_label, val in zip(labels, ds_values):
            line_data.append({"x": ts_label, "y": val})

        datasets.append({
            "label": tag_name,
            "data": line_data,
            "borderColor": color,
            "backgroundColor": color,
            "type": "line",
            "borderWidth": 1.5,
            "pointRadius": 0,
            "pointHoverRadius": 4,
            "tension": 0.1,
            "fill": False,
        })

    # 2. Добавляем scatter points для аномалий (timestamp-based формат)
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
                anom_ts_key = format_ts(anom_ts)

                key = f"{tag_name}|{anom_type}"
                if key not in anomalies_by_key:
                    anomalies_by_key[key] = {
                        "tag": tag_name,
                        "type": anom_type,
                        "points": []
                    }
                anomalies_by_key[key]["points"].append((anom_ts_key, value, anom_ts))

        # Создаём scatter dataset для каждой группы (tag, type)
        for key, info in anomalies_by_key.items():
            atype = info["type"]
            tag_name = info["tag"]
            color_info = type_colors.get(atype, type_colors["noise"])

            scatter_data = []
            for ts_key, val, orig_ts in info["points"]:
                # Ищем ближайший downsampled timestamp если точного нет
                if ts_key in ts_to_index:
                    scatter_data.append({"x": ts_key, "y": val})
                else:
                    try:
                        if isinstance(orig_ts, datetime):
                            orig_ts_dt = orig_ts
                        else:
                            ts_str = str(orig_ts).replace('T', ' ')[:16]
                            orig_ts_dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M")

                        min_diff = float('inf')
                        closest_label = None

                        for i, ds_ts in enumerate(ds_timestamps):
                            if isinstance(ds_ts, datetime):
                                diff = abs((ds_ts - orig_ts_dt).total_seconds())
                                if diff < min_diff:
                                    min_diff = diff
                                    closest_label = labels[i]

                        if closest_label is not None and min_diff < 1800:
                            scatter_data.append({"x": closest_label, "y": val})
                    except Exception:
                        pass

            if not scatter_data:
                continue

            label = f"{color_info['label']} ({tag_name})"

            # Все типы рисуем как scatter (точки)
            datasets.append({
                "label": label,
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
    print('✅ Функция полностью переписана с timestamp-based маппингом')
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
print('1. Downsampling с сохранением маппинга:')
print('   • Равномерная выборка по индексам (не min-max)')
print('   • Сохраняем список ds_indices для последующего маппинга')
print()
print('2. Основные линии (каждый тег):')
print('   • Timestamp-based формат: [{x: ts, y: val}, ...]')
print('   • Каждая точка знает свою X-координату')
print()
print('3. Scatter аномалии:')
print('   • Timestamp-based формат: [{x: ts, y: val}, ...]')
print('   • Правильный маппинг через ts_to_index словарь')
print('   • Fallback: если точного совпадения нет — ищем ближайший (до 30 мин)')
print()
print('4. Все типы аномалий (включая drift) — scatter точки')
print('   • Нет "линии через весь график"')
print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Перезапусти backend')
print()
print('2. Запусти анализ с 2+ тегами (например, KITCHEN2-CO2 + R001-CO2)')
print()
print('3. Проверь multi-tag график:')
print('   • Точки аномалий должны быть НА правильных местах')
print('   • Tooltip показывает правильные значения')
print('   • НЕТ "случайных" точек в пустых местах')
print('   • Все типы аномалий — точки (не линии)')