from pathlib import Path

print('=== refactor_dda_layout.py ===')
print()

# ============================================================================
# 1. Исправляем Chart.js регистрацию в DeepAnalysisPanel
# ============================================================================
panel_path = Path('frontend/src/components/DeepAnalysisPanel.svelte')
content = panel_path.read_text(encoding='utf-8')

# Добавляем ScatterController
old_imports = '''  import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
  } from 'chart.js'

  ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend
  )'''

new_imports = '''  import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    ScatterController,
  } from 'chart.js'

  ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    ScatterController
  )'''

if old_imports in content:
    content = content.replace(old_imports, new_imports)
    panel_path.write_text(content, encoding='utf-8', newline='\n')
    print('✓ Добавлен ScatterController в Chart.js регистрацию')
else:
    print('⚠ Не удалось найти блок импортов Chart.js')

# ============================================================================
# 2. Создаём DeepAnalysisControls.svelte (только controls для левой панели)
# ============================================================================
controls_path = Path('frontend/src/components/DeepAnalysisControls.svelte')

controls_content = '''<script lang="ts">
  import { Play, Activity } from 'lucide-svelte'
  import api from '../lib/api'

  interface Props {
    tags: any[]
    selectedTag: string
    period: number
    isAnalyzing: boolean
    error: string | null
    onTagChange: (tag: string) => void
    onPeriodChange: (period: number) => void
    onRunAnalysis: () => void
  }

  let { 
    tags, 
    selectedTag, 
    period, 
    isAnalyzing, 
    error,
    onTagChange, 
    onPeriodChange, 
    onRunAnalysis 
  }: Props = $props()
</script>

<div class="w-[350px] h-full bg-white dark:bg-neutral-900 border-r border-neutral-200 dark:border-neutral-700 flex flex-col overflow-hidden transition-colors">
  <!-- Header -->
  <div class="flex items-center gap-2 px-4 py-3 border-b border-neutral-200 dark:border-neutral-700 flex-shrink-0">
    <Activity size={18} class="text-blue-500" />
    <h2 class="text-base font-semibold text-neutral-900 dark:text-neutral-100">
      Deep Analysis
    </h2>
  </div>

  <!-- Controls -->
  <div class="flex-1 overflow-y-auto px-4 py-3 space-y-3">
    <!-- Tag selector -->
    <div>
      <label class="block text-xs font-medium text-neutral-600 dark:text-neutral-400 mb-1">
        Тег
      </label>
      <select
        value={selectedTag}
        onchange={(e) => onTagChange(e.currentTarget.value)}
        class="w-full px-3 py-1.5 text-sm border border-neutral-300 dark:border-neutral-600 rounded bg-white dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        {#each tags as tag}
          <option value={tag.tag_name}>
            {tag.tag_name}
            {#if tag.zone_name}({tag.zone_name}){/if}
          </option>
        {/each}
      </select>
    </div>

    <!-- Period selector -->
    <div>
      <label class="block text-xs font-medium text-neutral-600 dark:text-neutral-400 mb-1">
        Период
      </label>
      <div class="flex gap-1">
        {#each [7, 30, 120, 365] as p}
          <button
            type="button"
            onclick={() => onPeriodChange(p)}
            class="flex-1 px-2 py-1 text-xs rounded transition {period === p
              ? 'bg-blue-500 text-white'
              : 'bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 hover:bg-neutral-200 dark:hover:bg-neutral-700'}"
          >
            {p}д
          </button>
        {/each}
      </div>
    </div>

    <!-- Run button -->
    <button
      type="button"
      onclick={onRunAnalysis}
      disabled={isAnalyzing || !selectedTag}
      class="w-full px-4 py-2 bg-blue-500 hover:bg-blue-600 disabled:bg-neutral-300 dark:disabled:bg-neutral-700 text-white text-sm font-medium rounded transition flex items-center justify-center gap-2"
    >
      {#if isAnalyzing}
        <div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
        Анализ...
      {:else}
        <Play size={14} />
        Запустить анализ
      {/if}
    </button>

    <!-- Error message -->
    {#if error}
      <div class="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded text-sm text-red-700 dark:text-red-300">
        {error}
      </div>
    {/if}
  </div>
</div>
'''

controls_path.write_text(controls_content, encoding='utf-8', newline='\n')
print(f'✓ Создан: {controls_path}')

# ============================================================================
# 3. Создаём DeepAnalysisResults.svelte (результаты для центральной части)
# ============================================================================
results_path = Path('frontend/src/components/DeepAnalysisResults.svelte')

results_content = '''<script lang="ts">
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
    ScatterController,
  } from 'chart.js'
  import { TrendingUp, AlertTriangle, Activity } from 'lucide-svelte'

  ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    ScatterController
  )

  interface Props {
    analysisResult: any
    isAnalyzing: boolean
  }

  let { analysisResult, isAnalyzing }: Props = $props()

  // Chart.js данные
  let chartData = $derived(
    analysisResult?.visualizations?.time_series?.data || { labels: [], datasets: [] }
  )

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'top' as const,
        labels: {
          font: { size: 11 },
          boxWidth: 12,
        }
      },
      tooltip: {
        mode: 'index' as const,
        intersect: false,
      },
    },
    scales: {
      x: {
        display: true,
        grid: { display: false },
        ticks: {
          maxTicksLimit: 10,
          font: { size: 10 }
        }
      },
      y: {
        display: true,
        grid: { color: 'rgba(0, 0, 0, 0.05)' },
        ticks: {
          font: { size: 10 }
        }
      }
    },
    interaction: {
      mode: 'nearest' as const,
      axis: 'x' as const,
      intersect: false
    }
  }

  function formatNumber(value: number, decimals: number = 2): string {
    return value.toFixed(decimals)
  }
</script>

<div class="flex-1 flex flex-col bg-white dark:bg-neutral-900 overflow-hidden transition-colors">
  {#if isAnalyzing}
    <div class="flex-1 flex items-center justify-center">
      <div class="flex flex-col items-center text-center text-neutral-400 dark:text-neutral-500">
        <div class="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-3"></div>
        <p class="text-sm">Анализируем данные...</p>
      </div>
    </div>
  {:else if analysisResult}
    <div class="flex-1 overflow-y-auto px-6 py-6">
      <!-- Summary -->
      <div class="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded">
        <p class="text-sm text-blue-900 dark:text-blue-100">{analysisResult.summary}</p>
      </div>

      <!-- Statistics -->
      {#if analysisResult?.statistics && analysisResult.statistics.count > 0}
      <div class="mb-6">
        <h3 class="text-base font-semibold text-neutral-900 dark:text-neutral-100 mb-3 flex items-center gap-2">
          <TrendingUp size={18} />
          Статистика
        </h3>
        <div class="grid grid-cols-4 gap-3">
          <div class="p-3 bg-neutral-50 dark:bg-neutral-800 rounded">
            <div class="text-xs text-neutral-500 dark:text-neutral-400 mb-1">Среднее</div>
            <div class="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
              {formatNumber(analysisResult.statistics.mean)}
            </div>
          </div>
          <div class="p-3 bg-neutral-50 dark:bg-neutral-800 rounded">
            <div class="text-xs text-neutral-500 dark:text-neutral-400 mb-1">Std Dev</div>
            <div class="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
              {formatNumber(analysisResult.statistics.std)}
            </div>
          </div>
          <div class="p-3 bg-neutral-50 dark:bg-neutral-800 rounded">
            <div class="text-xs text-neutral-500 dark:text-neutral-400 mb-1">Min</div>
            <div class="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
              {formatNumber(analysisResult.statistics.min)}
            </div>
          </div>
          <div class="p-3 bg-neutral-50 dark:bg-neutral-800 rounded">
            <div class="text-xs text-neutral-500 dark:text-neutral-400 mb-1">Max</div>
            <div class="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
              {formatNumber(analysisResult.statistics.max)}
            </div>
          </div>
        </div>
      </div>
      {/if}

      <!-- Anomalies -->
      {#if analysisResult?.anomalies?.total_anomalies > 0}
        <div class="mb-6">
          <h3 class="text-base font-semibold text-neutral-900 dark:text-neutral-100 mb-3 flex items-center gap-2">
            <AlertTriangle size={18} class="text-red-500" />
            Аномалии ({analysisResult.anomalies.total_anomalies})
          </h3>
          <div class="text-sm text-neutral-600 dark:text-neutral-400 mb-3">
            Обнаружено {analysisResult.anomalies.total_anomalies} аномальных точек
            ({(analysisResult.anomalies.anomaly_rate * 100).toFixed(1)}% от общего числа)
          </div>
          <div class="space-y-2 max-h-60 overflow-y-auto">
            {#each analysisResult.anomalies.anomaly_values.slice(0, 20) as value, i}
              <div class="flex items-center justify-between p-3 bg-red-50 dark:bg-red-900/20 rounded">
                <span class="text-red-700 dark:text-red-300 font-mono text-sm">
                  {formatNumber(value)}
                </span>
                <span class="text-neutral-500 dark:text-neutral-400 text-sm">
                  {new Date(analysisResult.anomalies.anomaly_timestamps[i]).toLocaleString('ru-RU', {
                    day: '2-digit',
                    month: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </span>
              </div>
            {/each}
          </div>
        </div>
      {/if}

      <!-- Chart -->
      <div class="mb-6">
        <h3 class="text-base font-semibold text-neutral-900 dark:text-neutral-100 mb-3">
          График
        </h3>
        <div class="h-[400px] bg-white dark:bg-neutral-800 rounded border border-neutral-200 dark:border-neutral-700 p-4">
          {#if chartData.labels.length > 0}
            <Line 
              data={chartData} 
              options={chartOptions}
              key={analysisResult?.analysis_id || 'default'}
            />
          {:else}
            <div class="flex items-center justify-center h-full text-sm text-neutral-400">
              Нет данных
            </div>
          {/if}
        </div>
      </div>
    </div>
  {:else}
    <div class="flex-1 flex items-center justify-center">
      <div class="flex flex-col items-center text-center text-neutral-400 dark:text-neutral-500">
        <Activity size={64} class="mb-4 opacity-50" />
        <p class="text-base mb-2">Выберите тег и запустите анализ</p>
        <p class="text-sm">Результаты появятся здесь</p>
      </div>
    </div>
  {/if}
</div>
'''

results_path.write_text(results_content, encoding='utf-8', newline='\n')
print(f'✓ Создан: {results_path}')

# ============================================================================
# 4. Обновляем Home.svelte — разделяем Controls и Results
# ============================================================================
home_path = Path('frontend/src/routes/Home.svelte')
content = home_path.read_text(encoding='utf-8')

# Удаляем старый импорт DeepAnalysisPanel
content = content.replace(
    "  import DeepAnalysisPanel from '../components/DeepAnalysisPanel.svelte'\n",
    ""
)

# Добавляем новые импорты
if 'DeepAnalysisControls' not in content:
    content = content.replace(
        "  import SystemLogsPanel from '../components/SystemLogsPanel.svelte'",
        "  import SystemLogsPanel from '../components/SystemLogsPanel.svelte'\n  import DeepAnalysisControls from '../components/DeepAnalysisControls.svelte'\n  import DeepAnalysisResults from '../components/DeepAnalysisResults.svelte'"
    )

# Добавляем state для DDA
if 'let ddaSelectedTag' not in content:
    content = content.replace(
        "  let showDeepAnalysisPanel = $state(false)",
        """  let showDeepAnalysisPanel = $state(false)
  let ddaTags = $state<any[]>([])
  let ddaSelectedTag = $state<string>('')
  let ddaPeriod = $state<number>(30)
  let ddaIsAnalyzing = $state(false)
  let ddaAnalysisResult = $state<any>(null)
  let ddaError = $state<string | null>(null)"""
    )

# Добавляем функцию runDDAAnalysis
if 'async function runDDAAnalysis' not in content:
    insert_pos = content.find("async function handleSend")
    if insert_pos > 0:
        dda_function = """
  async function runDDAAnalysis() {
    if (!ddaSelectedTag) {
      ddaError = 'Выберите тег для анализа'
      return
    }

    ddaIsAnalyzing = true
    ddaError = null
    ddaAnalysisResult = null

    try {
      const response = await api.post('api/v1/deep_analysis/run', {
        json: {
          tags: [ddaSelectedTag],
          period: ddaPeriod,
          anomalies: true,
          correlations: false,
          seasonality: false,
          compare_periods: false,
        }
      }).json()

      console.log('🔍 DDA Analysis response:', response)
      ddaAnalysisResult = response
    } catch (e: any) {
      console.error('DDA Analysis failed:', e)
      ddaError = e?.message || 'Ошибка анализа'
    } finally {
      ddaIsAnalyzing = false
    }
  }

"""
        content = content[:insert_pos] + dda_function + content[insert_pos:]

# Добавляем onMount для загрузки тегов
if 'onMount' not in content or 'ddaTags' not in content.split('onMount')[1].split('})')[0]:
    # Ищем существующий onMount
    onmount_match = content.find("onMount(async () => {")
    if onmount_match > 0:
        # Находим конец onMount
        insert_pos = content.find("})", onmount_match) + 2
        dda_onmount = """

  // Загружаем теги для Deep Analysis при открытии панели
  $effect(() => {
    if (showDeepAnalysisPanel && ddaTags.length === 0) {
      api.get('api/v1/deep_analysis/tags').json().then((tags: any[]) => {
        ddaTags = tags
        if (tags.length > 0 && !ddaSelectedTag) {
          ddaSelectedTag = tags[0].tag_name
        }
      }).catch((e: any) => {
        console.error('Failed to fetch DDA tags:', e)
        ddaError = 'Не удалось загрузить список тегов'
      })
    }
  })
"""
        content = content[:insert_pos] + dda_onmount + content[insert_pos:]

# Заменяем рендеринг DeepAnalysisPanel на Controls
old_render = """    {#if showDeepAnalysisPanel}
      <DeepAnalysisPanel onClose={() => showDeepAnalysisPanel = false} />
    {/if}"""

new_render = """    {#if showDeepAnalysisPanel}
      <DeepAnalysisControls
        tags={ddaTags}
        selectedTag={ddaSelectedTag}
        period={ddaPeriod}
        isAnalyzing={ddaIsAnalyzing}
        error={ddaError}
        onTagChange={(tag) => ddaSelectedTag = tag}
        onPeriodChange={(period) => ddaPeriod = period}
        onRunAnalysis={runDDAAnalysis}
      />
    {/if}"""

if old_render in content:
    content = content.replace(old_render, new_render)

# Добавляем Results в центральную часть (после header, перед основным контентом)
# Ищем место после <div class="flex-1 flex overflow-hidden">
main_content_start = content.find('<div class="flex-1 flex overflow-hidden">')
if main_content_start > 0:
    insert_pos = main_content_start + len('<div class="flex-1 flex overflow-hidden">')
    results_render = """
    {#if showDeepAnalysisPanel}
      <DeepAnalysisResults
        analysisResult={ddaAnalysisResult}
        isAnalyzing={ddaIsAnalyzing}
      />
    {/if}
"""
    # Проверяем что ещё не добавили
    if '<DeepAnalysisResults' not in content[insert_pos:insert_pos+500]:
        content = content[:insert_pos] + results_render + content[insert_pos:]

home_path.write_text(content, encoding='utf-8', newline='\n')
print(f'✓ Обновлён: {home_path}')

print()
print('=' * 70)
print('РЕФАКТОРИНГ ЗАВЕРШЁН')
print('=' * 70)
print()
print('Что сделано:')
print('  1. ✓ Добавлен ScatterController в Chart.js')
print('  2. ✓ Создан DeepAnalysisControls.svelte (только controls)')
print('  3. ✓ Создан DeepAnalysisResults.svelte (результаты в центре)')
print('  4. ✓ Обновлён Home.svelte:')
print('     • Controls рендерятся слева (как SystemLogsPanel)')
print('     • Results рендерятся в центральной части')
print('     • State (теги, выбранный тег, результат) в Home.svelte')
print()
print('Frontend перезагрузится автоматически (Vite HMR).')
print()
print('Проверка:')
print('  1. Открой фронтенд')
print('  2. Клик Activity в хедере')
print('  3. Слева появится панель с controls (тег, период, кнопка)')
print('  4. Выбери тег → "Запустить анализ"')
print('  5. В центральной части появится:')
print('     • Блок статистики (mean, std, min, max)')
print('     • Список аномалий (если есть)')
print('     • График (высота 400px)')
print()
print('Скинь вывод консоли если будут ошибки!')