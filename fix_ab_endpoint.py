#!/usr/bin/env python3
"""
fix_ab_endpoint.py - исправляет endpoint A/B анализа
"""
from pathlib import Path

print('=' * 80)
print('ИСПРАВЛЕНИЕ: Endpoint A/B анализа')
print('=' * 80)
print()

api_path = Path('backend/modules/deep_analysis/api.py')
content = api_path.read_text(encoding='utf-8')

# 1. Проверяем импорты
print('【1】Проверяем импорты')
print('-' * 80)

imports_to_check = [
    ('from fastapi import', 'Request'),
    ('from datetime import', 'datetime'),
    ('from modules.deep_analysis.collectors.data_fetcher import', 'fetch_multiple_tags')
]

for import_line, import_name in imports_to_check:
    if import_name not in content:
        # Добавляем импорт
        if import_line in content:
            # Расширяем существующий импорт
            old_import = [line for line in content.split('\n') if line.startswith(import_line)][0]
            new_import = old_import.rstrip() + f', {import_name}'
            content = content.replace(old_import, new_import)
            print(f'✅ Добавлен импорт: {import_name}')
        else:
            # Добавляем новую строку импорта
            if 'from fastapi' in import_line:
                # Ищем последнюю строку с from fastapi
                lines = content.split('\n')
                insert_pos = 0
                for i, line in enumerate(lines):
                    if line.startswith('from fastapi'):
                        insert_pos = i + 1
                lines.insert(insert_pos, f'{import_line} {import_name}')
                content = '\n'.join(lines)
                print(f'✅ Добавлена строка импорта: {import_line} {import_name}')
    else:
        print(f'ℹ️  Импорт уже есть: {import_name}')

# 2. Удаляем старый endpoint если он был добавлен
print()
print('【2】Удаляем старый endpoint (если есть)')
print('-' * 80)

if '@app.post("/deep-analysis/ab"' in content:
    # Находим начало и конец старого endpoint
    lines = content.split('\n')
    start_idx = None
    end_idx = None
    
    for i, line in enumerate(lines):
        if '@app.post("/deep-analysis/ab"' in line:
            start_idx = i
        if start_idx and line.strip().startswith('async def ab_analysis'):
            # Ищем конец функции (следующая функция или конец файла)
            for j in range(i + 1, len(lines)):
                if lines[j].startswith('@') or lines[j].startswith('def '):
                    end_idx = j
                    break
            if end_idx is None:
                end_idx = len(lines)
            break
    
    if start_idx is not None:
        del lines[start_idx:end_idx]
        content = '\n'.join(lines)
        print(f'✅ Удалён старый endpoint (строки {start_idx}-{end_idx})')
else:
    print('ℹ️  Старый endpoint не найден')

# 3. Добавляем правильный endpoint
print()
print('【3】Добавляем правильный endpoint')
print('-' * 80)

ab_endpoint = '''

@router.post("/ab")
async def ab_analysis(request: Request):
    """
    A/B анализ: сравнение двух временных периодов или двух тегов.
    
    Modes:
    - before_after: один тег в разные периоды (snapshot_a.tag == snapshot_b.tag)
    - equipment_comparison: два тега в один период (snapshot_a.tag != snapshot_b.tag)
    """
    from modules.deep_analysis.analyzers.ab import (
        compare_snapshots,
        compare_patterns,
        generate_verdict
    )
    
    body = await request.json()
    
    snapshot_a = body.get('snapshot_a', {})
    snapshot_b = body.get('snapshot_b', {})
    
    tag_a = snapshot_a.get('tag')
    tag_b = snapshot_b.get('tag')
    start_a = datetime.fromisoformat(snapshot_a.get('start'))
    end_a = datetime.fromisoformat(snapshot_a.get('end'))
    start_b = datetime.fromisoformat(snapshot_b.get('start'))
    end_b = datetime.fromisoformat(snapshot_b.get('end'))
    
    log.info(
        "A/B analysis request",
        tag_a=tag_a,
        tag_b=tag_b,
        period_a=f"{start_a} - {end_a}",
        period_b=f"{start_b} - {end_b}"
    )
    
    # Определяем режим
    mode = "before_after" if tag_a == tag_b else "equipment_comparison"
    
    # Получаем данные
    data_a = await fetch_multiple_tags([tag_a], start_a, end_a)
    data_b = await fetch_multiple_tags([tag_b], start_b, end_b)
    
    values_a = data_a['tags'][tag_a]['values']
    values_b = data_b['tags'][tag_b]['values']
    
    # Базовое сравнение
    comparison = compare_snapshots(values_a, values_b)
    
    # Сравнение паттернов (опционально, если достаточно данных)
    pattern_comparison = None
    if len(values_a) >= 288 and len(values_b) >= 288:  # минимум 24 часа данных
        pattern_comparison = compare_patterns(values_a, values_b)
    
    # Генерируем вердикт
    verdict = generate_verdict(comparison, pattern_comparison, mode)
    
    # Формируем ответ
    result = {
        "mode": mode,
        "snapshot_a": {
            "tag": tag_a,
            "period": f"{start_a.isoformat()} - {end_a.isoformat()}",
            "data_points": len(values_a)
        },
        "snapshot_b": {
            "tag": tag_b,
            "period": f"{start_b.isoformat()} - {end_b.isoformat()}",
            "data_points": len(values_b)
        },
        "comparison": comparison,
        "verdict": verdict
    }
    
    if pattern_comparison:
        result["pattern_comparison"] = pattern_comparison
    
    return result
'''

# Проверяем что endpoint ещё не добавлен
if '@router.post("/ab")' not in content:
    content = content + ab_endpoint
    print('✅ Endpoint добавлен в конец файла')
else:
    print('ℹ️  Endpoint уже существует')

# 4. Сохраняем файл
print()
print('【4】Сохраняем файл')
print('-' * 80)
api_path.write_text(content, encoding='utf-8')
print('✅ Файл сохранён')

print()
print('=' * 80)
print('ИСПРАВЛЕНО:')
print('=' * 80)
print()
print('1. Изменён декоратор: @app.post → @router.post')
print('2. Изменён путь: "/deep-analysis/ab" → "/ab"')
print('3. Префикс /deep_analysis уже есть в router')
print('4. Префикс /api/v1 добавляется при подключении router')
print()
print('Итоговый URL: POST /api/v1/deep_analysis/ab')
print()
print('=' * 80)
print('ТЕСТИРОВАНИЕ:')
print('=' * 80)
print()
print('1. Перезапусти backend')
print()
print('2. Тестовый запрос:')
print('''
curl -X POST http://localhost:8081/api/v1/deep_analysis/ab \\
  -H "Content-Type: application/json" \\
  -d '{
    "snapshot_a": {
      "tag": "KITCHEN2-CO2",
      "start": "2026-01-01T00:00:00",
      "end": "2026-01-31T23:59:59"
    },
    "snapshot_b": {
      "tag": "KITCHEN2-CO2",
      "start": "2026-02-01T00:00:00",
      "end": "2026-02-28T23:59:59"
    }
  }' | python -m json.tool
''')
print()
print('Обрати внимание: путь изменился с /deep-analysis/ab на /deep_analysis/ab (подчёркивание)')