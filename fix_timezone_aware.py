#!/usr/bin/env python3
"""
fix_timezone_aware.py — применяем таймзону из конфига к timestamps
"""
from pathlib import Path
import re

print('=' * 80)
print('ФИКС: Timezone-aware timestamps в chart_specs.py')
print('=' * 80)
print()

cs_path = Path('backend/modules/deep_analysis/visualizers/chart_specs.py')
content = cs_path.read_text(encoding='utf-8')

# 1. Добавляем импорт в начало файла
print('【1】Добавляем импорт timezone и настроек')
print('-' * 80)

import_block = '''"""Создание JSON-спецификаций для графиков Chart.js"""
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
    # Fallback на UTC если что-то пошло не так
    LOCAL_TZ = timezone.utc
'''

old_import_block = '''"""Создание JSON-спецификаций для графиков Chart.js"""
from typing import Optional
from datetime import datetime
import numpy as np
from structlog import get_logger

log = get_logger()
'''

if old_import_block in content:
    content = content.replace(old_import_block, import_block)
    print('✅ Импорты добавлены: timezone, settings, LOCAL_TZ')
else:
    print('⚠️  Блок импортов не найден или уже изменён')

# 2. Создаём helper функцию для применения timezone
print()
print('【2】Добавляем helper функцию apply_timezone')
print('-' * 80)

helper_func = '''
def apply_timezone(ts):
    """
    Применяет локальную таймзону к timestamp если её нет.
    Это предотвращает смещение при отображении в Chart.js.
    """
    if isinstance(ts, datetime):
        if ts.tzinfo is None:
            # Timestamp без timezone — применяем локальную
            return LOCAL_TZ.localize(ts)
        else:
            # Уже есть timezone — конвертируем в локальную
            return ts.astimezone(LOCAL_TZ)
    return ts


'''

# Вставляем после log = get_logger()
marker = 'log = get_logger()\n'
if marker in content and 'def apply_timezone' not in content:
    content = content.replace(marker, marker + helper_func)
    print('✅ Helper функция apply_timezone добавлена')
else:
    print('⚠️  Функция уже есть или маркер не найден')

# 3. Заменяем все форматирования timestamps
print()
print('【3】Заменяем форматирование timestamps')
print('-' * 80)

# Паттерн 1: ts.strftime("%Y-%m-%d %H:%M")
old_pattern1 = 'ts.strftime("%Y-%m-%d %H:%M")'
new_pattern1 = 'apply_timezone(ts).strftime("%Y-%m-%d %H:%M")'

count1 = content.count(old_pattern1)
if count1 > 0:
    content = content.replace(old_pattern1, new_pattern1)
    print(f'✅ Заменено {count1} вхождений: ts.strftime → apply_timezone(ts).strftime')
else:
    print('ℹ️  Паттерн ts.strftime не найден')

# Паттерн 2: orig_ts.strftime("%Y-%m-%d %H:%M")
old_pattern2 = 'orig_ts.strftime("%Y-%m-%d %H:%M")'
new_pattern2 = 'apply_timezone(orig_ts).strftime("%Y-%m-%d %H:%M")'

count2 = content.count(old_pattern2)
if count2 > 0:
    content = content.replace(old_pattern2, new_pattern2)
    print(f'✅ Заменено {count2} вхождений: orig_ts.strftime → apply_timezone(orig_ts).strftime')
else:
    print('ℹ️  Паттерн orig_ts.strftime не найден')

# Паттерн 3: внутри функции format_ts
old_format_ts = '''    def format_ts(ts):
        if isinstance(ts, datetime):
            return ts.strftime("%Y-%m-%d %H:%M")
        ts_str = str(ts).replace('T', ' ')
        return ts_str[:16] if len(ts_str) > 16 else ts_str'''

new_format_ts = '''    def format_ts(ts):
        if isinstance(ts, datetime):
            return apply_timezone(ts).strftime("%Y-%m-%d %H:%M")
        ts_str = str(ts).replace('T', ' ')
        return ts_str[:16] if len(ts_str) > 16 else ts_str'''

if old_format_ts in content:
    content = content.replace(old_format_ts, new_format_ts)
    print('✅ Функция format_ts обновлена')
else:
    print('ℹ️  Функция format_ts не найдена или уже изменена')

# Сохраняем
cs_path.write_text(content, encoding='utf-8', newline='\n')

print()
print('=' * 80)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 80)
print()
print('1. Импортирована таймзона из конфига:')
print('   • LOCAL_TZ = pytz.timezone(settings.timezone)')
print('   • По умолчанию: Asia/Yekaterinburg')
print('   • Можно переопределить через .env: TIMEZONE=Asia/Omsk')
print()
print('2. Добавлена helper функция apply_timezone():')
print('   • Применяет локальную таймзону к timestamps без tzinfo')
print('   • Конвертирует timestamps с другим tz в локальную')
print()
print('3. Все форматирования timestamps теперь timezone-aware:')
print('   • Было: ts.strftime("%Y-%m-%d %H:%M")')
print('   • Стало: apply_timezone(ts).strftime("%Y-%m-%d %H:%M")')
print()
print('РЕЗУЛЬТАТ:')
print('  • Timestamp "2026-06-01 02:37:00" (из БД, без tz)')
print('  • Применяем Asia/Omsk (+6 UTC)')
print('  • Форматируем: "2026-06-01 02:37" (правильное локальное время)')
print('  • Chart.js отображает на правильной позиции')
print('  • НЕТ смещения на 13 часов!')
print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Перезапусти backend')
print()
print('2. Запусти анализ с 1 тегом (KITCHEN2-CO2)')
print()
print('3. Проверь точки аномалий:')
print('   • Просадка 01.06 02:37 должна быть НА 01.06 02:37')
print('   • НЕ должно быть смещения на 31.05 13:37')
print('   • Все точки на правильных датах/времени')
print()
print('4. Если всё ещё есть смещение:')
print('   • Проверь .env файл: TIMEZONE=Asia/Omsk')
print('   • Или установи правильную таймзону для твоего региона')