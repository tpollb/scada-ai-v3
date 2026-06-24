#!/usr/bin/env python3
"""
diagnose_db_and_limits.py — диагностика БД и SQL LIMIT
"""
from pathlib import Path
import re
import subprocess

print('=' * 80)
print('ДИАГНОСТИКА БД + SQL LIMIT + ДЕТАЛИ АНОМАЛИЙ')
print('=' * 80)
print()

# ============================================================================
# 1. Проверяем ВСЕ LIMIT в data_fetcher.py
# ============================================================================
print('【1】DATA_FETCHER.PY — ВСЕ вхождения LIMIT')
print('-' * 80)

fetcher_path = Path('backend/modules/deep_analysis/collectors/data_fetcher.py')
if fetcher_path.exists():
    content = fetcher_path.read_text(encoding='utf-8')
    lines = content.split('\n')
    
    limit_occurrences = []
    for i, line in enumerate(lines, 1):
        if 'LIMIT' in line.upper() and 'limit' not in line.split('#')[0].lower().replace('limit', ''):
            # Это SQL LIMIT, не Python-код
            if re.search(r'LIMIT\s+\d+', line, re.IGNORECASE):
                limit_occurrences.append((i, line.strip()))
    
    if limit_occurrences:
        print(f'  ❌ НАЙДЕНО {len(limit_occurrences)} SQL LIMIT:')
        for line_no, line in limit_occurrences:
            print(f'     Строка {line_no}: {line}')
    else:
        print('  ✅ SQL LIMIT не найден')
    
    # Ищем все SELECT запросы
    print()
    print('  SELECT запросы:')
    in_select = False
    select_lines = []
    for i, line in enumerate(lines, 1):
        if 'SELECT' in line.upper() and 'FROM' in '\n'.join(lines[i-1:min(i+15, len(lines))]).upper():
            in_select = True
            select_lines = []
        if in_select:
            select_lines.append((i, line))
            if 'ORDER BY' in line.upper() or 'LIMIT' in line.upper() or (line.strip() == '"""' and len(select_lines) > 5):
                # Конец запроса
                print(f'     Запрос начинается на строке {select_lines[0][0]}:')
                for ln, l in select_lines[-5:]:
                    print(f'       {ln}: {l}')
                print()
                in_select = False

# ============================================================================
# 2. Проверяем данные в БД после 08.06
# ============================================================================
print('【2】ПРЯМОЙ SQL К БД — проверка данных после 08.06')
print('-' * 80)

# Читаем параметры подключения из .env или settings
settings_path = Path('backend/config/settings.py')
db_url = None
if settings_path.exists():
    content = settings_path.read_text(encoding='utf-8')
    match = re.search(r'database_url\s*=\s*["\']([^"\']+)["\']', content)
    if match:
        db_url = match.group(1)
        print(f'  Database URL: {db_url[:50]}...' if len(db_url) > 50 else f'  Database URL: {db_url}')

# Читаем .env
env_path = Path('backend/.env')
if env_path.exists():
    env_content = env_path.read_text(encoding='utf-8')
    match = re.search(r'DATABASE_URL=["\']?([^"\'\n]+)["\']?', env_content)
    if match and not db_url:
        db_url = match.group(1)
        print(f'  Database URL (from .env): {db_url[:50]}...')

if db_url and 'postgresql' in db_url.lower():
    # Выполняем SQL запросы через psql или python
    print()
    print('  Выполняем проверочные SQL...')
    print()
    
    # Создаем Python скрипт для проверки
    check_script = f'''
import asyncio
import sys
sys.path.insert(0, 'backend')

async def check():
    try:
        from core.db import fetch, get_pool, init_pool
        from datetime import datetime, timedelta
        
        # Инициализируем пул
        await init_pool("{db_url}")
        
        # 1. Проверяем последнюю запись в БД
        rows = await fetch("""
            SELECT MAX(date_created) as last_ts, COUNT(*) as total
            FROM tags_value
            WHERE tag_id IN (SELECT tag_id FROM tags_dict WHERE tag_name = 'R001-CO2')
        """)
        print(f"  📊 R001-CO2:")
        print(f"     Последняя запись в БД: {{rows[0]['last_ts']}}")
        print(f"     Всего записей: {{rows[0]['total']}}")
        print()
        
        # 2. Проверяем данные по диапазонам
        ranges = [
            ('2026-05-01', '2026-05-15'),
            ('2026-05-15', '2026-06-01'),
            ('2026-06-01', '2026-06-15'),
            ('2026-06-15', '2026-06-24'),
        ]
        print('  📅 Распределение данных по диапазонам:')
        for start, end in ranges:
            rows = await fetch(f"""
                SELECT COUNT(*) as cnt
                FROM tags_value tv
                JOIN tags_dict td ON td.tag_id = tv.tag_id
                WHERE td.tag_name = 'R001-CO2'
                  AND tv.date_created >= '{start}'
                  AND tv.date_created < '{end}'
            """)
            print(f"     {{start}} — {{end}}: {{rows[0]['cnt']}} точек")
        print()
        
        # 3. Проверяем последние 10 записей
        rows = await fetch("""
            SELECT date_created, value
            FROM tags_value tv
            JOIN tags_dict td ON td.tag_id = tv.tag_id
            WHERE td.tag_name = 'R001-CO2'
            ORDER BY date_created DESC
            LIMIT 10
        """)
        print('  🕒 Последние 10 записей:')
        for r in rows:
            print(f"     {{r['date_created']}} → {{r['value']}}")
        
        await get_pool().close()
    except Exception as e:
        print(f"  ❌ Ошибка: {{e}}")
        import traceback
        traceback.print_exc()

asyncio.run(check())
'''
    
    try:
        result = subprocess.run(
            ['python', '-c', check_script],
            capture_output=True,
            text=True,
            timeout=30,
            cwd='.'
        )
        print(result.stdout)
        if result.stderr:
            print('  STDERR:', result.stderr[:500])
    except Exception as e:
        print(f'  ⚠️  Не удалось выполнить SQL: {e}')
else:
    print('  ⚠️  Не удалось получить DATABASE_URL')

# ============================================================================
# 3. Детальный анализ провалов для R001-CO2
# ============================================================================
print()
print('【3】ДЕТАЛЬНЫЙ АНАЛИЗ DIPS (R001-CO2)')
print('-' * 80)

check_anomalies_script = f'''
import asyncio
import sys
sys.path.insert(0, 'backend')

async def check():
    try:
        from modules.deep_analysis.collectors.data_fetcher import fetch_tag_data
        from modules.deep_analysis.analyzers.anomalies import (
            detect_anomalies_isolation_forest,
            detect_zero_dips,
            detect_significant_dips,
        )
        from datetime import datetime, timedelta
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        data = await fetch_tag_data('R001-CO2', start_date, end_date)
        print(f"  Всего точек: {{len(data['raw_values'])}}")
        print(f"  Первая: {{data['raw_timestamps'][0] if data['raw_timestamps'] else None}}")
        print(f"  Последняя: {{data['raw_timestamps'][-1] if data['raw_timestamps'] else None}}")
        print()
        
        # Zero dips
        zd = detect_zero_dips(data['raw_values'], data['raw_timestamps'])
        print(f"  Zero dips (падения в ноль):")
        print(f"     Событий: {{len(zd['events'])}}")
        print(f"     Точек: {{len(zd['anomaly_indices'])}}")
        for e in zd['events'][:5]:
            ts_start = data['raw_timestamps'][e['start_idx']] if e['start_idx'] < len(data['raw_timestamps']) else '?'
            ts_end = data['raw_timestamps'][e['end_idx']] if e['end_idx'] < len(data['raw_timestamps']) else '?'
            print(f"       {{ts_start}} — {{ts_end}} ({{e['duration']}} точек, min={{e['min_value']:.2f}})")
        print()
        
        # Significant dips
        sd = detect_significant_dips(data['raw_values'], data['raw_timestamps'], drop_ratio=0.30)
        print(f"  Significant dips (падения >30%):")
        print(f"     Событий: {{len(sd['events'])}}")
        print(f"     Точек: {{len(sd['anomaly_indices'])}}")
        for e in sd['events'][:10]:
            ts_start = data['raw_timestamps'][e['start_idx']] if e['start_idx'] < len(data['raw_timestamps']) else '?'
            ts_end = data['raw_timestamps'][e['end_idx']] if e['end_idx'] < len(data['raw_timestamps']) else '?'
            print(f"       {{ts_start}} — {{ts_end}} ({{e['duration']}} точек, drop={{e.get('drop_percent', 0)*100:.1f}}%)")
        print()
        
        # Общая детекция
        result = detect_anomalies_isolation_forest(
            data['raw_values'], data['raw_timestamps'],
            contamination=0.10, classify_types=True
        )
        print(f"  Итоговая классификация:")
        print(f"     {{result['type_counts']}}")
        
    except Exception as e:
        print(f"  ❌ Ошибка: {{e}}")
        import traceback
        traceback.print_exc()

asyncio.run(check())
'''

try:
    result = subprocess.run(
        ['python', '-c', check_anomalies_script],
        capture_output=True,
        text=True,
        timeout=60,
        cwd='.'
    )
    print(result.stdout)
    if result.stderr:
        print('  STDERR:', result.stderr[:1000])
except Exception as e:
    print(f'  ⚠️  Ошибка: {e}')

print()
print('=' * 80)
print('ЧТО ДЕЛАТЬ:')
print('=' * 80)
print()
print('После выполнения скрипта скинь ВЕСЬ вывод — я увижу:')
print('  1. Есть ли SQL LIMIT в data_fetcher.py')
print('  2. Есть ли данные в БД после 08.06')
print('  3. Что именно попадает в dips (с датами и значениями)')
print()
print('Возможные диагнозы:')
print('  • Если в БД нет данных после 08.06 — проблема НЕ в нашем коде')
print('     (SCADA перестала писать, или другой источник)')
print('  • Если SQL LIMIT найден — я дам точечный фикс')
print('  • Если все падения = significant_dips — снизим порог или уберем')