from pathlib import Path

print('=== fix_frontend_4tasks.py ===')
print()

# ============================================================================
# ЗАДАЧА 1 + 2: LifeSupportCard.svelte
# - Исправить баг с порядком переменных в формуле
# - Убрать блок "Проблемы"
# ============================================================================
lsc_path = Path('src/components/health/LifeSupportCard.svelte')
lsc = lsc_path.read_text(encoding='utf-8')

# 1. Убираем блок проблем (между бейджем статуса и {:else})
old_problems_block = '''    {#if problems.length > 0}
      <div class="pt-4 border-t border-neutral-200 dark:border-neutral-700">
        <div class="text-xs text-red-700 dark:text-red-400 font-semibold mb-2 uppercase tracking-wide">
          Проблемы ({problems.length})
        </div>
        <div class="space-y-1.5">
          {#each problems.slice(0, 4) as p}
            <div class="text-sm text-red-700 dark:text-red-400 flex items-start gap-2">
              <span class="text-red-500 flex-shrink-0 mt-1">●</span>
              <span class="leading-snug">{p}</span>
            </div>
          {/each}
          {#if problems.length > 4}
            <div class="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5 pl-5">...и ещё {problems.length - 4}</div>
          {/if}
        </div>
      </div>
    {/if}'''

if old_problems_block in lsc:
    lsc = lsc.replace(old_problems_block, '')
    print('✓ Задача 2: блок "Проблемы" удалён из LifeSupportCard')
else:
    print('⚠ Задача 2: не нашёл точный блок проблем')

# 2. Исправляем порядок переменных в таблице формулы
# Было: paramLabel использует p ДО того как p объявлен
old_formula_vars = '''              {@const cfg = paramLabels[key]}
                {@const paramLabel = p?.label_ru || cfg.label}
              {@const p = params[key]}'''

new_formula_vars = '''              {@const cfg = paramLabels[key]}
              {@const p = params[key]}
              {@const paramLabel = p?.label_ru || cfg.label}'''

if old_formula_vars in lsc:
    lsc = lsc.replace(old_formula_vars, new_formula_vars)
    print('✓ Задача 1: исправлен порядок переменных в формуле (кнопка i теперь работает)')
else:
    print('⚠ Задача 1: не нашёл точный паттерн переменных в формуле')

lsc_path.write_text(lsc, encoding='utf-8', newline='\n')
print(f'✓ Обновлён: {lsc_path}')
print()

# ============================================================================
# ЗАДАЧА 3: EnvironmentalPanel.svelte — локализация статусов
# ============================================================================
env_path = Path('src/components/health/EnvironmentalPanel.svelte')
env = env_path.read_text(encoding='utf-8')

# Добавляем функцию локализации статусов после statusColor
old_status_color = '''  function statusColor(status: string): string {
    if (status === 'CRITICAL') return 'text-red-600 bg-red-50 border-red-200'
    if (status === 'WARNING') return 'text-amber-600 bg-amber-50 border-amber-200'
    return 'text-green-700 bg-green-50 border-green-200'
  }'''

new_status_color = '''  const STATUS_RU: Record<string, string> = {
    'OK': 'Норма',
    'WARNING': 'Внимание',
    'CRITICAL': 'Критично',
    'NO_DATA': 'Нет данных',
  }

  function statusRu(status: string): string {
    return STATUS_RU[status] || status
  }

  function statusColor(status: string): string {
    if (status === 'CRITICAL') return 'text-red-600 bg-red-50 border-red-200'
    if (status === 'WARNING') return 'text-amber-600 bg-amber-50 border-amber-200'
    return 'text-green-700 bg-green-50 border-green-200'
  }'''

if old_status_color in env:
    env = env.replace(old_status_color, new_status_color)
    print('✓ Задача 3: добавлена функция statusRu() в EnvironmentalPanel')
else:
    print('⚠ Задача 3: не нашёл statusColor функцию')

# Заменяем отображение статуса в карточках параметров
# Было: <span class="text-xs px-2 py-0.5 rounded font-medium">{d.status || 'OK'}</span>
old_card_status = '''<span class="text-xs px-2 py-0.5 rounded font-medium">{d.status || 'OK'}</span>'''
new_card_status = '''<span class="text-xs px-2 py-0.5 rounded font-medium">{statusRu(d.status || 'OK')}</span>'''

count = env.count(old_card_status)
if count > 0:
    env = env.replace(old_card_status, new_card_status)
    print(f'✓ Задача 3: локализованы статусы в карточках параметров ({count} шт.)')
else:
    print('⚠ Задача 3: не нашёл статус в карточках')

# Локализуем статусы в таблице тегов модалки (OK / БИТЫЙ уже на русском, но проверим)
# Статусы в hourly таблице: OK / ! / !!! — оставим как есть (это символы, не текст)

env_path.write_text(env, encoding='utf-8', newline='\n')
print(f'✓ Обновлён: {env_path}')
print()

# ============================================================================
# ЗАДАЧА 4: AlarmsPanel.svelte — локализация HIGH/MEDIUM/LOW
# ============================================================================
alarms_path = Path('src/components/health/AlarmsPanel.svelte')
alarms = alarms_path.read_text(encoding='utf-8')

# Заменяем priorityConfig на русские лейблы
old_priority_config = """  const priorityConfig: Record<string, { label: string; color: string; bg: string }> = {
    high: { label: 'HIGH', color: 'text-red-700', bg: 'bg-red-50 border-red-200' },
    medium: { label: 'MEDIUM', color: 'text-amber-700', bg: 'bg-amber-50 border-amber-200' },
    low: { label: 'LOW', color: 'text-neutral-700', bg: 'bg-neutral-50 border-neutral-200' },
  }"""

new_priority_config = """  const priorityConfig: Record<string, { label: string; color: string; bg: string }> = {
    high: { label: 'Высокий', color: 'text-red-700', bg: 'bg-red-50 border-red-200' },
    medium: { label: 'Средний', color: 'text-amber-700', bg: 'bg-amber-50 border-amber-200' },
    low: { label: 'Низкий', color: 'text-neutral-700', bg: 'bg-neutral-50 border-neutral-200' },
  }"""

if old_priority_config in alarms:
    alarms = alarms.replace(old_priority_config, new_priority_config)
    print('✓ Задача 4: priorityConfig переведён на русский (Высокий/Средний/Низкий)')
else:
    print('⚠ Задача 4: не нашёл priorityConfig')

# В таблице журнала приоритет берётся через cfg.label — уже будет русский после замены выше
# Но в топ-issues отображается {issue.priority} — это английский ключ от бэкенда
# Нужно заменить на priorityConfig[issue.priority]?.label
old_top_priority = '''<span class="text-xs px-2 py-0.5 rounded font-medium flex-shrink-0 {priorityConfig[issue.priority]?.bg || ''} {priorityConfig[issue.priority]?.color || ''}">
                {issue.priority}
              </span>'''

new_top_priority = '''<span class="text-xs px-2 py-0.5 rounded font-medium flex-shrink-0 {priorityConfig[issue.priority]?.bg || ''} {priorityConfig[issue.priority]?.color || ''}">
                {priorityConfig[issue.priority]?.label || issue.priority}
              </span>'''

if old_top_priority in alarms:
    alarms = alarms.replace(old_top_priority, new_top_priority)
    print('✓ Задача 4: топ-issues теперь показывает русский приоритет')
else:
    print('⚠ Задача 4: не нашёл топ-issues приоритет')

# В фильтре модалки кнопки используют priorityConfig[p].label — уже будет русский
# Но кнопка "Все" использует хардкод 'Все' — это ок

# В таблице журнала колонка "Приоритет" использует cfg.label — уже будет русский

alarms_path.write_text(alarms, encoding='utf-8', newline='\n')
print(f'✓ Обновлён: {alarms_path}')

print()
print('=' * 60)
print('ФРОНТЕНД ГОТОВ. Что изменено:')
print('=' * 60)
print('1. LifeSupportCard: исправлен порядок переменных → кнопка (i) работает')
print('2. LifeSupportCard: удалён блок "Проблемы"')
print('3. EnvironmentalPanel: статусы OK→Норма, WARNING→Внимание, CRITICAL→Критично')
print('4. AlarmsPanel: HIGH→Высокий, MEDIUM→Средний, LOW→Низкий')
print('   (везде: карточки, таблица журнала, топ-issues, фильтр модалки)')
print()
print('Vite подхватит через HMR. Обнови страницу.')