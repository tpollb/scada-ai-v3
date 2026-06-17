from pathlib import Path

print('=== fix_raw_data_last_points.py ===')
print()

PROJECT_ROOT = Path('.')
trends_path = PROJECT_ROOT / 'backend/modules/analytics/analyzers/trends.py'

content = trends_path.read_text(encoding='utf-8')

# Заменяем data_points[:200] на data_points[-200:]
old_line = '    for p in data_points[:200]:'
new_line = '    for p in data_points[-200:]:'

if old_line in content:
    content = content.replace(old_line, new_line)
    trends_path.write_text(content, encoding='utf-8', newline='\n')
    print('✓ trends.py: raw_data теперь берёт ПОСЛЕДНИЕ 200 точек (не первые)')
    print()
    print('Было:   for p in data_points[:200]:  ← первые 200')
    print('Стало:  for p in data_points[-200]: ← последние 200')
else:
    print('ℹ Паттерн не найден (может уже исправлено)')

print()
print('Backend перезагрузится автоматически (hot-reload).')
print()
print('Проверка:')
print('  1. В чате: "покажи аналитику"')
print('  2. Графики должны показывать даты за последние дни (16-17 июня)')
print('  3. DevTools → Console: НЕ должно быть state_snapshot_uncloneable warnings')