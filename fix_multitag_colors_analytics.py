#!/usr/bin/env python3
"""
fix_multitag_colors_analytics.py — чиним цвета и аналитику в multi-tag
"""
from pathlib import Path
import re

print('=' * 80)
print('ФИКС: Цвета линий + аналитика в multi-tag')
print('=' * 80)
print()

cs_path = Path('backend/modules/deep_analysis/visualizers/chart_specs.py')
content = cs_path.read_text(encoding='utf-8')

# Находим нашу простую функцию
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
        tag_anomalies = anomalies_per_tag.get(tag_name)

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
print('  1. tag_line_colors — разные цвета для линий тегов')
print('  2. anomaly_colors — ОДИНАКОВЫЕ цвета для аномалий всех тегов')
print('  3. Для каждого dataset:')
print('     • j==0 (линия тега): цвет из tag_line_colors')
print('     • j>0 (аномалия): цвет из anomaly_colors по типу')
print('  4. Убираем дублирование имени тега в label аномалии')
print()
print('Результат:')
print('  • Линия KITCHEN2-CO2: синяя (#3b82f6)')
print('  • Линия R001-CO2: зелёная (#10b981)')
print('  • Пики для ВСЕХ тегов: красные (#ef4444)')
print('  • Провалы для ВСЕХ тегов: синие (#3b82f6)')
print('  • И т.д.')
print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Backend перезагрузится сам')
print('2. Запусти анализ с 2+ тегами')
print('3. Должны быть:')
print('   • 2+ линии разных цветов')
print('   • Точки аномалий (пики/провалы/дрейфы/шум)')
print('   • Аномалии одного типа — одного цвета для всех тегов')
print('   • График на весь экран')