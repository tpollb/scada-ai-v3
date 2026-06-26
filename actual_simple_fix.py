#!/usr/bin/env python3
"""
actual_simple_fix.py — ВЫЗЫВАЕМ create_time_series_spec для каждого тега
"""
from pathlib import Path

print('=' * 80)
print('ПРАВИЛЬНОЕ РЕШЕНИЕ: create_time_series_spec × N раз')
print('=' * 80)
print()

cs_path = Path('backend/modules/deep_analysis/visualizers/chart_specs.py')
content = cs_path.read_text(encoding='utf-8')

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
    Multi-tag: просто вызываем create_time_series_spec для каждого тега.
    Никакого своего downsampling — используем РАБОЧИЙ механизм single-tag.
    """
    if not anomalies_per_tag:
        anomalies_per_tag = {}

    all_datasets = []
    first_labels = None

    # Для каждого тега вызываем create_time_series_spec
    for tag_name, tag_data in tags_data.items():
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

        # Добавляем ВСЕ datasets из этого тега
        all_datasets.extend(tag_spec['data']['datasets'])

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
print('  for tag_name, tag_data in tags_data.items():')
print('      tag_spec = create_time_series_spec(...)  # РАБОЧИЙ механизм')
print('      all_datasets.extend(tag_spec["data"]["datasets"])')
print()
print('ВСЁ. Никакого своего downsampling, никакого своего маппинга.')
print('Просто вызываем create_time_series_spec N раз.')
print()
print('Если single-tag работает — multi-tag тоже работает.')