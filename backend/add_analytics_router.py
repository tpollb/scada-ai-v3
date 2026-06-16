from pathlib import Path

print('=== add_analytics_router.py ===')
print()

main_path = Path('main.py')
if not main_path.exists() or main_path.stat().st_size == 0:
    print('❌ main.py пустой или отсутствует. Сначала выполни: git checkout main.py')
    exit(1)

# Читаем файл через open (надёжнее чем write_text с newline)
with open(main_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f'✓ main.py прочитан: {len(lines)} строк')

# Ищем строки для модификации
import_line_idx = None
import_line_content = None
router_insert_idx = None

for i, line in enumerate(lines):
    # Ищем строку с импортом роутеров
    if 'from api.routes import' in line and 'chat' in line:
        import_line_idx = i
        import_line_content = line
        print(f'✓ Нашёл импорт роутеров на строке {i+1}')
        print(f'  {line.rstrip()}')
    
    # Ищем последний include_router (после него вставим analytics)
    if 'app.include_router(' in line and 'energy.router' in line:
        router_insert_idx = i
        print(f'✓ Нашёл energy.router на строке {i+1}')

# Проверяем, не добавлен ли уже analytics
content = ''.join(lines)
if 'analytics' in content and 'include_router(analytics.router)' in content:
    print('ℹ analytics уже подключён в main.py')
    exit(0)

changed = False

# 1. Добавляем analytics в импорт
if import_line_idx is not None and 'analytics' not in import_line_content:
    old = import_line_content
    # Заменяем последнюю часть импорта
    if old.rstrip().endswith('energy'):
        new = old.rstrip() + ', analytics\n'
    elif old.rstrip().endswith('energy,'):
        new = old.rstrip() + ' analytics\n'
    else:
        # Если формат другой - просто добавим
        new = old.rstrip() + ', analytics\n'
    lines[import_line_idx] = new
    print(f'✓ Добавлен analytics в импорт')
    changed = True

# 2. Добавляем include_router(analytics.router) после energy.router
if router_insert_idx is not None:
    # Находим отступ у текущей строки
    current_line = lines[router_insert_idx]
    indent = len(current_line) - len(current_line.lstrip())
    indent_str = ' ' * indent
    new_line = f'{indent_str}app.include_router(analytics.router)\n'
    lines.insert(router_insert_idx + 1, new_line)
    print(f'✓ Добавлен include_router(analytics.router) на строке {router_insert_idx + 2}')
    changed = True

if not changed:
    print('ℹ Изменений не требуется')
    exit(0)

# Записываем обратно через open (надёжно)
with open(main_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print()
print('✓ main.py сохранён')
print()
print('=' * 60)
print('ПРОВЕРКА:')
print('=' * 60)
print()

# Проверяем что main.py не пустой
with open(main_path, 'r', encoding='utf-8') as f:
    final_lines = f.readlines()
print(f'Размер файла: {len(final_lines)} строк')

# Показываем изменённые строки
for i, line in enumerate(final_lines):
    if 'analytics' in line:
        print(f'  {i+1}: {line.rstrip()}')

print()
print('Теперь запускай backend:')
print('  uvicorn main:app --host 0.0.0.0 --port 8081 --reload')