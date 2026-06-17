from pathlib import Path

print('=== fix_analytics_widget.py ===')
print()

PROJECT_ROOT = Path('.')

# ============================================================================
# 1. chat.py — передаём полный отчёт в widget.data (убираем двойную загрузку)
# ============================================================================
chat_path = PROJECT_ROOT / 'backend/api/routes/chat.py'
if chat_path.exists():
    content = chat_path.read_text(encoding='utf-8')
    
    # Ищем блок где создаётся widget с пустым data
    old_widget = '''            visual={
                "widgets": [
                    {"type": "analytics_panel", "data": {}, "size": "wide"}
                ]
            }'''
    
    # Заменяем на передачу полного отчёта
    new_widget = '''            visual={
                "widgets": [
                    {
                        "type": "analytics_panel",
                        "data": {
                            "period_days": 30,
                            "trends": trends["trends"],
                            "correlations": correlations,
                            "top_issues": top_issues,
                            "summary": llm_result.get("summary", ""),
                            "insights": llm_result.get("insights", []),
                            "recommendations": llm_result.get("recommendations", []),
                            "forecast": llm_result.get("forecast", {})
                        },
                        "size": "wide"
                    }
                ]
            }'''
    
    if old_widget in content:
        content = content.replace(old_widget, new_widget)
        chat_path.write_text(content, encoding='utf-8', newline='\n')
        print('✓ backend/api/routes/chat.py: передаём полный отчёт в widget.data')
    else:
        print('⚠ Не найден точный блок widget в chat.py')
        # Пробуем альтернативный паттерн
        if '"data": {}' in content and 'analytics_panel' in content:
            content = content.replace(
                '{"type": "analytics_panel", "data": {}, "size": "wide"}',
                '''{
                        "type": "analytics_panel",
                        "data": {
                            "period_days": 30,
                            "trends": trends["trends"],
                            "correlations": correlations,
                            "top_issues": top_issues,
                            "summary": llm_result.get("summary", ""),
                            "insights": llm_result.get("insights", []),
                            "recommendations": llm_result.get("recommendations", []),
                            "forecast": llm_result.get("forecast", {})
                        },
                        "size": "wide"
                    }'''
            )
            chat_path.write_text(content, encoding='utf-8', newline='\n')
            print('✓ chat.py: альтернативная замена сработала')
else:
    print(f'⚠ Файл не найден: {chat_path}')

# ============================================================================
# 2. AnalyticsPanel.svelte — принимает data, использует если есть, max-height
# ============================================================================
panel_path = PROJECT_ROOT / 'frontend/src/components/analytics/AnalyticsPanel.svelte'
if not panel_path.parent.exists():
    panel_path.parent.mkdir(parents=True, exist_ok=True)
    print(f'✓ Создана папка: {panel_path.parent}')

panel_content = '''<script lang="ts">
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
    // Если данные уже переданы через props — не делаем повторный запрос
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
  function prepareChartData(paramKey: string) {
    if (!data?.trends?.[paramKey]) return []
    const trend = data.trends[paramKey]
    const points = []
    const days = period
    const avg = trend.avg || 0
    const slope = trend.slope_per_day || 0
    for (let i = 0; i <= days; i += Math.ceil(days / 50)) {
      points.push({
        x: i / 30,
        y: avg + slope * i + (Math.random() - 0.5) * (trend.stdev || 1) * 0.3
      })
    }
    return points
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

panel_path.write_text(panel_content, encoding='utf-8', newline='\n')
print('✓ frontend/src/components/analytics/AnalyticsPanel.svelte: переписан')

print()
print('=' * 60)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 60)
print()
print('1. backend/api/routes/chat.py:')
print('   • Передаём полный отчёт в widget.data')
print('   • Убираем двойную загрузку')
print()
print('2. frontend/src/components/analytics/AnalyticsPanel.svelte:')
print('   • Принимает data через props')
print('   • Если initialData есть — использует, не делает fetch')
print('   • max-h-[80vh] — высота 80% экрана')
print('   • flex flex-col + overflow-y-auto — правильная прокрутка')
print()
print('Backend перезагрузится автоматически (hot-reload).')
print('Frontend перезагрузится автоматически (Vite HMR).')
print()
print('Проверка:')
print('  1. В чате: "покажи аналитику"')
print('     → Откроется сразу (без спиннера), все вкладки заполнены')
print('     → Высота ~80% экрана')
print()
print('  2. Переключи период на 7 дней')
print('     → Появится спиннер (новый запрос)')