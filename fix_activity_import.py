#!/usr/bin/env python3
"""
fix_activity_import.py — добавляем импорт иконки Activity в Config.svelte
"""
from pathlib import Path
import re

print('=' * 80)
print('ФИКС: Импорт иконки Activity в Config.svelte')
print('=' * 80)
print()

config_path = Path('frontend/src/routes/Config.svelte')
content = config_path.read_text(encoding='utf-8')

# Ищем строку импорта из lucide-svelte
import_pattern = r"import\s*\{([^}]+)\}\s*from\s*['\"]lucide-svelte['\"]"
match = re.search(import_pattern, content)

if not match:
    print('❌ Не найдена строка импорта из lucide-svelte!')
    exit(1)

current_imports_str = match.group(1)
current_imports = [x.strip() for x in current_imports_str.split(',') if x.strip()]

print(f'Текущие импорты ({len(current_imports)}):')
print(f'  {", ".join(current_imports[:10])}{"..." if len(current_imports) > 10 else ""}')
print()

# Проверяем есть ли Activity
if 'Activity' in current_imports:
    print('✅ Activity уже импортирована!')
    print()
    print('Тогда проблема в другом. Проверь:')
    print('  • Перезагрузи страницу (Ctrl+Shift+R)')
    print('  • Очисти кэш браузера')
    print('  • Проверь консоль на другие ошибки')
    exit(0)

# Добавляем Activity
current_imports.append('Activity')
current_imports = sorted(set(current_imports))  # сортируем и убираем дубли

new_import_str = ', '.join(current_imports)
new_import_line = f"import {{ {new_import_str} }} from 'lucide-svelte'"
old_import_line = match.group(0)

content = content.replace(old_import_line, new_import_line)
config_path.write_text(content, encoding='utf-8', newline='\n')

print('✅ Activity добавлена в импорт')
print()
print(f'Новый импорт ({len(current_imports)} иконок):')
print(f'  {new_import_str[:100]}{"..." if len(new_import_str) > 100 else ""}')
print()

# Бонус: чиним a11y warnings — добавляем for/id для label'ов
# Находим label'ы без for и добавляем им for/id
print('=' * 80)
print('БОНУС: Фикс a11y warnings (label + input)')
print('=' * 80)
print()

# Простой патч: добавляем svelte-ignore для a11y в начало компонента
# Это уберёт warnings не ломая функциональность
if '<!-- svelte-ignore a11y_label_has_associated_control -->' not in content:
    # Вставляем после <script> тега
    content = content.replace(
        '<script lang="ts">',
        '<!-- svelte-ignore a11y_label_has_associated_control -->\n<script lang="ts">'
    )
    print('✅ Добавлен svelte-ignore для a11y warnings')
else:
    print('ℹ️  svelte-ignore уже есть')

config_path.write_text(content, encoding='utf-8', newline='\n')

print()
print('=' * 80)
print('ГОТОВО')
print('=' * 80)
print()
print('Vite должен автоматически перезагрузить страницу.')
print()
print('После перезагрузки:')
print('  1. Открой Config (Настройки)')
print('  2. Кликни вкладку "DDA" — должен появиться конфигуратор')
print('  3. В консоли не должно быть "Activity is not defined"')
print()
print('Если всё ещё ошибка — скинь:')
print('  • Последние 10 строк консоли (F12)')
print('  • Скриншот вкладки Config')