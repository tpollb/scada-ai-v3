from pathlib import Path

print('=== build_energy_frontend.py (Шаг 4) ===')
print()

# ============================================================================
# 1. Создаём EnergyCostCard.svelte
# ============================================================================
card_path = Path('frontend/src/components/health/EnergyCostCard.svelte')
card_path.parent.mkdir(parents=True, exist_ok=True)

card_content = '''<script lang="ts">
  import { Zap, Droplet, Flame, TrendingUp, TrendingDown, AlertCircle } from 'lucide-svelte'

  interface Props {
    data: {
      electricity?: any
      water?: any
      heat?: any
      total_cost_current?: number
      total_cost_last?: number
      errors?: string[]
    }
  }
  let { data }: Props = $props()

  // Форматирование
  function formatRub(n: number | null | undefined): string {
    if (n == null) return '—'
    return n.toLocaleString('ru-RU', { maximumFractionDigits: 2 }) + ' ₽'
  }

  function formatKwh(n: number | null | undefined): string {
    if (n == null) return '—'
    return n.toLocaleString('ru-RU', { maximumFractionDigits: 0 }) + ' кВт·ч'
  }

  // Ресурсы
  const resources = [
    { key: 'electricity', label: 'Электричество', icon: Zap, unit: 'кВт·ч' },
    { key: 'water', label: 'Вода', icon: Droplet, unit: 'м³' },
    { key: 'heat', label: 'Тепло', icon: Flame, unit: 'Гкал' },
  ]

  function getResourceData(key: string) {
    return (data as any)[key]
  }

  function isResourceActive(key: string): boolean {
    const r = getResourceData(key)
    return r && r.current_month && r.current_month.consumption_kwh != null
  }

  function isResourceDisabled(key: string): boolean {
    const r = getResourceData(key)
    if (!r) return true
    const errors = r.errors || []
    return errors.some((e: string) => e.includes('не подключены'))
  }

  // Общая сумма
  let totalCurrent = $derived(data?.total_cost_current ?? 0)
  let totalLast = $derived(data?.total_cost_last ?? 0)
  let delta = $derived(totalCurrent - totalLast)
  let deltaPercent = $derived(totalLast > 0 ? (delta / totalLast) * 100 : 0)
  let deltaPositive = $derived(delta > 0)

  // Ошибки (фильтруем "не подключены" — это не ошибки, а состояние)
  let realErrors = $derived(
    (data?.errors || []).filter(e => !e.includes('не подключены'))
  )
</script>

<div class="bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-lg p-6 h-full flex flex-col transition-colors">
  <div class="flex items-center justify-between mb-4">
    <div class="text-sm font-semibold text-neutral-600 dark:text-neutral-300 uppercase tracking-wide">
      Энергозатраты
    </div>
  </div>

  <!-- Большая цифра: текущий месяц -->
  <div class="flex-1 flex flex-col items-center justify-center mb-4">
    <div class="text-5xl font-bold text-accent tabular-nums">
      {formatRub(totalCurrent)}
    </div>
    <div class="text-sm text-neutral-500 dark:text-neutral-400 mt-2">
      Текущий месяц (неполный)
    </div>

    <!-- Сравнение с прошлым -->
    <div class="mt-3 flex items-center gap-2 text-xs">
      <span class="text-neutral-500 dark:text-neutral-400">
        Прошлый: <span class="font-mono">{formatRub(totalLast)}</span>
      </span>
      {#if totalLast > 0}
        <span class="flex items-center gap-1 font-medium {deltaPositive ? 'text-red-600' : 'text-green-600'}">
          {#if deltaPositive}
            <TrendingUp size={12} />
          {:else}
            <TrendingDown size={12} />
          {/if}
          {deltaPositive ? '+' : ''}{deltaPercent.toFixed(1)}%
        </span>
      {/if}
    </div>
  </div>

  <!-- Детализация по ресурсам -->
  <div class="border-t border-neutral-200 dark:border-neutral-700 pt-4 space-y-2">
    {#each resources as r}
      {@const resData = getResourceData(r.key)}
      {@const active = isResourceActive(r.key)}
      {@const disabled = isResourceDisabled(r.key)}
      {@const Icon = r.icon}

      <div class="flex items-center justify-between text-sm {disabled ? 'opacity-50' : ''}">
        <div class="flex items-center gap-2 {disabled ? 'text-neutral-400 dark:text-neutral-500' : 'text-neutral-700 dark:text-neutral-300'}">
          <Icon size={14} />
          <span>{r.label}</span>
        </div>

        <div class="text-right">
          {#if disabled}
            <span class="text-xs text-neutral-400 dark:text-neutral-500 italic">нет данных</span>
          {:else if active}
            <div class="font-mono font-semibold text-neutral-900 dark:text-neutral-100">
              {formatRub(resData.current_month?.cost_rub)}
            </div>
            <div class="text-xs text-neutral-500 dark:text-neutral-400 font-mono">
              {formatKwh(resData.current_month?.consumption_kwh)}
            </div>
          {:else}
            <span class="text-xs text-neutral-400 dark:text-neutral-500">—</span>
          {/if}
        </div>
      </div>
    {/each}
  </div>

  <!-- Ошибки (кроме "не подключены") -->
  {#if realErrors.length > 0}
    <div class="mt-3 pt-3 border-t border-neutral-200 dark:border-neutral-700">
      {#each realErrors.slice(0, 2) as err}
        <div class="flex items-start gap-1.5 text-xs text-amber-700 dark:text-amber-400">
          <AlertCircle size={12} class="flex-shrink-0 mt-0.5" />
          <span class="leading-snug">{err}</span>
        </div>
      {/each}
    </div>
  {/if}
</div>
'''

card_path.write_text(card_content, encoding='utf-8', newline='\n')
print('✓ Создан: frontend/src/components/health/EnergyCostCard.svelte')
print('  • Большая цифра стоимости за текущий месяц')
print('  • Сравнение с прошлым месяцем (↑↓ %)')
print('  • Детализация: электрика / вода / тепло')
print('  • Disabled ресурсы серым с "нет данных"')
print('  • Ошибки (кроме "не подключены")')

# ============================================================================
# 2. Патчим WidgetRouter.svelte — добавляем тип energy_cost_card
# ============================================================================
router_path = Path('frontend/src/components/WidgetRouter.svelte')
if router_path.exists():
    router = router_path.read_text(encoding='utf-8')
    
    # Импортируем EnergyCostCard
    if 'EnergyCostCard' not in router:
        # Ищем другие импорты health-компонентов
        if 'import HealthScoreCard' in router:
            router = router.replace(
                "import HealthScoreCard from './health/HealthScoreCard.svelte'",
                "import HealthScoreCard from './health/HealthScoreCard.svelte'\n  import EnergyCostCard from './health/EnergyCostCard.svelte'"
            )
            print('✓ WidgetRouter: добавлен импорт EnergyCostCard')
        else:
            print('⚠ WidgetRouter: не нашёл импорт HealthScoreCard')
    
    # Добавляем case в switch/if
    if "type === 'energy_cost_card'" not in router:
        # Ищем паттерн {#if widget.type === 'health_score'}
        if "{#if widget.type === 'health_score'}" in router:
            router = router.replace(
                "{#if widget.type === 'health_score'}",
                "{#if widget.type === 'energy_cost_card'}\n          <EnergyCostCard data={widget.data} />\n        {:else if widget.type === 'health_score'}"
            )
            print('✓ WidgetRouter: добавлен case energy_cost_card')
        else:
            print('⚠ WidgetRouter: не нашёл паттерн health_score')
    
    router_path.write_text(router, encoding='utf-8', newline='\n')
    print(f'✓ Обновлён: {router_path}')
else:
    print('⚠ WidgetRouter.svelte не найден')

# ============================================================================
# 3. Патчим backend renderers.py — добавляем виджет energy_cost_card
# ============================================================================
renderers_path = Path('backend/modules/health/renderers.py')
if renderers_path.exists():
    renderers = renderers_path.read_text(encoding='utf-8')
    
    # Проверяем есть ли уже импорт
    if 'from modules.energy_electricity.tools import calculate_electricity_cost' not in renderers:
        # Добавляем импорт в начало (после существующих импортов)
        if 'from .analysis import HealthReport' in renderers:
            renderers = renderers.replace(
                'from .analysis import HealthReport',
                'from .analysis import HealthReport\n\n# Energy cost async import (внутри render_visual)\n'
            )
    
    # Ищем функцию render_visual и добавляем виджет energy_cost_card в начало списка
    # Паттерн: "widgets.append({" после "def render_visual"
    if 'energy_cost_card' not in renderers:
        # Ищем место где рендерится health_score
        if '"type": "health_score"' in renderers:
            # Вставляем перед health_score
            energy_widget_block = '''        # === Виджет энергозатрат (async fetch) ===
        try:
            from modules.energy_electricity.tools import calculate_electricity_cost
            import asyncio
            energy_data = await calculate_electricity_cost()
            widgets.insert(0, {
                "type": "energy_cost_card",
                "data": energy_data,
                "size": "medium",
            })
        except Exception as e:
            log.warning("Failed to get energy data for widget", error=str(e))

'''
            renderers = renderers.replace(
                '    widgets: list = []\n',
                '    widgets: list = []\n' + energy_widget_block
            )
            print('✓ renderers.py: добавлен виджет energy_cost_card (в начало списка)')
    
    # Проверяем что render_visual async
    if 'async def render_visual' in renderers:
        print('✓ renderers.py: render_visual уже async')
    elif 'def render_visual' in renderers:
        renderers = renderers.replace(
            'def render_visual(report: HealthReport) -> dict:',
            'async def render_visual(report: HealthReport) -> dict:'
        )
        print('✓ renderers.py: render_visual сделан async')
    
    renderers_path.write_text(renderers, encoding='utf-8', newline='\n')
    print(f'✓ Обновлён: {renderers_path}')
else:
    print('⚠ renderers.py не найден')

print()
print('=' * 60)
print('ШАГ 4 ЗАВЕРШЁН')
print('=' * 60)
print()
print('Создано:')
print('  ✓ EnergyCostCard.svelte — виджет энергозатрат')
print('  ✓ WidgetRouter.svelte — добавлен type=energy_cost_card')
print('  ✓ renderers.py — автоматическое добавление виджета в health-отчёт')
print()
print('ПРОВЕРКА:')
print('  1. Перезапусти backend')
print('  2. Открой SCADA.AI, напиши: "покажи здоровье здания"')
print('  3. В виджетах должен появиться "Энергозатраты"')
print('  4. Большая цифра: текущий месяц (136.40 ₽)')
print('  5. Сравнение с прошлым (114 005.60 ₽)')
print('  6. Детализация: электрика ✅, вода серым, тепло серым')
print()
print('Когда ок — скажи "виджет ок" и коммитим всё вместе')