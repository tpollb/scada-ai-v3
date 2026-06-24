#!/usr/bin/env python3
"""
fix_chevron_import.py — добавляем ChevronDown в импорт lucide-svelte
"""

from pathlib import Path
import re

print('=' * 70)
print('ФИКС: Импорт ChevronDown из lucide-svelte')
print('=' * 70)
print()

results_path = Path('frontend/src/components/DeepAnalysisResults.svelte')
content = results_path.read_text(encoding='utf-8')

# Все иконки которые нам нужны
required_icons = {
    'TrendingUp', 'AlertTriangle', 'Activity', 'Download', 'RotateCcw',
    'ZoomIn', 'ZoomOut', 'Grid3x3', 'ArrowRightLeft', 'Table', 'Info', 
    'Loader2', 'Lightbulb', 'Circle', 'ArrowUpCircle', 'ArrowDownCircle',
    'Waves', 'Zap', 'ChevronDown'
}

# Находим строку импорта lucide-svelte
# Паттерн: import { ... } from 'lucide-svelte'
import_pattern = r"import\s*\{([^}]+)\}\s*from\s*['\"]lucide-svelte['\"]"
match = re.search(import_pattern, content)

if not match:
    print('❌ Не найдена строка импорта lucide-svelte!')
    exit(1)

current_imports_str = match.group(1)
# Парсим текущие импорты
current_imports = set()
for part in current_imports_str.split(','):
    name = part.strip()
    if name:
        current_imports.add(name)

print(f'Текущие импорты lucide-svelte ({len(current_imports)}):')
print(f'  {", ".join(sorted(current_imports))}')
print()

# Проверяем каких иконок не хватает
missing = required_icons - current_imports
if not missing:
    print('✅ Все нужные иконки уже импортированы')
else:
    print(f'❌ Отсутствуют иконки ({len(missing)}):')
    for icon in sorted(missing):
        print(f'  • {icon}')
    print()
    
    # Добавляем недостающие
    all_imports = sorted(current_imports | required_icons)
    new_import_str = ', '.join(all_imports)
    
    new_import_line = f"import {{ {new_import_str} }} from 'lucide-svelte'"
    old_import_line = match.group(0)
    
    content = content.replace(old_import_line, new_import_line)
    results_path.write_text(content, encoding='utf-8', newline='\n')
    
    print('✅ Импорт обновлён:')
    print(f'  {new_import_line}')
    print()

# Дополнительная проверка: ищем все использования <ChevronDown в шаблоне
chevron_usages = len(re.findall(r'<ChevronDown\b', content))
print(f'Использований <ChevronDown /> в шаблоне: {chevron_usages}')

# Проверка других иконок которые мы добавляли
print()
print('Проверка всех используемых иконок:')
for icon in sorted(required_icons):
    usages = len(re.findall(rf'<{icon}\b', content))
    imported = icon in (current_imports | required_icons)
    status = '✅' if imported else '❌'
    print(f'  {status} {icon}: импортирован={imported}, использований={usages}')

print()
print('=' * 70)
print('ГОТОВО!')
print('=' * 70)
print()
print('Vite должен автоматически перезагрузить страницу.')
print('Если всё ок — аккордеон будет работать с поворачивающейся стрелкой.')