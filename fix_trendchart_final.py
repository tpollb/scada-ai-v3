from pathlib import Path

print('=== fix_trendchart_final.py ===')
print()

PROJECT_ROOT = Path('.')
chart_path = PROJECT_ROOT / 'frontend/src/components/analytics/TrendChart.svelte'

file_content = '''<script lang="ts">
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
  }

  let { data = [], label = '', unit = '', color = '#2563eb' }: Props = $props()

  // Конвертируем данные в формат Chart.js
  let chartData = $derived({
    labels: data.map(d => {
      const date = new Date(d.timestamp)
      return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
    }),
    datasets: [
      {
        label: label || 'Значение',
        data: data.map(d => d.value),
        borderColor: color,
        backgroundColor: color + '20',
        tension: 0.3,
        fill: true,
        pointRadius: 0,
        pointHoverRadius: 4,
      }
    ]
  })

  // ВАЖНО: используем обычный const (НЕ $state, НЕ $state.raw)
  // Это полностью убирает state_snapshot_uncloneable warning,
  // потому что svelte-chartjs не пытается клонировать нереактивный объект.
  // Callback убран — Chart.js использует дефолтный формат.
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        mode: 'index' as const,
        intersect: false
        // callbacks убраны — используем дефолтный формат
      }
    },
    scales: {
      x: {
        display: true,
        grid: {
          display: false
        },
        ticks: {
          maxTicksLimit: 6,
          font: {
            size: 10
          }
        }
      },
      y: {
        display: true,
        grid: {
          color: 'rgba(0, 0, 0, 0.05)'
        },
        ticks: {
          font: {
            size: 10
          }
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

  <div class="h-[180px]">
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

chart_path.write_text(file_content, encoding='utf-8', newline='\n')
print(f'✓ TrendChart.svelte переписан')
print()
print('Что изменилось:')
print('  1. $state.raw() → const (объект не реактивный)')
print('  2. tooltip.callbacks.label убран (больше нет функций в options)')
print('  3. Chart.js использует дефолтный tooltip формат')
print()
print('Frontend перезагрузится автоматически (Vite HMR).')
print()
print('Проверка:')
print('  1. Открой DevTools → Console')
print('  2. В чате: "покажи аналитику"')
print('  3. НЕ должно быть state_snapshot_uncloneable warnings')