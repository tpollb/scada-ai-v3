<script lang="ts">
  function formatAnomalyDate(timestamp: any): string {
    if (!timestamp) return '—'
    try {
      const d = new Date(timestamp)
      if (isNaN(d.getTime())) return String(timestamp)
      return d.toLocaleString('ru-RU', {
        day: '2-digit', month: '2-digit', year: '2-digit',
        hour: '2-digit', minute: '2-digit'
      })
    } catch {
      return String(timestamp)
    }
  }

  import { Line } from 'svelte-chartjs'
  import ChartModal from './ChartModal.svelte'
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
    BubbleController,
    Filler,
  } from 'chart.js'
  import zoomPlugin from 'chartjs-plugin-zoom'
  import { Activity, AlertTriangle, ArrowDownCircle, ArrowRightLeft, ArrowUpCircle, ChevronDown, Circle, Download, Grid3x3, Info, Lightbulb, Loader2, RotateCcw, Table, TrendingUp, Waves, Zap, ZoomIn, ZoomOut, Maximize2, Brain} from 'lucide-svelte'
  import api from '../lib/api'
  import DDAInterpretation from './DDAInterpretation.svelte'

  ChartJS.register(
    CategoryScale, LinearScale, PointElement, LineElement,
    Title, Tooltip, Legend, ScatterController, BubbleController, zoomPlugin, Filler
  )

  interface Props {
    analysisResult: any
    isAnalyzing: boolean
    forceTab?: 'overview' | 'correlations' | 'table' | 'interpretation' | null
  }

  let { analysisResult, isAnalyzing, forceTab }: Props = $props()

  // Режим: single-tag или multi-tag
  
  // === Seasonal analysis helpers ===
  function samplePattern(pattern: number[], maxPoints: number = 200): number[] {
    if (!pattern || pattern.length === 0) return []
    if (pattern.length <= maxPoints) return pattern
    const step = pattern.length / maxPoints
    const result: number[] = []
    for (let i = 0; i < maxPoints; i++) {
      result.push(pattern[Math.floor(i * step)])
    }
    return result
  }

  function getPatternStats(pattern: number[]) {
    const valid = pattern.filter((v: any) => v !== null && v !== undefined)
    if (valid.length === 0) return { min: 0, max: 0, range: 0 }
    const min = Math.min(...valid)
    const max = Math.max(...valid)
    return { min, max, range: max - min }
  }

  function formatPeriod(period: number): string {
    // 5-мин sampling rate: 12 точек/час, 288/день, 2016/неделя
    const pointsPerDay = 288
    const days = period / pointsPerDay
    const hours = period / 12
    
    // Точные суточные/недельные периоды
    if (period >= 270 && period <= 310) return '~24ч (сутки)'
    if (period >= 135 && period <= 150) return '~12ч'
    if (period >= 560 && period <= 590) return '~2 дня'
    if (period >= 850 && period <= 880) return '~3 дня'
    if (period >= 1140 && period <= 1170) return '~4 дня'
    if (period >= 1420 && period <= 1460) return '~5 дней'
    if (period >= 1710 && period <= 1750) return '~6 дней'
    if (period >= 2000 && period <= 2040) return '~7 дней (неделя)'
    if (period >= 2860 && period <= 2900) return '~10 дней'
    if (period >= 4300 && period <= 4350) return '~15 дней'
    if (period >= 5740 && period <= 5780) return '~20 дней'
    if (period >= 8620 && period <= 8660) return '~30 дней (месяц)'
    
    // Округляем до дней/часов
    if (days >= 1) return `~${days.toFixed(1)} дней`
    if (hours >= 1) return `~${hours.toFixed(1)}ч`
    return `${period} точек`
  }

let isMultiTag = $derived(
    analysisResult?.tags?.length > 1 && 
    analysisResult?.correlations !== null &&
    analysisResult?.correlations !== undefined
  )

  let expandedType = $state<string | null>(null)
  let activeTab = $state<'overview' | 'correlations' | 'table' | 'interpretation'>('overview')

  // Переключение вкладки извне (например, после A/B анализа)
  $effect(() => {
    if (forceTab && forceTab !== activeTab) {
      activeTab = forceTab
      // Добавляем в visitedTabs чтобы вкладка отрендерилась
      visitedTabs[forceTab] = true
    }
  })
  let visitedTabs = $state<Record<string, boolean>>({ overview: true })

  // Keep alive: запоминаем открытые вкладки чтобы не терять состояние
  $effect(() => {
    if (activeTab && !visitedTabs[activeTab]) {
      visitedTabs[activeTab] = true
    }
  })

  $effect(() => {
    if (isMultiTag) activeTab = 'correlations'
    else activeTab = 'overview'
  })

  // Chart instances
  let tsChartInstance: ChartJS | null = $state(null)
  let scatterChartInstance: ChartJS | null = $state(null)
  const tsChartId = `dda-ts-${Math.random().toString(36).slice(2, 9)}`
  const scatterChartId = `dda-scatter-${Math.random().toString(36).slice(2, 9)}`
  const patternChartId = `dda-pattern-${Math.random().toString(36).slice(2, 9)}`
  let patternChartInstances: Record<string, ChartJS> = $state({})
  // ChartModal state
  let modalOpen = $state(false)
  let modalChartType = $state<'line' | 'bar'>('line')
  let modalTitle = $state('')
  let modalData = $state<any>(null)
  let modalOptions = $state<any>(null)

  function openChartModal(type: 'line' | 'bar', title: string, data: any, options: any) {
    modalChartType = type
    modalTitle = title
    modalData = data
    modalOptions = options
    modalOpen = true
  }

  function closeChartModal() {
    modalOpen = false
  }


  // Данные графиков
  let timeSeriesData = $derived(
    analysisResult?.visualizations?.time_series?.data || { labels: [], datasets: [] }
  )



  let correlationMatrix = $derived(analysisResult?.correlations)

  // Выбранная пара тегов (для scatter plot)
  let selectedPair = $state<{tag1: string, tag2: string} | null>(null)
  let pairAnalysis = $state<any>(null)
  let isLoadingPair = $state(false)
  let pairError = $state<string | null>(null)

  // Инициализация: выбираем первую пару по умолчанию
  $effect(() => {
    if (correlationMatrix?.tags?.length >= 2 && !selectedPair) {
      selectedPair = {
        tag1: correlationMatrix.tags[0],
        tag2: correlationMatrix.tags[1]
      }
    }
  })

  // При смене выбранной пары — загружаем данные
  $effect(() => {
    if (selectedPair) {
      loadPairAnalysis(selectedPair.tag1, selectedPair.tag2)
    }
  })

  async function loadPairAnalysis(tag1: string, tag2: string) {
    if (!analysisResult?.period) return
    
    isLoadingPair = true
    pairError = null
    
    try {
      // Извлекаем период из строки "30 days"
      const periodMatch = analysisResult.period.match(/(\d+)/)
      const periodDays = periodMatch ? parseInt(periodMatch[1]) : 30
      
      const response = await api.post('api/v1/deep_analysis/pair', {
        json: { tag1, tag2, period: periodDays }
      }).json()
      
      pairAnalysis = response
    } catch (e: any) {
      console.error('Failed to load pair:', e)
      pairError = e?.message || 'Ошибка загрузки пары'
    } finally {
      isLoadingPair = false
    }
  }

  function selectPair(tag1: string, tag2: string) {
    if (tag1 === tag2) return // Не выбираем диагональ
    selectedPair = { tag1, tag2 }
  }

  // Scatter данные (из pairAnalysis)
  let scatterData = $derived.by(() => {
    if (!pairAnalysis?.scatter_spec?.data) {
      return { datasets: [] }
    }
    return pairAnalysis.scatter_spec.data
  })

  // Downsampling scatter
  let downsampledScatterData = $derived.by(() => {
    if (!scatterData.datasets || scatterData.datasets.length === 0) {
      return scatterData
    }
    
    const MAX_POINTS = 800
    return {
      datasets: scatterData.datasets.map((ds: any) => {
        if (ds.type === 'line') return ds // Регрессию не даунсемплим
        
        if (!Array.isArray(ds.data) || ds.data.length <= MAX_POINTS) {
          return {
            ...ds,
            backgroundColor: 'rgba(59, 130, 246, 0.35)',
            borderColor: 'rgba(59, 130, 246, 0.7)',
            pointRadius: ds.data.length > 500 ? 2 : 3,
            pointHoverRadius: 5,
          }
        }
        
        const indices: number[] = []
        const step = ds.data.length / MAX_POINTS
        for (let i = 0; i < MAX_POINTS; i++) {
          indices.push(Math.floor(i * step))
        }
        return {
          ...ds,
          data: indices.map((idx: number) => ds.data[idx]),
          backgroundColor: 'rgba(59, 130, 246, 0.4)',
          borderColor: 'rgba(59, 130, 246, 0.8)',
          pointRadius: 2.5,
          pointHoverRadius: 5,
        }
      })
    }
  })

  const timeSeriesOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: true, position: 'top' as const, labels: { font: { size: 11 }, boxWidth: 12 } },
      tooltip: { mode: 'index' as const, intersect: false },
      zoom: {
        pan: { enabled: true, mode: 'x' as const, modifierKey: null },
        zoom: {
          wheel: { enabled: true, speed: 0.05 },
          pinch: { enabled: true },
          drag: { enabled: true, modifierKey: 'shift' as const, backgroundColor: 'rgba(59, 130, 246, 0.1)', borderColor: 'rgba(59, 130, 246, 0.5)', borderWidth: 1 },
          mode: 'x' as const,
        },
      },
    },
    scales: {
      x: { type: 'category' as const, display: true, grid: { display: false }, ticks: { maxTicksLimit: 10, font: { size: 10 } } },
      y: { display: true, grid: { color: 'rgba(0, 0, 0, 0.05)' }, ticks: { font: { size: 10 } } }
    },
    interaction: { mode: 'nearest' as const, axis: 'x' as const, intersect: false }
  }

  const scatterOptions = $derived.by(() => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: true, position: 'top' as const },
      tooltip: { 
        mode: 'nearest' as const, 
        intersect: true,
        callbacks: {
          label: (ctx: any) => {
            const tagX = pairAnalysis?.tag1 || 'X'
            const tagY = pairAnalysis?.tag2 || 'Y'
            return `${tagX}: ${ctx.parsed.x.toFixed(2)}, ${tagY}: ${ctx.parsed.y.toFixed(2)}`
          }
        }
      },
      zoom: {
        pan: { enabled: true, mode: 'xy' as const, modifierKey: null },
        zoom: {
          wheel: { enabled: true, speed: 0.05 },
          pinch: { enabled: true },
          drag: { enabled: true, modifierKey: 'shift' as const, backgroundColor: 'rgba(59, 130, 246, 0.1)', borderColor: 'rgba(59, 130, 246, 0.5)', borderWidth: 1 },
          mode: 'xy' as const,
        },
      },
    },
    scales: {
      x: { 
        type: 'linear' as const, 
        title: { display: true, text: pairAnalysis?.tag1 || '' },
        grid: { color: 'rgba(0, 0, 0, 0.05)' }
      },
      y: { 
        type: 'linear' as const, 
        title: { display: true, text: pairAnalysis?.tag2 || '' },
        grid: { color: 'rgba(0, 0, 0, 0.05)' }
      }
    }
  }))

  $effect(() => {
    if (timeSeriesData.labels.length > 0) {
      setTimeout(() => {
        const container = document.getElementById(tsChartId)
        if (container) {
          const canvas = container.querySelector('canvas')
          if (canvas) tsChartInstance = ChartJS.getChart(canvas) || null
        }
      }, 200)
    }
  })

  $effect(() => {
    if (analysisResult?.seasonality?.pattern?.pattern?.length > 0) {
      setTimeout(() => {
        const newInstances: Record<string, ChartJS> = {}
        // Single-tag pattern
        const singleContainer = document.getElementById(patternChartId)
        if (singleContainer) {
          const canvas = singleContainer.querySelector('canvas')
          if (canvas) {
            const chart = ChartJS.getChart(canvas)
            if (chart) newInstances['single'] = chart
          }
        }
        // Multi-tag patterns (каждый тег)
        if (analysisResult?.tags && Array.isArray(analysisResult.tags)) {
          analysisResult.tags.forEach((tag: string) => {
            const multiContainer = document.getElementById(`pattern-chart-${tag}`)
            if (multiContainer) {
              const canvas = multiContainer.querySelector('canvas')
              if (canvas) {
                const chart = ChartJS.getChart(canvas)
                if (chart) newInstances[tag] = chart
              }
            }
          })
        }
        patternChartInstances = newInstances
      }, 300)
    }
  })

  $effect(() => {
    if (downsampledScatterData.datasets?.length > 0) {
      setTimeout(() => {
        const container = document.getElementById(scatterChartId)
        if (container) {
          const canvas = container.querySelector('canvas')
          if (canvas) scatterChartInstance = ChartJS.getChart(canvas) || null
        }
      }, 200)
    }
  })

  function resetZoomTs() {
    try {
      if (tsChartInstance && typeof tsChartInstance.resetZoom === 'function') {
        tsChartInstance.resetZoom()
      }
    } catch (e) {
      console.warn('Reset zoom failed:', e)
    }
  }
  
  function zoomInTs() {
    try {
      if (tsChartInstance && typeof tsChartInstance.zoom === 'function') {
        tsChartInstance.zoom(1.2)
      }
    } catch (e) {
      console.warn('Zoom in failed:', e)
    }
  }
  
  function zoomOutTs() {
    try {
      if (tsChartInstance && typeof tsChartInstance.zoom === 'function') {
        tsChartInstance.zoom(0.8)
      }
    } catch (e) {
      console.warn('Zoom out failed:', e)
    }
  }

  // === Pattern chart controls ===
  function zoomInPattern(tagKey: string = 'single') {
    try {
      const chart = patternChartInstances[tagKey]
      if (chart && typeof chart.zoom === 'function') {
        chart.zoom(1.2)
      }
    } catch (e) { console.warn('Pattern zoom in failed:', e) }
  }
  function zoomOutPattern(tagKey: string = 'single') {
    try {
      const chart = patternChartInstances[tagKey]
      if (chart && typeof chart.zoom === 'function') {
        chart.zoom(0.8)
      }
    } catch (e) { console.warn('Pattern zoom out failed:', e) }
  }
  function resetZoomPattern(tagKey: string = 'single') {
    try {
      const chart = patternChartInstances[tagKey]
      if (chart && typeof chart.resetZoom === 'function') {
        chart.resetZoom()
      }
    } catch (e) { console.warn('Pattern reset zoom failed:', e) }
  }

  function openPatternModal(pattern: number[], title: string) {
    const labels = pattern.map((_: any, i: number) => i)
    modalChartType = 'line'
    modalTitle = title
    modalData = {
      labels,
      datasets: [{
        label: title,
        data: pattern,
        borderColor: 'rgb(168, 85, 247)',
        backgroundColor: 'rgba(168, 85, 247, 0.1)',
        borderWidth: 2,
        pointRadius: 0,
        pointHoverRadius: 4,
        tension: 0.2,
        fill: true,
      }]
    }
    modalOptions = timeSeriesOptions
    modalOpen = true
  }
  
  function resetZoomScatter() {
    try {
      if (scatterChartInstance && typeof scatterChartInstance.resetZoom === 'function') {
        scatterChartInstance.resetZoom()
      }
    } catch (e) {
      console.warn('Reset zoom scatter failed:', e)
    }
  }
  
  function zoomInScatter() {
    try {
      if (scatterChartInstance && typeof scatterChartInstance.zoom === 'function') {
        scatterChartInstance.zoom(1.2)
      }
    } catch (e) {
      console.warn('Zoom in scatter failed:', e)
    }
  }
  
  function zoomOutScatter() {
    try {
      if (scatterChartInstance && typeof scatterChartInstance.zoom === 'function') {
        scatterChartInstance.zoom(0.8)
      }
    } catch (e) {
      console.warn('Zoom out scatter failed:', e)
    }
  }
  
  function downloadPNG(chartInstance: ChartJS | null, prefix: string) {
    if (!chartInstance) return
    const canvas = chartInstance.canvas
    const link = document.createElement('a')
    const tagNames = analysisResult?.tags?.join('_') || 'analysis'
    const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-')
    link.download = `scada_ai_${prefix}_${tagNames}_${timestamp}.png`
    link.href = canvas.toDataURL('image/png', 1.0)
    link.click()
  }

  function formatNumber(value: number, decimals: number = 2): string {
    if (value === null || value === undefined) return '—'
    return value.toFixed(decimals)
  }

  function corrColor(value: number): string {
    if (value >= 0) {
      const intensity = Math.min(Math.abs(value), 1)
      return `rgba(59, 130, 246, ${0.15 + intensity * 0.75})`
    } else {
      const intensity = Math.min(Math.abs(value), 1)
      return `rgba(239, 68, 68, ${0.15 + intensity * 0.75})`
    }
  }

  function shortenTagName(name: string, maxLen: number = 25): string {
    if (name.length <= maxLen) return name
    return name.slice(0, maxLen - 3) + '...'
  }

  function isPairSelected(tag1: string, tag2: string): boolean {
    if (!selectedPair) return false
    return (selectedPair.tag1 === tag1 && selectedPair.tag2 === tag2) ||
           (selectedPair.tag1 === tag2 && selectedPair.tag2 === tag1)
  }

  let correlationPairs = $derived.by(() => {
    if (!correlationMatrix?.matrix) return []
    const pairs: Array<{tag1: string, tag2: string, coef: number, p_value: number}> = []
    const tags = correlationMatrix.tags
    const matrix = correlationMatrix.matrix
    const pValues = correlationMatrix.p_values
    
    for (let i = 0; i < tags.length; i++) {
      for (let j = i + 1; j < tags.length; j++) {
        pairs.push({
          tag1: tags[i],
          tag2: tags[j],
          coef: matrix[i][j],
          p_value: pValues?.[i]?.[j] ?? 1.0
        })
      }
    }
    
    return pairs.sort((a, b) => Math.abs(b.coef) - Math.abs(a.coef))
  })

  function significanceBadge(p: number) {
    if (p < 0.001) return { label: '***', color: 'green', title: 'Высоко значимая (p < 0.001)' }
    if (p < 0.01) return { label: '**', color: 'green', title: 'Значимая (p < 0.01)' }
    if (p < 0.05) return { label: '*', color: 'yellow', title: 'Слабо значимая (p < 0.05)' }
    return { label: 'ns', color: 'neutral', title: 'Не значимая (p ≥ 0.05)' }
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
    <!-- Tabs -->
    <div class="flex items-center gap-4 px-4 py-3 flex-shrink-0 border-b border-neutral-200 dark:border-neutral-700">
      {#if !isMultiTag}
        <button
          type="button"
          onclick={() => activeTab = 'overview'}
          class="border-none bg-transparent p-0 cursor-pointer text-base font-medium leading-6 transition-colors flex items-center gap-1.5 {activeTab === 'overview' ? 'text-blue-600 dark:text-blue-400' : 'text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-200'}"
        >
          <TrendingUp size={16} />
          Обзор
        </button>
        <button
          type="button"
          onclick={() => activeTab = 'interpretation'}
          class="border-none bg-transparent p-0 cursor-pointer text-base font-medium leading-6 transition-colors flex items-center gap-1.5 {activeTab === 'interpretation' ? 'text-purple-600 dark:text-purple-400' : 'text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-200'}"
        >
          <Brain size={16} />
          Интерпретация
        </button>
      {/if}
      {#if isMultiTag}
        <button
          type="button"
          onclick={() => activeTab = 'correlations'}
          class="border-none bg-transparent p-0 cursor-pointer text-base font-medium leading-6 transition-colors flex items-center gap-1.5 {activeTab === 'correlations' ? 'text-blue-600 dark:text-blue-400' : 'text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-200'}"
        >
          <Grid3x3 size={16} />
          Корреляции
        </button>
        <button
          type="button"
          onclick={() => activeTab = 'table'}
          class="border-none bg-transparent p-0 cursor-pointer text-base font-medium leading-6 transition-colors flex items-center gap-1.5 {activeTab === 'table' ? 'text-blue-600 dark:text-blue-400' : 'text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-200'}"
        >
          <Table size={16} />
          Таблица пар
        </button>
        <button
          type="button"
          onclick={() => activeTab = 'interpretation'}
          class="border-none bg-transparent p-0 cursor-pointer text-base font-medium leading-6 transition-colors flex items-center gap-1.5 {activeTab === 'interpretation' ? 'text-purple-600 dark:text-purple-400' : 'text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-200'}"
        >
          <Brain size={16} />
          Интерпретация
        </button>
      {/if}
    </div>

    <div class="flex-1 overflow-y-auto px-6 py-4">
      <!-- Summary -->
      <div class="mb-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded">
        <p class="text-sm text-blue-900 dark:text-blue-100">{analysisResult.summary}</p>
      </div>

      <!-- ==================== SINGLE TAG: OVERVIEW ==================== -->
      {#if !isMultiTag && activeTab === 'overview'}
        {#if analysisResult?.statistics && analysisResult.statistics.count > 0}
        <div class="mb-4">
          <h3 class="text-sm font-semibold mb-2 flex items-center gap-2">
            <TrendingUp size={16} />
            Статистика
          </h3>
          <div class="grid grid-cols-4 gap-2">
            <div class="p-2 bg-neutral-50 dark:bg-neutral-800 rounded">
              <div class="text-xs text-neutral-500 dark:text-neutral-400 mb-1">Среднее</div>
              <div class="text-base font-semibold">{formatNumber(analysisResult.statistics.mean)}</div>
            </div>
            <div class="p-2 bg-neutral-50 dark:bg-neutral-800 rounded">
              <div class="text-xs text-neutral-500 dark:text-neutral-400 mb-1">Std Dev</div>
              <div class="text-base font-semibold">{formatNumber(analysisResult.statistics.std)}</div>
            </div>
            <div class="p-2 bg-neutral-50 dark:bg-neutral-800 rounded">
              <div class="text-xs text-neutral-500 dark:text-neutral-400 mb-1">Min</div>
              <div class="text-base font-semibold">{formatNumber(analysisResult.statistics.min)}</div>
            </div>
            <div class="p-2 bg-neutral-50 dark:bg-neutral-800 rounded">
              <div class="text-xs text-neutral-500 dark:text-neutral-400 mb-1">Max</div>
              <div class="text-base font-semibold">{formatNumber(analysisResult.statistics.max)}</div>
            </div>
          </div>
        </div>
        {/if}

        {#if analysisResult?.anomalies?.total_anomalies > 0}
          <div class="mb-4">
            <h3 class="text-sm font-semibold mb-2 flex items-center gap-2">
              <AlertTriangle size={16} class="text-red-500" />
              Аномалии ({analysisResult.anomalies.total_anomalies})
            </h3>
            <div class="space-y-1 max-h-40 overflow-y-auto">
              {#each analysisResult.anomalies.anomaly_values.slice(0, 20) as value, i}
                <div class="flex items-center justify-between p-2 bg-red-50 dark:bg-red-900/20 rounded text-xs">
                  <span class="text-red-700 dark:text-red-300 font-mono">{formatNumber(value)}</span>
                  <span class="text-neutral-500 dark:text-neutral-400">
                    {new Date(analysisResult.anomalies.anomaly_timestamps[i]).toLocaleString('ru-RU', {
                      day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit'
                    })}
                  </span>
                </div>
              {/each}
            </div>
          </div>
        {/if}

        <div class="mb-4">
          <div class="flex items-center justify-between mb-2">
            <h3 class="text-sm font-semibold">График</h3>
            <div class="flex items-center gap-1">
              <button type="button" onclick={zoomInTs} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Приблизить"><ZoomIn size={14} class="text-neutral-600 dark:text-neutral-400" /></button>
              <button type="button" onclick={zoomOutTs} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Отдалить"><ZoomOut size={14} class="text-neutral-600 dark:text-neutral-400" /></button>
              <button type="button" onclick={resetZoomTs} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Сбросить"><RotateCcw size={14} class="text-neutral-600 dark:text-neutral-400" /></button>
              <button type="button" onclick={() => downloadPNG(tsChartInstance, 'timeseries')} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Скачать PNG"><Download size={14} class="text-neutral-600 dark:text-neutral-400" /></button>
              <button type="button" onclick={() => openChartModal('line', `Временной ряд: ${analysisResult?.tags?.[0] || 'Tag'}`, timeSeriesData, timeSeriesOptions)} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Полноэкранный режим"><Maximize2 size={14} class="text-neutral-600 dark:text-neutral-400" /></button>
            </div>
          </div>
          <div id={tsChartId} class="h-[300px] bg-white dark:bg-neutral-800 rounded border border-neutral-200 dark:border-neutral-700 p-3">
            {#if timeSeriesData?.labels?.length > 0}
              <Line data={timeSeriesData} options={timeSeriesOptions} key={analysisResult?.analysis_id || 'default'} />
            {:else}
              <div class="flex items-center justify-center h-full text-sm text-neutral-400">Нет данных</div>
            {/if}
          </div>
        </div>
        <!-- Сезонный анализ -->
        {#if analysisResult?.seasonality?.periods?.detected_periods?.length > 0}
        <div class="mb-4">
          <h3 class="text-sm font-semibold mb-2 flex items-center gap-2">
            <Waves size={16} class="text-purple-500" />
            Сезонность
          </h3>
          
          {#if analysisResult.seasonality.periods.detected_periods.length > 0}
          <div class="mb-3">
            <div class="text-xs text-neutral-600 dark:text-neutral-400 mb-2">Обнаруженные периоды:</div>
            <div class="grid grid-cols-2 gap-2">
              {#each analysisResult.seasonality.periods.detected_periods.slice(0, 4) as period}
                <div class="p-2 bg-purple-50 dark:bg-purple-900/20 rounded border border-purple-200 dark:border-purple-800">
                  <div class="text-xs text-neutral-600 dark:text-neutral-400">Период</div>
                  <div class="text-sm font-semibold text-purple-700 dark:text-purple-300">
                    {period.period} точек
                    <span class="text-xs text-neutral-500">({formatPeriod(period.period)})</span>
                  </div>
                  <div class="text-xs text-neutral-500 mt-1">
                    Уверенность: {(period.confidence * 100).toFixed(0)}%
                  </div>
                </div>
              {/each}
            </div>
          </div>
          {/if}

          {#if analysisResult.seasonality.decomposition?.variance_explained}
          {@const ve = analysisResult.seasonality.decomposition.variance_explained}
          <div class="mb-3">
            <div class="text-xs text-neutral-600 dark:text-neutral-400 mb-2">Распределение дисперсии:</div>
            <div class="space-y-1">
              <div class="flex items-center gap-2">
                <div class="w-20 text-xs text-neutral-600 dark:text-neutral-400">Тренд:</div>
                <div class="flex-1 bg-neutral-200 dark:bg-neutral-700 rounded-full h-4 overflow-hidden">
                  <div class="bg-blue-500 h-full" style="width: {ve.trend}%"></div>
                </div>
                <div class="w-12 text-xs text-right font-mono">{ve.trend.toFixed(1)}%</div>
              </div>
              <div class="flex items-center gap-2">
                <div class="w-20 text-xs text-neutral-600 dark:text-neutral-400">Сезонность:</div>
                <div class="flex-1 bg-neutral-200 dark:bg-neutral-700 rounded-full h-4 overflow-hidden">
                  <div class="bg-purple-500 h-full" style="width: {ve.seasonal}%"></div>
                </div>
                <div class="w-12 text-xs text-right font-mono">{ve.seasonal.toFixed(1)}%</div>
              </div>
              <div class="flex items-center gap-2">
                <div class="w-20 text-xs text-neutral-600 dark:text-neutral-400">Остаток:</div>
                <div class="flex-1 bg-neutral-200 dark:bg-neutral-700 rounded-full h-4 overflow-hidden">
                  <div class="bg-neutral-500 h-full" style="width: {ve.residual}%"></div>
                </div>
                <div class="w-12 text-xs text-right font-mono">{ve.residual.toFixed(1)}%</div>
              </div>
            </div>
          </div>
                    {/if}

          {#if analysisResult.seasonality.pattern?.pattern?.length > 0}
          {@const pattern = analysisResult.seasonality.pattern.pattern}
          {@const stats = getPatternStats(pattern)}
          {@const patternData = {
            labels: pattern.map((_: any, i: number) => i),
            datasets: [{
              label: 'Типичный паттерн',
              data: pattern,
              borderColor: 'rgb(168, 85, 247)',
              backgroundColor: 'rgba(168, 85, 247, 0.1)',
              borderWidth: 2,
              pointRadius: pattern.length > 100 ? 0 : 2,
              pointHoverRadius: 5,
              tension: 0.2,
              fill: true,
            }]
          }}
          <div class="mb-3">
            <div class="flex items-center justify-between mb-2">
              <div class="text-xs text-neutral-600 dark:text-neutral-400">
                Типичный паттерн (период {analysisResult.seasonality.periods.detected_periods[0].period} точек, {formatPeriod(analysisResult.seasonality.periods.detected_periods[0].period)})
              </div>
              <div class="flex items-center gap-1">
                <button type="button" onclick={() => zoomInPattern('single')} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Приблизить"><ZoomIn size={14} class="text-neutral-600 dark:text-neutral-400" /></button>
                <button type="button" onclick={() => zoomOutPattern('single')} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Отдалить"><ZoomOut size={14} class="text-neutral-600 dark:text-neutral-400" /></button>
                <button type="button" onclick={() => resetZoomPattern('single')} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Сбросить"><RotateCcw size={14} class="text-neutral-600 dark:text-neutral-400" /></button>
                <button type="button" onclick={() => downloadPNG(patternChartInstances['single'], 'pattern')} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Скачать PNG"><Download size={14} class="text-neutral-600 dark:text-neutral-400" /></button>
                <button type="button" onclick={() => openPatternModal(pattern, 'Типичный паттерн')} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Полноэкранный режим"><Maximize2 size={14} class="text-neutral-600 dark:text-neutral-400" /></button>
              </div>
            </div>
            <div class="text-xs text-neutral-600 dark:text-neutral-400 mb-2">
              Мин: {stats.min.toFixed(1)} | Макс: {stats.max.toFixed(1)} | Размах: {stats.range.toFixed(1)}
            </div>
            <div id={patternChartId} class="h-40 bg-white dark:bg-neutral-800 rounded border border-neutral-200 dark:border-neutral-700 p-3">
              <Line data={patternData} options={{...timeSeriesOptions, plugins: {...timeSeriesOptions.plugins, legend: {display: false}}}} key={`pattern-single-${analysisResult?.analysis_id || 'default'}`} />
            </div>
          </div>
          {/if}
        </div>
        {/if}

      {/if}

      <!-- ==================== MULTI-TAG: CORRELATIONS ==================== -->
      {#if isMultiTag && activeTab === 'correlations'}


        <!-- 0. Time series с аномалиями (если есть) -->
        {#if analysisResult?.visualizations?.time_series?.data?.datasets?.length > 0}
        <div class="mb-4">
          <div class="flex items-center justify-between mb-2">
            <h3 class="text-sm font-semibold">
              Временные ряды ({analysisResult.tags.length} тегов) с аномалиями
            </h3>
            <div class="flex items-center gap-1">
              <button type="button" onclick={zoomInTs} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Приблизить"><ZoomIn size={14} class="text-neutral-600 dark:text-neutral-400" /></button>
              <button type="button" onclick={zoomOutTs} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Отдалить"><ZoomOut size={14} class="text-neutral-600 dark:text-neutral-400" /></button>
              <button type="button" onclick={resetZoomTs} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Сбросить"><RotateCcw size={14} class="text-neutral-600 dark:text-neutral-400" /></button>
              <button type="button" onclick={() => downloadPNG(tsChartInstance, 'multitag_timeseries')} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Скачать PNG"><Download size={14} class="text-neutral-600 dark:text-neutral-400" /></button>
              <button type="button" onclick={() => openChartModal('line', 'Временные ряды (мульти-тег)', timeSeriesData, timeSeriesOptions)} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Полноэкранный режим"><Maximize2 size={14} class="text-neutral-600 dark:text-neutral-400" /></button>
            </div>
          </div>
          <div class="text-xs text-neutral-500 dark:text-neutral-400 mb-2 flex items-center gap-1.5">
            <Lightbulb size={12} />
            <span>Колёсико — zoom · Shift+drag — область · Drag — прокрутка</span>
          </div>
          <div id={tsChartId} class="h-[300px] bg-white dark:bg-neutral-800 rounded border border-neutral-200 dark:border-neutral-700 p-3">
            <Line data={timeSeriesData} options={timeSeriesOptions} key={analysisResult?.analysis_id || 'multitag'} />
          </div>
          
          <!-- Сводка по типам аномалий -->
          {#if analysisResult?.anomalies?.type_counts}
            {@const tc = analysisResult.anomalies.type_counts}
            <!-- Раскрывающаяся сводка с описаниями типов и списком значений -->
            <div class="mt-3 space-y-2">
              <!-- Заголовок-подсказка -->
              <div class="text-[11px] text-neutral-600 dark:text-neutral-400 p-2 bg-neutral-50 dark:bg-neutral-800/50 rounded">
                💡 Кликните на тип аномалии чтобы увидеть подробности и список значений
              </div>

              <!-- Пики -->
              <details class="border border-red-200 dark:border-red-800 rounded bg-red-50 dark:bg-red-900/10" open={expandedType === 'spike'}>
                <summary class="p-2 cursor-pointer hover:bg-red-100 dark:hover:bg-red-900/30 transition flex items-center justify-between" onclick={(e) => { e.preventDefault(); expandedType = expandedType === 'spike' ? null : 'spike'; }}>
                  <div class="flex items-center gap-2">
                    <ArrowUpCircle size={14} class="text-red-500" />
                    <span class="text-sm font-semibold text-red-700 dark:text-red-300">Пики (Spike)</span>
                    <span class="text-xs px-1.5 py-0.5 bg-red-200 dark:bg-red-900/40 text-red-800 dark:text-red-200 rounded">{tc.spike || 0}</span>
                  </div>
                  <span class="text-red-500 transition-transform" class:rotate-180={expandedType === 'spike'}>
                      <ChevronDown size={14} />
                    </span>
                </summary>
                <div class="p-2 border-t border-red-200 dark:border-red-800">
                  <p class="text-[11px] text-red-700 dark:text-red-300 mb-2">
                    <strong>Пик (Spike)</strong> — резкий одиночный скачок значения вверх относительно соседей. 
                    Обычно вызван кратковременным сбоем датчика, электромагнитной помехой или мгновенным событием в системе.
                    Математика: локальный z-score &gt; 1.5 (отклонение больше 1.5 стандартных отклонений от локального среднего).
                  </p>
                  {#if analysisResult?.anomalies?.per_tag}
                    {#each Object.entries(analysisResult.anomalies.per_tag) as [tagName, tagData]}
                      {@const spikePoints = (tagData.anomaly_indices || []).filter((idx, i) => (tagData.anomaly_types || [])[i] === 'spike')}
                      {#if spikePoints.length > 0}
                        <div class="mt-2">
                          <div class="text-[10px] font-semibold text-red-700 dark:text-red-300 mb-1">{tagName} ({spikePoints.length}):</div>
                          <div class="max-h-32 overflow-y-auto space-y-0.5">
                            {#each spikePoints.slice(0, 20) as idx, i}
                              {@const val = (tagData.anomaly_values || [])[tagData.anomaly_indices.indexOf(idx)]}
                              <div class="text-[10px] font-mono text-red-600 dark:text-red-400 flex justify-between">
                                <span>#{idx}</span>
                                <span class="font-semibold">{val !== undefined ? val.toFixed(2) : '—'}</span>
                              </div>
                            {/each}
                            {#if spikePoints.length > 20}
                              <div class="text-[10px] text-red-500 italic">... и ещё {spikePoints.length - 20}</div>
                            {/if}
                          </div>
                        </div>
                      {/if}
                    {/each}
                  {:else if analysisResult?.anomalies?.anomaly_indices}
                    <div class="max-h-32 overflow-y-auto space-y-0.5 mt-1">
                      {#each analysisResult.anomalies.anomaly_indices.map((idx, i) => ({idx, val: analysisResult.anomalies.anomaly_values[i], ts: analysisResult.anomalies.anomaly_timestamps?.[i], type: analysisResult.anomalies.anomaly_types?.[i]})).filter(p => p.type === 'spike').slice(0, 30) as p}
                        <div class="text-[10px] font-mono text-red-600 dark:text-red-400 flex justify-between gap-2">
                          <span class="text-neutral-500">{formatAnomalyDate(p.ts)}</span>
                          <span class="font-semibold">{p.val !== undefined && p.val !== null ? p.val.toFixed(2) : '—'}</span>
                        </div>
                      {/each}
                    </div>
                  {/if}
                </div>
              </details>

              <!-- Провалы -->
              <details class="border border-blue-200 dark:border-blue-800 rounded bg-blue-50 dark:bg-blue-900/10" open={expandedType === 'dip'}>
                <summary class="p-2 cursor-pointer hover:bg-blue-100 dark:hover:bg-blue-900/30 transition flex items-center justify-between" onclick={(e) => { e.preventDefault(); expandedType = expandedType === 'dip' ? null : 'dip'; }}>
                  <div class="flex items-center gap-2">
                    <ArrowDownCircle size={14} class="text-blue-500" />
                    <span class="text-sm font-semibold text-blue-700 dark:text-blue-300">Провалы (Dip)</span>
                    <span class="text-xs px-1.5 py-0.5 bg-blue-200 dark:bg-blue-900/40 text-blue-800 dark:text-blue-200 rounded">{tc.dip || 0}</span>
                  </div>
                  <span class="text-blue-500 transition-transform" class:rotate-180={expandedType === 'dip'}>
                      <ChevronDown size={14} />
                    </span>
                </summary>
                <div class="p-2 border-t border-blue-200 dark:border-blue-800">
                  <p class="text-[11px] text-blue-700 dark:text-blue-300 mb-2">
                    <strong>Провал (Dip)</strong> — резкое падение значения вниз, в том числе <strong>падение в ноль</strong>.
                    Типичные причины: отключение датчика, обрыв связи, кратковременный сбой оборудования, потеря питания.
                    Детектируется двумя способами: (1) падение в ноль (&lt;5% от среднего значения) — эвристика, 
                    (2) локальный z-score &lt; -1.5 (сильное отклонение вниз).
                  </p>
                  {#if analysisResult?.anomalies?.zero_dips_events && analysisResult.anomalies.zero_dips_events.length > 0}
                    <div class="mt-2 p-2 bg-blue-100 dark:bg-blue-900/30 rounded">
                      <div class="text-[10px] font-semibold text-blue-800 dark:text-blue-200 mb-1">
                        📉 Падения в ноль ({analysisResult.anomalies.zero_dips_events.length} событий):
                      </div>
                      <div class="max-h-32 overflow-y-auto space-y-0.5">
                        {#each analysisResult.anomalies.zero_dips_events.slice(0, 20) as event}
                          <div class="text-[10px] font-mono text-blue-700 dark:text-blue-300 flex justify-between">
                            <span>#{event.start_idx}–#{event.end_idx}</span>
                            <span>длит: {event.duration}</span>
                            <span class="font-semibold">min: {event.min_value.toFixed(2)}</span>
                          </div>
                        {/each}
                      </div>
                    </div>
                  {/if}
                  {#if analysisResult?.anomalies?.per_tag}
                    {#each Object.entries(analysisResult.anomalies.per_tag) as [tagName, tagData]}
                      {@const dipData = (tagData.anomaly_indices || []).map((idx, i) => ({idx, val: (tagData.anomaly_values || [])[i], ts: (tagData.anomaly_timestamps || [])[i], type: (tagData.anomaly_types || [])[i]})).filter(p => p.type === 'dip')}
                      {#if dipData.length > 0}
                        <div class="mt-2">
                          <div class="text-[10px] font-semibold text-blue-700 dark:text-blue-300 mb-1">{tagName} ({dipData.length}):</div>
                          <div class="max-h-32 overflow-y-auto space-y-0.5">
                            {#each dipData.slice(0, 20) as p}
                              <div class="text-[10px] font-mono text-blue-600 dark:text-blue-400 flex justify-between gap-2">
                                <span class="text-neutral-500">{formatAnomalyDate(p.ts)}</span>
                                <span class="font-semibold">{p.val !== undefined && p.val !== null ? p.val.toFixed(2) : '—'}</span>
                              </div>
                            {/each}
                            {#if dipData.length > 20}
                              <div class="text-[10px] text-blue-500 italic">... и ещё {dipData.length - 20}</div>
                            {/if}
                          </div>
                        </div>
                      {/if}
                    {/each}
                  {/if}
                </div>
              </details>

              <!-- Дрейфы -->
              <details class="border border-amber-200 dark:border-amber-800 rounded bg-amber-50 dark:bg-amber-900/10" open={expandedType === 'drift'}>
                <summary class="p-2 cursor-pointer hover:bg-amber-100 dark:hover:bg-amber-900/30 transition flex items-center justify-between" onclick={(e) => { e.preventDefault(); expandedType = expandedType === 'drift' ? null : 'drift'; }}>
                  <div class="flex items-center gap-2">
                    <Waves size={14} class="text-amber-500" />
                    <span class="text-sm font-semibold text-amber-700 dark:text-amber-300">Дрейфы (Drift)</span>
                    <span class="text-xs px-1.5 py-0.5 bg-amber-200 dark:bg-amber-900/40 text-amber-800 dark:text-amber-200 rounded">{tc.drift || 0}</span>
                  </div>
                  <span class="text-amber-500 transition-transform" class:rotate-180={expandedType === 'drift'}>
                      <ChevronDown size={14} />
                    </span>
                </summary>
                <div class="p-2 border-t border-amber-200 dark:border-amber-800">
                  <p class="text-[11px] text-amber-700 dark:text-amber-300 mb-2">
                    <strong>Дрейф (Drift)</strong> — постепенное монотонное смещение уровня сигнала от нормы.
                    В отличие от пика (резкий скачок), дрейф развивается во времени — значение медленно уходит вверх или вниз.
                    Типичные причины: старение датчика, засорение, калибровочный сдвиг, накопление отложений.
                    Математика: минимум 5 подряд идущих аномальных точек + монотонность (&gt;75% в одну сторону) + R² линейного тренда &gt; 0.6.
                  </p>
                  {#if analysisResult?.anomalies?.per_tag}
                    {#each Object.entries(analysisResult.anomalies.per_tag) as [tagName, tagData]}
                      {@const driftData = (tagData.anomaly_indices || []).map((idx, i) => ({idx, val: (tagData.anomaly_values || [])[i], ts: (tagData.anomaly_timestamps || [])[i], type: (tagData.anomaly_types || [])[i]})).filter(p => p.type === 'drift')}
                      {#if driftData.length > 0}
                        <div class="mt-2">
                          <div class="text-[10px] font-semibold text-amber-700 dark:text-amber-300 mb-1">{tagName} ({driftData.length}):</div>
                          <div class="max-h-32 overflow-y-auto space-y-0.5">
                            {#each driftData.slice(0, 20) as p}
                              <div class="text-[10px] font-mono text-amber-600 dark:text-amber-400 flex justify-between gap-2">
                                <span class="text-neutral-500">{formatAnomalyDate(p.ts)}</span>
                                <span class="font-semibold">{p.val !== undefined && p.val !== null ? p.val.toFixed(2) : '—'}</span>
                              </div>
                            {/each}
                            {#if driftData.length > 20}
                              <div class="text-[10px] text-amber-500 italic">... и ещё {driftData.length - 20}</div>
                            {/if}
                          </div>
                        </div>
                      {/if}
                    {/each}
                  {/if}
                </div>
              </details>

              <!-- Шум -->
              <details class="border border-neutral-200 dark:border-neutral-700 rounded bg-neutral-50 dark:bg-neutral-800/50" open={expandedType === 'noise'}>
                <summary class="p-2 cursor-pointer hover:bg-neutral-100 dark:hover:bg-neutral-800 transition flex items-center justify-between" onclick={(e) => { e.preventDefault(); expandedType = expandedType === 'noise' ? null : 'noise'; }}>
                  <div class="flex items-center gap-2">
                    <Zap size={14} class="text-neutral-500" />
                    <span class="text-sm font-semibold text-neutral-700 dark:text-neutral-300">Шум (Noise)</span>
                    <span class="text-xs px-1.5 py-0.5 bg-neutral-200 dark:bg-neutral-700 text-neutral-800 dark:text-neutral-200 rounded">{tc.noise || 0}</span>
                  </div>
                  <span class="text-neutral-500 transition-transform" class:rotate-180={expandedType === 'noise'}>
                      <ChevronDown size={14} />
                    </span>
                </summary>
                <div class="p-2 border-t border-neutral-200 dark:border-neutral-700">
                  <p class="text-[11px] text-neutral-700 dark:text-neutral-300 mb-2">
                    <strong>Шум (Noise)</strong> — быстрые хаотичные колебания значения без выраженного тренда.
                    В отличие от дрейфа (монотонный уход) или пика (одиночный выброс), шум — это беспорядочные 
                    колебания вокруг некоторого уровня. Типичные причины: электромагнитные помехи, плохой контакт,
                    вибрация, квантование АЦП, флуктуации процесса.
                    Математика: высокая производная (быстрые скачки) + низкий R² (нет линейного тренда).
                  </p>
                  {#if analysisResult?.anomalies?.per_tag}
                    {#each Object.entries(analysisResult.anomalies.per_tag) as [tagName, tagData]}
                      {@const noiseData = (tagData.anomaly_indices || []).map((idx, i) => ({idx, val: (tagData.anomaly_values || [])[i], ts: (tagData.anomaly_timestamps || [])[i], type: (tagData.anomaly_types || [])[i]})).filter(p => p.type === 'noise')}
                      {#if noiseData.length > 0}
                        <div class="mt-2">
                          <div class="text-[10px] font-semibold text-neutral-700 dark:text-neutral-300 mb-1">{tagName} ({noiseData.length}):</div>
                          <div class="max-h-32 overflow-y-auto space-y-0.5">
                            {#each noiseData.slice(0, 20) as p}
                              <div class="text-[10px] font-mono text-neutral-600 dark:text-neutral-400 flex justify-between gap-2">
                                <span class="text-neutral-500">{formatAnomalyDate(p.ts)}</span>
                                <span class="font-semibold">{p.val !== undefined && p.val !== null ? p.val.toFixed(2) : '—'}</span>
                              </div>
                            {/each}
                            {#if noiseData.length > 20}
                              <div class="text-[10px] text-neutral-500 italic">... и ещё {noiseData.length - 20}</div>
                            {/if}
                          </div>
                        </div>
                      {/if}
                    {/each}
                  {/if}
                </div>
              </details>
            </div>
          {/if}
        </div>
        {/if}
        

        <!-- Сезонный анализ (multi-tag) -->
        {#if analysisResult?.seasonality && Object.keys(analysisResult.seasonality).length > 0}
        <div class="mb-4">
          <h3 class="text-sm font-semibold mb-3 flex items-center gap-2">
            <Waves size={16} class="text-purple-500" />
            Сезонный анализ ({Object.keys(analysisResult.seasonality).length} тегов)
          </h3>
          
          {#each Object.entries(analysisResult.seasonality) as [tagName, tagSeasonality]}
            {#if tagSeasonality?.periods?.detected_periods?.length > 0}
            <div class="mb-4 p-3 bg-neutral-50 dark:bg-neutral-800 rounded border border-neutral-200 dark:border-neutral-700">
              <h4 class="text-sm font-medium mb-2 text-neutral-700 dark:text-neutral-300">{tagName}</h4>
              
              {#if tagSeasonality.periods.detected_periods.length > 0}
              <div class="mb-3">
                <div class="text-xs text-neutral-600 dark:text-neutral-400 mb-2">Обнаруженные периоды:</div>
                <div class="grid grid-cols-2 gap-2">
                  {#each tagSeasonality.periods.detected_periods.slice(0, 4) as period}
                    <div class="p-2 bg-purple-50 dark:bg-purple-900/20 rounded border border-purple-200 dark:border-purple-800">
                      <div class="text-xs text-neutral-600 dark:text-neutral-400">Период</div>
                      <div class="text-sm font-semibold text-purple-700 dark:text-purple-300">
                        {period.period} точек
                        <span class="text-xs text-neutral-500">({formatPeriod(period.period)})</span>
                      </div>
                      <div class="text-xs text-neutral-500 mt-1">
                        Уверенность: {(period.confidence * 100).toFixed(0)}%
                      </div>
                    </div>
                  {/each}
                </div>
              </div>
              {/if}

              {#if tagSeasonality.decomposition?.variance_explained}
              {@const ve = tagSeasonality.decomposition.variance_explained}
              <div class="mb-3">
                <div class="text-xs text-neutral-600 dark:text-neutral-400 mb-2">Распределение дисперсии:</div>
                <div class="space-y-1">
                  <div class="flex items-center gap-2">
                    <div class="w-20 text-xs text-neutral-600 dark:text-neutral-400">Тренд:</div>
                    <div class="flex-1 bg-neutral-200 dark:bg-neutral-700 rounded-full h-4 overflow-hidden">
                      <div class="bg-blue-500 h-full" style="width: {ve.trend}%"></div>
                    </div>
                    <div class="w-12 text-xs text-right font-mono">{ve.trend.toFixed(1)}%</div>
                  </div>
                  <div class="flex items-center gap-2">
                    <div class="w-20 text-xs text-neutral-600 dark:text-neutral-400">Сезонность:</div>
                    <div class="flex-1 bg-neutral-200 dark:bg-neutral-700 rounded-full h-4 overflow-hidden">
                      <div class="bg-purple-500 h-full" style="width: {ve.seasonal}%"></div>
                    </div>
                    <div class="w-12 text-xs text-right font-mono">{ve.seasonal.toFixed(1)}%</div>
                  </div>
                  <div class="flex items-center gap-2">
                    <div class="w-20 text-xs text-neutral-600 dark:text-neutral-400">Остаток:</div>
                    <div class="flex-1 bg-neutral-200 dark:bg-neutral-700 rounded-full h-4 overflow-hidden">
                      <div class="bg-neutral-500 h-full" style="width: {ve.residual}%"></div>
                    </div>
                    <div class="w-12 text-xs text-right font-mono">{ve.residual.toFixed(1)}%</div>
                  </div>
                </div>
              </div>
                            {/if}

              {#if tagSeasonality.pattern?.pattern?.length > 0}
              {@const pattern = tagSeasonality.pattern.pattern}
              {@const stats = getPatternStats(pattern)}
              {@const patternData = {
                labels: pattern.map((_: any, i: number) => i),
                datasets: [{
                  label: tagName,
                  data: pattern,
                  borderColor: 'rgb(168, 85, 247)',
                  backgroundColor: 'rgba(168, 85, 247, 0.1)',
                  borderWidth: 2,
                  pointRadius: pattern.length > 100 ? 0 : 2,
                  pointHoverRadius: 5,
                  tension: 0.2,
                  fill: true,
                }]
              }}
              <div class="mb-3">
                <div class="flex items-center justify-between mb-2">
                  <div class="text-xs text-neutral-600 dark:text-neutral-400">
                    Типичный паттерн (период {tagSeasonality.periods.detected_periods[0].period} точек, {formatPeriod(tagSeasonality.periods.detected_periods[0].period)})
                  </div>
                  <div class="flex items-center gap-1">
                    <button type="button" onclick={() => zoomInPattern(tagName)} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Приблизить"><ZoomIn size={14} class="text-neutral-600 dark:text-neutral-400" /></button>
                    <button type="button" onclick={() => zoomOutPattern(tagName)} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Отдалить"><ZoomOut size={14} class="text-neutral-600 dark:text-neutral-400" /></button>
                    <button type="button" onclick={() => resetZoomPattern(tagName)} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Сбросить"><RotateCcw size={14} class="text-neutral-600 dark:text-neutral-400" /></button>
                    <button type="button" onclick={() => downloadPNG(patternChartInstances[tagName], `pattern_${tagName}`)} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Скачать PNG"><Download size={14} class="text-neutral-600 dark:text-neutral-400" /></button>
                    <button type="button" onclick={() => openPatternModal(pattern, `Паттерн: ${tagName}`)} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Полноэкранный режим"><Maximize2 size={14} class="text-neutral-600 dark:text-neutral-400" /></button>
                  </div>
                </div>
                <div class="text-xs text-neutral-600 dark:text-neutral-400 mb-2">
                  Мин: {stats.min.toFixed(1)} | Макс: {stats.max.toFixed(1)} | Размах: {stats.range.toFixed(1)}
                </div>
                <div id={`pattern-chart-${tagName}`} class="h-40 bg-white dark:bg-neutral-800 rounded border border-neutral-200 dark:border-neutral-700 p-3">
                  <Line data={patternData} options={{...timeSeriesOptions, plugins: {...timeSeriesOptions.plugins, legend: {display: false}}}} key={`pattern-multi-${tagName}`} />
                </div>
              </div>
              {/if}
            </div>
            {/if}
          {/each}
        </div>
        {/if}

        <!-- 1. Матрица корреляций (кликабельная!) -->
        <div class="mb-4">
          <h3 class="text-sm font-semibold mb-2 flex items-center gap-2">
            <Grid3x3 size={16} />
            Матрица корреляций ({correlationMatrix?.tags?.length || 0} тегов)
            <span class="text-xs font-normal text-neutral-500 dark:text-neutral-400">
              — кликните на ячейку для scatter plot
            </span>
          </h3>
          
          {#if correlationMatrix?.matrix}
            <div class="overflow-auto border border-neutral-200 dark:border-neutral-700 rounded">
              <table class="text-xs w-full">
                <thead>
                  <tr>
                    <th class="p-2 bg-neutral-100 dark:bg-neutral-800 border-b border-r border-neutral-200 dark:border-neutral-700 sticky left-0 z-10 min-w-[180px]"></th>
                    {#each correlationMatrix.tags as tag}
                      <th 
                        class="p-2 bg-neutral-100 dark:bg-neutral-800 border-b border-r border-neutral-200 dark:border-neutral-700 text-center min-w-[100px]" 
                        title={tag}
                      >
                        <div class="font-medium text-[11px]">{shortenTagName(tag)}</div>
                      </th>
                    {/each}
                  </tr>
                </thead>
                <tbody>
                  {#each correlationMatrix.tags as tag1, i}
                    <tr>
                      <td class="p-2 bg-neutral-100 dark:bg-neutral-800 border-b border-r border-neutral-200 dark:border-neutral-700 font-medium sticky left-0 z-10" title={tag1}>
                        <div class="text-[11px]">{shortenTagName(tag1)}</div>
                      </td>
                      {#each correlationMatrix.tags as tag2, j}
                        {@const value = correlationMatrix.matrix[i][j]}
                        {@const isSelected = isPairSelected(tag1, tag2)}
                        <td 
                          class="p-2 text-center border-b border-r border-neutral-200 dark:border-neutral-700 transition font-mono {tag1 === tag2 ? 'cursor-default' : 'cursor-pointer hover:ring-2 hover:ring-blue-500'} {isSelected ? 'ring-2 ring-blue-600 ring-offset-1 dark:ring-offset-neutral-900' : ''}"
                          style="background-color: {corrColor(value)}; color: {Math.abs(value) > 0.5 ? 'white' : 'inherit'}"
                          title="{tag1} ↔ {tag2}: r = {formatNumber(value, 3)}{tag1 === tag2 ? '' : ' (клик для scatter plot)'}"
                          onclick={() => tag1 !== tag2 && selectPair(tag1, tag2)}
                        >
                          {formatNumber(value, 2)}
                        </td>
                      {/each}
                    </tr>
                  {/each}
                </tbody>
              </table>
            </div>
            
            <div class="text-[10px] text-neutral-500 dark:text-neutral-400 mt-1 flex items-center gap-3 flex-wrap">
              <span class="flex items-center gap-1">
                <Circle size={10} class="fill-blue-500 text-blue-500" />
                положительная
              </span>
              <span class="flex items-center gap-1">
                <Circle size={10} class="fill-red-500 text-red-500" />
                отрицательная
              </span>
              <span>•</span>
              <span class="flex items-center gap-1">
                <div class="w-2.5 h-2.5 border-2 border-blue-600 dark:border-blue-400"></div>
                выбранная пара
              </span>
              <span>•</span>
              <span>Кликните на ячейку для scatter plot</span>
            </div>
          {/if}
        </div>

        <!-- 2. Scatter plot (интерактивный) -->
        <div class="mb-4">
          <div class="flex items-center justify-between mb-2">
            <h3 class="text-sm font-semibold flex items-center gap-2">
              <ArrowRightLeft size={16} />
              Scatter plot
              {#if pairAnalysis}
                <span class="text-xs font-normal text-neutral-500 dark:text-neutral-400">
                  ({pairAnalysis.tag1} × {pairAnalysis.tag2})
                </span>
              {/if}
            </h3>
            <div class="flex items-center gap-1">
              {#if !isLoadingPair}
                <button type="button" onclick={zoomInScatter} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Приблизить"><ZoomIn size={14} class="text-neutral-600 dark:text-neutral-400" /></button>
                <button type="button" onclick={zoomOutScatter} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Отдалить"><ZoomOut size={14} class="text-neutral-600 dark:text-neutral-400" /></button>
                <button type="button" onclick={resetZoomScatter} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Сбросить"><RotateCcw size={14} class="text-neutral-600 dark:text-neutral-400" /></button>
                <button type="button" onclick={() => downloadPNG(scatterChartInstance, 'scatter')} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Скачать PNG"><Download size={14} class="text-neutral-600 dark:text-neutral-400" /></button>
              {/if}
            </div>
          </div>
          
          <div id={scatterChartId} class="h-[400px] bg-white dark:bg-neutral-800 rounded border border-neutral-200 dark:border-neutral-700 p-3 relative">
            {#if isLoadingPair}
              <div class="absolute inset-0 flex items-center justify-center bg-white/80 dark:bg-neutral-800/80 rounded z-10">
                <div class="flex flex-col items-center gap-2">
                  <Loader2 size={32} class="animate-spin text-blue-500" />
                  <span class="text-sm text-neutral-600 dark:text-neutral-400">Загружаем пару...</span>
                </div>
              </div>
            {/if}
            
            {#if pairError}
              <div class="flex items-center justify-center h-full text-sm text-red-600 dark:text-red-400">
                {pairError}
              </div>
            {:else if downsampledScatterData.datasets.length > 0}
              <Line data={downsampledScatterData} options={scatterOptions} key={`${pairAnalysis?.tag1}_${pairAnalysis?.tag2}`} />
            {:else}
              <div class="flex items-center justify-center h-full text-sm text-neutral-400">
                Выберите пару тегов в матрице выше
              </div>
            {/if}
          </div>
          
          {#if pairAnalysis}
            <div class="mt-3 grid grid-cols-4 gap-2">
              <div class="p-2 bg-neutral-50 dark:bg-neutral-800 rounded">
                <div class="text-[10px] text-neutral-500 dark:text-neutral-400 mb-1">Pearson</div>
                <div class="text-xs font-semibold">{pairAnalysis.pearson.interpretation}</div>
              </div>
              <div class="p-2 bg-neutral-50 dark:bg-neutral-800 rounded">
                <div class="text-[10px] text-neutral-500 dark:text-neutral-400 mb-1">Spearman</div>
                <div class="text-xs font-semibold">{pairAnalysis.spearman.interpretation}</div>
              </div>
              <div class="p-2 bg-neutral-50 dark:bg-neutral-800 rounded">
                <div class="text-[10px] text-neutral-500 dark:text-neutral-400 mb-1">Mutual Info</div>
                <div class="text-xs font-semibold">{pairAnalysis.mutual_info.interpretation}</div>
              </div>
              <div class="p-2 bg-neutral-50 dark:bg-neutral-800 rounded">
                <div class="text-[10px] text-neutral-500 dark:text-neutral-400 mb-1">Cross-corr lag</div>
                <div class="text-xs font-semibold">{pairAnalysis.cross_correlation.interpretation}</div>
              </div>
            </div>
          {/if}
        </div>
      {/if}

      <!-- ==================== MULTI-TAG: TABLE ==================== -->
      {#if isMultiTag && activeTab === 'table'}
        <div>
          <div class="flex items-center justify-between mb-2">
            <h3 class="text-sm font-semibold">
              Все пары (сортировано по силе корреляции)
            </h3>
            <span class="text-xs text-neutral-500 dark:text-neutral-400">
              Кликните на строку → scatter plot
            </span>
          </div>
          <div class="border border-neutral-200 dark:border-neutral-700 rounded overflow-hidden">
            <table class="text-xs w-full">
              <thead>
                <tr class="bg-neutral-100 dark:bg-neutral-800">
                  <th class="p-2 text-left font-medium w-10">#</th>
                  <th class="p-2 text-left font-medium">Тег 1</th>
                  <th class="p-2 text-left font-medium">Тег 2</th>
                  <th class="p-2 text-right font-medium w-24">Коэф. r</th>
                  <th class="p-2 text-right font-medium w-24">p-value</th>
                  <th class="p-2 text-center font-medium w-24">Значимость</th>
                </tr>
              </thead>
              <tbody>
                {#each correlationPairs as pair, i}
                  {@const badge = significanceBadge(pair.p_value)}
                  {@const isSelected = isPairSelected(pair.tag1, pair.tag2)}
                  <tr 
                    class="border-t border-neutral-200 dark:border-neutral-700 cursor-pointer transition {isSelected ? 'bg-blue-50 dark:bg-blue-900/20' : 'hover:bg-neutral-50 dark:hover:bg-neutral-800/50'}"
                    onclick={() => { selectPair(pair.tag1, pair.tag2); activeTab = 'correlations'; }}
                  >
                    <td class="p-2 text-neutral-500">{i + 1}</td>
                    <td class="p-2 font-mono text-[11px] truncate max-w-[200px]" title={pair.tag1}>{pair.tag1}</td>
                    <td class="p-2 font-mono text-[11px] truncate max-w-[200px]" title={pair.tag2}>{pair.tag2}</td>
                    <td class="p-2 text-right font-semibold" style="color: {corrColor(pair.coef).replace('0.15', '0.9')}">
                      {pair.coef > 0 ? '+' : ''}{formatNumber(pair.coef, 3)}
                    </td>
                    <td class="p-2 text-right text-neutral-500 dark:text-neutral-400 font-mono text-[11px]">
                      {pair.p_value < 0.001 ? '<0.001' : formatNumber(pair.p_value, 4)}
                    </td>
                    <td class="p-2 text-center" title={badge.title}>
                      {#if badge.color === 'green'}
                        <span class="px-1.5 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded text-[10px] font-medium">{badge.label}</span>
                      {:else if badge.color === 'yellow'}
                        <span class="px-1.5 py-0.5 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300 rounded text-[10px] font-medium">{badge.label}</span>
                      {:else}
                        <span class="px-1.5 py-0.5 bg-neutral-100 dark:bg-neutral-800 text-neutral-500 rounded text-[10px] font-medium">{badge.label}</span>
                      {/if}
                    </td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>

          <!-- Подробные пояснения -->
          <div class="mt-6 space-y-4">
            <div class="p-4 bg-neutral-50 dark:bg-neutral-800 rounded border border-neutral-200 dark:border-neutral-700">
              <h4 class="text-sm font-semibold mb-2 flex items-center gap-2">
                <Info size={14} class="text-blue-500" />
                Коэффициент корреляции Пирсона (r)
              </h4>
              <p class="text-xs text-neutral-700 dark:text-neutral-300 mb-2">
                Показывает <strong>силу и направление линейной связи</strong> между двумя тегами.
              </p>
              <div class="grid grid-cols-2 gap-3 text-xs text-neutral-700 dark:text-neutral-300">
                <div>
                  <div class="font-medium mb-1">Направление:</div>
                  <ul class="space-y-1 ml-3 list-disc">
                    <li><span class="font-semibold text-blue-600 dark:text-blue-400">r &gt; 0</span> — положительная связь (растёт X → растёт Y)</li>
                    <li><span class="font-semibold text-red-600 dark:text-red-400">r &lt; 0</span> — отрицательная (растёт X → падает Y)</li>
                    <li><span class="font-semibold">r ≈ 0</span> — линейной связи нет</li>
                  </ul>
                </div>
                <div>
                  <div class="font-medium mb-1">Сила связи:</div>
                  <ul class="space-y-1 ml-3 list-disc">
                    <li><span class="font-semibold">|r| ≥ 0.7</span> — сильная</li>
                    <li><span class="font-semibold">0.5 ≤ |r| &lt; 0.7</span> — умеренная</li>
                    <li><span class="font-semibold">0.3 ≤ |r| &lt; 0.5</span> — слабая</li>
                    <li><span class="font-semibold">|r| &lt; 0.3</span> — очень слабая</li>
                  </ul>
                </div>
              </div>
            </div>

            <div class="p-4 bg-neutral-50 dark:bg-neutral-800 rounded border border-neutral-200 dark:border-neutral-700">
              <h4 class="text-sm font-semibold mb-2 flex items-center gap-2">
                <Info size={14} class="text-blue-500" />
                p-value (уровень значимости)
              </h4>
              <p class="text-xs text-neutral-700 dark:text-neutral-300 mb-2">
                Показывает <strong>вероятность получить такую корреляцию случайно</strong>, если на самом деле связи между тегами нет.
              </p>
              <div class="text-xs text-neutral-700 dark:text-neutral-300">
                <div class="font-medium mb-1">Интерпретация:</div>
                <ul class="space-y-1 ml-3 list-disc">
                  <li><span class="font-semibold">p &lt; 0.001</span> — высоко значимая (&lt; 0.1%)</li>
                  <li><span class="font-semibold">p &lt; 0.01</span> — значимая (&lt; 1%)</li>
                  <li><span class="font-semibold">p &lt; 0.05</span> — слабо значимая (&lt; 5%)</li>
                  <li><span class="font-semibold">p ≥ 0.05</span> — не значимая (нельзя доверять)</li>
                </ul>
              </div>
            </div>

            <div class="p-4 bg-neutral-50 dark:bg-neutral-800 rounded border border-neutral-200 dark:border-neutral-700">
              <h4 class="text-sm font-semibold mb-2 flex items-center gap-2">
                <Info size={14} class="text-blue-500" />
                Значимость (звёзды в таблице)
              </h4>
              <div class="grid grid-cols-2 gap-2 text-xs mb-3">
                <div class="flex items-center gap-2 p-2 bg-white dark:bg-neutral-900 rounded">
                  <span class="px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded font-medium">***</span>
                  <span class="text-neutral-700 dark:text-neutral-300">Высоко значимая (p &lt; 0.001)</span>
                </div>
                <div class="flex items-center gap-2 p-2 bg-white dark:bg-neutral-900 rounded">
                  <span class="px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded font-medium">**</span>
                  <span class="text-neutral-700 dark:text-neutral-300">Значимая (p &lt; 0.01)</span>
                </div>
                <div class="flex items-center gap-2 p-2 bg-white dark:bg-neutral-900 rounded">
                  <span class="px-2 py-1 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300 rounded font-medium">*</span>
                  <span class="text-neutral-700 dark:text-neutral-300">Слабо значимая (p &lt; 0.05)</span>
                </div>
                <div class="flex items-center gap-2 p-2 bg-white dark:bg-neutral-900 rounded">
                  <span class="px-2 py-1 bg-neutral-100 dark:bg-neutral-800 text-neutral-500 rounded font-medium">ns</span>
                  <span class="text-neutral-700 dark:text-neutral-300">Не значимая (p ≥ 0.05)</span>
                </div>
              </div>
              <p class="text-[11px] text-neutral-500 dark:text-neutral-400">
                💡 Доверять стоит только значимым корреляциям. Пары с <code class="px-1 bg-neutral-200 dark:bg-neutral-700 rounded">ns</code> статистически не отличаются от случайного шума.
              </p>
            </div>
          </div>
        </div>
      {/if}
    </div>
      {#if visitedTabs.interpretation}
        <div class:hidden={activeTab !== 'interpretation'}>
          <DDAInterpretation {analysisResult} />
        </div>
      {/if}
  {:else}
    <div class="flex-1 flex items-center justify-center">
      <div class="flex flex-col items-center text-center text-neutral-400 dark:text-neutral-500">
        <Activity size={48} class="mb-3 opacity-50" />
        <p class="text-sm mb-1">Выберите теги и запустите анализ</p>
        <p class="text-xs">1 тег = статистика · 2+ тега = корреляции</p>
      </div>
    </div>
  {/if}
</div>

<ChartModal
  isOpen={modalOpen}
  title={modalTitle}
  chartType={modalChartType}
  chartData={modalData}
  chartOptions={modalOptions}
  onClose={closeChartModal}
/>
