from pathlib import Path

print('=== fix_chart_buttons.py ===')
print()

PROJECT_ROOT = Path('.')
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
  import zoomPlugin from 'chartjs-plugin-zoom'
  import { ZoomIn, ZoomOut, RotateCcw, Download } from 'lucide-svelte'

  ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    Filler,
    zoomPlugin
  )

  interface Props {
    data: Array<{ timestamp: string; value: number }>
    label?: string
    unit?: string
    color?: string
    trend?: { slope_per_day: number; r_squared: number; direction: string }
    yRange?: { min: number; max: number }
  }

  let { data = [], label = '', unit = '', color = '#2563eb', trend, yRange }: Props = $props()

  // Chart instance — сохраняем через callback ref
  let chartInstance: ChartJS | null = null

  function setChartRef(node: any) {
    // svelte-chartjs возвращает { chart: ChartJS }
    chartInstance = node?.chart || node || null
  }

  function clip(value: number): number {
    if (!yRange) return value
    return Math.max(yRange.min, Math.min(yRange.max, value))
  }

  let chartData = $derived.by(() => {
    if (!data || data.length === 0) {
      return { labels: [], datasets: [] }
    }

    const values = data.map(d => typeof d.value === 'number' ? d.value : parseFloat(d.value) || 0)

    const labels = data.map(d => {
      const date = new Date(d.timestamp)
      return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
    })

    const datasets: any[] = [
      {
        label: 'Данные',
        data: values,
        borderColor: color,
        backgroundColor: color + '20',
        tension: 0.3,
        fill: true,
        pointRadius: 0,
        pointHoverRadius: 4,
        order: 2,
      }
    ]

    if (values.length >= 2 && trend && trend.slope_per_day !== 0) {
      const n = values.length
      
      const firstDate = new Date(data[0].timestamp)
      const daysArray = data.map(d => {
        const date = new Date(d.timestamp)
        return (date.getTime() - firstDate.getTime()) / 86400000
      })

      const avgDays = daysArray.reduce((a, b) => a + b, 0) / n
      const avgValue = values.reduce((a, b) => a + b, 0) / n
      const intercept = avgValue - trend.slope_per_day * avgDays

      const trendValues = daysArray.map(days => trend.slope_per_day * days + intercept)

      datasets.push({
        label: trend.r_squared < 0.1 ? 'Тренд (слабый)' : 'Тренд',
        data: trendValues,
        borderColor: trend.r_squared < 0.1 ? '#9ca3af' : '#64748b',
        borderDash: [5, 5],
        borderWidth: trend.r_squared < 0.1 ? 1 : 1.5,
        pointRadius: 0,
        fill: false,
        order: 1,
      })

      if (n >= 7) {
        const maValues: (number | null)[] = []
        for (let i = 0; i < n; i++) {
          if (i < 6) {
            maValues.push(null)
          } else {
            const sum = values.slice(i - 6, i + 1).reduce((a, b) => a + b, 0)
            maValues.push(sum / 7)
          }
        }

        datasets.push({
          label: 'MA-7 (скользящая средняя)',
          data: maValues,
          borderColor: '#9ca3af',
          borderWidth: 2,
          pointRadius: 0,
          fill: false,
          order: 0,
        })
      }

      const forecastPoints = Math.ceil(n * 0.3)
      const forecastLabels: string[] = []
      const forecastValues: (number | null)[] = [...Array(n).fill(null)]
      const lastDate = new Date(data[data.length - 1].timestamp)
      const lastDays = daysArray[n - 1]

      for (let i = 1; i <= forecastPoints; i++) {
        const forecastDate = new Date(lastDate.getTime() + i * 3600000)
        forecastLabels.push(
          forecastDate.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' }) + ' (прогноз)'
        )
        const forecastDays = lastDays + (i / 24)
        const rawValue = trend.slope_per_day * forecastDays + intercept
        forecastValues.push(clip(rawValue))
      }

      datasets.push({
        label: 'Прогноз',
        data: forecastValues,
        borderColor: '#f97316',
        borderDash: [3, 3],
        borderWidth: 1.5,
        pointRadius: 0,
        fill: false,
        order: -1,
      })

      labels.push(...forecastLabels)
    }

    return { labels, datasets }
  })

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
      },
      zoom: {
        pan: {
          enabled: true,
          mode: 'x' as const,
        },
        zoom: {
          wheel: {
            enabled: true,
          },
          pinch: {
            enabled: true,
          },
          mode: 'x' as const,
        },
      },
    },
    scales: {
      x: {
        display: true,
        grid: { display: false },
        ticks: {
          maxTicksLimit: 6,
          font: { size: 9 }
        }
      },
      y: {
        display: true,
        grid: { color: 'rgba(0, 0, 0, 0.05)' },
        suggestedMin: yRange?.min,
        suggestedMax: yRange?.max,
        ticks: {
          font: { size: 9 }
        }
      }
    },
    interaction: {
      mode: 'nearest' as const,
      axis: 'x' as const,
      intersect: false
    }
  }

  // Функции управления графиком
  function zoomIn() {
    console.log('zoomIn called, chartInstance:', chartInstance)
    if (chartInstance) {
      chartInstance.zoom(1.2)
    } else {
      console.warn('Chart instance not available')
    }
  }

  function zoomOut() {
    console.log('zoomOut called, chartInstance:', chartInstance)
    if (chartInstance) {
      chartInstance.zoom(0.8)
    } else {
      console.warn('Chart instance not available')
    }
  }

  function resetZoom() {
    console.log('resetZoom called, chartInstance:', chartInstance)
    if (chartInstance) {
      chartInstance.resetZoom()
    } else {
      console.warn('Chart instance not available')
    }
  }

  function downloadPNG() {
    console.log('downloadPNG called, chartInstance:', chartInstance)
    if (!chartInstance) {
      console.warn('Chart instance not available')
      return
    }
    
    const base64 = chartInstance.toBase64Image('image/png', 1.0)
    const link = document.createElement('a')
    const param = label || 'chart'
    const date = new Date().toISOString().slice(0, 10)
    link.download = `scada_${param}_${date}.png`
    link.href = base64
    link.click()
  }
</script>

<div class="w-full">
  <div class="flex items-center justify-between mb-2">
    {#if label}
      <div class="text-xs font-medium text-neutral-600 dark:text-neutral-400">{label}</div>
    {:else}
      <div></div>
    {/if}
    
    <!-- Кнопки управления графиком -->
    <div class="flex items-center gap-1">
      <button
        type="button"
        onclick={zoomIn}
        class="p-1 rounded hover:bg-neutral-100 dark:hover:bg-neutral-700 text-neutral-500 hover:text-neutral-700 dark:text-neutral-400 dark:hover:text-neutral-200 transition"
        title="Приблизить (или колёсико мыши)"
      >
        <ZoomIn size={14} />
      </button>
      <button
        type="button"
        onclick={zoomOut}
        class="p-1 rounded hover:bg-neutral-100 dark:hover:bg-neutral-700 text-neutral-500 hover:text-neutral-700 dark:text-neutral-400 dark:hover:text-neutral-200 transition"
        title="Отдалить"
      >
        <ZoomOut size={14} />
      </button>
      <button
        type="button"
        onclick={resetZoom}
        class="p-1 rounded hover:bg-neutral-100 dark:hover:bg-neutral-700 text-neutral-500 hover:text-neutral-700 dark:text-neutral-400 dark:hover:text-neutral-200 transition"
        title="Сбросить масштаб"
      >
        <RotateCcw size={14} />
      </button>
      <div class="w-px h-4 bg-neutral-300 dark:bg-neutral-600 mx-0.5"></div>
      <button
        type="button"
        onclick={downloadPNG}
        class="p-1 rounded hover:bg-neutral-100 dark:hover:bg-neutral-700 text-neutral-500 hover:text-neutral-700 dark:text-neutral-400 dark:hover:text-neutral-200 transition"
        title="Скачать PNG"
      >
        <Download size={14} />
      </button>
    </div>
  </div>

  <div class="h-[200px]">
    {#if data.length > 0}
      <Line use:ref={setChartRef} data={chartData} options={chartOptions} />
    {:else}
      <div class="flex items-center justify-center h-full text-sm text-neutral-400">
        Нет данных для графика
      </div>
    {/if}
  </div>
  
  <div class="text-[10px] text-neutral-400 dark:text-neutral-500 mt-1 text-center">
    Колёсико мыши — масштаб · Перетаскивание — прокрутка
  </div>
</div>
'''

chart_path.write_text(chart_content, encoding='utf-8', newline='\n')
print('✓ TrendChart.svelte: исправлены кнопки управления')
print()
print('=' * 60)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 60)
print()
print('1. Доступ к Chart instance:')
print('   • БЫЛО: bind:this={chartRef} — не работает с svelte-chartjs')
print('   • СТАЛО: use:ref={setChartRef} — callback получает node.chart')
print('   • chartInstance сохраняется в переменной')
print()
print('2. Функции управления:')
print('   • Добавлены console.log для дебага')
print('   • Проверяется наличие chartInstance перед вызовом методов')
print('   • Если chartInstance = null — выводится warning в консоль')
print()
print('3. Методы Chart.js:')
print('   • zoom(1.2) — увеличивает масштаб на 20%')
print('   • zoom(0.8) — уменьшает масштаб на 20%')
print('   • resetZoom() — сбрасывает масштаб')
print('   • toBase64Image() — экспортирует PNG')
print()
print('Frontend перезагрузится автоматически (Vite HMR).')
print()
print('Проверка:')
print('  1. В чате: "покажи аналитику"')
print('  2. Открой DevTools → Console')
print('  3. Нажми кнопку Zoom In — должно появиться:')
print('     "zoomIn called, chartInstance: Chart {...}"')
print('  4. Если chartInstance = null — будет warning:')
print('     "Chart instance not available"')
print('  5. Если всё ок — график масштабируется/скачивается')
print()
print('Скинь вывод из DevTools Console после нажатия кнопок —')
print('я увижу что именно не работает.')