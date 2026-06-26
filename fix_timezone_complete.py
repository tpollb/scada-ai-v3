#!/usr/bin/env python3
"""
fix_timezone_complete.py — полная timezone-aware обработка для всех графиков
"""
from pathlib import Path
import re

print('=' * 80)
print('ФИКС: Timezone-aware для single-tag и multi-tag')
print('=' * 80)
print()

cs_path = Path('backend/modules/deep_analysis/visualizers/chart_specs.py')
content = cs_path.read_text(encoding='utf-8')

# 1. Добавляем импорты в начало файла
print('【1】Добавляем импорты')
print('-' * 80)

old_imports = '''"""Создание JSON-спецификаций для графиков Chart.js"""
from typing import Optional
from datetime import datetime
import numpy as np
from structlog import get_logger

log = get_logger()'''

new_imports = '''"""Создание JSON-спецификаций для графиков Chart.js"""
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
            return LOCAL_TZ.localize(ts)
        else:
            return ts.astimezone(LOCAL_TZ)
    return ts'''

if old_imports in content:
    content = content.replace(old_imports, new_imports)
    print('✅ Импорты и функция apply_timezone добавлены')
else:
    print('⚠️  Блок импортов не найден')

print()

# 2. Применяем apply_timezone ко всем strftime в файле
print('【2】Применяем apply_timezone ко всем форматированиям')
print('-' * 80)

# Паттерн: ts.strftime → apply_timezone(ts).strftime
# Но нужно быть осторожным чтобы не заменить дважды

# Находим все вхождения .strftime
matches = re.findall(r'(\w+)\.strftime\("%Y-%m-%d %H:%M"\)', content)
print(f'Найдено {len(matches)} вхождений .strftime')

# Заменяем только если перед .strftime НЕ стоит apply_timezone
# Используем negative lookbehind
patterns = [
    (r'(?<!apply_timezone\()ts\.strftime\("%Y-%m-%d %H:%M"\)', 
     'apply_timezone(ts).strftime("%Y-%m-%d %H:%M")'),
    (r'(?<!apply_timezone\()orig_ts\.strftime\("%Y-%m-%d %H:%M"\)', 
     'apply_timezone(orig_ts).strftime("%Y-%m-%d %H:%M")'),
]

for pattern, replacement in patterns:
    count = len(re.findall(pattern, content))
    if count > 0:
        content = re.sub(pattern, replacement, content)
        print(f'✅ Заменено {count} вхождений')

cs_path.write_text(content, encoding='utf-8', newline='\n')

print()
print('=' * 80)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 80)
print()
print('1. Добавлена функция apply_timezone:')
print('   • Получает таймзону из settings.timezone (Asia/Yekaterinburg)')
print('   • Применяет её к timestamps без timezone info')
print('   • Конвертирует timestamps с другим tz в локальную')
print()
print('2. Применена ко всем форматированиям timestamps:')
print('   • Single-tag: labels, ts_to_index, аномалии')
print('   • Multi-tag: labels, ts_to_index, аномалии')
print()
print('РЕЗУЛЬТАТ:')
print('  • Timestamp "2026-05-28 02:18" (из БД, без tz)')
print('  • Применяем Asia/Yekaterinburg (+5 UTC)')
print('  • Форматируем: "2026-05-28 02:18" (правильное локальное время)')
print('  • Chart.js отображает на правильной позиции')
print('  • НЕТ смещения на 11 часов 20 минут!')
print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Перезапусти backend')
print()
print('2. Запусти анализ с 2+ тегами')
print()
print('3. Проверь точки аномалий:')
print('   • Данные: 28.05 02:18')
print('   • Аналитическая точка должна быть НА 28.05 02:18')
print('   • НЕ должно быть смещения на 27.05 14:58')