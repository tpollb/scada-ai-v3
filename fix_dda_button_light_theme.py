#!/usr/bin/env python3
"""
fix_dda_button_light_theme.py — делаем кнопку DDA такой же как остальные в светлой теме
"""
from pathlib import Path
import re

print('=' * 80)
print('ФИКС: Кнопка DDA в светлой теме')
print('=' * 80)
print()

config_path = Path('frontend/src/routes/Config.svelte')
content = config_path.read_text(encoding='utf-8')

# 1. Находим стиль активной кнопки для других вкладок (например, modules)
# Ищем паттерн: {activeTab === 'modules' ? '...' : '...'}
modules_pattern = r"activeTab === 'modules' \? '([^']+)'"
match = re.search(modules_pattern, content)

if not match:
    print('❌ Не удалось найти стиль активной кнопки modules')
    exit(1)

active_style = match.group(1)
print(f'✅ Найден стиль активной кнопки: {active_style}')

# 2. Находим текущий стиль активной кнопки DDA
# Ищем: {activeTab === 'dda' ? '...' : '...'}
dda_pattern = r"(activeTab === 'dda' \? ')([^']+)(' : ')([^']+)(')"
dda_match = re.search(dda_pattern, content)

if not dda_match:
    print('❌ Не удалось найти стиль кнопки DDA')
    exit(1)

current_dda_active = dda_match.group(2)
current_dda_inactive = dda_match.group(4)

print(f'   Текущий активный стиль DDA: {current_dda_active}')
print(f'   Текущий неактивный стиль DDA: {current_dda_inactive}')

# 3. Заменяем активный стиль DDA на тот же что у других кнопок
if current_dda_active == active_style:
    print()
    print('ℹ️  Стили уже совпадают — ничего менять не нужно')
else:
    # Создаём новый паттерн
    new_dda_pattern = f"activeTab === 'dda' ? '{active_style}' : '{current_dda_inactive}'"
    old_dda_pattern = dda_match.group(0)
    
    content = content.replace(old_dda_pattern, new_dda_pattern)
    config_path.write_text(content, encoding='utf-8', newline='\n')
    
    print()
    print(f'✅ Кнопка DDA теперь использует тот же стиль что и другие:')
    print(f'   Было: {current_dda_active}')
    print(f'   Стало: {active_style}')

print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Vite автоматически перезагрузит страницу')
print('2. Открой Настройки → вкладка DDA')
print('3. В светлой теме активная кнопка DDA должна быть того же цвета, что и:')
print('   • Modules (когда активна)')
print('   • System (когда активна)')
print('   • Docs (когда активна)')
print('   • Energy (когда активна)')
print()
print('4. Переключись в тёмную тему — кнопка DDA тоже должна выглядеть правильно')