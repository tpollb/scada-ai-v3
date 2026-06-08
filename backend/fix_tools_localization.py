from pathlib import Path

print('=== fix_tools_localization_v2.py ===')
print()

# Используем относительные пути (работаем из корня backend)
backend_system = Path('api/routes/system.py')
frontend_home = Path('../frontend/src/routes/Home.svelte')

# Проверяем что файлы существуют
if not backend_system.exists():
    print(f'❌ Backend файл не найден: {backend_system.absolute()}')
    print('Убедись что ты в директории backend/')
    exit(1)

if not frontend_home.exists():
    print(f'❌ Frontend файл не найден: {frontend_home.absolute()}')
    print('Убедись что структура проекта правильная')
    exit(1)

print(f'✓ Backend: {backend_system.absolute()}')
print(f'✓ Frontend: {frontend_home.absolute()}')
print()

# ============================================================================
# 1. BACKEND: system.py — добавляем tools_names в ответ /system/info
# ============================================================================
content = backend_system.read_text(encoding='utf-8')

# Заменяем возврат — добавляем tools_names
old_return = '''    return {
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "modules": list(registry._modules.keys()),
        "tools_count": len(executor._tools),
        "db_host": settings.db_host,'''

new_return = '''    return {
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "modules": list(registry._modules.keys()),
        "tools_count": len(executor._tools),
        "tools_names": list(executor._tools.keys()),
        "db_host": settings.db_host,'''

if old_return in content:
    content = content.replace(old_return, new_return)
    backend_system.write_text(content, encoding='utf-8', newline='\n')
    print('✓ Backend: system.py — добавлен tools_names в ответ /system/info')
else:
    print('⚠ Backend: не нашёл точный паттерн return блока')

print()

# ============================================================================
# 2. FRONTEND: Home.svelte — локализуем "Tools" и добавляем чипсы имён
# ============================================================================
home = frontend_home.read_text(encoding='utf-8')

# 2.1. Обновляем интерфейс SystemInfo — добавляем tools_names
old_interface = '''    tools_count: number
    db_status: 'ok' | 'error' | 'unknown' '''

new_interface = '''    tools_count: number
    tools_names: string[]
    db_status: 'ok' | 'error' | 'unknown' '''

if old_interface in home:
    home = home.replace(old_interface, new_interface)
    print('✓ Frontend: интерфейс SystemInfo обновлён (добавлен tools_names)')
else:
    print('⚠ Frontend: не нашёл точный паттерн интерфейса')

# 2.2. Заменяем блок "Tools" на "Инструменты" + чипсы
old_tools_block = '''            <div class="flex items-center justify-between mt-2">
              <div class="flex items-center gap-2 text-neutral-700 dark:text-neutral-300">
                <Zap size={14} />
                <span>Tools</span>
              </div>
              <span class="text-xs font-mono text-neutral-500 dark:text-neutral-400">{health?.tools ?? systemInfo.tools_count ?? 0} шт</span>
            </div>'''

new_tools_block = '''            <div class="flex items-center justify-between mt-2">
              <div class="flex items-center gap-2 text-neutral-700 dark:text-neutral-300">
                <Zap size={14} />
                <span>Инструменты</span>
              </div>
              <span class="text-xs font-mono text-neutral-500 dark:text-neutral-400">{systemInfo.tools_names?.length ?? systemInfo.tools_count ?? 0} шт</span>
            </div>
            {#if systemInfo.tools_names && systemInfo.tools_names.length > 0}
              <div class="flex flex-wrap gap-1 pl-6 mt-1">
                {#each systemInfo.tools_names as tool}
                  <span class="px-2 py-0.5 bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded text-xs font-mono text-neutral-700 dark:text-neutral-300">
                    {tool}
                  </span>
                {/each}
              </div>
            {/if}'''

if old_tools_block in home:
    home = home.replace(old_tools_block, new_tools_block)
    print('✓ Frontend: "Tools" → "Инструменты", добавлены чипсы с именами')
else:
    print('⚠ Frontend: не нашёл точный паттерн Tools блока')

frontend_home.write_text(home, encoding='utf-8', newline='\n')
print(f'✓ Обновлён: {frontend_home}')

print()
print('=' * 60)
print('ЧТО ИЗМЕНЕНО:')
print('=' * 60)
print('1. Backend (api/routes/system.py):')
print('   • В ответ /system/info добавлено поле tools_names: list[str]')
print('   • Берётся из executor._tools.keys() — имена зарегистрированных tools')
print()
print('2. Frontend (src/routes/Home.svelte):')
print('   • "Tools" → "Инструменты"')
print('   • Количество: берётся из tools_names.length (если есть)')
print('   • Ниже — чипсы с именами инструментов (как у модулей)')
print('   • Дизайн идентичный модулям: mono шрифт, рамки, отступ pl-6')
print()
print('Перезапусти backend после применения.')
print('Frontend подхватит через HMR.')