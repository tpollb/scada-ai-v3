<script lang="ts">
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
  import zoomPlugin from 'chartjs-plugin-zoom'
  import { TrendingUp, AlertTriangle, Activity, Download, RotateCcw, ZoomIn, ZoomOut } from 'lucide-svelte'

  ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    ScatterController,
    zoomPlugin
  )

  interface Props {
    analysisResult: any
    isAnalyzing: boolean
  }

  let { analysisResult, isAnalyzing }: Props = $props()

  let chartInstance: ChartJS | null = $state(null)
  const chartId = `dda-chart-${Math.random().toString(36).slice(2, 9)}`

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
        labels: { font: { size: 11 }, boxWidth: 12 }
      },
      tooltip: { mode: 'index' as const, intersect: false },
      zoom: {
        pan: { enabled: true, mode: 'x' as const, modifierKey: null },
        zoom: {
          wheel: { enabled: true, speed: 0.05 },
          pinch: { enabled: true },
          drag: {
            enabled: true,
            modifierKey: 'shift' as const,
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            borderColor: 'rgba(59, 130, 246, 0.5)',
            borderWidth: 1,
          },
          mode: 'x' as const,
        },
      },
    },
    scales: {
      x: {
        display: true,
        grid: { display: false },
        ticks: { maxTicksLimit: 10, font: { size: 10 } }
      },
      y: {
        display: true,
        grid: { color: 'rgba(0, 0, 0, 0.05)' },
        ticks: { font: { size: 10 } }
      }
    },
    interaction: { mode: 'nearest' as const, axis: 'x' as const, intersect: false }
  }

  $effect(() => {
    if (chartData.labels.length > 0) {
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
    const tagName = analysisResult?.tags?.[0] || 'analysis'
    const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-')
    link.download = `scada_ai_analysis_${tagName}_${timestamp}.png`
    link.href = canvas.toDataURL('image/png', 1.0)
    link.click()
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
    <div class="flex-1 overflow-y-auto px-6 py-4">
      <div class="mb-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded">
        <p class="text-sm text-blue-900 dark:text-blue-100">{analysisResult.summary}</p>
      </div>

      {#if analysisResult?.statistics && analysisResult.statistics.count > 0}
      <div class="mb-4">
        <h3 class="text-sm font-semibold text-neutral-900 dark:text-neutral-100 mb-2 flex items-center gap-2">
          <TrendingUp size={16} />
          Статистика
        </h3>
        <div class="grid grid-cols-4 gap-2">
          <div class="p-2 bg-neutral-50 dark:bg-neutral-800 rounded">
            <div class="text-xs text-neutral-500 dark:text-neutral-400 mb-1">Среднее</div>
            <div class="text-base font-semibold text-neutral-900 dark:text-neutral-100">
              {formatNumber(analysisResult.statistics.mean)}
            </div>
          </div>
          <div class="p-2 bg-neutral-50 dark:bg-neutral-800 rounded">
            <div class="text-xs text-neutral-500 dark:text-neutral-400 mb-1">Std Dev</div>
            <div class="text-base font-semibold text-neutral-900 dark:text-neutral-100">
              {formatNumber(analysisResult.statistics.std)}
            </div>
          </div>
          <div class="p-2 bg-neutral-50 dark:bg-neutral-800 rounded">
            <div class="text-xs text-neutral-500 dark:text-neutral-400 mb-1">Min</div>
            <div class="text-base font-semibold text-neutral-900 dark:text-neutral-100">
              {formatNumber(analysisResult.statistics.min)}
            </div>
          </div>
          <div class="p-2 bg-neutral-50 dark:bg-neutral-800 rounded">
            <div class="text-xs text-neutral-500 dark:text-neutral-400 mb-1">Max</div>
            <div class="text-base font-semibold text-neutral-900 dark:text-neutral-100">
              {formatNumber(analysisResult.statistics.max)}
            </div>
          </div>
        </div>
      </div>
      {/if}

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

      <div class="mb-4">
        <div class="flex items-center justify-between mb-2">
          <h3 class="text-sm font-semibold text-neutral-900 dark:text-neutral-100">График</h3>
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
        <div id={chartId} class="h-[350px] bg-white dark:bg-neutral-800 rounded border border-neutral-200 dark:border-neutral-700 p-3">
          {#if chartData.labels.length > 0}
            <Line data={chartData} options={chartOptions} key={analysisResult?.analysis_id || 'default'} />
          {:else}
            <div class="flex items-center justify-center h-full text-sm text-neutral-400">Нет данных</div>
          {/if}
        </div>
      </div>
    </div>
  {:else}
    <div class="flex-1 flex items-center justify-center">
      <div class="flex flex-col items-center text-center text-neutral-400 dark:text-neutral-500">
        <Activity size={48} class="mb-3 opacity-50" />
        <p class="text-sm mb-1">Выберите тег и запустите анализ</p>
        <p class="text-xs">Результаты появятся здесь</p>
      </div>
    </div>
  {/if}
</div>
