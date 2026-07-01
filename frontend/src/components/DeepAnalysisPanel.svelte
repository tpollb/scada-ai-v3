<script lang="ts">
  import { ArrowRightLeft, onMount } from 'svelte'
  import { ArrowRightLeft, Line } from 'svelte-chartjs'
  import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
  } from 'chart.js'
  import { ArrowRightLeft, X, Play, AlertTriangle, TrendingUp, Activity } from 'lucide-svelte'
  import api from '../lib/api'

  ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend
  )

  interface Props {
    onClose: () => void
  }

  let { onClose }: Props = $props()

  // State
  let tags = $state<any[]>([])
  let selectedTag = $state<string>('')
  let period = $state<number>(30)
  let isAnalyzing = $state(false)
  let analysisResult = $state<any>(null)
  let abModalOpen = $state(false)
  let abResult = $state<any>(null)
  let error = $state<string | null>(null)

  // Chart instance
  let chartInstance: ChartJS | null = null
  const chartId = `dda-chart-${Math.random().toString(36).slice(2, 9)}`

  // Загружаем список тегов при монтировании
  onMount(async () => {
    try {
      const response = await api.get('api/v1/deep_analysis/tags').json()
      tags = response
      if (tags.length > 0) {
        selectedTag = tags[0].tag_name
      }
    } catch (e) {
      console.error('Failed to fetch tags:', e)
      error = 'Не удалось загрузить список тегов'
    }
  })

  // Запуск анализа
  async function runAnalysis() {
    if (!selectedTag) {
      error = 'Выберите тег для анализа'
      return
    }

    isAnalyzing = true
    error = null
    analysisResult = null

    try {
      const response = await api.post('api/v1/deep_analysis/run', {
        json: {
          tags: [selectedTag],
          period: period,
          anomalies: true,
          correlations: false,
          seasonality: false,
          compare_periods: false,
        }
      }).json()

      console.log('🔍 Analysis response:', response)
      console.log('🔍 Response type:', typeof response)
      console.log('🔍 Response keys:', Object.keys(response || {}))
      console.log('🔍 Has visualizations?', !!response?.visualizations)
      analysisResult = response
      
      console.log('📈 Visualization data:', {
        has_visualizations: !!response.visualizations,
        has_time_series: !!response.visualizations?.time_series,
        has_data: !!response.visualizations?.time_series?.data,
        labels_count: response.visualizations?.time_series?.data?.labels?.length || 0
      })
      
      // Получаем Chart instance после рендеринга
      setTimeout(() => {
        const container = document.getElementById(chartId)
        if (container) {
          const canvas = container.querySelector('canvas')
          if (canvas) {
            chartInstance = ChartJS.getChart(canvas) || null
          }
        }
      }, 200)

    } catch (e: any) {
      console.error('Analysis failed:', e)
      error = e?.message || 'Ошибка анализа'
    } finally {
      isAnalyzing = false
    }
  }

  // Chart.js данные
  let chartData = $derived(
    analysisResult?.visualizations?.time_series?.data || { labels: [], datasets: [] }
  )

  // Отладка: логируем что приходит в chartData
  $effect(() => {
    if (chartData.labels.length > 0) {
      console.log('📊 Chart data received:', {
        labels_count: chartData.labels.length,
        datasets_count: chartData.datasets?.length,
        first_label: chartData.labels[0],
        first_dataset: chartData.datasets?.[0]
      })
    }
  })

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

  // Форматирование числа
  function formatNumber(value: number, decimals: number = 2): string {
    return value.toFixed(decimals)
  }
</script>

<div class="w-[500px] h-full bg-white dark:bg-neutral-900 border-r border-neutral-200 dark:border-neutral-700 flex flex-col overflow-hidden transition-colors">
  <!-- Header -->
  <div class="flex items-center justify-between px-4 py-3 border-b border-neutral-200 dark:border-neutral-700 flex-shrink-0">
    <div class="flex items-center gap-2">
      <Activity size={18} class="text-blue-500" />
      <h2 class="text-base font-semibold text-neutral-900 dark:text-neutral-100">
        Deep Analysis
      </h2>
    </div>
    <button
      type="button"
      onclick={onClose}
      class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition"
      title="Закрыть"
    >
      <X size={16} class="text-neutral-500" />
    </button>
  </div>

  <!-- Controls -->
  <div class="px-4 py-3 border-b border-neutral-200 dark:border-neutral-700 flex-shrink-0 space-y-3 max-h-[400px] overflow-y-auto">
    <!-- Tag selector -->
    <div>
      <label class="block text-xs font-medium text-neutral-600 dark:text-neutral-400 mb-1">
        Тег
      </label>
      <select
        bind:value={selectedTag}
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
            onclick={() => period = p}
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
      onclick={runAnalysis}
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
    
    <!-- Кнопка A/B сравнения -->
    <button
      type="button"
      onclick={() => abModalOpen = true}
      disabled={!selectedTag}
      class="w-full py-2.5 bg-neutral-100 dark:bg-neutral-800 hover:bg-neutral-200 dark:hover:bg-neutral-700 disabled:opacity-50 text-neutral-700 dark:text-neutral-300 rounded font-medium flex items-center justify-center gap-2 transition mt-2"
    >
      <ArrowRightLeft size={16} />
      Сравнить периоды (A/B)
    </button>
  </div>

  <!-- Content -->
  <div class="flex-1 overflow-y-auto px-4 py-4">
    {#if error}
      <div class="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded text-sm text-red-700 dark:text-red-300 flex items-start gap-2">
        <AlertTriangle size={16} class="flex-shrink-0 mt-0.5" />
        <span>{error}</span>
      </div>
    {:else if analysisResult}
      <!-- Summary -->
      <div class="mb-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded">
        <p class="text-sm text-blue-900 dark:text-blue-100">{analysisResult.summary}</p>
      </div>

      <!-- Statistics -->
      {#if analysisResult?.statistics && analysisResult.statistics.count > 0}
      <div class="mb-4">
        <h3 class="text-sm font-semibold text-neutral-900 dark:text-neutral-100 mb-2 flex items-center gap-1">
          <TrendingUp size={14} />
          Статистика
        </h3>
        <div class="grid grid-cols-2 gap-2 text-xs">
          <div class="p-2 bg-neutral-50 dark:bg-neutral-800 rounded">
            <div class="text-neutral-500 dark:text-neutral-400">Среднее</div>
            <div class="font-semibold text-neutral-900 dark:text-neutral-100">
              {formatNumber(analysisResult.statistics?.mean ?? 0)}
            </div>
          </div>
          <div class="p-2 bg-neutral-50 dark:bg-neutral-800 rounded">
            <div class="text-neutral-500 dark:text-neutral-400">Std Dev</div>
            <div class="font-semibold text-neutral-900 dark:text-neutral-100">
              {formatNumber(analysisResult.statistics?.std ?? 0)}
            </div>
          </div>
          <div class="p-2 bg-neutral-50 dark:bg-neutral-800 rounded">
            <div class="text-neutral-500 dark:text-neutral-400">Min</div>
            <div class="font-semibold text-neutral-900 dark:text-neutral-100">
              {formatNumber(analysisResult.statistics?.min ?? 0)}
            </div>
          </div>
          <div class="p-2 bg-neutral-50 dark:bg-neutral-800 rounded">
            <div class="text-neutral-500 dark:text-neutral-400">Max</div>
            <div class="font-semibold text-neutral-900 dark:text-neutral-100">
              {formatNumber(analysisResult.statistics?.max ?? 0)}
            </div>
          </div>
        </div>
      </div>
      {/if}

      <!-- Anomalies -->
      {#if analysisResult?.anomalies?.total_anomalies > 0}
        <div class="mb-4">
          <h3 class="text-sm font-semibold text-neutral-900 dark:text-neutral-100 mb-2 flex items-center gap-1">
            <AlertTriangle size={14} class="text-red-500" />
            Аномалии ({analysisResult.anomalies.total_anomalies})
          </h3>
          <div class="text-xs text-neutral-600 dark:text-neutral-400 mb-2">
            Обнаружено {analysisResult.anomalies.total_anomalies} аномальных точек
            ({(analysisResult.anomalies.anomaly_rate * 100).toFixed(1)}% от общего числа)
          </div>
          <div class="space-y-1 max-h-40 overflow-y-auto">
            {#each analysisResult.anomalies.anomaly_values.slice(0, 10) as value, i}
              <div class="flex items-center justify-between p-2 bg-red-50 dark:bg-red-900/20 rounded text-xs">
                <span class="text-red-700 dark:text-red-300 font-mono">
                  {formatNumber(value)}
                </span>
                <span class="text-neutral-500 dark:text-neutral-400">
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
      <div class="mb-4">
        <h3 class="text-sm font-semibold text-neutral-900 dark:text-neutral-100 mb-2">
          График
        </h3>
        <div id={chartId} class="h-[300px] bg-white dark:bg-neutral-800 rounded border border-neutral-200 dark:border-neutral-700 p-2">
          {#if chartData.labels.length > 0}
            <Line data={chartData} options={chartOptions} />
          {:else}
            <div class="flex items-center justify-center h-full text-sm text-neutral-400">
              Нет данных
            </div>
          {/if}
        </div>
      </div>

    {:else if !isAnalyzing}
      <div class="flex flex-col items-center justify-center h-full text-center text-neutral-400 dark:text-neutral-500">
        <Activity size={48} class="mb-3 opacity-50" />
        <p class="text-sm">Выберите тег и запустите анализ</p>
      </div>
    {:else}
      <div class="flex flex-col items-center justify-center h-full text-center text-neutral-400 dark:text-neutral-500">
        <div class="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-3"></div>
        <p class="text-sm">Анализируем данные...</p>
      </div>
    {/if}
  </div>
  
  <!-- A/B Comparison Modal -->
  <ABComparisonModal
    isOpen={abModalOpen}
    availableTags={availableTags}
    defaultTag={selectedTags[0]}
    onClose={() => abModalOpen = false}
    onResult={(result) => {
      abResult = result
      // Если есть анализ — добавляем ab_comparison и обновляем
      if (analysisResult) {
        analysisResult.ab_comparison = result
      }
    }}
  />
</div>
