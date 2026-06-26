#!/usr/bin/env python3
"""
fix_multitag_anomalies_indices.py — преобразуем индексы аномалий
"""
from pathlib import Path
import re

print('=' * 80)
print('ФИКС: Индексы аномалий в multi-tag')
print('=' * 80)
print()

cs_path = Path('backend/modules/deep_analysis/visualizers/chart_specs.py')
content = cs_path.read_text(encoding='utf-8')

# Находим нашу функцию
pattern = r'def create_multitag_time_series_spec\(.*?\n(?=\n\ndef |\Z)'
match = re.search(pattern, content, re.DOTALL)

if not match:
    print('❌ Функция не найдена')
    exit(1)

old_func = match.group(0)

new_func = '''def create_multitag_time_series_spec(
    tags_data: dict,
    common_timestamps: list,
    anomalies_per_tag: dict = None,
    max_points: int = 3000,
) -> dict:
    """
    Multi-tag: просто вызываем create_time_series_spec для каждого тега.
    Если single-tag работает — повторяем его механизм.
    """
    if not anomalies_per_tag:
        anomalies_per_tag = {}

    all_datasets = []
    first_labels = None

    # Цвета для линий тегов
    tag_line_colors = [
        "#3b82f6", "#10b981", "#f59e0b", "#ef4444",
        "#8b5cf6", "#ec4899", "#14b8a6", "#f97316",
    ]

    # Цвета для аномалий (ОДИНАКОВЫЕ для всех тегов)
    anomaly_colors = {
        "spike": {"color": "#ef4444", "label": "Пики (Spike)"},
        "dip": {"color": "#3b82f6", "label": "Провалы (Dip)"},
        "drift": {"color": "#f59e0b", "label": "Дрейфы (Drift)"},
        "noise": {"color": "#9ca3af", "label": "Шум (Noise)"},
    }

    # Для каждого тега вызываем create_time_series_spec
    for i, (tag_name, tag_data) in enumerate(tags_data.items()):
        aligned_values = tag_data.get('aligned_values', [])
        tag_anomalies_raw = anomalies_per_tag.get(tag_name)

        # ВАЖНО: преобразуем индексы аномалий из valid_values в aligned_values
        # Потому что в API детекция идёт на отфильтрованных значениях
        tag_anomalies = None
        if tag_anomalies_raw and tag_anomalies_raw.get('anomaly_indices'):
            # Создаём маппинг: valid_idx → aligned_idx
            valid_idx = 0
            idx_map = {}
            for aligned_idx, v in enumerate(aligned_values):
                if v is not None:
                    idx_map[valid_idx] = aligned_idx
                    valid_idx += 1

            # Преобразуем индексы
            converted_indices = []
            converted_timestamps = []
            converted_values = []
            converted_types = []

            for anom_idx, anom_ts, anom_val, anom_type in zip(
                tag_anomalies_raw.get('anomaly_indices', []),
                tag_anomalies_raw.get('anomaly_timestamps', []),
                tag_anomalies_raw.get('anomaly_values', []),
                tag_anomalies_raw.get('anomaly_types', [])
            ):
                # Преобразуем индекс из valid_values в aligned_values
                aligned_idx = idx_map.get(anom_idx)
                if aligned_idx is not None and aligned_idx < len(aligned_values):
                    converted_indices.append(aligned_idx)
                    converted_timestamps.append(anom_ts)
                    converted_values.append(aligned_values[aligned_idx])
                    converted_types.append(anom_type)

            if converted_indices:
                tag_anomalies = {
                    'anomaly_indices': converted_indices,
                    'anomaly_timestamps': converted_timestamps,
                    'anomaly_values': converted_values,
                    'anomaly_types': converted_types,
                    'total_anomalies': len(converted_indices),
                }

        # Вызываем РАБОЧИЙ single-tag механизм
        tag_spec = create_time_series_spec(
            timestamps=common_timestamps,
            values=aligned_values,
            tag_name=tag_name,
            anomalies=tag_anomalies,
            max_points=max_points,
        )

        # Берём labels из первого тега
        if first_labels is None:
            first_labels = tag_spec['data']['labels']

        # Обрабатываем datasets
        for j, dataset in enumerate(tag_spec['data']['datasets']):
            if j == 0:
                # Первый dataset — основная линия тега: меняем цвет
                dataset['borderColor'] = tag_line_colors[i % len(tag_line_colors)]
                dataset['backgroundColor'] = tag_line_colors[i % len(tag_line_colors)]
                all_datasets.append(dataset)
            else:
                # Остальные — аномалии: используем общие цвета
                label = dataset.get('label', '')
                for atype, color_info in anomaly_colors.items():
                    if atype in label.lower() or color_info['label'] in label:
                        dataset['borderColor'] = color_info['color']
                        dataset['backgroundColor'] = color_info['color']
                        # Убираем имя тега из label аномалии чтобы не дублировать
                        if f"({tag_name})" in label:
                            dataset['label'] = color_info['label']
                        break
                all_datasets.append(dataset)

    if first_labels is None:
        first_labels = []

    return {
        "type": "line",
        "data": {
            "labels": first_labels,
            "datasets": all_datasets,
        },
        "options": {
            "responsive": True,
            "maintainAspectRatio": False,
            "plugins": {
                "legend": {
                    "display": True,
                    "position": "top",
                    "labels": {"font": {"size": 10}, "boxWidth": 10},
                },
                "tooltip": {
                    "mode": "index",
                    "intersect": False,
                },
            },
            "scales": {
                "x": {
                    "type": "category",
                    "display": True,
                    "ticks": {"maxTicksLimit": 10, "font": {"size": 9}},
                },
                "y": {
                    "display": True,
                    "grid": {"color": "rgba(0, 0, 0, 0.05)"},
                    "ticks": {"font": {"size": 9}},
                },
            },
        },
    }

'''

content = content.replace(old_func, new_func)
cs_path.write_text(content, encoding='utf-8', newline='\n')

print('✅ create_multitag_time_series_spec обновлена')
print()
print('Что исправлено:')
print('  • В API детекция идёт на valid_values (без None)')
print('  • anomaly_indices — это индексы в valid_values')
print('  • Но create_time_series_spec ожидает индексы в aligned_values')
print()
print('  Теперь:')
print('  1. Создаём idx_map: {valid_idx: aligned_idx}')
print('  2. Для каждой аномалии: aligned_idx = idx_map[anom_idx]')
print('  3. Передаём преобразованные индексы в create_time_series_spec')
print()
print('Результат:')
print('  • Single-tag: работает (индексы уже правильные)')
print('  • Multi-tag: теперь тоже работает (индексы преобразованы)')
print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Backend перезагрузится сам')
print('2. Запусти анализ с 2+ тегами')
print('3. Должны появиться точки аномалий (пики/провалы/дрейфы/шум)')
print('4. Точки должны быть на правильных местах')