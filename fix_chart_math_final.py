from pathlib import Path

print('=== fix_chart_math_final.py ===')
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

  // Хелпер: ограничиваем значение пределами yRange
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

    // Линия тренда — ПРАВИЛЬНАЯ математика
    if (values.length >= 2 && trend && trend.slope_per_day !== 0) {
      const n = values.length
      
      // Вычисляем дни от начала для каждой точки
      const firstDate = new Date(data[0].timestamp)
      const daysArray = data.map(d => {
        const date = new Date(d.timestamp)
        return (date.getTime() - firstDate.getTime()) / 86400000 // дни
      })

      // Линейная регрессия: y = slope_per_day * days + intercept
      const avgDays = daysArray.reduce((a, b) => a + b, 0) / n
      const avgValue = values.reduce((a, b) => a + b, 0) / n
      const intercept = avgValue - trend.slope_per_day * avgDays

      // Точки тренда на реальных днях
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

      // MA-7 (скользящая средняя) — фиолетовый
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
          borderColor: '#8b5cf6',
          borderWidth: 2,
          pointRadius: 0,
          fill: false,
          order: 0,
        })
      }

      // Прогноз — ограничен пределами yRange
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
        const forecastDays = lastDays + (i / 24) // +i часов в днях
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

      // DEBUG: логируем что передаём в Chart.js
      if (label === 'Температура' || label === 'temperature') {
        console.log('TrendChart DEBUG:', {
          label,
          yRange,
          dataPoints: n,
          firstDays: daysArray[0],
          lastDays: daysArray[n - 1],
          slope_per_day: trend.slope_per_day,
          intercept,
          trendValues_sample: trendValues.slice(0, 3),
          forecastValues_sample: forecastValues.slice(n, n + 3),
        })
      }
    }

    return { labels, datasets }
  })

  // ИСПРАВЛЕНО: используем suggestedMin/suggestedMax вместо min/max
  // Это позволяет Chart.js показывать данные за пределами, но масштабировать вокруг yRange
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
print('✓ TrendChart.svelte: полностью переписан')
print()
print('=' * 60)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 60)
print()
print('1. Математика тренда:')
print('   • БЫЛО: slope * (n / 30) — неправильная нормализация')
print('   • СТАЛО: slope_per_day * days — правильная формула')
print('   • days = (timestamp - first_timestamp) / 86400000')
print('   • y = slope_per_day * days + intercept')
print()
print('2. Пределы оси Y:')
print('   • БЫЛО: min/max (жёсткие ограничения, данные за пределами обрезаются)')
print('   • СТАЛО: suggestedMin/suggestedMax (мягкие рекомендации)')
print('   • Chart.js масштабирует вокруг yRange, но показывает все данные')
print()
print('3. Прогноз ограничен пределами:')
print('   • clip() обрезает значения прогноза пределами yRange')
print('   • График не будет показывать -400 или +300')
print()
print('4. DEBUG логирование:')
print('   • Консоль покажет что передаётся в Chart.js для температуры')
print('   • Проверь DevTools → Console после запуска')
print()
print('Frontend перезагрузится автоматически (Vite HMR).')
print()
print('Проверка:')
print('  1. В чате: "покажи аналитику"')
print('  2. Открой DevTools → Console')
print('  3. Найди строку "TrendChart DEBUG:" для температуры')
print('  4. Графики должны показывать реальные тренды (не линейные вверх)')
print('  5. Пределы оси Y должны быть ~0..50 для температуры (не -400..+300)')
print()
print('Скинь вывод из DevTools Console (строка "TrendChart DEBUG:") —')
print('я увижу что реально передаётся в Chart.js и дам финальный фикс если нужно.')