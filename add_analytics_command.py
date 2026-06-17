from pathlib import Path

print('=== add_analytics_command.py ===')
print()

PROJECT_ROOT = Path('.')
home_path = PROJECT_ROOT / 'frontend/src/routes/Home.svelte'

content = home_path.read_text(encoding='utf-8')

# Ищем блок где добавляются команды для health и добавляем analytics после него
old_block = '''    if (systemInfo?.modules?.includes('health')) {
      caps.push({ text: 'покажи здоровье здания', category: 'Анализ' })
      caps.push({ text: 'проанализируй системный лог', category: 'Анализ' })
      caps.push({ text: 'покажи логи', category: 'Система', action: 'logs' })
    }
    if (systemInfo?.modules?.includes('schedules')) {'''

new_block = '''    if (systemInfo?.modules?.includes('health')) {
      caps.push({ text: 'покажи здоровье здания', category: 'Анализ' })
      caps.push({ text: 'проанализируй системный лог', category: 'Анализ' })
      caps.push({ text: 'покажи логи', category: 'Система', action: 'logs' })
    }
    if (systemInfo?.modules?.includes('analytics')) {
      caps.push({ text: 'покажи аналитику', category: 'Анализ', action: 'analytics_panel' })
    }
    if (systemInfo?.modules?.includes('schedules')) {'''

if old_block in content:
    content = content.replace(old_block, new_block)
    home_path.write_text(content, encoding='utf-8', newline='\n')
    print('✓ Home.svelte: добавлена команда "покажи аналитику" в категорию "Анализ"')
    print()
    print('=' * 60)
    print('ЧТО ДОБАВЛЕНО:')
    print('=' * 60)
    print()
    print('Новая команда в правой инфопанели:')
    print('  покажи аналитику → Анализ')
    print()
    print('Список команд теперь:')
    print('  • покажи здоровье здания → Анализ')
    print('  • проанализируй системный лог → Анализ')
    print('  • покажи аналитику → Анализ ← НОВАЯ')
    print('  • покажи логи → Система')
    print('  • открой конфигуратор → Настройки')
    print()
    print('Команда появится только если backend вернёт модуль "analytics"')
    print('(systemInfo.modules.includes("analytics"))')
    print()
    print('Frontend перезагрузится автоматически (Vite HMR).')
    print()
    print('Проверка:')
    print('  1. Открой правую инфопанель')
    print('  2. Найди раздел "Доступные команды"')
    print('  3. В категории "Анализ" должна появиться "покажи аналитику"')
    print('  4. Клик на команду → откроется AnalyticsPanel')
else:
    print('⚠ Блок не найден')
    print('Показываю реальное содержимое вокруг "покажи здоровье здания":')
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'покажи здоровье здания' in line:
            start = max(0, i - 5)
            end = min(len(lines), i + 10)
            for j in range(start, end):
                marker = '>>>' if j == i else '   '
                print(f'{marker} {j+1}: {lines[j]}')
            break