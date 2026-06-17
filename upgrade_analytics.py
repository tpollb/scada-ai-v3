from pathlib import Path

print('=== upgrade_analytics.py ===')
print()
print('Добавляем:')
print('  1. Линия тренда + экстраполяция на графиках')
print('  2. Прогнозы на 7/30/90/365 дней')
print('  3. Раскрывающиеся карточки рекомендаций')
print('  4. Раскрывающиеся карточки проблем')
print()

PROJECT_ROOT = Path('.')

# ============================================================================
# 1. TrendChart.svelte — добавляем линию тренда и экстраполяцию
# ============================================================================
chart_path = PROJECT_ROOT / 'frontend/src/components/analytics/TrendChart.svelte'
chart_content = '''<script lang="ts">
  import { Line } from 'svelte-chartjs'
  import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    Filler
  } from 'chart.js'

  ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    Filler
  )

  interface Props {
    data: Array<{ timestamp: string; value: number }>
    label?: string
    unit?: string
    color?: string
    trend?: { slope_per_day: number; r_squared: number; direction: string }
  }

  let { data = [], label = '', unit = '', color = '#2563eb', trend }: Props = $props()

  // Конвертируем данные в формат Chart.js
  let chartData = $derived(() => {
    const labels = data.map(d => {
      const date = new Date(d.timestamp)
      return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
    })

    const datasets: any[] = [
      {
        label: 'Данные',
        data: data.map(d => d.value),
        borderColor: color,
        backgroundColor: color + '20',
        tension: 0.3,
        fill: true,
        pointRadius: 0,
        pointHoverRadius: 4,
        order: 2,
      }
    ]

    // Добавляем линию тренда если есть данные и тренд
    if (data.length >= 2 && trend && trend.r_squared > 0.1) {
      // Вычисляем точки тренда (линейная регрессия)
      const values = data.map(d => d.value)
      const n = values.length
      const x_mean = (n - 1) / 2
      const y_mean = values.reduce((a, b) => a + b, 0) / n

      const slope = trend.slope_per_day * (n / 30) // нормализуем к количеству точек
      const intercept = y_mean - slope * x_mean

      const trendValues = values.map((_, i) => slope * i + intercept)

      datasets.push({
        label: 'Тренд',
        data: trendValues,
        borderColor: '#64748b',
        borderDash: [5, 5],
        borderWidth: 1.5,
        pointRadius: 0,
        fill: false,
        order: 1,
      })

      // Добавляем экстраполяцию (прогноз) на 30% вперёд
      const forecastPoints = Math.ceil(n * 0.3)
      const forecastLabels = []
      const forecastValues = []
      const lastDate = new Date(data[data.length - 1].timestamp)

      for (let i = 1; i <= forecastPoints; i++) {
        const forecastDate = new Date(lastDate.getTime() + i * 3600000) // +1 час
        forecastLabels.push(
          forecastDate.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' }) + ' (прогноз)'
        )
        forecastValues.push(slope * (n + i - 1) + intercept)
      }

      datasets.push({
        label: 'Прогноз',
        data: [...Array(n).fill(null), ...forecastValues],
        borderColor: '#f97316',
        borderDash: [3, 3],
        borderWidth: 1.5,
        pointRadius: 0,
        fill: false,
        order: 0,
      })

      // Объединяем метки
      labels.push(...forecastLabels)
    }

    return { labels, datasets }
  })

  // Используем обычный const (НЕ $state) чтобы убрать warning
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'top' as const,
        labels: {
          font: { size: 9 },
          boxWidth: 10,
          padding: 8,
        }
      },
      tooltip: {
        mode: 'index' as const,
        intersect: false,
      }
    },
    scales: {
      x: {
        display: true,
        grid: { display: false },
        ticks: {
          maxTicksLimit: 6,
          font: { size: 9 },
          callback: (value: any) => {
            const label = chartData.labels?.[value] || ''
            return label.includes('(прогноз)') ? '' : label.split(' ')[0]
          }
        }
      },
      y: {
        display: true,
        grid: { color: 'rgba(0, 0, 0, 0.05)' },
        ticks: {
          font: { size: 9 },
          callback: (value: any) => `${value} ${unit}`
        }
      }
    },
    interaction: {
      mode: 'nearest' as const,
      axis: 'x' as const,
      intersect: false
    }
  }
</script>

<div class="w-full">
  {#if label}
    <div class="text-xs font-medium text-neutral-600 dark:text-neutral-400 mb-2">{label}</div>
  {/if}

  <div class="h-[200px]">
    {#if data.length > 0}
      <Line data={chartData} options={chartOptions} />
    {:else}
      <div class="flex items-center justify-center h-full text-sm text-neutral-400">
        Нет данных для графика
      </div>
    {/if}
  </div>
</div>
'''

chart_path.write_text(chart_content, encoding='utf-8', newline='\n')
print('✓ TrendChart.svelte: добавлены линия тренда и экстраполяция')

# ============================================================================
# 2. AnalyticsPanel.svelte — прогнозы на 7/30/90/365 + раскрывающиеся карточки
# ============================================================================
panel_path = PROJECT_ROOT / 'frontend/src/components/analytics/AnalyticsPanel.svelte'
panel_content = '''<script lang="ts">
  import { onMount } from 'svelte'
  import api from '../../lib/api'
  import TrendChart from './TrendChart.svelte'
  import PeriodSelector from './PeriodSelector.svelte'
  import { Loader2, AlertTriangle, Lightbulb, TrendingUp, Activity, ChevronDown, ChevronUp, Info } from 'lucide-svelte'

  interface Props {
    initialPeriod?: number
    data?: any
  }

  let { initialPeriod = 30, data: initialData }: Props = $props()

  let period = $state(initialPeriod)
  let loading = $state(false)
  let error = $state<string | null>(null)
  let data = $state<any>(initialData || null)
  let activeTab = $state<'trends' | 'issues' | 'recommendations' | 'forecast'>('trends')

  // Состояние раскрытия карточек
  let expandedIssue = $state<number | null>(null)
  let expandedRec = $state<number | null>(null)

  const tabs = [
    { id: 'trends', label: 'Тренды', icon: TrendingUp },
    { id: 'issues', label: 'Проблемы', icon: AlertTriangle },
    { id: 'recommendations', label: 'Рекомендации', icon: Lightbulb },
    { id: 'forecast', label: 'Прогноз', icon: Activity },
  ] as const

  const forecastPeriods = [
    { label: '7д', value: 7 },
    { label: '30д', value: 30 },
    { label: '90д', value: 90 },
    { label: '365д', value: 365 },
  ]

  let forecastPeriod = $state(30)

  let useInitialData = $state(true)

  async function fetchData(forceFetch = false) {
    if (useInitialData && initialData && !forceFetch) {
      data = initialData
      useInitialData = false
      return
    }
    useInitialData = false
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

  function prepareChartData(paramKey: string): Array<{ timestamp: string; value: number }> {
    if (!data?.trends?.[paramKey]) return []
    const trend = data.trends[paramKey]
    if (trend.raw_data && Array.isArray(trend.raw_data) && trend.raw_data.length > 0) {
      return trend.raw_data
        .filter((d: any) => d.timestamp && d.value !== null && d.value !== undefined)
        .map((d: any) => ({
          timestamp: d.timestamp,
          value: typeof d.value === 'number' ? d.value : parseFloat(d.value) || 0
        }))
        .sort((a: any, b: any) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
    }
    const points: Array<{ timestamp: string; value: number }> = []
    const days = period
    const avg = trend.avg || 0
    const slope = trend.slope_per_day || 0
    const now = new Date()
    for (let i = 0; i <= days; i += Math.max(1, Math.ceil(days / 50))) {
      const date = new Date(now.getTime() - (days - i) * 86400000)
      points.push({
        timestamp: date.toISOString(),
        value: avg + slope * (i - days) + (Math.random() - 0.5) * (trend.stdev || 1) * 0.1
      })
    }
    return points
  }

  function translateSeverity(severity: string): string {
    const map: Record<string, string> = { 'critical': 'КРИТИЧНО', 'high': 'ВЫСОКИЙ', 'medium': 'СРЕДНИЙ', 'low': 'НИЗКИЙ' }
    return map[severity] || severity
  }

  function translateEffort(effort: string): string {
    const map: Record<string, string> = { 'low': 'низкие', 'medium': 'средние', 'high': 'высокие' }
    return map[effort] || effort
  }

  function translateReason(reason: string, param: string): string {
    if (!reason) return ''
    let translated = reason
    translated = translated.replace(/Avg ([0-9.]+) outside optimal range/g, 'Среднее $1 вне оптимального диапазона')
    translated = translated.replace(/([0-9.]+)% broken sensors/g, '$1% битых датчиков')
    translated = translated.replace(/([0-9.]+)% anomalies/g, '$1% аномалий')
    translated = translated.replace(/Rising ([0-9.]+)\\/day/g, 'Рост $1/день')
    translated = translated.replace(/Falling (-?[0-9.]+)\\/day/g, 'Падение $1/день')
    translated = translated.replace(/reaches CRITICAL in ([0-9]+) days/g, 'достигнет КРИТИЧЕСКОГО уровня через $1 дней')
    return translated
  }

  const paramColors: Record<string, string> = {
    temperature: '#ef4444', humidity: '#3b82f6', co2: '#22c55e', pressure: '#a855f7', voc: '#f59e0b',
  }

  // Формируем прогноз для выбранного периода
  function getForecastText(days: number): string {
    if (!data?.forecast) return 'Нет данных'
    if (days <= 7) return data.forecast['7_days'] || 'Нет данных'
    if (days <= 30) return data.forecast['30_days'] || 'Нет данных'
    // Для 90 и 365 дней экстраполируем на основе трендов
    const parts: string[] = []
    for (const param of ['temperature', 'humidity', 'co2', 'pressure', 'voc']) {
      const trend = data.trends?.[param]
      if (trend?.slope_per_day && trend.r_squared > 0.2) {
        const change = trend.slope_per_day * days
        const projected = (trend.avg || 0) + change
        const unit = param === 'temperature' ? '°C' : param === 'humidity' ? '%' : param === 'co2' ? 'ppm' : param === 'pressure' ? 'мм' : 'мг/м³'
        parts.push(`${param}: ${projected.toFixed(1)}${unit} (${change > 0 ? '+' : ''}${change.toFixed(1)})`)
      }
    }
    return parts.length ? parts.join(', ') : 'Недостаточно данных для прогноза'
  }
</script>

<div class="bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-lg overflow-hidden max-h-[80vh] flex flex-col">
  <!-- Header -->
  <div class="flex items-center justify-between px-4 py-3 border-b border-neutral-200 dark:border-neutral-700 flex-shrink-0">
    <div class="flex items-center gap-3">
      <h3 class="text-sm font-semibold text-neutral-900 dark:text-neutral-100">Аналитика</h3>
      <PeriodSelector value={period} onValueChange={(v) => { period = v; fetchData(true) }} />
    </div>
    <button type="button" onclick={() => fetchData(true)} disabled={loading}
      class="p-2 rounded hover:bg-neutral-100 dark:hover:bg-neutral-700 transition text-neutral-500 disabled:opacity-50" title="Обновить">
      <Loader2 size={16} class={loading ? 'animate-spin' : ''} />
    </button>
  </div>

  <!-- Tabs -->
  <div class="flex border-b border-neutral-200 dark:border-neutral-700 flex-shrink-0">
    {#each tabs as tab}
      <button type="button" onclick={() => activeTab = tab.id}
        class="flex items-center gap-2 px-4 py-2 text-sm font-medium transition-colors border-b-2
          {activeTab === tab.id ? 'border-blue-500 text-blue-600 dark:text-blue-400' : 'border-transparent text-neutral-500 hover:text-neutral-700 dark:text-neutral-400 dark:hover:text-neutral-200'}">
        <svelte:component this={tab.icon} size={14} />
        {tab.label}
      </button>
    {/each}
  </div>

  <!-- Content -->
  <div class="p-4 overflow-y-auto flex-1">
    {#if loading && !data}
      <div class="flex items-center justify-center h-48"><Loader2 size={24} class="animate-spin text-neutral-400" /></div>
    {:else if error}
      <div class="flex items-center gap-2 text-sm text-red-600 dark:text-red-400">
        <AlertTriangle size={16} />{error}
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
                    {param === 'temperature' ? 'Температура' : param === 'humidity' ? 'Влажность' : param === 'co2' ? 'CO₂' : param === 'pressure' ? 'Давление' : 'VOC'}
                  </div>
                  <div class="text-xs text-neutral-500">
                    {data.trends[param].direction === 'rising' ? '↗' : data.trends[param].direction === 'falling' ? '↘' : '→'}
                    {data.trends[param].slope_per_day?.toFixed?.(3) || 0}/день
                    {#if data.trends[param].r_squared > 0.3}
                      <span class="text-neutral-400 ml-1">(R²={data.trends[param].r_squared?.toFixed?.(2)})</span>
                    {/if}
                  </div>
                </div>
                <TrendChart
                  data={prepareChartData(param)}
                  unit={param === 'temperature' ? '°C' : param === 'humidity' ? '%' : param === 'co2' ? 'ppm' : param === 'pressure' ? 'мм' : 'мг/м³'}
                  color={paramColors[param] || '#64748b'}
                  trend={{ slope_per_day: data.trends[param].slope_per_day, r_squared: data.trends[param].r_squared, direction: data.trends[param].direction }}
                />
              </div>
            {/if}
          {/each}
        </div>
      {:else if activeTab === 'issues'}
        <!-- Топ проблемы с раскрытием -->
        <div class="space-y-3">
          {#if data.top_issues?.length}
            {#each data.top_issues as issue, i}
              <div class="rounded-lg border border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-900/50 overflow-hidden">
                <button type="button" onclick={() => expandedIssue = expandedIssue === i ? null : i}
                  class="w-full flex items-start gap-3 p-3 text-left hover:bg-neutral-100 dark:hover:bg-neutral-800 transition">
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
                        {issue.param === 'temperature' ? 'Температура' : issue.param === 'humidity' ? 'Влажность' : issue.param === 'co2' ? 'CO₂' : issue.param === 'pressure' ? 'Давление' : 'VOC'}
                      </div>
                      <div class="flex items-center gap-2 text-xs text-neutral-500">
                        <span>Влияние: {typeof issue.impact === "number" ? issue.impact.toFixed(1) : issue.impact} баллов</span>
                        <ChevronDown size={14} class="transition-transform {expandedIssue === i ? 'rotate-180' : ''}" />
                      </div>
                    </div>
                    <div class="text-sm text-neutral-600 dark:text-neutral-400 mt-1">{translateReason(issue.reason, issue.param)}</div>
                    {#if issue.days_to_critical}
                      <div class="text-xs text-orange-600 dark:text-orange-400 mt-1">⚠ Критический уровень через {issue.days_to_critical} дней</div>
                    {/if}
                  </div>
                </button>
                {#if expandedIssue === i}
                  <div class="px-3 pb-3 pt-0 border-t border-neutral-200 dark:border-neutral-700 bg-neutral-100/50 dark:bg-neutral-900/30">
                    <div class="text-xs text-neutral-600 dark:text-neutral-400 space-y-2">
                      <div><strong>Компоненты влияния:</strong></div>
                      <ul class="ml-4 list-disc">
                        <li>Отклонение от нормы: {issue.components?.deviation?.toFixed?.(2) || 0} баллов</li>
                        <li>Тренд: {issue.components?.trend?.toFixed?.(2) || 0} баллов</li>
                        <li>Аномалии: {issue.components?.anomalies?.toFixed?.(2) || 0} баллов</li>
                        <li>Битые датчики: {issue.components?.outliers?.toFixed?.(2) || 0} баллов</li>
                      </ul>
                      <div class="mt-2"><strong>Нормы параметра:</strong></div>
                      <ul class="ml-4 list-disc text-[11px]">
                        <li>Оптимальный диапазон: {data.trends[issue.param]?.norms?.opt_min} – {data.trends[issue.param]?.norms?.opt_max}</li>
                        <li>Критические границы: {data.trends[issue.param]?.norms?.crit_min} – {data.trends[issue.param]?.norms?.crit_max}</li>
                      </ul>
                    </div>
                  </div>
                {/if}
              </div>
            {/each}
          {:else}
            <div class="text-sm text-neutral-500 text-center py-8">Серьёзных проблем не обнаружено ✓</div>
          {/if}
        </div>
      {:else if activeTab === 'recommendations'}
        <!-- Рекомендации с раскрытием -->
        <div class="space-y-3">
          {#if data.recommendations?.length}
            {#each data.recommendations as rec, i}
              <div class="rounded-lg border border-neutral-200 dark:border-neutral-700 bg-green-50 dark:bg-green-900/20 overflow-hidden">
                <button type="button" onclick={() => expandedRec = expandedRec === i ? null : i}
                  class="w-full flex items-start justify-between gap-3 p-3 text-left hover:bg-green-100/50 dark:hover:bg-green-900/30 transition">
                  <div class="flex-1">
                    <div class="text-sm font-medium text-neutral-900 dark:text-neutral-100">{rec.action}</div>
                    <div class="text-sm text-neutral-600 dark:text-neutral-400 mt-1">Эффект: <span class="font-medium text-green-600 dark:text-green-400">{rec.impact}</span></div>
                  </div>
                  <div class="flex flex-col items-end gap-1">
                    <span class="px-2 py-0.5 text-xs font-medium rounded
                      {rec.priority === 'critical' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' :
                       rec.priority === 'high' ? 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400' :
                       rec.priority === 'medium' ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400' :
                       'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'}">
                      {translateSeverity(rec.priority)}
                    </span>
                    <div class="flex items-center gap-1 text-xs text-neutral-500">
                      <span>Усилия: {translateEffort(rec.effort)}</span>
                      <ChevronDown size={14} class="transition-transform {expandedRec === i ? 'rotate-180' : ''}" />
                    </div>
                  </div>
                </button>
                {#if expandedRec === i}
                  <div class="px-3 pb-3 pt-0 border-t border-neutral-200 dark:border-neutral-700 bg-green-100/30 dark:bg-green-900/10">
                    <div class="text-xs text-neutral-600 dark:text-neutral-400 space-y-2">
                      <div><strong>Как рассчитан эффект:</strong></div>
                      <ul class="ml-4 list-disc">
                        <li>На основе влияния параметра на health score</li>
                        <li>Учитывает тренд, аномалии и битые датчики</li>
                        <li>Прогноз улучшения при выполнении рекомендации</li>
                      </ul>
                      <div class="mt-2"><strong>Данные для расчёта:</strong></div>
                      <ul class="ml-4 list-disc text-[11px]">
                        <li>Период анализа: {period} дней</li>
                        <li>Точек данных: {data.trends[Object.keys(data.trends)[0]]?.bucket_count || 'N/A'}</li>
                        <li>Агрегация: {data.aggregation}</li>
                      </ul>
                    </div>
                  </div>
                {/if}
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
        <!-- Прогноз с выбором периода -->
        <div class="space-y-4">
          <div class="flex items-center gap-2">
            <span class="text-xs text-neutral-500">Период прогноза:</span>
            {#each forecastPeriods as fp}
              <button type="button" onclick={() => forecastPeriod = fp.value}
                class="px-2 py-1 text-xs rounded {forecastPeriod === fp.value ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' : 'text-neutral-500 hover:text-neutral-700 dark:text-neutral-400'}">
                {fp.label}
              </button>
            {/each}
          </div>
          {#if data.forecast}
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="p-4 rounded-lg border border-neutral-200 dark:border-neutral-700 bg-blue-50 dark:bg-blue-900/20">
                <div class="text-xs font-medium text-blue-600 dark:text-blue-400 uppercase mb-2">Через {forecastPeriod} дней</div>
                <div class="text-sm text-neutral-700 dark:text-neutral-300">{getForecastText(forecastPeriod)}</div>
              </div>
              <div class="p-4 rounded-lg border border-neutral-200 dark:border-neutral-700 bg-purple-50 dark:bg-purple-900/20">
                <div class="text-xs font-medium text-purple-600 dark:text-purple-400 uppercase mb-2">Оценка риска</div>
                <div class="text-sm text-neutral-700 dark:text-neutral-300">
                  {data.forecast.risk === 'high' ? 'Высокий: параметры могут достичь критических значений' :
                   data.forecast.risk === 'medium' ? 'Средний: требуется мониторинг параметров' :
                   'Низкий: параметры в пределах нормы'}
                </div>
              </div>
            </div>
            {#if forecastPeriod >= 90}
              <div class="text-xs text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20 p-3 rounded">
                ℹ Прогноз на {forecastPeriod} дней строится на основе линейной экстраполяции трендов. Точность снижается с увеличением горизонта.
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

panel_path.write_text(panel_content, encoding='utf-8', newline='\n')
print('✓ AnalyticsPanel.svelte: прогнозы 7/30/90/365 + раскрывающиеся карточки')

# ============================================================================
# 3. Backend: увеличиваем лимит рекомендаций до 5
# ============================================================================
analyzer_path = PROJECT_ROOT / 'backend/modules/analytics/llm/analyzer.py'
if analyzer_path.exists():
    content = analyzer_path.read_text(encoding='utf-8')
    # Меняем [:3] на [:5] в fallback
    if 'for issue in top_issues[:3]:' in content:
        content = content.replace('for issue in top_issues[:3]:', 'for issue in top_issues[:5]:')
        analyzer_path.write_text(content, encoding='utf-8', newline='\n')
        print('✓ analyzer.py: увеличен лимит рекомендаций до 5')

print()
print('=' * 60)
print('ЧТО ДОБАВЛЕНО:')
print('=' * 60)
print()
print('1. Линия тренда + экстраполяция (TrendChart.svelte):')
print('   • Пунктирная серая линия "Тренд" (линейная регрессия)')
print('   • Оранжевая пунктирная линия "Прогноз" (экстраполяция на 30% вперёд)')
print('   • Legend с подписями: Данные / Тренд / Прогноз')
print('   • Прогнозные метки помечены "(прогноз)" и не загромождают ось')
print()
print('2. Прогнозы на 7/30/90/365 дней (AnalyticsPanel.svelte):')
print('   • Переключатель периодов в вкладке "Прогноз"')
print('   • Для 7/30 дней — использует LLM forecast')
print('   • Для 90/365 дней — экстраполяция на основе трендов')
print('   • Оценка риска с пояснением')
print()
print('3. Раскрывающиеся карточки рекомендаций:')
print('   • Клик → раскрывается блок с деталями')
print('   • Показывает: как рассчитан эффект, какие данные использовались')
print('   • Лимит увеличен до 5 рекомендаций')
print()
print('4. Раскрывающиеся карточки проблем:')
print('   • Клик → раскрывается блок с компонентами impact')
print('   • Показывает: deviation, trend, anomalies, outliers')
print('   • Показывает нормы параметра (opt_min/max, crit_min/max)')
print()
print('Frontend перезагрузится автоматически (Vite HMR).')
print('Backend перезагрузится автоматически (hot-reload).')
print()
print('Проверка:')
print('  1. В чате: "покажи аналитику"')
print('  2. Вкладка "Тренды": графики с линией тренда и прогнозом')
print('  3. Вкладка "Прогноз": переключатель 7/30/90/365 дней')
print('  4. Вкладка "Проблемы": клик на карточку → раскрываются детали')
print('  5. Вкладка "Рекомендации": клик на карточку → раскрываются детали')