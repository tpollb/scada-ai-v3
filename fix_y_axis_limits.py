from pathlib import Path

print('=== fix_y_axis_limits.py ===')
print()

PROJECT_ROOT = Path('.')

# ============================================================================
# 1. TrendChart.svelte — добавляем prop yRange для фиксированных пределов
# ============================================================================
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
    trend?: { slope_per_day: number; r_squared: number; direction: string }
    yRange?: { min: number; max: number }
  }

  let { data = [], label = '', unit = '', color = '#2563eb', trend, yRange }: Props = $props()

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
      const x_mean = (n - 1) / 2
      const y_mean = values.reduce((a, b) => a + b, 0) / n

      const slope = trend.slope_per_day * (n / 30)
      const intercept = y_mean - slope * x_mean

      const trendValues = values.map((_, i) => slope * i + intercept)

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
        const maValues = []
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
          borderColor: '#f59e0b',
          borderWidth: 2,
          pointRadius: 0,
          fill: false,
          order: 0,
        })
      }

      const forecastPoints = Math.ceil(n * 0.3)
      const forecastLabels = []
      const forecastValues = []
      const lastDate = new Date(data[data.length - 1].timestamp)

      for (let i = 1; i <= forecastPoints; i++) {
        const forecastDate = new Date(lastDate.getTime() + i * 3600000)
        forecastLabels.push(
          forecastDate.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' }) + ' (прогноз)'
        )
        forecastValues.push(slope * (n + i - 1) + intercept)
      }

      datasets.push({
        label: 'Прогноз',
        data: [...Array(n).fill(null), ...forecastValues],
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
      }
    },
    scales: {
      x: {
        display: true,
        grid: { display: false },
        ticks: {
          maxTicksLimit: 6,
          font: { size: 9 },
          callback: (value: any, index: number) => {
            const label = chartData.labels?.[index] || ''
            return label.includes('(прогноз)') ? '' : label.split(' ')[0]
          }
        }
      },
      y: {
        display: true,
        grid: { color: 'rgba(0, 0, 0, 0.05)' },
        // ФИКСИРОВАННЫЕ ПРЕДЕЛЫ если передан yRange
        min: yRange?.min,
        max: yRange?.max,
        ticks: {
          font: { size: 9 },
          callback: (value: any) => `${value} ${unit}`
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

  <div class="h-[200px]">
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

chart_path.write_text(chart_content, encoding='utf-8', newline='\n')
print('✓ TrendChart.svelte: добавлен prop yRange для фиксированных пределов')

# ============================================================================
# 2. AnalyticsPanel.svelte — передаём yRange для каждого параметра
# ============================================================================
panel_path = PROJECT_ROOT / 'frontend/src/components/analytics/AnalyticsPanel.svelte'
content = panel_path.read_text(encoding='utf-8')

# Физические границы для параметров
y_ranges = {
    'temperature': { min: 0, max: 50 },
    'humidity': { min: 0, max: 100 },
    'co2': { min: 300, max: 2000 },
    'pressure': { min: 700, max: 800 },
    'voc': { min: 0, max: 1000 },
}

# Обновляем каждый вызов TrendChart
for param, y_range in y_ranges.items():
    # Ищем паттерн: <TrendChart ... /> для этого параметра
    # и добавляем yRange={{ min: X, max: Y }}
    old_pattern = f'''<TrendChart
                  data={{prepareChartData('{param}')}}
                  unit={{'{param}' === 'temperature' ? '°C' : '{param}' === 'humidity' ? '%' : '{param}' === 'co2' ? 'ppm' : '{param}' === 'pressure' ? 'мм' : 'мг/м³'}}
                  color={{paramColors['{param}'] || '#64748b'}}
                  trend={{{{ slope_per_day: data.trends['{param}'].slope_per_day, r_squared: data.trends['{param}'].r_squared, direction: data.trends['{param}'].direction }}}}
                />'''
    
    new_pattern = f'''<TrendChart
                  data={{prepareChartData('{param}')}}
                  unit={{'{param}' === 'temperature' ? '°C' : '{param}' === 'humidity' ? '%' : '{param}' === 'co2' ? 'ppm' : '{param}' === 'pressure' ? 'мм' : 'мг/м³'}}
                  color={{paramColors['{param}'] || '#64748b'}}
                  trend={{{{ slope_per_day: data.trends['{param}'].slope_per_day, r_squared: data.trends['{param}'].r_squared, direction: data.trends['{param}'].direction }}}}
                  yRange={{{{ min: {y_range['min']}, max: {y_range['max']} }}}}
                />'''
    
    if old_pattern in content:
        content = content.replace(old_pattern, new_pattern)
        print(f'✓ {param}: добавлен yRange min={y_range["min"]}, max={y_range["max"]}')
    else:
        print(f'⚠ {param}: паттерн не найден')

panel_path.write_text(content, encoding='utf-8', newline='\n')

print()
print('=' * 60)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 60)
print()
print('Добавлены фиксированные пределы для оси Y:')
print('  • temperature: 0..50 °C')
print('  • humidity: 0..100 %')
print('  • co2: 300..2000 ppm')
print('  • pressure: 700..800 мм рт. ст.')
print('  • voc: 0..1000 мг/м³')
print()
print('Теперь графики не будут масштабироваться до нереалистичных значений')
print('(-400..+300) из-за экстраполяции тренда.')
print()
print('Frontend перезагрузится автоматически (Vite HMR).')
print()
print('Проверка:')
print('  1. В чате: "покажи аналитику"')
print('  2. Все графики должны показывать реалистичные пределы оси Y')
print('  3. Экстраполяция прогноза может выходить за пределы (это нормально)')