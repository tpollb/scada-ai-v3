from pathlib import Path

print('=== fix_alarm_priority_display.py ===')
print()

# ============================================================================
# ВОЗВРАЩАЕМ английские ключи в _priority_label
# Локализация должна быть ТОЛЬКО на фронте для отображения
# ============================================================================
dc_path = Path('modules/health/data_collectors.py')
content = dc_path.read_text(encoding='utf-8')

old_func = '''def _priority_label(priority: int | None) -> str:
    """Возвращает локализованную метку приоритета аварии."""
    if priority is None:
        return "Неизвестно"
    if priority >= 150: return "Высокий"
    if priority >= 100: return "Средний"
    return "Низкий"'''

new_func = '''def _priority_label(priority: int | None) -> str:
    """Возвращает машинный ключ приоритета. Локализация — на фронте."""
    if priority is None:
        return "unknown"
    if priority >= 150: return "high"
    if priority >= 100: return "medium"
    return "low"'''

if old_func in content:
    content = content.replace(old_func, new_func)
    dc_path.write_text(content, encoding='utf-8', newline='\n')
    print('✓ data_collectors.py: _priority_label возвращает английские ключи')
    print('  high/medium/low — для API и маппинга во фронте')
    print('  Локализация (Высокий/Средний/Низкий) уже есть в AlarmsPanel priorityConfig.label')
else:
    # Возможно предыдущий скрипт не применился или применён частично
    # Проверяем текущее состояние
    if 'return "high"' in content and 'return "medium"' in content:
        print('ℹ data_collectors.py: уже возвращает английские ключи')
    else:
        print('⚠ Не нашёл точный паттерн. Проверь вручную:')
        for i, line in enumerate(content.split('\n'), 1):
            if '_priority_label' in line or ('return' in line and any(w in line for w in ['high', 'medium', 'low', 'Высокий', 'Средний', 'Низкий'])):
                print(f'  {i}: {line}')

print()
print('=' * 60)
print('ЧТО ПРОИСХОДИТ:')
print('=' * 60)
print('Бэкенд: priority_label = "high"/"medium"/"low" (машинные ключи)')
print('Фронтенд: priorityConfig["high"].label = "Высокий" (для отображения)')
print()
print('В таблице журнала: cfg = priorityConfig[a.priority_label]')
print('  a.priority_label = "high" → cfg.label = "Высокий" ✓')
print()
print('В модалке деталей: cfg = priorityConfig[selectedAlarm.priority_label]')  
print('  selectedAlarm.priority_label = "high" → cfg.label = "Высокий" ✓')
print()
print('Перезапусти backend после применения.')