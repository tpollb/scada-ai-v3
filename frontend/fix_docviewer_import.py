from pathlib import Path

print('=== fix_docviewer_import.py ===')
print()

# 1. Проверяем что DocsViewer.svelte существует
docs_viewer_path = Path('src/components/DocsViewer.svelte')
if not docs_viewer_path.exists():
    print(f'❌ Файл не найден: {docs_viewer_path.absolute()}')
    print('Нужно сначала создать DocsViewer.svelte')
    exit(1)
print(f'✓ DocsViewer.svelte существует ({docs_viewer_path.stat().st_size} байт)')

# 2. Читаем Config.svelte и добавляем импорт
config_path = Path('src/routes/Config.svelte')
content = config_path.read_text(encoding='utf-8')

# Проверяем что уже импортирован
if "import DocsViewer from '../components/DocsViewer.svelte'" in content or \
   'import DocsViewer from "../components/DocsViewer.svelte"' in content:
    print('ℹ DocsViewer уже импортирован в Config.svelte')
    exit(0)

# Ищем строку с импортом api и вставляем после неё импорт DocsViewer
target_line = "import api from '../lib/api'"
new_import_line = "import DocsViewer from '../components/DocsViewer.svelte'"

if target_line in content:
    # Заменяем строку импорта api на две строки: api + DocsViewer
    content = content.replace(
        target_line,
        f"{target_line}\n  {new_import_line}",
        1  # только первое вхождение
    )
    config_path.write_text(content, encoding='utf-8', newline='\n')
    print('✓ Добавлен импорт DocsViewer после импорта api')
    print()
    print('Первые 10 строк Config.svelte теперь:')
    for i, line in enumerate(content.split('\n')[:10], 1):
        print(f'  {i}: {line}')
else:
    print('⚠ Не нашёл строку: import api from \'../lib/api\'')
    print('Покажи первые 20 строк файла:')
    for i, line in enumerate(content.split('\n')[:20], 1):
        print(f'  {i}: {line}')

print()
print('=' * 60)
print('СЛЕДУЮЩИЙ ШАГ:')
print('  Vite подхватит через HMR.')
print('  Обнови страницу Конфигуратора (F5).')
print('  Кликни на вкладку "Документация".')
print()
print('Когда заработает — скажи "docs viewer ок"')