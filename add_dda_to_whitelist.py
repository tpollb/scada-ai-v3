#!/usr/bin/env python3
"""
add_dda_to_whitelist.py — добавляем DDA.md в whitelist документации
"""
from pathlib import Path

print('=' * 80)
print('ФИКС: Добавляем DDA.md в ALLOWED_FILES')
print('=' * 80)
print()

docs_path = Path('backend/api/routes/docs.py')
content = docs_path.read_text(encoding='utf-8')

# Находим блок ALLOWED_FILES и добавляем DDA.md
old_whitelist = '''# Whitelist разрешённых файлов (безопасность)
ALLOWED_FILES = [
    "README.md",
    "MODULES.md",
    "API.md",
    "CHAT_EXAMPLES.md",
    "ARCHITECTURE.md",
    "CHANGELOG.md",
    "ANALYTICS.md",
]'''

new_whitelist = '''# Whitelist разрешённых файлов (безопасность)
ALLOWED_FILES = [
    "README.md",
    "MODULES.md",
    "API.md",
    "CHAT_EXAMPLES.md",
    "ARCHITECTURE.md",
    "CHANGELOG.md",
    "ANALYTICS.md",
    "DDA.md",
]'''

if old_whitelist in content:
    content = content.replace(old_whitelist, new_whitelist)
    docs_path.write_text(content, encoding='utf-8', newline='\n')
    print('✅ DDA.md добавлен в ALLOWED_FILES')
    print()
    print('Теперь whitelist содержит 8 файлов:')
    print('  1. README.md')
    print('  2. MODULES.md')
    print('  3. API.md')
    print('  4. CHAT_EXAMPLES.md')
    print('  5. ARCHITECTURE.md')
    print('  6. CHANGELOG.md')
    print('  7. ANALYTICS.md')
    print('  8. DDA.md ← ДОБАВЛЕНО')
else:
    print('⚠️  Whitelist не найден в ожидаемом виде')
    if '"DDA.md"' in content:
        print('ℹ️  DDA.md уже есть в файле')
    else:
        print('❌ Нужно добавить вручную')

print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Backend перезагрузится сам (--reload)')
print('2. Открой Config → Документация')
print('3. В списке должен появиться:')
print('   • Deep Data Analysis (DDA) - Полная документация')
print('   • DDA.md • 26.7 KB')
print('4. Кликни на него — должна открыться полная документация')