#!/usr/bin/env python3
"""
simple_multitag_fix.py — используем create_time_series_spec для каждого тега
"""
from pathlib import Path

print('=' * 80)
print('ПРОСТОЕ РЕШЕНИЕ: Повторяем create_time_series_spec для каждого тега')
print('=' * 80)
print()

cs_path = Path('backend/modules/deep_analysis/visualizers/chart_specs.py')
content = cs_path.read_text(encoding='utf-8')

# Находим функцию create_multitag_time_series_spec и полностью заменяем
import re

old_func_start = 'def create_multitag_time_series_spec('
old_func_end = '\n\n\ndef create_histogram_spec('

start_idx = content.find(old_func_start)
end_idx = content.find(old_func_end)

if start_idx == -1 or end_idx == -1:
    print('❌ Не удалось найти функцию')
    exit(1)

new_func = '''def create_multitag_time_series_spec(
    tags_data: dict,
    common_timestamps: list,
    anomalies_per_tag: dict = None,
    max_points: int = 3000,
) -> dict:
    """
    Multi-tag time series: просто вызываем create_time_series_spec для каждого тега.
    Если single-tag работает — повторяем его механизм.
    """
    if not anomalies_per_tag:
        anomalies_per_tag = {}

    all_datasets = []
    first_labels = None

    tag_colors = [
        "#3b82f6", "#10b981", "#f59e0b", "#ef4444",
        "#8b5cf6", "#ec4899", "#14b8a6", "#f97316",
    ]

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

        # Берём labels из первого тега (они должны быть одинаковые)
        if first_labels is None:
            first_labels = tag_spec['data']['labels']

        # Добавляем все datasets с правильным цветом
        for j, dataset in enumerate(tag_spec['data']['datasets']):
            # Первый dataset — основная линия (меняем цвет)
            if j == 0:
                color = tag_colors[i % len(tag_colors)]
                dataset['borderColor'] = color
                dataset['backgroundColor'] = color
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

content = content[:start_idx] + new_func + content[end_idx:]
cs_path.write_text(content, encoding='utf-8', newline='\n')

print('✅ create_multitag_time_series_spec переписана')
print()
print('Что сделано:')
print('  • Для каждого тега вызываем create_time_series_spec')
print('  • Single-tag механизм работает — повторяем его')
print('  • Объединяем datasets из всех тегов')
print('  • Labels берём из первого тега')
print()
print('Преимущества:')
print('  • НЕТ отдельной сложной логики multi-tag')
print('  • Используется РАБОЧИЙ механизм single-tag')
print('  • НЕТ рассинхрона (каждый тег downsample правильно)')
print('  • НЕТ проблем с маппингом (single-tag уже работает)')
print('  • Код проще в 10 раз')
print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Backend перезагрузится сам')
print('2. Запусти анализ с 2+ тегами')
print('3. Должно работать точно как single-tag, но с несколькими линиями')