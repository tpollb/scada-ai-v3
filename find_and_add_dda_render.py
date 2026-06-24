#!/usr/bin/env python3
"""
find_and_add_dda_render.py — универсальный поиск места для вставки
"""
from pathlib import Path
import re

print('=' * 80)
print('УНИВЕРСАЛЬНЫЙ ПОИСК И ВСТАВКА БЛОКА DDA')
print('=' * 80)
print()

config_path = Path('frontend/src/routes/Config.svelte')
content = config_path.read_text(encoding='utf-8')
lines = content.split('\n')

# 1. Ищем все строки с activeTab ===
print('【1】Все строки с activeTab ===')
print('-' * 80)
active_tab_lines = []
for i, line in enumerate(lines, 1):
    if 'activeTab ===' in line:
        print(f'  Строка {i}: {line.strip()[:100]}')
        active_tab_lines.append((i, line))

print()

# 2. Ищем кнопки вкладок
print('【2】Кнопки вкладок')
print('-' * 80)
for i, line in enumerate(lines, 1):
    if "onclick={() => activeTab =" in line or "onclick={() => activeTab=" in line:
        print(f'  Строка {i}: {line.strip()[:100]}')

print()

# 3. Проверяем есть ли блок рендеринга dda
print('【3】Проверка блока рендеринга DDA')
print('-' * 80)
has_dda_block = False
for i, line in enumerate(lines, 1):
    if "activeTab === 'dda'" in line and '{#if' in line:
        print(f'  ✅ Блок рендеринга найден на строке {i}')
        has_dda_block = True
        # Показываем контекст
        for j in range(max(0, i-2), min(len(lines), i+5)):
            print(f'    {j+1}: {lines[j]}')
        break

if not has_dda_block:
    print('  ❌ Блок рендеринга НЕ НАЙДЕН')
    
    # Ищем где заканчивается блок modules
    print()
    print('【4】Поиск конца блока modules')
    print('-' * 80)
    
    # Паттерн: после {#if activeTab === 'modules'} ... {/if} идёт следующий блок
    modules_if_line = None
    for i, line in enumerate(lines):
        if "activeTab === 'modules'" in line and '{#if' in line:
            modules_if_line = i
            print(f'  Начало блока modules: строка {i+1}')
            break
    
    if modules_if_line is not None:
        # Ищем закрывающий {/if} этого блока
        # Считаем вложенность
        depth = 0
        for i in range(modules_if_line, len(lines)):
            line = lines[i]
            if '{#if' in line:
                depth += 1
            if '{/if}' in line:
                depth -= 1
                if depth == 0:
                    print(f'  Конец блока modules: строка {i+1}')
                    
                    # Показываем контекст вокруг
                    print()
                    print(f'  Контекст (строки {i-2} до {i+5}):')
                    for j in range(max(0, i-2), min(len(lines), i+6)):
                        marker = '>>>' if j == i else '   '
                        print(f'  {marker} {j+1}: {lines[j]}')
                    
                    # Вставляем блок DDA после {/if}
                    dda_block = '''
      {#if activeTab === 'dda'}
        <div class="p-6">
          <DDAConfigPanel />
        </div>
      {/if}
'''
                    # Вставляем после строки i
                    lines.insert(i + 1, dda_block)
                    new_content = '\n'.join(lines)
                    config_path.write_text(new_content, encoding='utf-8', newline='\n')
                    
                    print()
                    print('  ✅ Блок DDA вставлен после строки', i+1)
                    break
        else:
            print('  ❌ Не удалось найти конец блока modules')
    else:
        print('  ❌ Не удалось найти начало блока modules')

print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Vite автоматически перезагрузит страницу')
print('2. Открой: Настройки → вкладка DDA')
print('3. Должно появиться:')
print('   • Заголовок "🔧 Deep Data Analysis — ТЕСТОВЫЙ КОМПОНЕНТ"')
print('   • Спиннер → JSON с настройками')
print('4. В Network tab появится запрос к /config/modules/deep_analysis/settings')
print('5. В Console появятся логи "DDAConfigPanel: ..."')