from pathlib import Path
import re

print('=== fix_docs_whitelist.py ===')
print()

PROJECT_ROOT = Path('.')
docs_dir = PROJECT_ROOT / 'backend/docs'
docs_route = PROJECT_ROOT / 'backend/api/routes/docs.py'

# 1. Находим все .md файлы в backend/docs/
if not docs_dir.exists():
    print(f'⚠ Папка не найдена: {docs_dir}')
    exit(1)

md_files = sorted([f.name for f in docs_dir.glob('*.md')])
print(f'Найдено {len(md_files)} .md файлов в backend/docs/:')
for f in md_files:
    print(f'  • {f}')
print()

# 2. Читаем docs.py
content = docs_route.read_text(encoding='utf-8')

# 3. Извлекаем текущий ALLOWED_FILES
pattern = r'ALLOWED_FILES\s*=\s*\[(.*?)\]'
match = re.search(pattern, content, re.DOTALL)

if not match:
    print('⚠ Не найден ALLOWED_FILES в docs.py')
    exit(1)

current_files_str = match.group(1)
# Парсим текущие файлы
current_files = re.findall(r'"([^"]+)"', current_files_str)
print(f'Текущий whitelist ({len(current_files)}):')
for f in current_files:
    print(f'  • {f}')
print()

# 4. Объединяем — добавляем новые
all_files = list(dict.fromkeys(current_files + md_files))  # сохраняем порядок, убираем дубли
print(f'Новый whitelist ({len(all_files)}):')
for f in all_files:
    marker = ' ← НОВЫЙ' if f not in current_files else ''
    print(f'  • {f}{marker}')
print()

# 5. Формируем новый ALLOWED_FILES
new_allowed = 'ALLOWED_FILES = [\n'
for f in all_files:
    new_allowed += f'    "{f}",\n'
new_allowed += ']'

# 6. Заменяем в файле
old_allowed_block = 'ALLOWED_FILES = [' + current_files_str + ']'
content = content.replace(old_allowed_block, new_allowed)
docs_route.write_text(content, encoding='utf-8', newline='\n')
print(f'✓ docs.py: ALLOWED_FILES обновлён ({len(current_files)} → {len(all_files)})')

print()
print('=' * 60)
print('ЧТО СДЕЛАНО:')
print('=' * 60)
print()
print('1. Просканированы все .md файлы в backend/docs/')
print('2. Новые файлы добавлены в ALLOWED_FILES')
print('3. backend/api/routes/docs.py обновлён')
print()
print('Backend перезагрузится автоматически (hot-reload).')
print()
print('Проверка:')
print('  1. Открой в UI раздел "Документация"')
print('  2. В списке должен появиться твой новый файл')
print('  3. Клик на файл → откроется содержимое')