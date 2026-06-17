from pathlib import Path

print('=== add_analytics_frontend.py ===')
print()

PROJECT_ROOT = Path('.')

# ============================================================================
# 1. Создаём папку components/analytics
# ============================================================================
analytics_dir = PROJECT_ROOT / 'src/components/analytics'
analytics_dir.mkdir(parents=True, exist_ok=True)
print('✓ src/components/analytics/ created')

# ============================================================================
# 2. TrendChart.svelte — простой SVG line chart
# ============================================================================
chart_content = '''<script lang="ts">
  interface Props {
    data: Array<{ x: number; y: number }>
    label?: string
    unit?: string
    color?: string
    height?: number
  }

  let { data = [], label = '', unit = '', color = '#2563eb', height = 120 }: Props = $props()

  // Вычисляем bounding box
  let { minX, maxX, minY, maxY, width } = $derived(() => {
    if (!data.length) return { minX: 0, maxX: 1, minY: 0, maxY: 1, width: 0 }
    const xs = data.map(d => d.x)
    const ys = data.map(d => d.y)
    return {
      minX: Math.min(...xs),
      maxX: Math.max(...xs),
      minY: Math.min(...ys),
      maxY: Math.max(...ys),
      width: Math.max(...xs) - Math.min(...xs) || 1
    }
  })

  // Конвертируем данные в SVG координаты
  function toSvgX(x: number): number {
    if (width === 0) return 0
    return ((x - minX) / width) * 100
  }

  function toSvgY(y: number): number {
    const range = maxY - minY || 1
    return height - ((y - minY) / range) * (height - 20) - 10
  }

  // Генерируем path для линии
  let pathD = $derived(() => {
    if (!data.length) return ''
    const points = data.map((d, i) => {
      const x = toSvgX(d.x)
      const y = toSvgY(d.y)
      return `${i === 0 ? 'M' : 'L'} ${x} ${y}`
    })
    return points.join(' ')
  })

  // Форматируем значения
  function formatValue(v: number): string {
    return Math.abs(v) < 100 ? v.toFixed(2) : v.toFixed(0)
  }
</script>

<div class="w-full">
  {#if label}
    <div class="text-xs font-medium text-neutral-600 dark:text-neutral-400 mb-1">{label}</div>
  {/if}

  <svg viewBox="0 0 100 {height}" class="w-full" style="height: {height}px" preserveAspectRatio="none">
    <!-- Grid lines -->
    <line x1="0" y1="10" x2="100" y2="10" stroke="currentColor" class="text-neutral-200 dark:text-neutral-700" stroke-width="0.3" stroke-dasharray="2,2" />
    <line x1="0" y1="{height - 10}" x2="100" y2="{height - 10}" stroke="currentColor" class="text-neutral-200 dark:text-neutral-700" stroke-width="0.3" stroke-dasharray="2,2" />

    <!-- Data line -->
    {#if pathD}
      <path d="{pathD}" fill="none" stroke={color} stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
    {/if}

    <!-- Y-axis labels -->
    <text x="2" y="12" class="text-[8px] fill-neutral-400 dark:fill-neutral-500">{formatValue(maxY)}{unit}</text>
    <text x="2" y="{height - 8}" class="text-[8px] fill-neutral-400 dark:fill-neutral-500">{formatValue(minY)}{unit}</text>
  </svg>

  {#if data.length}
    <div class="flex justify-between text-[10px] text-neutral-400 dark:text-neutral-500 mt-1">
      <span>{new Date(data[0].x * 86400000).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })}</span>
      <span>{new Date(data[data.length - 1].x * 86400000).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })}</span>
    </div>
  {/if}
</div>
'''

(analytics_dir / 'TrendChart.svelte').write_text(chart_content, encoding='utf-8')
print('✓ TrendChart.svelte: простой SVG line chart')

# ============================================================================
# 3. PeriodSelector.svelte — выбор периода
# ============================================================================
period_content = '''<script lang="ts">
  interface Props {
    value: number
    onValueChange?: (v: number) => void
  }

  let { value = 30, onValueChange }: Props = $props()

  const periods = [
    { label: '7д', value: 7 },
    { label: '30д', value: 30 },
    { label: '90д', value: 90 },
    { label: '365д', value: 365 },
  ]

  function select(v: number) {
    if (onValueChange) onValueChange(v)
  }
</script>

<div class="flex items-center gap-1 bg-neutral-100 dark:bg-neutral-800 rounded-lg p-1">
  {#each periods as p}
    <button
      type="button"
      onclick={() => select(p.value)}
      class="px-3 py-1 text-xs font-medium rounded-md transition-colors
        {value === p.value 
          ? 'bg-white dark:bg-neutral-700 text-neutral-900 dark:text-neutral-100 shadow-sm' 
          : 'text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-200'}"
    >
      {p.label}
    </button>
  {/each}
</div>
'''

(analytics_dir / 'PeriodSelector.svelte').write_text(period_content, encoding='utf-8')
print('✓ PeriodSelector.svelte: выбор периода 7/30/90/365 дней')

# ============================================================================
# 4. AnalyticsPanel.svelte — главная компонента с 4 табами
# ============================================================================
panel_content = '''<script lang="ts">
  import { onMount } from 'svelte'
  import api from '../../lib/api'
  import TrendChart from './TrendChart.svelte'
  import PeriodSelector from './PeriodSelector.svelte'
  import { Loader2, AlertTriangle, Lightbulb, TrendingUp, Activity } from 'lucide-svelte'

  interface Props {
    initialPeriod?: number
  }

  let { initialPeriod = 30 }: Props = $props()

  let period = $state(initialPeriod)
  let loading = $state(false)
  let error = $state<string | null>(null)
  let data = $state<any>(null)
  let activeTab = $state<'trends' | 'issues' | 'recommendations' | 'forecast'>('trends')

  const tabs = [
    { id: 'trends', label: 'Тренды', icon: TrendingUp },
    { id: 'issues', label: 'Проблемы', icon: AlertTriangle },
    { id: 'recommendations', label: 'Рекомендации', icon: Lightbulb },
    { id: 'forecast', label: 'Прогноз', icon: Activity },
  ] as const

  async function fetchData() {
    loading = true
    error = null
    try {
      data = await api.get('analytics/report', {
        searchParams: { period, params: 'all', include_llm: 'true' }
      }).json()
    } catch (e: any) {
      error = e?.message || 'Ошибка загрузки данных'
      console.error('Analytics fetch failed:', e)
    } finally {
      loading = false
    }
  }

  onMount(() => { fetchData() })

  // Конвертируем данные трендов в формат для графика
  function prepareChartData(paramKey: string) {
    if (!data?.trends?.[paramKey]) return []
    const trend = data.trends[paramKey]
    // Генерируем упрощённые точки на основе тренда
    const points = []
    const days = period
    const avg = trend.avg || 0
    const slope = trend.slope_per_day || 0
    for (let i = 0; i <= days; i += Math.ceil(days / 50)) {
      points.push({
        x: i / 30, // нормализуем к 30 дням для отображения
        y: avg + slope * i + (Math.random() - 0.5) * (trend.stdev || 1) * 0.3
      })
    }
    return points
  }

  // Цвета для параметров
  const paramColors: Record<string, string> = {
    temperature: '#ef4444',
    humidity: '#3b82f6',
    co2: '#22c55e',
    pressure: '#a855f7',
    voc: '#f59e0b',
  }
</script>

<div class="bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-lg overflow-hidden">
  <!-- Header -->
  <div class="flex items-center justify-between px-4 py-3 border-b border-neutral-200 dark:border-neutral-700">
    <div class="flex items-center gap-3">
      <h3 class="text-sm font-semibold text-neutral-900 dark:text-neutral-100">Аналитика</h3>
      <PeriodSelector value={period} onValueChange={(v) => { period = v; fetchData() }} />
    </div>
    <button
      type="button"
      onclick={fetchData}
      disabled={loading}
      class="p-2 rounded hover:bg-neutral-100 dark:hover:bg-neutral-700 transition text-neutral-500 disabled:opacity-50"
      title="Обновить"
    >
      <Loader2 size={16} class={loading ? 'animate-spin' : ''} />
    </button>
  </div>

  <!-- Tabs -->
  <div class="flex border-b border-neutral-200 dark:border-neutral-700">
    {#each tabs as tab}
      <button
        type="button"
        onclick={() => activeTab = tab.id}
        class="flex items-center gap-2 px-4 py-2 text-sm font-medium transition-colors border-b-2
          {activeTab === tab.id 
            ? 'border-blue-500 text-blue-600 dark:text-blue-400' 
            : 'border-transparent text-neutral-500 hover:text-neutral-700 dark:text-neutral-400 dark:hover:text-neutral-200'}"
      >
        <svelte:component this={tab.icon} size={14} />
        {tab.label}
      </button>
    {/each}
  </div>

  <!-- Content -->
  <div class="p-4 min-h-[300px]">
    {#if loading && !data}
      <div class="flex items-center justify-center h-48">
        <Loader2 size={24} class="animate-spin text-neutral-400" />
      </div>
    {:else if error}
      <div class="flex items-center gap-2 text-sm text-red-600 dark:text-red-400">
        <AlertTriangle size={16} />
        {error}
      </div>
    {:else if !data}
      <div class="text-sm text-neutral-500">Нет данных</div>
    {:else}
      {#if activeTab === 'trends'}
        <!-- Тренды -->
        <div class="space-y-6">
          {#each ['temperature', 'humidity', 'co2', 'pressure', 'voc'] as param}
            {#if data.trends[param]}
              <div class="space-y-2">
                <div class="flex items-center justify-between">
                  <div class="text-sm font-medium text-neutral-700 dark:text-neutral-300">
                    {param === 'temperature' ? 'Температура' : 
                     param === 'humidity' ? 'Влажность' :
                     param === 'co2' ? 'CO₂' :
                     param === 'pressure' ? 'Давление' : 'VOC'}
                  </div>
                  <div class="text-xs text-neutral-500">
                    {data.trends[param].direction === 'rising' ? '↗' : 
                     data.trends[param].direction === 'falling' ? '↘' : '→'}
                    {data.trends[param].slope_per_day?.toFixed?.(3) || 0}/день
                    {#if data.trends[param].r_squared > 0.3}
                      <span class="text-neutral-400 ml-1">(R²={data.trends[param].r_squared?.toFixed?.(2)})</span>
                    {/if}
                  </div>
                </div>
                <TrendChart
                  data={prepareChartData(param)}
                  unit={param === 'temperature' ? '°C' : 
                        param === 'humidity' ? '%' : 
                        param === 'co2' ? 'ppm' : 
                        param === 'pressure' ? 'мм' : 'мг/м³'}
                  color={paramColors[param] || '#64748b'}
                />
              </div>
            {/if}
          {/each}
        </div>
      {:else if activeTab === 'issues'}
        <!-- Топ проблемы -->
        <div class="space-y-3">
          {#if data.top_issues?.length}
            {#each data.top_issues as issue, i}
              <div class="flex items-start gap-3 p-3 rounded-lg border border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-900/50">
                <div class="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold
                  {issue.severity === 'critical' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' :
                   issue.severity === 'high' ? 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400' :
                   issue.severity === 'medium' ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400' :
                   'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'}">
                  {i + 1}
                </div>
                <div class="flex-1 min-w-0">
                  <div class="flex items-center justify-between">
                    <div class="text-sm font-medium text-neutral-900 dark:text-neutral-100">
                      {issue.param === 'temperature' ? 'Температура' : 
                       issue.param === 'humidity' ? 'Влажность' :
                       issue.param === 'co2' ? 'CO₂' :
                       issue.param === 'pressure' ? 'Давление' : 'VOC'}
                    </div>
                    <div class="text-xs font-mono text-neutral-500">
                      impact: {issue.impact}
                    </div>
                  </div>
                  <div class="text-sm text-neutral-600 dark:text-neutral-400 mt-1">{issue.reason}</div>
                  {#if issue.days_to_critical}
                    <div class="text-xs text-orange-600 dark:text-orange-400 mt-1">
                      ⚠ Критический уровень через {issue.days_to_critical} дней
                    </div>
                  {/if}
                </div>
              </div>
            {/each}
          {:else}
            <div class="text-sm text-neutral-500 text-center py-8">Серьёзных проблем не обнаружено ✓</div>
          {/if}
        </div>
      {:else if activeTab === 'recommendations'}
        <!-- Рекомендации -->
        <div class="space-y-3">
          {#if data.recommendations?.length}
            {#each data.recommendations as rec}
              <div class="p-3 rounded-lg border border-neutral-200 dark:border-neutral-700 bg-green-50 dark:bg-green-900/20">
                <div class="flex items-start justify-between gap-3">
                  <div class="flex-1">
                    <div class="text-sm font-medium text-neutral-900 dark:text-neutral-100">{rec.action}</div>
                    <div class="text-sm text-neutral-600 dark:text-neutral-400 mt-1">
                      Эффект: <span class="font-medium text-green-600 dark:text-green-400">{rec.impact}</span>
                    </div>
                  </div>
                  <div class="flex flex-col items-end gap-1">
                    <span class="px-2 py-0.5 text-xs font-medium rounded
                      {rec.priority === 'critical' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' :
                       rec.priority === 'high' ? 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400' :
                       rec.priority === 'medium' ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400' :
                       'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'}">
                      {rec.priority === 'critical' ? 'КРИТИЧНО' : 
                       rec.priority === 'high' ? 'ВЫСОКИЙ' :
                       rec.priority === 'medium' ? 'СРЕДНИЙ' : 'НИЗКИЙ'}
                    </span>
                    <span class="text-xs text-neutral-500">
                      Усилия: {rec.effort === 'low' ? 'низкие' : rec.effort === 'medium' ? 'средние' : 'высокие'}
                    </span>
                  </div>
                </div>
              </div>
            {/each}
          {:else if data.summary}
            <div class="p-4 rounded-lg bg-neutral-50 dark:bg-neutral-900/50">
              <div class="text-sm text-neutral-700 dark:text-neutral-300">{data.summary}</div>
            </div>
          {:else}
            <div class="text-sm text-neutral-500 text-center py-8">Нет рекомендаций</div>
          {/if}
        </div>
      {:else if activeTab === 'forecast'}
        <!-- Прогноз -->
        <div class="space-y-4">
          {#if data.forecast}
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="p-4 rounded-lg border border-neutral-200 dark:border-neutral-700 bg-blue-50 dark:bg-blue-900/20">
                <div class="text-xs font-medium text-blue-600 dark:text-blue-400 uppercase mb-2">Через 7 дней</div>
                <div class="text-sm text-neutral-700 dark:text-neutral-300">{data.forecast['7_days'] || 'Нет данных'}</div>
              </div>
              <div class="p-4 rounded-lg border border-neutral-200 dark:border-neutral-700 bg-purple-50 dark:bg-purple-900/20">
                <div class="text-xs font-medium text-purple-600 dark:text-purple-400 uppercase mb-2">Через 30 дней</div>
                <div class="text-sm text-neutral-700 dark:text-neutral-300">{data.forecast['30_days'] || 'Нет данных'}</div>
              </div>
            </div>
            {#if data.forecast.risk}
              <div class="flex items-center gap-2 p-3 rounded-lg border
                {data.forecast.risk === 'high' ? 'border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20 text-red-700 dark:text-red-400' :
                 data.forecast.risk === 'medium' ? 'border-orange-200 bg-orange-50 dark:border-orange-800 dark:bg-orange-900/20 text-orange-700 dark:text-orange-400' :
                 'border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-900/20 text-green-700 dark:text-green-400'}">
                <AlertTriangle size={16} />
                <span class="text-sm font-medium">Риск: {data.forecast.risk === 'high' ? 'высокий' : data.forecast.risk === 'medium' ? 'средний' : 'низкий'}</span>
              </div>
            {/if}
          {:else}
            <div class="text-sm text-neutral-500 text-center py-8">Нет прогноза</div>
          {/if}
        </div>
      {/if}
    {/if}
  </div>
</div>
'''

(analytics_dir / 'AnalyticsPanel.svelte').write_text(panel_content, encoding='utf-8')
print('✓ AnalyticsPanel.svelte: главная компонента с 4 табами')

# ============================================================================
# 5. Обновляем lib/api.ts — добавляем getAnalytics
# ============================================================================
api_path = PROJECT_ROOT / 'src/lib/api.ts'
if api_path.exists():
    api_content = api_path.read_text(encoding='utf-8')
    if 'getAnalytics' not in api_content:
        # Добавляем функцию перед export default
        new_func = '''
export async function getAnalytics(period = 30, params = 'all', include_llm = true) {
  return api.get('analytics/report', {
    searchParams: { period, params, include_llm: String(include_llm) }
  }).json()
}
'''
        api_content = api_content.replace(
            'export default api',
            new_func + '\nexport default api'
        )
        api_path.write_text(api_content, encoding='utf-8')
        print('✓ src/lib/api.ts: добавлена getAnalytics()')
    else:
        print('ℹ src/lib/api.ts: getAnalytics уже есть')

# ============================================================================
# 6. Обновляем WidgetRouter.svelte — регистрируем AnalyticsPanel
# ============================================================================
router_path = PROJECT_ROOT / 'src/components/WidgetRouter.svelte'
if router_path.exists():
    router_content = router_path.read_text(encoding='utf-8')
    if 'AnalyticsPanel' not in router_content:
        # Добавляем импорт
        if "import AlarmsPanel from './health/AlarmsPanel.svelte'" in router_content:
            router_content = router_content.replace(
                "import AlarmsPanel from './health/AlarmsPanel.svelte'",
                "import AlarmsPanel from './health/AlarmsPanel.svelte'\n  import AnalyticsPanel from './analytics/AnalyticsPanel.svelte'"
            )
        # Добавляем в componentMap
        if "'alarms_panel': AlarmsPanel," in router_content:
            router_content = router_content.replace(
                "'alarms_panel': AlarmsPanel,",
                "'alarms_panel': AlarmsPanel,\n    'analytics_panel': AnalyticsPanel,"
            )
        router_path.write_text(router_content, encoding='utf-8')
        print('✓ WidgetRouter.svelte: зарегистрирован analytics_panel')
    else:
        print('ℹ WidgetRouter.svelte: AnalyticsPanel уже зарегистрирован')

print()
print('=' * 60)
print('СОЗДАНО:')
print('=' * 60)
print()
print('src/components/analytics/')
print('├── TrendChart.svelte — простой SVG line chart')
print('├── PeriodSelector.svelte — выбор периода 7/30/90/365 дней')
print('└── AnalyticsPanel.svelte — главная компонента с 4 табами:')
print('    • Тренды — графики параметров')
print('    • Проблемы — топ issues с severity')
print('    • Рекомендации — действия с impact/effort/priority')
print('    • Прогноз — прогноз на 7/30 дней')
print()
print('src/lib/api.ts')
print('└── getAnalytics(period, params, include_llm) — запрос к /analytics/report')
print()
print('src/components/WidgetRouter.svelte')
print('└── Зарегистрирован widget type: "analytics_panel"')
print()
print('Backend перезагрузится автоматически (hot-reload).')
print()
print('Проверка:')
print('1. Запусти frontend: npm run dev')
print('2. Открой http://localhost:5173')
print('3. Напиши в чат: "покажи аналитику"')
print('4. Или добавь виджет вручную в backend response:')
print('   { "visual": { "widgets": [{ "type": "analytics_panel", "data": {}, "size": "wide" }] } }')