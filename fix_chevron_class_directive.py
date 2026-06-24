#!/usr/bin/env python3
"""
fix_chevron_class_directive.py — исправляет class: на компонентах lucide-svelte
"""

from pathlib import Path

print('=' * 70)
print('ФИКС: class:rotate-180 на компонентах ChevronDown')
print('=' * 70)
print()

results_path = Path('frontend/src/components/DeepAnalysisResults.svelte')
content = results_path.read_text(encoding='utf-8')

# 4 типа аномалий с разными цветами
types = [
    ('spike', 'red'),
    ('dip', 'blue'),
    ('drift', 'amber'),
    ('noise', 'neutral'),
]

changes = 0

for atype, color in types:
    old = f'<ChevronDown size={{14}} class="text-{color}-500 transition-transform" class:rotate-180={{expandedType === \'{atype}\'}} />'
    new = f'''<span class="text-{color}-500 transition-transform" class:rotate-180={{expandedType === '{atype}'}}>
                      <ChevronDown size={{14}} />
                    </span>'''
    
    if old in content:
        content = content.replace(old, new)
        changes += 1
        print(f'✓ Обёрнут ChevronDown для типа: {atype}')

results_path.write_text(content, encoding='utf-8', newline='\n')

print()
print('=' * 70)
print(f'ИТОГО: исправлено {changes} вхождений')
print('=' * 70)
print()
print('Что изменилось:')
print('  Было: <ChevronDown class="..." class:rotate-180={{...}} />')
print('  Стало: <span class="..." class:rotate-180={{...}}><ChevronDown /></span>')
print()
print('Почему это работает:')
print('  • class: директива в Svelte работает только с DOM элементами')
print('  • <ChevronDown /> — это Svelte компонент, не DOM элемент')
print('  • Оборачиваем в <span> — теперь class: работает на span')
print('  • transform применяется к span → вращает иконку внутри')
print()
print('Vite должен автоматически перезагрузить страницу.')