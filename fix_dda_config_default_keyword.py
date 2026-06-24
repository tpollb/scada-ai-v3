#!/usr/bin/env python3
"""
fix_dda_config_default_keyword.py — исправляем использование зарезервированного слова default
"""
from pathlib import Path

print('=' * 80)
print('ФИКС: Зарезервированное слово "default" в DDAConfigPanel.svelte')
print('=' * 80)
print()

panel_path = Path('frontend/src/components/config/DDAConfigPanel.svelte')

if not panel_path.exists():
    print(f'❌ Файл {panel_path} не найден!')
    exit(1)

content = panel_path.read_text(encoding='utf-8')

# Заменяем default на defaultColor в блоке each
old_pattern = "{#each [['spike', 'Пики', '#ef4444'], ['dip', 'Провалы', '#3b82f6'], ['drift', 'Дрейфы', '#f59e0b'], ['noise', 'Шум', '#9ca3af']] as [key, label, default]}"
new_pattern = "{#each [['spike', 'Пики', '#ef4444'], ['dip', 'Провалы', '#3b82f6'], ['drift', 'Дрейфы', '#f59e0b'], ['noise', 'Шум', '#9ca3af']] as [key, label, defaultColor]}"

if old_pattern in content:
    content = content.replace(old_pattern, new_pattern)
    print('✅ Заменено: default → defaultColor в блоке {#each}')
else:
    print('⚠️  Паттерн не найден (возможно уже исправлено)')

# Также заменяем использование default внутри блока
old_usage = "onclick={() => settings.colors[key] = default}"
new_usage = "onclick={() => settings.colors[key] = defaultColor}"

if old_usage in content:
    content = content.replace(old_usage, new_usage)
    print('✅ Заменено использование: default → defaultColor')
else:
    print('⚠️  Использование не найдено')

panel_path.write_text(content, encoding='utf-8', newline='\n')

print()
print('=' * 80)
print('ИСПРАВЛЕНО')
print('=' * 80)
print()
print('Проблема: "default" — зарезервированное слово в JavaScript')
print('Решение: переименовано в "defaultColor"')
print()
print('Vite должен автоматически перезагрузить страницу.')