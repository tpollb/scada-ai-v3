#!/usr/bin/env python3
"""
final_fix_config_dda_render.py — добавляем блок рендеринга DDAConfigPanel
"""
from pathlib import Path
import re

print('=' * 80)
print('ФИНАЛЬНЫЙ ФИКС: Блок рендеринга DDAConfigPanel в Config.svelte')
print('=' * 80)
print()

config_path = Path('frontend/src/routes/Config.svelte')
content = config_path.read_text(encoding='utf-8')

# Проверяем есть ли блок рендеринга
if "activeTab === 'dda'" in content and "<DDAConfigPanel" in content:
    print('✅ Блок рендеринга уже есть')
    
    # Показываем контекст
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        if 'activeTab === \'dda\'' in line and '{#if' in line:
            print(f'   Найдено на строке {i}:')
            for j in range(max(0, i-2), min(len(lines), i+8)):
                marker = '>>>' if j == i-1 else '   '
                print(f'   {marker} {j+1}: {lines[j]}')
            break
    
    print()
    print('Тогда проблема в другом. Проверь:')
    print('  1. Открой DevTools (F12) → Console')
    print('  2. Кликни на вкладку DDA')
    print('  3. Есть ли ошибки JavaScript?')
    print('  4. Есть ли логи "DDAConfigPanel: ..."?')
else:
    print('❌ Блок рендеринга НЕ найден!')
    print('   Добавляю принудительно...')
    print()
    
    # Ищем место где заканчивается блок modules
    # Паттерн: {/if} перед {#if activeTab === 'system'}
    pattern = r"(\{/if\})\s*(\{#if activeTab === 'system'\})"
    match = re.search(pattern, content)
    
    if match:
        dda_block = '''{/if}

      {#if activeTab === 'dda'}
        <div class="p-6">
          <DDAConfigPanel />
        </div>
      {/if}

      {#if activeTab === 'system'}'''
        
        content = content.replace(match.group(0), dda_block)
        config_path.write_text(content, encoding='utf-8', newline='\n')
        
        print('✅ Блок рендеринга добавлен:')
        print('   {#if activeTab === \'dda\'}')
        print('     <div class="p-6">')
        print('       <DDAConfigPanel />')
        print('     </div>')
        print('   {/if}')
    else:
        print('❌ Не удалось найти место для вставки')
        print()
        print('Показываю структуру Config.svelte:')
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if 'activeTab ===' in line and '{#if' in line:
                print(f'   Строка {i}: {line.strip()[:80]}')

print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Vite автоматически перезагрузит страницу')
print('2. Открой: Настройки → вкладка DDA')
print('3. Что должно появиться:')
print('   • Заголовок "🔧 Deep Data Analysis — ТЕСТОВЫЙ КОМПОНЕНТ"')
print('   • Спиннер "Загрузка настроек..."')
print('   • После загрузки — JSON с настройками')
print()
print('4. Открой DevTools (F12) → Console:')
print('   • Должны быть логи:')
print('     "DDAConfigPanel: загружаю настройки..."')
print('     "DDAConfigPanel: настройки загружены"')
print()
print('Если всё ещё пусто:')
print('  • Сделай скриншот вкладки DDA')
print('  • Скинь все ошибки из Console (F12)')
print('  • Проверь Network tab — есть ли запрос к /config/modules/deep_analysis/settings')