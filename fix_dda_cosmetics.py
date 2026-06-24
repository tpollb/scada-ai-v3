#!/usr/bin/env python3
"""
fix_dda_cosmetics.py — 4 косметических исправления
"""
from pathlib import Path

print('=' * 80)
print('КОСМЕТИЧЕСКИЕ ИСПРАВЛЕНИЯ DDA')
print('=' * 80)
print()

# ============================================================================
# 1. DDAConfigPanel.svelte — все 4 правки
# ============================================================================
panel_path = Path('frontend/src/components/config/DDAConfigPanel.svelte')
content = panel_path.read_text(encoding='utf-8')
changes = []

# 1a. Инфо-блоки: bg-blue-50 text-blue-900 → bg-neutral-50 text-neutral-700
# Заменяем все 4 вхождения (аномалии, корреляции, визуализация, цвета)
old_info = '<div class="bg-blue-50 border border-blue-200 rounded p-3 text-sm text-blue-900">'
new_info = '<div class="bg-neutral-50 border border-neutral-200 rounded p-3 text-sm text-neutral-700">'
count_info = content.count(old_info)
if count_info > 0:
    content = content.replace(old_info, new_info)
    changes.append(f'1. Инфо-блоки: заменено {count_info} блоков на монохром (neutral)')

# 1b. AlertCircle в инфо-блоках — делаем серым
old_alert = '<AlertCircle size={14} class="inline mr-1" />'
new_alert = '<AlertCircle size={14} class="inline mr-1 text-neutral-500" />'
if old_alert in content:
    content = content.replace(old_alert, new_alert)
    changes.append('1b. AlertCircle иконка: добавлен text-neutral-500')

# 3. Заголовок "Deep Data Analysis — Настройки": Activity синяя → чёрная
old_header_icon = '<Activity size={20} class="text-blue-600" />'
new_header_icon = '<Activity size={20} class="text-neutral-900" />'
if old_header_icon in content:
    content = content.replace(old_header_icon, new_header_icon)
    changes.append('3. Заголовок: иконка Activity теперь монохром (neutral-900)')

# 4. Убираем Activity из "Детекция аномалий (Isolation Forest)"
old_detect_title = '''          <h3 class="text-lg font-semibold text-neutral-900 mb-4 flex items-center gap-2">
            <Activity size={18} class="text-blue-600" />
            Детекция аномалий (Isolation Forest)
          </h3>'''
new_detect_title = '''          <h3 class="text-lg font-semibold text-neutral-900 mb-4">
            Детекция аномалий (Isolation Forest)
          </h3>'''
if old_detect_title in content:
    content = content.replace(old_detect_title, new_detect_title)
    changes.append('4. Убрана иконка Activity из "Детекция аномалий (Isolation Forest)"')

panel_path.write_text(content, encoding='utf-8', newline='\n')

for c in changes:
    print(f'✅ {c}')

# ============================================================================
# 2. Config.svelte — кнопка DDA активная чёрная
# ============================================================================
print()
config_path = Path('frontend/src/routes/Config.svelte')
config_content = config_path.read_text(encoding='utf-8')

# Ищем паттерн активной кнопки DDA
# Было: {activeTab === 'dda' ? 'bg-blue-600 text-white' : 'text-neutral-600 hover:bg-neutral-100'}
# Нужно: {activeTab === 'dda' ? 'bg-neutral-900 text-white' : 'text-neutral-600 hover:bg-neutral-100'}

old_dda_active = "activeTab === 'dda' ? 'bg-blue-600 text-white'"
new_dda_active = "activeTab === 'dda' ? 'bg-neutral-900 text-white'"

if old_dda_active in config_content:
    config_content = config_content.replace(old_dda_active, new_dda_active)
    config_path.write_text(config_content, encoding='utf-8', newline='\n')
    print('✅ 2. Кнопка DDA в хедере: активная теперь чёрная (bg-neutral-900)')
else:
    # Попробуем другие варианты
    alt_patterns = [
        ("activeTab === 'dda' ? 'bg-blue-600 text-white'", "activeTab === 'dda' ? 'bg-neutral-900 text-white'"),
        ("activeTab === 'dda' ? 'bg-blue-500 text-white'", "activeTab === 'dda' ? 'bg-neutral-900 text-white'"),
    ]
    found = False
    for old, new in alt_patterns:
        if old in config_content:
            config_content = config_content.replace(old, new)
            config_path.write_text(config_content, encoding='utf-8', newline='\n')
            print(f'✅ 2. Кнопка DDA: активная теперь чёрная')
            found = True
            break
    
    if not found:
        # Ищем вручную через regex
        import re
        pattern = r"(activeTab === 'dda' \? '[^']*')"
        match = re.search(pattern, config_content)
        if match:
            print(f'   Найден паттерн: {match.group(1)}')
            # Заменяем на чёрный
            config_content = re.sub(
                r"activeTab === 'dda' \? '([^']*text-white[^']*)'",
                "activeTab === 'dda' ? 'bg-neutral-900 text-white'",
                config_content
            )
            config_path.write_text(config_content, encoding='utf-8', newline='\n')
            print('✅ 2. Кнопка DDA: активная теперь чёрная (regex)')
        else:
            print('⚠️  Не удалось найти паттерн активной кнопки DDA')

print()
print('=' * 80)
print('ИТОГО:')
print('=' * 80)
print()
print('✅ 1. Инфо-блоки стали монохромные (neutral-50/neutral-700)')
print('     — хорошо читается на светлом фоне')
print('✅ 2. Кнопка DDA в хедере активная — чёрная (bg-neutral-900)')
print('✅ 3. Иконка в заголовке "Deep Data Analysis — Настройки" — чёрная')
print('✅ 4. Убрана иконка из "Детекция аномалий (Isolation Forest)"')
print()
print('Vite автоматически перезагрузит страницу.')