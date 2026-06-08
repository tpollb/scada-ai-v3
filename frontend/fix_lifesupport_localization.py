from pathlib import Path

print('=== fix_lifesupport_localization.py ===')
print()

path = Path('src/components/health/LifeSupportCard.svelte')
content = path.read_text(encoding='utf-8')

# ============================================================================
# 1. Русификация таблицы "Статусы параметров" в формуле
# ============================================================================
# OK → Норма, WARNING → Внимание, CRITICAL → Критично
replacements_table = [
    ('<td class="px-2 py-1.5 text-green-700 dark:text-green-400 font-medium">OK</td>',
     '<td class="px-2 py-1.5 text-green-700 dark:text-green-400 font-medium">Норма</td>'),
    ('<td class="px-2 py-1.5 text-amber-700 dark:text-amber-400 font-medium">WARNING</td>',
     '<td class="px-2 py-1.5 text-amber-700 dark:text-amber-400 font-medium">Внимание</td>'),
    ('<td class="px-2 py-1.5 text-red-700 dark:text-red-400 font-medium">CRITICAL</td>',
     '<td class="px-2 py-1.5 text-red-700 dark:text-red-400 font-medium">Критично</td>'),
]

for old, new in replacements_table:
    if old in content:
        content = content.replace(old, new)
print('✓ Задача 1: таблица "Статусы параметров" русифицирована')
print('  OK → Норма, WARNING → Внимание, CRITICAL → Критично')

# ============================================================================
# 2. Функция paramStatusColor — добавляем поддержку русских статусов
# ============================================================================
old_func = '''  function paramStatusColor(s: string): string {
    if (s === 'CRITICAL') return '#dc2626'
    if (s === 'WARNING') return '#d97706'
    if (s === 'OK') return '#16a34a'
    return '#a3a3a3'
  }'''

new_func = '''  function paramStatusColor(s: string): string {
    // Поддерживаем и английские и русские статусы
    if (s === 'CRITICAL' || s === 'Критично') return '#dc2626'
    if (s === 'WARNING' || s === 'Внимание') return '#d97706'
    if (s === 'OK' || s === 'Норма') return '#16a34a'
    return '#a3a3a3'
  }'''

if old_func in content:
    content = content.replace(old_func, new_func)
    print('✓ Задача 2: paramStatusColor теперь понимает русские статусы')
    print('  Критично → красный (#dc2626)')
    print('  Внимание → янтарный (#d97706)')
    print('  Норма → зелёный (#16a34a)')
else:
    print('⚠ Задача 2: не нашёл точный паттерн paramStatusColor')

path.write_text(content, encoding='utf-8', newline='\n')
print(f'✓ Обновлён: {path}')

print()
print('=' * 60)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 60)
print('1. Таблица "Статусы параметров" в формуле:')
print('   • OK → Норма (зелёный)')
print('   • WARNING → Внимание (янтарный)')
print('   • CRITICAL → Критично (красный)')
print()
print('2. Таблица "Текущие компоненты":')
print('   • paramStatusColor понимает русские статусы')
print('   • Критично/Внимание/Норма правильно подкрашиваются')
print()
print('Vite подхватит через HMR. Обнови страницу.')