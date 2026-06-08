from pathlib import Path

print('=== fix_backend_priority.py ===')
print()

dc_path = Path('modules/health/data_collectors.py')
content = dc_path.read_text(encoding='utf-8')

old_func = '''def _priority_label(priority: int | None) -> str:
    if priority is None:
        return "unknown"
    if priority >= 150: return "high"
    if priority >= 100: return "medium"
    return "low"'''

new_func = '''def _priority_label(priority: int | None) -> str:
    """Возвращает локализованную метку приоритета аварии."""
    if priority is None:
        return "Неизвестно"
    if priority >= 150: return "Высокий"
    if priority >= 100: return "Средний"
    return "Низкий"'''

if old_func in content:
    content = content.replace(old_func, new_func)
    dc_path.write_text(content, encoding='utf-8', newline='\n')
    print('✓ data_collectors.py: _priority_label() возвращает русские метки')
    print('  high → Высокий, medium → Средний, low → Низкий')
else:
    print('⚠ Не нашёл точный паттерн _priority_label')

print()
print('ВАЖНО: фронтенд AlarmsPanel использует priorityConfig по ключу')
print('(high/medium/low), а не по priority_label. Поэтому бэкенд-изменение')
print('не сломает фронтенд — они работают независимо.')
print('Бэкенд-изменение влияет только на API-ответ и narrative-рендер.')