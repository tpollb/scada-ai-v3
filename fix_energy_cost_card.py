from pathlib import Path

print('=== fix_energy_cost_card.py ===')
print()

card_path = Path('frontend/src/components/health/EnergyCostCard.svelte')

new_content = '''<script lang="ts">
  import { Zap, Droplet, Flame, TrendingUp, TrendingDown, AlertCircle, Info } from 'lucide-svelte'

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
  let showFormula = $state(false)

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

  function isResourceActive(key: string, period: 'current' | 'last' = 'last'): boolean {
    const r = getResourceData(key)
    return r && r[period + '_month'] && r[period + '_month'].consumption_kwh != null
  }

  function isResourceDisabled(key: string): boolean {
    const r = getResourceData(key)
    if (!r) return true
    const errors = r.errors || []
    return errors.some((e: string) => e.includes('не подключены'))
  }

  // Общая сумма — ПРОШЛЫЙ месяц как основной
  let totalLast = $derived(data?.total_cost_last ?? 0)
  let totalCurrent = $derived(data?.total_cost_current ?? 0)
  let delta = $derived(totalCurrent - totalLast)
  let deltaPercent = $derived(totalLast > 0 ? (delta / totalLast) * 100 : 0)
  let deltaPositive = $derived(delta > 0)

  // Ошибки (фильтруем "не подключены" — это не ошибки, а состояние)
  let realErrors = $derived(
    (data?.errors || []).filter(e => !e.includes('не подключены'))
  )

  // Получаем месяц прошлого периода
  function getLastMonthName(): string {
    const now = new Date()
    const lastMonth = new Date(now.getFullYear(), now.getMonth() - 1, 1)
    return lastMonth.toLocaleDateString('ru-RU', { month: 'long', year: 'numeric' })
  }

  function getCurrentMonthName(): string {
    const now = new Date()
    return now.toLocaleDateString('ru-RU', { month: 'long', year: 'numeric' })
  }
</script>

<div class="bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-lg p-6 h-full flex flex-col transition-colors">
  <div class="flex items-center justify-between mb-4">
    <div class="text-sm font-semibold text-neutral-600 dark:text-neutral-300 uppercase tracking-wide">
      Энергозатраты
    </div>
    <button
      type="button"
      onclick={() => showFormula = !showFormula}
      class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-700 transition text-neutral-500 dark:text-neutral-400 hover:text-neutral-700 dark:hover:text-neutral-200"
      title={showFormula ? 'Скрыть формулу' : 'Показать формулу расчёта'}
    >
      <Info size={16} />
    </button>
  </div>

  {#if !showFormula}
    <!-- Большая цифра: ПРОШЛЫЙ месяц (полные данные) -->
    <div class="flex-1 flex flex-col items-center justify-center mb-4">
      <div class="text-5xl font-bold text-accent tabular-nums">
        {formatRub(totalLast)}
      </div>
      <div class="text-sm text-neutral-500 dark:text-neutral-400 mt-2">
        {getLastMonthName()}
      </div>

      <!-- Текущий месяц (неполный) -->
      {#if totalCurrent > 0}
        <div class="mt-3 flex items-center gap-2 text-xs">
          <span class="text-neutral-500 dark:text-neutral-400">
            Текущий: <span class="font-mono">{formatRub(totalCurrent)}</span>
            <span class="text-neutral-400 dark:text-neutral-500">(неполный месяц)</span>
          </span>
        </div>
      {/if}

      <!-- Сравнение с прошлым -->
      {#if totalLast > 0 && totalCurrent > 0}
        <div class="mt-2 flex items-center gap-2 text-xs">
          <span class="flex items-center gap-1 font-medium {deltaPositive ? 'text-red-600' : 'text-green-600'}">
            {#if deltaPositive}
              <TrendingUp size={12} />
            {:else}
              <TrendingDown size={12} />
            {/if}
            {deltaPositive ? '+' : ''}{deltaPercent.toFixed(1)}% к прошлому
          </span>
        </div>
      {/if}
    </div>

    <!-- Детализация по ресурсам (ПРОШЛЫЙ месяц) -->
    <div class="border-t border-neutral-200 dark:border-neutral-700 pt-4 space-y-2">
      {#each resources as r}
        {@const resData = getResourceData(r.key)}
        {@const activeLast = isResourceActive(r.key, 'last')}
        {@const activeCurrent = isResourceActive(r.key, 'current')}
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
            {:else if activeLast}
              <div class="font-mono font-semibold text-neutral-900 dark:text-neutral-100">
                {formatRub(resData.last_month?.cost_rub)}
              </div>
              <div class="text-xs text-neutral-500 dark:text-neutral-400 font-mono">
                {formatKwh(resData.last_month?.consumption_kwh)}
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

  {:else}
    <!-- Формула расчёта -->
    <div class="text-sm text-neutral-700 dark:text-neutral-300 flex-1 overflow-y-auto">
      <div class="font-semibold text-neutral-900 dark:text-neutral-100 mb-2">Формула расчёта</div>
      <div class="p-3 bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-700 rounded font-mono text-xs mb-4">
        Стоимость = Потребление × Тариф
      </div>

      <div class="font-semibold text-neutral-900 dark:text-neutral-100 mb-2">Интервальные тарифы</div>
      <div class="border border-neutral-200 dark:border-neutral-700 rounded overflow-hidden mb-4">
        <table class="w-full text-xs">
          <thead class="bg-neutral-50 dark:bg-neutral-900 border-b border-neutral-200 dark:border-neutral-700">
            <tr>
              <th class="text-left px-2 py-2 font-semibold text-neutral-700 dark:text-neutral-300">Период</th>
              <th class="text-right px-2 py-2 font-semibold text-neutral-700 dark:text-neutral-300">Тариф</th>
            </tr>
          </thead>
          <tbody>
            <tr class="border-t border-neutral-100 dark:border-neutral-700">
              <td class="px-2 py-1.5 text-neutral-700 dark:text-neutral-300">2025-01-01 → 2026-02-01</td>
              <td class="text-right px-2 py-1.5 font-mono text-neutral-700 dark:text-neutral-300 font-semibold">5.50 ₽/кВт·ч</td>
            </tr>
            <tr class="border-t border-neutral-100 dark:border-neutral-700">
              <td class="px-2 py-1.5 text-neutral-700 dark:text-neutral-300">2026-02-01 → ∞</td>
              <td class="text-right px-2 py-1.5 font-mono text-neutral-700 dark:text-neutral-300 font-semibold">6.20 ₽/кВт·ч</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="text-xs text-neutral-500 dark:text-neutral-400">
        <div class="font-semibold text-neutral-700 dark:text-neutral-300 mb-2">Источники данных:</div>
        <div class="space-y-1">
          <div>• Теги ЛЭРС: <span class="font-mono">LERS.electricity meter current/last month N</span></div>
          <div>• Тарифы: <span class="font-mono">data/tariffs.json</span></div>
          <div>• Конфиг счётчиков: <span class="font-mono">data/energy_config.json</span></div>
        </div>
      </div>

      <div class="mt-4 text-xs text-neutral-500 dark:text-neutral-400 italic">
        Прошлый месяц показан как основной (полные данные). Текущий месяц неполный — данные накапливаются.
      </div>
    </div>
  {/if}
</div>
'''

card_path.write_text(new_content, encoding='utf-8', newline='\n')
print('✓ EnergyCostCard.svelte обновлён')
print()
print('ИЗМЕНЕНИЯ:')
print('  • Большая цифра: ПРОШЛЫЙ месяц (полные данные)')
print('  • Текущий месяц: маленьким текстом "(неполный месяц)"')
print('  • Детализация по ресурсам: показывает прошлый месяц')
print('  • Кнопка (i): открывает формулу расчёта + таблицу тарифов')
print('  • Формула: Стоимость = Потребление × Тариф')
print('  • Таблица тарифов: 5.50 ₽ (2025) → 6.20 ₽ (2026)')
print('  • Источники данных: теги ЛЭРС, tariffs.json, energy_config.json')
print()
print('Vite подхватит через HMR.')
print('Обнови страницу — виджет должен показать:')
print('  • 114 005,60 ₽ (май 2026)')
print('  • 18 388 кВт·ч')
print('  • Тариф 6.20 ₽/кВт·ч')
print()
print('Когда ок — скажи "энергозатраты ок" и коммитим')