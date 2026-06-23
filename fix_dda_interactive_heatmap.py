#!/usr/bin/env python3
"""
fix_dda_interactive_heatmap.py — интерактивный heatmap с кликом по ячейкам
"""

from pathlib import Path

print('=' * 70)
print('ИНТЕРАКТИВНЫЙ HEATMAP + ENDPOINT ДЛЯ ПАРЫ')
print('=' * 70)
print()

# ============================================================================
# 1. Добавляем endpoint /deep_analysis/pair в api.py
# ============================================================================
api_path = Path('backend/modules/deep_analysis/api.py')
content = api_path.read_text(encoding='utf-8')

# Импортируем compute_pair_correlation (уже должен быть импортирован)
if 'compute_pair_correlation' not in content:
    content = content.replace(
        'from modules.deep_analysis.analyzers.correlations import compute_correlation_matrix',
        'from modules.deep_analysis.analyzers.correlations import compute_correlation_matrix, compute_pair_correlation'
    )

# Добавляем Pydantic модель для запроса пары
pair_models = '''

class PairAnalysisRequest(BaseModel):
    """Запрос анализа конкретной пары тегов"""
    tag1: str = Field(..., description="Первый тег")
    tag2: str = Field(..., description="Второй тег")
    period: int = Field(30, description="Период в днях", ge=1, le=365)


class PairAnalysisResponse(BaseModel):
    """Ответ с детальным анализом пары"""
    tag1: str
    tag2: str
    period: str
    pearson: dict
    spearman: dict
    mutual_info: dict
    cross_correlation: dict
    scatter_data: dict
    scatter_spec: dict
'''

# Вставляем модели перед классом AnalysisResponse
if 'class PairAnalysisRequest' not in content:
    content = content.replace(
        'class AnalysisResponse(BaseModel):',
        pair_models + '\n\nclass AnalysisResponse(BaseModel):'
    )
    print('✓ Добавлены модели PairAnalysisRequest/Response')

# Добавляем endpoint перед @router.get("/tags")
pair_endpoint = '''

@router.post("/pair", response_model=PairAnalysisResponse)
async def analyze_pair(request: PairAnalysisRequest):
    """
    Детальный анализ конкретной пары тегов.
    Используется при клике на ячейку в heatmap.
    """
    log.info(
        "Analyzing pair",
        tag1=request.tag1,
        tag2=request.tag2,
        period=request.period
    )
    
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=request.period)
        period_str = f"{request.period} days"
        
        # Собираем данные с выравниванием
        data = await fetch_multiple_tags(
            [request.tag1, request.tag2],
            start_date, end_date,
            resample_freq='5min',
            align=True
        )
        
        if not data['common_timestamps']:
            raise HTTPException(
                status_code=400,
                detail="No common data for pair analysis"
            )
        
        # Детальный анализ пары
        pair_analysis = compute_pair_correlation(
            data['tags'][request.tag1].get('aligned_values', []),
            data['tags'][request.tag2].get('aligned_values', []),
            request.tag1, request.tag2
        )
        
        # Scatter spec
        scatter_spec = create_scatter_spec(
            pair_analysis['scatter_data']['x'],
            pair_analysis['scatter_data']['y'],
            request.tag1, request.tag2,
            pair_analysis['pearson']['coefficient']
        )
        
        return PairAnalysisResponse(
            tag1=request.tag1,
            tag2=request.tag2,
            period=period_str,
            pearson=pair_analysis['pearson'],
            spearman=pair_analysis['spearman'],
            mutual_info=pair_analysis['mutual_info'],
            cross_correlation=pair_analysis['cross_correlation'],
            scatter_data=pair_analysis['scatter_data'],
            scatter_spec=scatter_spec,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        log.error("Pair analysis failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

'''

# Вставляем перед @router.get("/tags")
if '@router.post("/pair"' not in content:
    content = content.replace(
        '@router.get("/tags"',
        pair_endpoint + '\n@router.get("/tags"'
    )
    print('✓ Добавлен endpoint POST /deep_analysis/pair')

api_path.write_text(content, encoding='utf-8', newline='\n')
print('✓ api.py обновлён')

# ============================================================================
# 2. Обновляем DeepAnalysisResults.svelte — интерактивный heatmap
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
    ZoomIn, ZoomOut, Grid3x3, ArrowRightLeft, Table, Info, Loader2
  } from 'lucide-svelte'
  import api from '../lib/api'

  ChartJS.register(
    CategoryScale, LinearScale, PointElement, LineElement,
    Title, Tooltip, Legend, ScatterController, BubbleController, zoomPlugin
  )

  interface Props {
    analysisResult: any
    isAnalyzing: boolean
  }

  let { analysisResult, isAnalyzing }: Props = $props()

  // Режим: single-tag или multi-tag
  let isMultiTag = $derived(
    analysisResult?.tags?.length > 1 && 
    analysisResult?.correlations !== null &&
    analysisResult?.correlations !== undefined
  )

  let activeTab = $state<'overview' | 'correlations' | 'table'>('overview')
  $effect(() => {
    if (isMultiTag) activeTab = 'correlations'
    else activeTab = 'overview'
  })

  // Chart instances
  let tsChartInstance: ChartJS | null = $state(null)
  let scatterChartInstance: ChartJS | null = $state(null)
  const tsChartId = `dda-ts-${Math.random().toString(36).slice(2, 9)}`
  const scatterChartId = `dda-scatter-${Math.random().toString(36).slice(2, 9)}`

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
      const periodMatch = analysisResult.period.match(/(\\d+)/)
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
      x: { display: true, grid: { display: false }, ticks: { maxTicksLimit: 10, font: { size: 10 } } },
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

  function resetZoomTs() { tsChartInstance?.resetZoom() }
  function zoomInTs() { tsChartInstance?.zoom(1.2) }
  function zoomOutTs() { tsChartInstance?.zoom(0.8) }
  function resetZoomScatter() { scatterChartInstance?.resetZoom() }
  function zoomInScatter() { scatterChartInstance?.zoom(1.2) }
  function zoomOutScatter() { scatterChartInstance?.zoom(0.8) }
  
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
            </div>
          </div>
          <div id={tsChartId} class="h-[300px] bg-white dark:bg-neutral-800 rounded border border-neutral-200 dark:border-neutral-700 p-3">
            {#if timeSeriesData.labels.length > 0}
              <Line data={timeSeriesData} options={timeSeriesOptions} key={analysisResult?.analysis_id || 'default'} />
            {:else}
              <div class="flex items-center justify-center h-full text-sm text-neutral-400">Нет данных</div>
            {/if}
          </div>
        </div>
      {/if}

      <!-- ==================== MULTI-TAG: CORRELATIONS ==================== -->
      {#if isMultiTag && activeTab === 'correlations'}
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
            
            <div class="text-[10px] text-neutral-500 dark:text-neutral-400 mt-1 flex items-center gap-3">
              <span>🔵 положительная</span>
              <span>🔴 отрицательная</span>
              <span>•</span>
              <span>🟦 рамка = выбранная пара</span>
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
print('✓ DeepAnalysisResults.svelte обновлён (интерактивный heatmap)')

print()
print('=' * 70)
print('ЧТО СДЕЛАНО:')
print('=' * 70)
print()
print('1. ✓ Новый endpoint: POST /deep_analysis/pair')
print('   • Принимает {tag1, tag2, period}')
print('   • Возвращает полный анализ пары + scatter_spec')
print('   • Быстрый ответ (~1-2 сек) без пере-запуска всего анализа')
print()
print('2. ✓ Интерактивный heatmap')
print('   • Клик на ячейку (i, j) → загружается scatter plot для пары')
print('   • Диагональ (i=i) не кликабельна (это 1.0)')
print('   • Выбранная ячейка подсвечивается синей рамкой')
print('   • Tooltip показывает "клик для scatter plot"')
print()
print('3. ✓ State для выбранной пары')
print('   • selectedPair = {tag1, tag2}')
print('   • $effect автоматически загружает данные при смене пары')
print('   • Loading state с спиннером поверх графика')
print()
print('4. ✓ Кликабельная таблица пар')
print('   • Клик на строку в таблице → переключает на вкладку "Корреляции"')
print('   • И загружает scatter для этой пары')
print('   • Выбранная строка подсвечивается')
print()
print('5. ✓ Scatter plot с правильными метками осей')
print('   • Ось X: "KITCHEN2-CO2" (полное имя первого тега)')
print('   • Ось Y: "R204-CO2" (полное имя второго тега)')
print('   • Заголовок: "(KITCHEN2-CO2 × R204-CO2)"')
print()
print('=' * 70)
print('ПРОВЕРКА:')
print('=' * 70)
print()
print('1. Открой фронтенд → Activity → выбери 4 тега → анализ')
print('2. Вкладка "Корреляции":')
print('   • Видишь матрицу 4×4')
print('   • По умолчанию выбрана пара [0,1]')
print('   • Снизу — scatter plot для этой пары')
print()
print('3. КЛИК НА ДРУГУЮ ЯЧЕЙКУ:')
print('   • Например, клик на пересечении "KITCHEN2-VOC" × "R206-VOC"')
print('   • Видишь спиннер "Загружаем пару..."')
print('   • Через 1-2 сек scatter plot перерисовывается')
print('   • В заголовке: "(KITCHEN2-VOC × R206-VOC)"')
print('   • Оси: X = KITCHEN2-VOC, Y = R206-VOC')
print()
print('4. КЛИК В ТАБЛИЦЕ:')
print('   • Перейди во вкладку "Таблица пар"')
print('   • Клик на любую строку → авто-переключение на "Корреляции"')
print('   • И загрузка scatter для этой пары')
print()
print('5. Зум на scatter:')
print('   • Колёсико мыши → zoom')
print('   • Shift+drag → область')
print('   • Drag → прокрутка')
print('   • Кнопки ZoomIn/Out/Reset/Download')