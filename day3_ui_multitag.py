#!/usr/bin/env python3
"""
day3_ui_multitag.py — UI для мульти-тег анализа (heatmap + scatter + checkboxes)
"""

from pathlib import Path

print('=' * 70)
print('DAY 3: UI ДЛЯ МУЛЬТИ-ТЕГ АНАЛИЗА')
print('=' * 70)
print()

# ============================================================================
# 1. Обновляем DeepAnalysisControls — checkboxes для выбора нескольких тегов
# ============================================================================
controls_path = Path('frontend/src/components/DeepAnalysisControls.svelte')

new_controls = '''<script lang="ts">
  import { Play, Activity, X, Search, CheckSquare, Square } from 'lucide-svelte'

  interface Props {
    tags: any[]
    selectedTags: string[]
    period: number
    isAnalyzing: boolean
    error: string | null
    onTagsChange: (tags: string[]) => void
    onPeriodChange: (period: number) => void
    onRunAnalysis: () => void
    onClose: () => void
  }

  let { 
    tags, 
    selectedTags, 
    period, 
    isAnalyzing, 
    error,
    onTagsChange, 
    onPeriodChange, 
    onRunAnalysis,
    onClose
  }: Props = $props()

  let searchQuery = $state('')

  // Фильтруем теги по поиску
  let filteredTags = $derived(
    tags.filter(tag => 
      tag.tag_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (tag.zone_name || '').toLowerCase().includes(searchQuery.toLowerCase())
    )
  )

  function toggleTag(tagName: string) {
    const newSelection = selectedTags.includes(tagName)
      ? selectedTags.filter(t => t !== tagName)
      : [...selectedTags, tagName]
    onTagsChange(newSelection)
  }

  function selectAll() {
    onTagsChange(filteredTags.map(t => t.tag_name))
  }

  function clearAll() {
    onTagsChange([])
  }
</script>

<div class="w-[350px] h-full bg-white dark:bg-neutral-900 border-r border-neutral-200 dark:border-neutral-700 flex flex-col overflow-hidden transition-colors">
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

  <div class="flex-1 overflow-y-auto px-4 py-3 space-y-3">
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

    <!-- Tags selector with search -->
    <div>
      <label class="block text-xs font-medium text-neutral-600 dark:text-neutral-400 mb-1">
        Теги (выбрано: {selectedTags.length})
      </label>
      
      <!-- Search input -->
      <div class="relative mb-2">
        <Search size={14} class="absolute left-2 top-1/2 -translate-y-1/2 text-neutral-400" />
        <input
          type="text"
          placeholder="Поиск тегов..."
          bind:value={searchQuery}
          class="w-full pl-7 pr-3 py-1.5 text-sm border border-neutral-300 dark:border-neutral-600 rounded bg-white dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <!-- Select all / Clear -->
      <div class="flex gap-2 mb-2">
        <button
          type="button"
          onclick={selectAll}
          class="flex-1 px-2 py-1 text-xs bg-neutral-100 dark:bg-neutral-800 hover:bg-neutral-200 dark:hover:bg-neutral-700 text-neutral-700 dark:text-neutral-300 rounded transition flex items-center justify-center gap-1"
        >
          <CheckSquare size={12} />
          Выбрать все
        </button>
        <button
          type="button"
          onclick={clearAll}
          class="flex-1 px-2 py-1 text-xs bg-neutral-100 dark:bg-neutral-800 hover:bg-neutral-200 dark:hover:bg-neutral-700 text-neutral-700 dark:text-neutral-300 rounded transition flex items-center justify-center gap-1"
        >
          <Square size={12} />
          Очистить
        </button>
      </div>

      <!-- Tags list -->
      <div class="max-h-60 overflow-y-auto border border-neutral-200 dark:border-neutral-700 rounded">
        {#each filteredTags as tag}
          <button
            type="button"
            onclick={() => toggleTag(tag.tag_name)}
            class="w-full px-2 py-1.5 text-xs text-left hover:bg-neutral-100 dark:hover:bg-neutral-800 transition flex items-center gap-2 border-b border-neutral-100 dark:border-neutral-800 last:border-0 {selectedTags.includes(tag.tag_name) ? 'bg-blue-50 dark:bg-blue-900/20' : ''}"
          >
            {#if selectedTags.includes(tag.tag_name)}
              <CheckSquare size={14} class="text-blue-500 flex-shrink-0" />
            {:else}
              <Square size={14} class="text-neutral-400 flex-shrink-0" />
            {/if}
            <div class="flex-1 min-w-0">
              <div class="truncate text-neutral-900 dark:text-neutral-100">{tag.tag_name}</div>
              {#if tag.zone_name}
                <div class="text-[10px] text-neutral-500 dark:text-neutral-400 truncate">{tag.zone_name}</div>
              {/if}
            </div>
          </button>
        {/each}
        
        {#if filteredTags.length === 0}
          <div class="px-2 py-4 text-xs text-center text-neutral-400">
            Теги не найдены
          </div>
        {/if}
      </div>

      <div class="text-[10px] text-neutral-500 dark:text-neutral-400 mt-1">
        1 тег = статистика + аномалии · 2+ тега = корреляции
      </div>
    </div>

    <!-- Run button -->
    <button
      type="button"
      onclick={onRunAnalysis}
      disabled={isAnalyzing || selectedTags.length === 0}
      class="w-full px-4 py-2 bg-blue-500 hover:bg-blue-600 disabled:bg-neutral-300 dark:disabled:bg-neutral-700 text-white text-sm font-medium rounded transition flex items-center justify-center gap-2"
    >
      {#if isAnalyzing}
        <div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
        Анализ...
      {:else}
        <Play size={14} />
        Запустить анализ ({selectedTags.length} {selectedTags.length === 1 ? 'тег' : 'тегов'})
      {/if}
    </button>

    {#if error}
      <div class="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded text-sm text-red-700 dark:text-red-300">
        {error}
      </div>
    {/if}
  </div>
</div>
'''

controls_path.write_text(new_controls, encoding='utf-8', newline='\n')
print('✓ DeepAnalysisControls.svelte обновлён (checkboxes + search)')

# ============================================================================
# 2. Обновляем DeepAnalysisResults — вкладки для single/multi mode
# ============================================================================
results_path = Path('frontend/src/components/DeepAnalysisResults.svelte')

new_results = '''<script lang="ts">
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
    BubbleController,
  } from 'chart.js'
  import zoomPlugin from 'chartjs-plugin-zoom'
  import { 
    TrendingUp, AlertTriangle, Activity, Download, RotateCcw, 
    ZoomIn, ZoomOut, Grid3x3, ArrowRightLeft, Table
  } from 'lucide-svelte'

  ChartJS.register(
    CategoryScale, LinearScale, PointElement, LineElement,
    Title, Tooltip, Legend, ScatterController, BubbleController, zoomPlugin
  )

  interface Props {
    analysisResult: any
    isAnalyzing: boolean
  }

  let { analysisResult, isAnalyzing }: Props = $props()

  // Определяем режим: single-tag или multi-tag
  let isMultiTag = $derived(
    analysisResult?.tags?.length > 1 && 
    analysisResult?.correlations !== null &&
    analysisResult?.correlations !== undefined
  )

  // Активная вкладка
  let activeTab = $state<'overview' | 'correlations' | 'table'>('overview')
  $effect(() => {
    // Если multi-tag — по умолчанию переключаемся на correlations
    if (isMultiTag) {
      activeTab = 'correlations'
    } else {
      activeTab = 'overview'
    }
  })

  // Chart instance и id
  let chartInstance: ChartJS | null = $state(null)
  const chartId = `dda-chart-${Math.random().toString(36).slice(2, 9)}`

  // Chart.js данные для time series (single mode)
  let timeSeriesData = $derived(
    analysisResult?.visualizations?.time_series?.data || { labels: [], datasets: [] }
  )

  // Scatter plot данные (multi mode)
  let scatterData = $derived(
    analysisResult?.visualizations?.scatter?.data || { datasets: [] }
  )

  // Heatmap данные
  let correlationMatrix = $derived(analysisResult?.correlations)

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
      x: { display: true, grid: { display: false }, ticks: { maxTicksLimit: 10, font: { size: 10 } } },
      y: { display: true, grid: { color: 'rgba(0, 0, 0, 0.05)' }, ticks: { font: { size: 10 } } }
    },
    interaction: { mode: 'nearest' as const, axis: 'x' as const, intersect: false }
  }

  const scatterOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: true, position: 'top' as const },
      tooltip: { mode: 'nearest' as const, intersect: true }
    },
    scales: {
      x: { type: 'linear' as const, title: { display: true, text: '' } },
      y: { type: 'linear' as const, title: { display: true, text: '' } }
    }
  }

  $effect(() => {
    if (timeSeriesData.labels.length > 0 || scatterData.datasets.length > 0) {
      setTimeout(() => {
        const container = document.getElementById(chartId)
        if (container) {
          const canvas = container.querySelector('canvas')
          if (canvas) chartInstance = ChartJS.getChart(canvas) || null
        }
      }, 200)
    }
  })

  function resetZoom() { chartInstance?.resetZoom() }
  function zoomIn() { chartInstance?.zoom(1.2) }
  function zoomOut() { chartInstance?.zoom(0.8) }
  
  function downloadPNG() {
    if (!chartInstance) return
    const canvas = chartInstance.canvas
    const link = document.createElement('a')
    const tagNames = analysisResult?.tags?.join('_') || 'analysis'
    const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-')
    link.download = `scada_ai_${activeTab}_${tagNames}_${timestamp}.png`
    link.href = canvas.toDataURL('image/png', 1.0)
    link.click()
  }

  function formatNumber(value: number, decimals: number = 2): string {
    return value.toFixed(decimals)
  }

  // Цвет для корреляции (red → white → blue)
  function corrColor(value: number): string {
    if (value >= 0) {
      const intensity = Math.min(Math.abs(value), 1)
      return `rgba(59, 130, 246, ${0.2 + intensity * 0.7})`
    } else {
      const intensity = Math.min(Math.abs(value), 1)
      return `rgba(239, 68, 68, ${0.2 + intensity * 0.7})`
    }
  }

  // Пары корреляций для таблицы (сортированные по силе)
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
    <div class="flex border-b border-neutral-200 dark:border-neutral-700 px-6 pt-3 flex-shrink-0">
      {#if !isMultiTag}
        <button
          type="button"
          onclick={() => activeTab = 'overview'}
          class="px-4 py-2 text-sm font-medium border-b-2 transition {activeTab === 'overview' ? 'border-blue-500 text-blue-600 dark:text-blue-400' : 'border-transparent text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-200'}"
        >
          <div class="flex items-center gap-1.5">
            <TrendingUp size={14} />
            Обзор
          </div>
        </button>
      {/if}
      {#if isMultiTag}
        <button
          type="button"
          onclick={() => activeTab = 'correlations'}
          class="px-4 py-2 text-sm font-medium border-b-2 transition {activeTab === 'correlations' ? 'border-blue-500 text-blue-600 dark:text-blue-400' : 'border-transparent text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-200'}"
        >
          <div class="flex items-center gap-1.5">
            <Grid3x3 size={14} />
            Корреляции
          </div>
        </button>
        <button
          type="button"
          onclick={() => activeTab = 'table'}
          class="px-4 py-2 text-sm font-medium border-b-2 transition {activeTab === 'table' ? 'border-blue-500 text-blue-600 dark:text-blue-400' : 'border-transparent text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-200'}"
        >
          <div class="flex items-center gap-1.5">
            <Table size={14} />
            Таблица пар
          </div>
        </button>
      {/if}
    </div>

    <!-- Content -->
    <div class="flex-1 overflow-y-auto px-6 py-4">
      <!-- Summary -->
      <div class="mb-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded">
        <p class="text-sm text-blue-900 dark:text-blue-100">{analysisResult.summary}</p>
      </div>

      <!-- SINGLE TAG MODE: Обзор -->
      {#if !isMultiTag && activeTab === 'overview'}
        <!-- Statistics -->
        {#if analysisResult?.statistics && analysisResult.statistics.count > 0}
        <div class="mb-4">
          <h3 class="text-sm font-semibold text-neutral-900 dark:text-neutral-100 mb-2 flex items-center gap-2">
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

        <!-- Anomalies -->
        {#if analysisResult?.anomalies?.total_anomalies > 0}
          <div class="mb-4">
            <h3 class="text-sm font-semibold text-neutral-900 dark:text-neutral-100 mb-2 flex items-center gap-2">
              <AlertTriangle size={16} class="text-red-500" />
              Аномалии ({analysisResult.anomalies.total_anomalies})
            </h3>
            <div class="text-xs text-neutral-600 dark:text-neutral-400 mb-2">
              Обнаружено {analysisResult.anomalies.total_anomalies} аномальных точек
              ({(analysisResult.anomalies.anomaly_rate * 100).toFixed(1)}% от общего числа)
            </div>
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

        <!-- Chart (time series) -->
        <div class="mb-4">
          <div class="flex items-center justify-between mb-2">
            <h3 class="text-sm font-semibold">График</h3>
            <div class="flex items-center gap-1">
              <button type="button" onclick={zoomIn} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Приблизить">
                <ZoomIn size={14} class="text-neutral-600 dark:text-neutral-400" />
              </button>
              <button type="button" onclick={zoomOut} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Отдалить">
                <ZoomOut size={14} class="text-neutral-600 dark:text-neutral-400" />
              </button>
              <button type="button" onclick={resetZoom} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Сбросить масштаб">
                <RotateCcw size={14} class="text-neutral-600 dark:text-neutral-400" />
              </button>
              <button type="button" onclick={downloadPNG} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Скачать PNG">
                <Download size={14} class="text-neutral-600 dark:text-neutral-400" />
              </button>
            </div>
          </div>
          <div class="text-xs text-neutral-500 dark:text-neutral-400 mb-2">
            💡 Колёсико — zoom · Shift+drag — область · Drag — прокрутка
          </div>
          <div id={chartId} class="h-[300px] bg-white dark:bg-neutral-800 rounded border border-neutral-200 dark:border-neutral-700 p-3">
            {#if timeSeriesData.labels.length > 0}
              <Line data={timeSeriesData} options={timeSeriesOptions} key={analysisResult?.analysis_id || 'default'} />
            {:else}
              <div class="flex items-center justify-center h-full text-sm text-neutral-400">Нет данных</div>
            {/if}
          </div>
        </div>
      {/if}

      <!-- MULTI-TAG MODE: Корреляции (heatmap + scatter) -->
      {#if isMultiTag && activeTab === 'correlations'}
        <div class="grid grid-cols-2 gap-4">
          <!-- Heatmap -->
          <div>
            <h3 class="text-sm font-semibold mb-2 flex items-center gap-2">
              <Grid3x3 size={16} />
              Матрица корреляций ({correlationMatrix?.tags?.length || 0} тегов)
            </h3>
            
            {#if correlationMatrix?.matrix}
              <!-- Custom heatmap as table -->
              <div class="overflow-auto border border-neutral-200 dark:border-neutral-700 rounded">
                <table class="text-xs w-full">
                  <thead>
                    <tr>
                      <th class="p-1 bg-neutral-100 dark:bg-neutral-800 border-b border-r border-neutral-200 dark:border-neutral-700 sticky left-0 z-10"></th>
                      {#each correlationMatrix.tags as tag}
                        <th class="p-1 bg-neutral-100 dark:bg-neutral-800 border-b border-r border-neutral-200 dark:border-neutral-700 text-center" title={tag}>
                          <div class="truncate max-w-[80px]">{tag.split('-').pop()}</div>
                        </th>
                      {/each}
                    </tr>
                  </thead>
                  <tbody>
                    {#each correlationMatrix.tags as tag1, i}
                      <tr>
                        <td class="p-1 bg-neutral-100 dark:bg-neutral-800 border-b border-r border-neutral-200 dark:border-neutral-700 font-medium sticky left-0 z-10" title={tag1}>
                          <div class="truncate max-w-[80px]">{tag1.split('-').pop()}</div>
                        </td>
                        {#each correlationMatrix.tags as tag2, j}
                          {@const value = correlationMatrix.matrix[i][j]}
                          <td 
                            class="p-1 text-center border-b border-r border-neutral-200 dark:border-neutral-700 cursor-pointer hover:ring-2 hover:ring-blue-500 transition"
                            style="background-color: {corrColor(value)}; color: {Math.abs(value) > 0.5 ? 'white' : 'inherit'}"
                            title="{tag1} ↔ {tag2}: {formatNumber(value)}"
                          >
                            {formatNumber(value, 2)}
                          </td>
                        {/each}
                      </tr>
                    {/each}
                  </tbody>
                </table>
              </div>
              
              <div class="text-[10px] text-neutral-500 dark:text-neutral-400 mt-1">
                🔵 положительная · 🔴 отрицательная · Наведите курсор для деталей
              </div>
            {:else}
              <div class="h-60 flex items-center justify-center border border-neutral-200 dark:border-neutral-700 rounded text-sm text-neutral-400">
                Нет данных матрицы
              </div>
            {/if}
          </div>

          <!-- Scatter plot -->
          <div>
            <div class="flex items-center justify-between mb-2">
              <h3 class="text-sm font-semibold flex items-center gap-2">
                <ArrowRightLeft size={16} />
                Scatter plot
              </h3>
              <button type="button" onclick={downloadPNG} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Скачать PNG">
                <Download size={14} class="text-neutral-600 dark:text-neutral-400" />
              </button>
            </div>
            <div id={chartId} class="h-[300px] bg-white dark:bg-neutral-800 rounded border border-neutral-200 dark:border-neutral-700 p-3">
              {#if scatterData.datasets.length > 0}
                <Line data={scatterData} options={scatterOptions} key={analysisResult?.analysis_id || 'scatter'} />
              {:else}
                <div class="flex items-center justify-center h-full text-sm text-neutral-400">Нет данных</div>
              {/if}
            </div>
            
            {#if analysisResult?.pair_analysis}
              <div class="mt-2 space-y-1 text-xs">
                <div class="flex justify-between p-1.5 bg-neutral-50 dark:bg-neutral-800 rounded">
                  <span class="text-neutral-600 dark:text-neutral-400">Pearson:</span>
                  <span class="font-semibold">{analysisResult.pair_analysis.pearson.interpretation}</span>
                </div>
                <div class="flex justify-between p-1.5 bg-neutral-50 dark:bg-neutral-800 rounded">
                  <span class="text-neutral-600 dark:text-neutral-400">Spearman:</span>
                  <span class="font-semibold">{analysisResult.pair_analysis.spearman.interpretation}</span>
                </div>
                <div class="flex justify-between p-1.5 bg-neutral-50 dark:bg-neutral-800 rounded">
                  <span class="text-neutral-600 dark:text-neutral-400">Mutual Info:</span>
                  <span class="font-semibold">{analysisResult.pair_analysis.mutual_info.interpretation}</span>
                </div>
                <div class="flex justify-between p-1.5 bg-neutral-50 dark:bg-neutral-800 rounded">
                  <span class="text-neutral-600 dark:text-neutral-400">Cross-corr lag:</span>
                  <span class="font-semibold">{analysisResult.pair_analysis.cross_correlation.interpretation}</span>
                </div>
              </div>
            {/if}
          </div>
        </div>
      {/if}

      <!-- MULTI-TAG MODE: Таблица пар -->
      {#if isMultiTag && activeTab === 'table'}
        <div>
          <h3 class="text-sm font-semibold mb-2">
            Все пары (сортировано по силе корреляции)
          </h3>
          <div class="border border-neutral-200 dark:border-neutral-700 rounded overflow-hidden">
            <table class="text-xs w-full">
              <thead>
                <tr class="bg-neutral-100 dark:bg-neutral-800">
                  <th class="p-2 text-left font-medium">#</th>
                  <th class="p-2 text-left font-medium">Тег 1</th>
                  <th class="p-2 text-left font-medium">Тег 2</th>
                  <th class="p-2 text-right font-medium">Коэф. r</th>
                  <th class="p-2 text-right font-medium">p-value</th>
                  <th class="p-2 text-center font-medium">Значимость</th>
                </tr>
              </thead>
              <tbody>
                {#each correlationPairs as pair, i}
                  <tr class="border-t border-neutral-200 dark:border-neutral-700 hover:bg-neutral-50 dark:hover:bg-neutral-800/50 transition">
                    <td class="p-2 text-neutral-500">{i + 1}</td>
                    <td class="p-2 font-mono text-[11px] truncate max-w-[150px]" title={pair.tag1}>{pair.tag1}</td>
                    <td class="p-2 font-mono text-[11px] truncate max-w-[150px]" title={pair.tag2}>{pair.tag2}</td>
                    <td class="p-2 text-right font-semibold" style="color: {corrColor(pair.coef).replace('0.2', '0.8')}">
                      {pair.coef > 0 ? '+' : ''}{formatNumber(pair.coef, 3)}
                    </td>
                    <td class="p-2 text-right text-neutral-500 dark:text-neutral-400">
                      {pair.p_value < 0.001 ? '<0.001' : formatNumber(pair.p_value, 4)}
                    </td>
                    <td class="p-2 text-center">
                      {#if pair.p_value < 0.001}
                        <span class="px-1.5 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded text-[10px] font-medium">***</span>
                      {:else if pair.p_value < 0.01}
                        <span class="px-1.5 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded text-[10px] font-medium">**</span>
                      {:else if pair.p_value < 0.05}
                        <span class="px-1.5 py-0.5 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300 rounded text-[10px] font-medium">*</span>
                      {:else}
                        <span class="px-1.5 py-0.5 bg-neutral-100 dark:bg-neutral-800 text-neutral-500 rounded text-[10px] font-medium">ns</span>
                      {/if}
                    </td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
          <div class="text-[10px] text-neutral-500 dark:text-neutral-400 mt-2">
            *** p&lt;0.001 · ** p&lt;0.01 · * p&lt;0.05 · ns = незначимая
          </div>
        </div>
      {/if}
    </div>
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
'''

results_path.write_text(new_results, encoding='utf-8', newline='\n')
print('✓ DeepAnalysisResults.svelte обновлён (вкладки + heatmap + table)')

# ============================================================================
# 3. Обновляем Home.svelte — selectedTags (массив) + логика single/multi
# ============================================================================
home_path = Path('frontend/src/routes/Home.svelte')
content = home_path.read_text(encoding='utf-8')

# Меняем ddaSelectedTag на ddaSelectedTags (массив)
if 'let ddaSelectedTag = $state' in content:
    content = content.replace(
        "let ddaSelectedTag = $state<string>('')",
        "let ddaSelectedTags = $state<string[]>([])"
    )
    print('✓ Изменён state: ddaSelectedTag → ddaSelectedTags (массив)')

# Меняем onTagChange на onTagsChange в DeepAnalysisControls
if 'onTagChange={(tag) => ddaSelectedTag = tag}' in content:
    content = content.replace(
        'selectedTag={ddaSelectedTag}',
        'selectedTags={ddaSelectedTags}'
    )
    content = content.replace(
        'onTagChange={(tag) => ddaSelectedTag = tag}',
        'onTagsChange={(tags) => ddaSelectedTags = tags}'
    )
    print('✓ Обновлены props: selectedTag → selectedTags, onTagChange → onTagsChange')

# Меняем проверку в runDDAAnalysis (было !ddaSelectedTag, стало ddaSelectedTags.length === 0)
if '!ddaSelectedTag' in content:
    content = content.replace(
        "if (!ddaSelectedTag) {",
        "if (ddaSelectedTags.length === 0) {"
    )
    print('✓ Обновлена проверка на пустой выбор')

# Меняем запрос API (было tags: [ddaSelectedTag], стало tags: ddaSelectedTags)
if 'tags: [ddaSelectedTag]' in content:
    content = content.replace(
        'tags: [ddaSelectedTag]',
        'tags: ddaSelectedTags'
    )
    print('✓ Обновлён API запрос: передаём массив тегов')

# Обновляем эффект загрузки тегов (выбор первого тега)
if "ddaSelectedTag = tags[0].tag_name" in content:
    content = content.replace(
        "if (tags.length > 0 && !ddaSelectedTag) {",
        "if (tags.length > 0 && ddaSelectedTags.length === 0) {"
    )
    content = content.replace(
        "ddaSelectedTag = tags[0].tag_name",
        "ddaSelectedTags = [tags[0].tag_name]"
    )
    print('✓ Обновлён эффект начального выбора')

home_path.write_text(content, encoding='utf-8', newline='\n')
print('✓ Home.svelte обновлён')

print()
print('=' * 70)
print('ГОТОВО! ВСЕ 3 ДНЯ ИТЕРАЦИИ B ЗАВЕРШЕНЫ')
print('=' * 70)
print()
print('Что сделано:')
print()
print('✅ Day 1: Синхронизация данных')
print('   • data_fetcher.py: общий grid + pandas.resample')
print('   • Интерполяция пропусков, выравнивание по общим timestamps')
print()
print('✅ Day 2: Математика корреляций')
print('   • correlations.py: Pearson, Spearman, Mutual Info, Cross-corr')
print('   • Матрица NxN + pair_analysis для первой пары')
print()
print('✅ Day 3: UI мульти-тег')
print('   • Controls: checkboxes + search + select all/clear')
print('   • Results: вкладки "Обзор" / "Корреляции" / "Таблица"')
print('   • Heatmap с цветовой шкалой (🔵+/🔴-)')
print('   • Scatter plot с линией регрессии')
print('   • Таблица пар с p-values и значимостью (***/**/*/ns)')
print('   • Автоматическое переключение режимов (1 тег vs N тегов)')
print()
print('ПРОВЕРКА:')
print('  1. Открой фронтенд → Activity → выбери 3-5 тегов')
print('  2. "Запустить анализ (N тегов)"')
print('  3. Должно автоматически переключиться на вкладку "Корреляции"')
print('  4. Слева: heatmap (матрица NxN)')
print('  5. Справа: scatter plot для первой пары + 4 метрики')
print('  6. Переключись на "Таблица пар" — увидишь все пары сортированные по силе')
print()
print('КОММИТ (готов?):')
print('  git add -A')
print('  git commit -m "feat(dda): multi-tag correlation analysis (Iteration B)"')
print('  git push origin main')