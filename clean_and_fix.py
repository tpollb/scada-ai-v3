#!/usr/bin/env python3
"""
clean_and_fix.py — полный откат + одно правильное изменение
"""
import subprocess
from pathlib import Path

print('=' * 80)
print('ПОЛНЫЙ ОТКАТ + ОДНО ПРАВИЛЬНОЕ ИЗМЕНЕНИЕ')
print('=' * 80)
print()

# 1. Откатываем файл через git
print('【1】Откат файла через git restore')
print('-' * 80)
result = subprocess.run(
    ['git', 'restore', 'backend/modules/deep_analysis/visualizers/chart_specs.py'],
    capture_output=True,
    text=True,
    encoding='utf-8'
)
if result.returncode == 0:
    print('✅ Файл откачен к последнему коммиту')
else:
    print(f'❌ Ошибка: {result.stderr}')
    exit(1)

print()

# 2. Читаем чистый файл
print('【2】Читаем чистый файл')
print('-' * 80)
cs_path = Path('backend/modules/deep_analysis/visualizers/chart_specs.py')
content = cs_path.read_text(encoding='utf-8')
print(f'✅ Файл прочитан ({len(content)} символов)')

print()

# 3. Добавляем apply_timezone в начало файла
print('【3】Добавляем apply_timezone в начало файла')
print('-' * 80)

old_header = '''"""Создание JSON-спецификаций для графиков Chart.js"""
from typing import Optional
from datetime import datetime
import numpy as np
from structlog import get_logger

log = get_logger()'''

new_header = '''"""Создание JSON-спецификаций для графиков Chart.js"""
from typing import Optional
from datetime import datetime, timezone
import numpy as np
from structlog import get_logger
from config.settings import settings

log = get_logger()

# Получаем таймзону из конфига
try:
    import pytz
    LOCAL_TZ = pytz.timezone(settings.timezone)
except Exception:
    LOCAL_TZ = timezone.utc


def apply_timezone(ts):
    """Применяет локальную таймзону к timestamp."""
    if isinstance(ts, datetime):
        if ts.tzinfo is None:
            try:
                return LOCAL_TZ.localize(ts)
            except Exception:
                return ts
        else:
            try:
                return ts.astimezone(LOCAL_TZ)
            except Exception:
                return ts
    return ts'''

if old_header in content:
    content = content.replace(old_header, new_header)
    print('✅ apply_timezone добавлена')
else:
    print('⚠️  Заголовок не найден в ожидаемом виде')

print()

# 4. Заменяем create_multitag_time_series_spec на простую версию
print('【4】Заменяем create_multitag_time_series_spec')
print('-' * 80)

import re

# Находим функцию
pattern = r'def create_multitag_time_series_spec\(.*?\n(?=\n\ndef |\Z)'
match = re.search(pattern, content, re.DOTALL)

if match:
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
    
    content = content.replace(old_func, new_func)
    print('✅ create_multitag_time_series_spec заменена на простую версию')
else:
    print('❌ Функция не найдена')
    exit(1)

# 5. Сохраняем
print()
print('【5】Сохраняем файл')
print('-' * 80)
cs_path.write_text(content, encoding='utf-8', newline='\n')
print('✅ Файл сохранён')

print()

# 6. Проверяем что только одна функция
print('【6】Проверяем что только одна функция')
print('-' * 80)
count = len(list(re.finditer(r'^def create_multitag_time_series_spec\(', content, re.MULTILINE)))
print(f'Найдено функций create_multitag_time_series_spec: {count}')

if count == 1:
    print('✅ Только одна функция — всё правильно')
else:
    print(f'❌ Найдено {count} функций — что-то не так')

print()
print('=' * 80)
print('ГОТОВО')
print('=' * 80)
print()
print('Что сделано:')
print('  1. Файл откачен через git restore')
print('  2. Добавлена apply_timezone')
print('  3. create_multitag_time_series_spec заменена на простую версию')
print('  4. Проверено что только одна функция')
print()
print('Теперь multi-tag буквально вызывает create_time_series_spec N раз.')
print('Если single-tag работает — multi-tag работает.')
print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Backend перезагрузится сам')
print('2. Запусти анализ с 2+ тегами')
print('3. График должен быть на ВЕСЬ экран (как single-tag)')
print('4. Все аналитические точки должны быть на своих местах')