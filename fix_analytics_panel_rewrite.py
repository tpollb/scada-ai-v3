from pathlib import Path

print('=== fix_analytics_panel_rewrite.py ===')
print()

PROJECT_ROOT = Path('.')
panel_path = PROJECT_ROOT / 'frontend/src/components/analytics/AnalyticsPanel.svelte'

# ============================================================================
# Полностью переписываем файл с правильной структурой
# ============================================================================
file_content = '''<script lang="ts">
  import { onMount } from 'svelte'
  import api from '../../lib/api'
  import TrendChart from './TrendChart.svelte'
  import PeriodSelector from './PeriodSelector.svelte'
  import { Loader2, AlertTriangle, Lightbulb, TrendingUp, Activity } from 'lucide-svelte'

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

  const tabs = [
    { id: 'trends', label: 'Тренды', icon: TrendingUp },
    { id: 'issues', label: 'Проблемы', icon: AlertTriangle },
    { id: 'recommendations', label: 'Рекомендации', icon: Lightbulb },
    { id: 'forecast', label: 'Прогноз', icon: Activity },
  ] as const

  async function fetchData() {
    if (initialData) {
      data = initialData
      return
    }

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

  onMount(() => {
    if (!initialData) {
      fetchData()
    }
  })

  // Конвертируем данные трендов в формат для графика
  function prepareChartData(paramKey: string): Array<{ timestamp: string; value: number }> {
    if (!data?.trends?.[paramKey]) return []
    const trend = data.trends[paramKey]

    // Используем raw_data из trends (реальные timestamps)
    if (trend.raw_data && Array.isArray(trend.raw_data) && trend.raw_data.length > 0) {
      return trend.raw_data
        .filter((d: any) => d.timestamp && d.value !== null && d.value !== undefined)
        .map((d: any) => ({
          timestamp: d.timestamp,
          value: typeof d.value === 'number' ? d.value : parseFloat(d.value) || 0
        }))
        .sort((a: any, b: any) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
    }

    // Fallback: генерируем точки на основе тренда
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

  // Перевод severity на русский
  function translateSeverity(severity: string): string {
    const map: Record<string, string> = {
      'critical': 'КРИТИЧНО',
      'high': 'ВЫСОКИЙ',
      'medium': 'СРЕДНИЙ',
      'low': 'НИЗКИЙ'
    }
    return map[severity] || severity
  }

  // Перевод effort на русский
  function translateEffort(effort: string): string {
    const map: Record<string, string> = {
      'low': 'низкие',
      'medium': 'средние',
      'high': 'высокие'
    }
    return map[effort] || effort
  }

  // Перевод reason на русский (простые замены)
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
    temperature: '#ef4444',
    humidity: '#3b82f6',
    co2: '#22c55e',
    pressure: '#a855f7',
    voc: '#f59e0b',
  }
</script>

<div class="bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-lg overflow-hidden max-h-[80vh] flex flex-col">
  <!-- Header -->
  <div class="flex items-center justify-between px-4 py-3 border-b border-neutral-200 dark:border-neutral-700 flex-shrink-0">
    <div class="flex items-center gap-3">
      <h3 class="text-sm font-semibold text-neutral-900 dark:text-neutral-100">Аналитика</h3>
      <PeriodSelector value={period} onValueChange={(v) => { period = v; initialData = null; fetchData() }} />
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
  <div class="flex border-b border-neutral-200 dark:border-neutral-700 flex-shrink-0">
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
  <div class="p-4 overflow-y-auto flex-1">
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
                      Влияние: {typeof issue.impact === "number" ? issue.impact.toFixed(1) : issue.impact} баллов
                    </div>
                  </div>
                  <div class="text-sm text-neutral-600 dark:text-neutral-400 mt-1">{translateReason(issue.reason, issue.param)}</div>
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
                      {translateSeverity(rec.priority)}
                    </span>
                    <span class="text-xs text-neutral-500">
                      Усилия: {translateEffort(rec.effort)}
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

# Записываем файл
panel_path.write_text(file_content, encoding='utf-8', newline='\n')
print(f'✓ Файл перезаписан: {panel_path}')
print(f'  Размер: {len(file_content)} байт')

print()
print('=' * 60)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 60)
print()
print('Файл переписан полностью с правильной структурой:')
print()
print('✓ Удалён лишний `return points` вне функции')
print('✓ Удалена лишняя закрывающая `}`')
print('✓ Все функции (prepareChartData, translate*) закрыты правильно')
print('✓ Template часть сохранена с русификацией')
print('✓ max-h-[80vh] + flex flex-col для правильной высоты')
print()
print('Frontend перезагрузится автоматически (Vite HMR).')
print()
print('Проверка:')
print('  1. Открой браузер → консоль (F12)')
print('  2. В чате напиши: "покажи аналитику"')
print('  3. Должен открыться AnalyticsPanel')
print('  4. Графики должны показывать реальные даты (не "1 января")')
print('  5. Все тексты на русском')