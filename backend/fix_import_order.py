from pathlib import Path

print('=== fix_import_order.py ===')
print()

main_path = Path('main.py')
content = main_path.read_text(encoding='utf-8')

# Чиним конкретную сломанную строку
wrong_line = 'from api.routes import chat, config, health, system, docs, energy  # noqa: E402, analytics'
correct_line = 'from api.routes import chat, config, health, system, docs, energy, analytics  # noqa: E402'

if wrong_line in content:
    content = content.replace(wrong_line, correct_line)
    main_path.write_text(content, encoding='utf-8', newline='\n')
    print('✓ Исправлена строка импорта')
    print(f'  Было: {wrong_line}')
    print(f'  Стало: {correct_line}')
else:
    print('ℹ Сломанная строка не найдена')

print()
print('Backend перезагрузится автоматически (hot-reload).')
print('Проверка:')
print('  curl http://localhost:8081/analytics/ping')
print('  curl "http://localhost:8081/analytics/report?period=30&params=temperature,co2"')