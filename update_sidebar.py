from pathlib import Path

print('=== update_sidebar.py ===')
print()

# Читаем Home.svelte
home_path = Path('frontend/src/routes/Home.svelte')
content = home_path.read_text(encoding='utf-8')

# 1. Добавляем импорты иконок Wrench, Package, ChevronDown, ChevronUp
if "import { Settings" in content:
    old_import = "import { Settings, Volume2, Database, Cpu, Zap, Clock, CheckCircle, XCircle, AlertCircle, Sun, Moon, Terminal } from 'lucide-svelte'"
    new_import = "import { Settings, Volume2, Database, Cpu, Zap, Clock, CheckCircle, XCircle, AlertCircle, Sun, Moon, Terminal, Wrench, Package, ChevronDown, ChevronUp } from 'lucide-svelte'"
    if old_import in content:
        content = content.replace(old_import, new_import)
        print('✓ Добавлены импорты Wrench, Package, ChevronDown, ChevronUp')
    else:
        print('⚠ Точный паттерн импорта не найден — проверь вручную')

# 2. Добавляем state для collapsed списков (после currentWidgets)
if 'let collapsedModules = $state(false)' not in content:
    if 'let currentWidgets = $state<any[]>([]);' in content:
        content = content.replace(
            'let currentWidgets = $state<any[]>([]);',
            '''let currentWidgets = $state<any[]>([]);
  let collapsedModules = $state(false);
  let collapsedTools = $state(false);'''
        )
        print('✓ Добавлены collapsedModules и collapsedTools state')
    elif 'let currentWidgets = $state<any[]>([])' in content:
        # Без точки с запятой
        content = content.replace(
            'let currentWidgets = $state<any[]>([])',
            '''let currentWidgets = $state<any[]>([])
  let collapsedModules = $state(false)
  let collapsedTools = $state(false)'''
        )
        print('✓ Добавлены collapsedModules и collapsedTools state (без ;)')
    else:
        print('⚠ Не нашёл currentWidgets — добавь state вручную')

# 3. Заменяем блок Модулей на раскрывающийся (ищем по ключевым строкам)
# Ищем паттерн с <Cpu> для Модулей
if '<Cpu size={14} />' in content and 'Модули</span>' in content:
    # Находим блок Модулей и заменяем его
    import re
    # Паттерн: от <div class="flex items-center justify-between"> с Cpu и Модули 
    # до </div> закрывающего flex flex-wrap
    pattern = r'<div class="flex items-center justify-between">\s*<div class="flex items-center gap-2 text-neutral-700 dark:text-neutral-300">\s*<Cpu size=\{14\} />\s*<span>Модули</span>\s*</div>\s*<span class="text-xs font-mono text-neutral-500 dark:text-neutral-400">\{systemInfo\.modules\.length\} шт</span>\s*</div>\s*<div class="flex flex-wrap gap-1 pl-6">\s*\{#each systemInfo\.modules as mod\}\s*<span class="px-2 py-0\.5 bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded text-xs font-mono text-neutral-700 dark:text-neutral-300">\s*\{mod\}\s*</span>\s*\{/each\}\s*</div>'
    
    new_modules_block = '''<button
              type="button"
              onclick={() => collapsedModules = !collapsedModules}
              class="w-full flex items-center justify-between hover:bg-neutral-100 dark:hover:bg-neutral-800 rounded px-1 -mx-1 transition"
            >
              <div class="flex items-center gap-2 text-neutral-700 dark:text-neutral-300">
                <Package size={14} />
                <span>Модули</span>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-xs font-mono text-neutral-500 dark:text-neutral-400">{systemInfo.modules.length} шт</span>
                {#if collapsedModules}
                  <ChevronDown size={14} class="text-neutral-400" />
                {:else}
                  <ChevronUp size={14} class="text-neutral-400" />
                {/if}
              </div>
            </button>
            {#if !collapsedModules}
              <div class="flex flex-wrap gap-1 pl-6 mt-1">
                {#each systemInfo.modules as mod}
                  <span class="px-2 py-0.5 bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded text-xs font-mono text-neutral-700 dark:text-neutral-300">
                    {mod}
                  </span>
                {/each}
              </div>
            {/if}'''
    
    if re.search(pattern, content):
        content = re.sub(pattern, new_modules_block, content)
        print('✓ Блок Модулей заменён на раскрывающийся с иконкой Package')
    else:
        print('⚠ Regex не нашёл блок Модулей — проверь форматирование')

# 4. Заменяем блок Инструментов на раскрывающийся
if '<Zap size={14} />' in content and 'Инструменты</span>' in content:
    pattern = r'<div class="flex items-center justify-between mt-2">\s*<div class="flex items-center gap-2 text-neutral-700 dark:text-neutral-300">\s*<Zap size=\{14\} />\s*<span>Инструменты</span>\s*</div>\s*<span class="text-xs font-mono text-neutral-500 dark:text-neutral-400">\{systemInfo\.tools_names\?\.length \?\? systemInfo\.tools_count \?\? 0\} шт</span>\s*</div>\s*\{#if systemInfo\.tools_names && systemInfo\.tools_names\.length > 0\}\s*<div class="flex flex-wrap gap-1 pl-6 mt-1">\s*\{#each systemInfo\.tools_names as tool\}\s*<span class="px-2 py-0\.5 bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded text-xs font-mono text-neutral-700 dark:text-neutral-300">\s*\{tool\}\s*</span>\s*\{/each\}\s*</div>\s*\{/if\}'
    
    new_tools_block = '''<button
              type="button"
              onclick={() => collapsedTools = !collapsedTools}
              class="w-full flex items-center justify-between mt-2 hover:bg-neutral-100 dark:hover:bg-neutral-800 rounded px-1 -mx-1 transition"
            >
              <div class="flex items-center gap-2 text-neutral-700 dark:text-neutral-300">
                <Wrench size={14} />
                <span>Инструменты</span>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-xs font-mono text-neutral-500 dark:text-neutral-400">{systemInfo.tools_names?.length ?? systemInfo.tools_count ?? 0} шт</span>
                {#if collapsedTools}
                  <ChevronDown size={14} class="text-neutral-400" />
                {:else}
                  <ChevronUp size={14} class="text-neutral-400" />
                {/if}
              </div>
            </button>
            {#if !collapsedTools && systemInfo.tools_names && systemInfo.tools_names.length > 0}
              <div class="flex flex-wrap gap-1 pl-6 mt-1">
                {#each systemInfo.tools_names as tool}
                  <span class="px-2 py-0.5 bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded text-xs font-mono text-neutral-700 dark:text-neutral-300">
                    {tool}
                  </span>
                {/each}
              </div>
            {/if}'''
    
    if re.search(pattern, content):
        content = re.sub(pattern, new_tools_block, content)
        print('✓ Блок Инструменты заменён на раскрывающийся с иконкой Wrench')
    else:
        print('⚠ Regex не нашёл блок Инструменты — проверь форматирование')

# Сохраняем
home_path.write_text(content, encoding='utf-8', newline='\n')
print()
print('✅ Home.svelte обновлён')
print()
print('ИЗМЕНЕНИЯ:')
print('  • Модули: иконка Package (коробка), раскрывающийся список')
print('  • Инструменты: иконка Wrench (гаечный ключ), раскрывающийся список')
print('  • Добавлены ChevronDown/ChevronUp для индикации состояния')
print('  • По умолчанию списки раскрыты (collapsedModules = false)')
print()
print('Vite подхватит через HMR.')
print('Попробуй кликнуть на заголовки "Модули" и "Инструменты" — они должны сворачиваться.')
print()
print('Когда ок — скажи "сайдбар ок" и коммитим')