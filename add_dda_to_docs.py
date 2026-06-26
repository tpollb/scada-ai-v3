#!/usr/bin/env python3
"""
add_dda_to_docs.py — добавляем DDA.md в whitelist документации
"""
from pathlib import Path

print('=' * 80)
print('ФИКС: Добавляем DDA.md в список документации')
print('=' * 80)
print()

docs_path = Path('backend/api/routes/docs.py')
content = docs_path.read_text(encoding='utf-8')

# Находим блок ALLOWED_FILES
old_whitelist = '''# Whitelist разрешённых файлов (безопасность)
ALLOWED_FILES = [
    "README.md",
    "MODULES.md",
    "API.md",
    "CHAT_EXAMPLES.md",
    "ARCHITECTURE.md",
    "CHANGELOG.md",
]'''

new_whitelist = '''# Whitelist разрешённых файлов (безопасность)
ALLOWED_FILES = [
    "README.md",
    "MODULES.md",
    "API.md",
    "CHAT_EXAMPLES.md",
    "ARCHITECTURE.md",
    "CHANGELOG.md",
    "DDA.md",
]'''

if old_whitelist in content:
    content = content.replace(old_whitelist, new_whitelist)
    docs_path.write_text(content, encoding='utf-8', newline='\n')
    print('✅ DDA.md добавлен в whitelist')
else:
    print('⚠️  Whitelist не найден в ожидаемом виде — проверяем вручную')
    if '"DDA.md"' in content:
        print('ℹ️  DDA.md уже есть в файле')
    else:
        print('❌ Нужно добавить вручную')

# Проверяем что DDA.md физически существует
dda_path = Path('backend/docs/DDA.md')
if dda_path.exists():
    size = dda_path.stat().st_size
    print(f'✅ DDA.md существует ({size / 1024:.1f} KB)')
else:
    print(f'❌ DDA.md не найден по пути {dda_path}')

print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Backend перезагрузится сам (--reload)')
print('2. Открой Config → Документация')
print('3. В списке должен появиться:')
print('   • Deep Data Analysis (DDA) - Полная документация')
print('   • DDA.md • ~XX KB')
print('4. Кликни на него — должен отрендериться markdown')
print()
print('Если не появляется — проверь в DevTools Network:')
print('  GET /docs/list → в массиве files должен быть DDA.md')