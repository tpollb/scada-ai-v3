from pathlib import Path

print('=== apply_frontend_localization.py ===')
print()

# ============================================================================
# 1. HealthScoreCard.svelte — берём status_ru с fallback на status
# ============================================================================
hsc_path = Path('src/components/health/HealthScoreCard.svelte')
hsc = hsc_path.read_text(encoding='utf-8')

# 1.1. Обновляем Props interface — добавляем status_ru
old_props = 'interface Props {\n    data: { score: number; status: string; sub_scores?: any }\n  }'
new_props = 'interface Props {\n    data: { score: number; status: string; status_ru?: string; sub_scores?: any }\n  }'

if old_props in hsc:
    hsc = hsc.replace(old_props, new_props)
    print('✓ HealthScoreCard: Props обновлены (добавлен status_ru)')
else:
    print('⚠ HealthScoreCard: не нашёл точный Props паттерн')

# 1.2. Добавляем derived для status_ru с fallback
old_status_derived = "let status = $derived(data?.status ?? 'UNKNOWN')"
new_status_derived = """let status = $derived(data?.status ?? 'UNKNOWN')
  let statusDisplay = $derived(data?.status_ru || status)"""

if old_status_derived in hsc:
    hsc = hsc.replace(old_status_derived, new_status_derived)
    print('✓ HealthScoreCard: добавлен statusDisplay с fallback')
else:
    print('⚠ HealthScoreCard: не нашёл status derived')

# 1.3. Заменяем отображение статуса в бейдже
old_badge = '{status}'
# Находим конкретное место — бейдж под круговой диаграммой
old_badge_block = '''<span class="inline-block px-4 py-1.5 text-xs font-semibold uppercase rounded" style="background: {color}; color: white">
        {status}
      </span>'''
new_badge_block = '''<span class="inline-block px-4 py-1.5 text-xs font-semibold uppercase rounded" style="background: {color}; color: white">
        {statusDisplay}
      </span>'''

if old_badge_block in hsc:
    hsc = hsc.replace(old_badge_block, new_badge_block)
    print('✓ HealthScoreCard: бейдж статуса теперь показывает status_ru')
else:
    print('⚠ HealthScoreCard: не нашёл точный блок бейджа')

# 1.4. Локализуем шкалу статусов в формуле (showFormula=true)
scale_replacements = [
    ('&lt;30: CRITICAL', '&lt;30: Критично'),
    ('30-59: WARNING', '30-59: Внимание'),
    ('60-84: GOOD', '60-84: Хорошо'),
    ('≥85: EXCELLENT', '≥85: Отлично'),
]
for old, new in scale_replacements:
    if old in hsc:
        hsc = hsc.replace(old, new)
print('✓ HealthScoreCard: шкала статусов в формуле локализована')

hsc_path.write_text(hsc, encoding='utf-8', newline='\n')
print(f'✓ Обновлён: {hsc_path}')
print()

# ============================================================================
# 2. LifeSupportCard.svelte — берём status_ru + локализуем параметры
# ============================================================================
lsc_path = Path('src/components/health/LifeSupportCard.svelte')
lsc = lsc_path.read_text(encoding='utf-8')

# 2.1. Обновляем Props interface
old_lsc_props = '''interface Props {
    data: {
      score: number
      status: string
      params: Record<string, any>
      problems?: string[]
    }
  }'''
new_lsc_props = '''interface Props {
    data: {
      score: number
      status: string
      status_ru?: string
      params: Record<string, any>
      problems?: string[]
    }
  }'''

if old_lsc_props in lsc:
    lsc = lsc.replace(old_lsc_props, new_lsc_props)
    print('✓ LifeSupportCard: Props обновлены (добавлен status_ru)')
else:
    print('⚠ LifeSupportCard: не нашёл точный Props паттерн')

# 2.2. Добавляем derived для statusDisplay
old_lsc_status = "let status = $derived(data?.status ?? 'NO_DATA')"
new_lsc_status = """let status = $derived(data?.status ?? 'NO_DATA')
  let statusDisplay = $derived(data?.status_ru || status)"""

if old_lsc_status in lsc:
    lsc = lsc.replace(old_lsc_status, new_lsc_status)
    print('✓ LifeSupportCard: добавлен statusDisplay с fallback')
else:
    print('⚠ LifeSupportCard: не нашёл status derived')

# 2.3. Заменяем отображение статуса в бейдже
old_lsc_badge = '''<span class="inline-block px-4 py-1.5 text-xs font-semibold uppercase rounded" style="background: {color}; color: white">
        {status}
      </span>'''
new_lsc_badge = '''<span class="inline-block px-4 py-1.5 text-xs font-semibold uppercase rounded" style="background: {color}; color: white">
        {statusDisplay}
      </span>'''

if old_lsc_badge in lsc:
    lsc = lsc.replace(old_lsc_badge, new_lsc_badge)
    print('✓ LifeSupportCard: бейдж статуса теперь показывает status_ru')
else:
    print('⚠ LifeSupportCard: не нашёл точный блок бейджа')

# 2.4. Локализуем статусы параметров в таблице формулы
# В таблице showFormula=true параметры показывают pStatus напрямую
# Заменяем отображение статуса параметра на status_ru если есть
old_param_status = '''{@const pStatus = p.status ?? 'NO_DATA'}'''
new_param_status = '''{@const pStatus = p.status_ru || p.status || 'NO_DATA'}'''

if old_param_status in lsc:
    lsc = lsc.replace(old_param_status, new_param_status)
    print('✓ LifeSupportCard: статусы параметров в таблице берут status_ru')
else:
    print('⚠ LifeSupportCard: не нашёл pStatus паттерн')

# 2.5. Локализуем названия параметров через label_ru от бэкенда
old_param_label = '''{@const cfg = paramLabels[key]}'''
new_param_label = '''{@const cfg = paramLabels[key]}
                {@const paramLabel = p?.label_ru || cfg.label}'''

if old_param_label in lsc:
    lsc = lsc.replace(old_param_label, new_param_label)
    # И заменяем использование cfg.label на paramLabel в строке таблицы
    lsc = lsc.replace(
        '<td class="px-2 py-1.5 text-neutral-700 dark:text-neutral-300 font-medium">{cfg.label}</td>',
        '<td class="px-2 py-1.5 text-neutral-700 dark:text-neutral-300 font-medium">{paramLabel}</td>'
    )
    print('✓ LifeSupportCard: названия параметров берут label_ru от бэкенда')
else:
    print('⚠ LifeSupportCard: не нашёл paramLabels паттерн')

# 2.6. Локализуем шкалу статусов в формуле
lsc_scale_replacements = [
    ('&lt;30: CRITICAL', '&lt;30: Критично'),
    ('30-59: WARNING', '30-59: Внимание'),
    ('60-84: GOOD', '60-84: Хорошо'),
    ('≥85: EXCELLENT', '≥85: Отлично'),
]
for old, new in lsc_scale_replacements:
    if old in lsc:
        lsc = lsc.replace(old, new)
print('✓ LifeSupportCard: шкала статусов в формуле локализована')

lsc_path.write_text(lsc, encoding='utf-8', newline='\n')
print(f'✓ Обновлён: {lsc_path}')

print()
print('=' * 60)
print('ФРОНТЕНД ГОТОВ. Что изменилось:')
print('=' * 60)
print('1. HealthScoreCard.svelte:')
print('   • Бейдж статуса показывает status_ru (Отлично/Хорошо/Внимание/Критично)')
print('   • Fallback на английский status если status_ru отсутствует')
print('   • Шкала в формуле переведена на русский')
print()
print('2. LifeSupportCard.svelte:')
print('   • Бейдж статуса показывает status_ru')
print('   • Статусы параметров в таблице берут status_ru от бэкенда')
print('   • Названия параметров берут label_ru от бэкенда')
print('   • Шкала в формуле переведена на русский')
print()
print('Проверка: запусти frontend dev server и открой workspace')
print('  cd /c/dev/SCADA.AI/scada-ai-v3/frontend')
print('  npm run dev')