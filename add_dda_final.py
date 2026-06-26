#!/usr/bin/env python3
"""
add_dda_final.py — добавляем DDA.md в whitelist документации
"""
from pathlib import Path

print('=' * 80)
print('ФИНАЛЬНЫЙ ФИКС: DDA.md в whitelist')
print('=' * 80)
print()

docs_path = Path('backend/api/routes/docs.py')
content = docs_path.read_text(encoding='utf-8')

# Заменяем whitelist
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
    print('Теперь в документации доступно 8 файлов:')
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

print()
print('=' * 80)
print('СЛЕДУЮЩИЕ ШАГИ:')
print('=' * 80)
print()
print('Запусти для коммита и пуша:')
print()
print('  cd /c/dev/SCADA.AI/scada-ai-v3')
print('  git add -A')
print('  git commit -m "docs(dda): add DDA.md to documentation viewer (v3.2.5)"')
print('  git push')
print()
print('Или одной командой:')
print('  cd /c/dev/SCADA.AI/scada-ai-v3 && git add -A && git commit -m "docs(dda): add DDA.md to documentation viewer (v3.2.5)" && git push')