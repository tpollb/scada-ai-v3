from pathlib import Path

print('=== fix_main.py ===')
print()

main_path = Path('main.py')
content = main_path.read_text(encoding='utf-8')
changed = False

# 1. Добавляем analytics в импорт
if 'from api.routes import chat, config, health, system, docs, energy' in content and 'analytics' not in content.split('from api.routes import')[1].split('\n')[0]:
    content = content.replace(
        'from api.routes import chat, config, health, system, docs, energy',
        'from api.routes import chat, config, health, system, docs, energy, analytics'
    )
    changed = True
    print('✓ main.py: добавлен импорт analytics')
else:
    print('ℹ analytics уже в импорте или паттерн не найден')

# 2. Добавляем include_router
if 'app.include_router(energy.router)' in content and 'analytics.router' not in content:
    content = content.replace(
        'app.include_router(energy.router)',
        'app.include_router(energy.router)\napp.include_router(analytics.router)'
    )
    changed = True
    print('✓ main.py: добавлен include_router(analytics.router)')
else:
    print('ℹ analytics.router уже подключён или паттерн не найден')

if changed:
    main_path.write_text(content, encoding='utf-8', newline='\n')
    print('\n✓ main.py сохранён')
else:
    print('\nℹ Изменений не требуется')

print()
print('=' * 60)
print('ПРОВЕРКА:')
print('=' * 60)
print()

# Проверяем что файлы модуля на месте
analytics_path = Path('modules/analytics')
files_to_check = [
    '__init__.py',
    'config.yaml',
    'tools.py',
    'prompts.py',
    'collectors/__init__.py',
    'collectors/history.py',
    'analyzers/__init__.py',
    'analyzers/trends.py',
    'renderers.py',
]

print('Файлы модуля analytics:')
for f in files_to_check:
    p = analytics_path / f
    if p.exists():
        print(f'  ✓ {f}')
    else:
        print(f'  ✗ {f} (ОТСУТСТВУЕТ)')

print()
print('Роутер:')
router_path = Path('api/routes/analytics.py')
if router_path.exists():
    print(f'  ✓ api/routes/analytics.py')
else:
    print(f'  ✗ api/routes/analytics.py (ОТСУТСТВУЕТ)')

print()
print('Backend перезагрузится автоматически (hot-reload).')
print()
print('Проверка:')
print('  curl http://localhost:8081/analytics/ping')
print('  curl "http://localhost:8081/analytics/report?period=30&params=temperature,co2"')