#!/usr/bin/env python3
"""
test_dda_panel.py — проверка что DDAConfigPanel рендерится
"""
from pathlib import Path

print('=' * 80)
print('ТЕСТ: Проверка DDAConfigPanel.svelte')
print('=' * 80)
print()

panel_path = Path('frontend/src/components/config/DDAConfigPanel.svelte')

if not panel_path.exists():
    print('❌ Файл не найден!')
    exit(1)

content = panel_path.read_text(encoding='utf-8')

# Проверяем ключевые элементы
checks = [
    ('<script lang="ts">', 'Script tag'),
    ('import api from', 'API import'),
    ('let settings = $state', 'Settings state'),
    ('async function loadSettings', 'Load function'),
    ('onMount', 'onMount hook'),
    ('{#if loading}', 'Loading state'),
    ('{#if settings}', 'Settings render'),
    ('<button', 'Buttons'),
]

print('Проверка структуры компонента:')
for pattern, name in checks:
    if pattern in content:
        print(f'  ✅ {name}')
    else:
        print(f'  ❌ {name} НЕ НАЙДЕН')

print()
print('=' * 80)
print('ЧТО ДЕЛАТЬ:')
print('=' * 80)
print()
print('1. Открой фронтенд → Настройки → вкладка DDA')
print('2. Открой DevTools (F12)')
print('3. Сделай скриншот вкладки')
print('4. Проверь Console tab на ошибки')
print('5. Проверь Network tab — запрос к /config/modules/deep_analysis/settings')
print()
print('Скинь:')
print('  • Скриншот вкладки')
print('  • Ошибки из Console (если есть)')
print('  • Status и Response из Network tab')