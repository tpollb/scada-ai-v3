from pathlib import Path

print('=== fix_chart_final.py ===')
print()

PROJECT_ROOT = Path('.')

# ============================================================================
# 1. TrendChart.svelte — полная перезапись
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

  // Хелпер: ограничиваем значение пределами yRange (для прогноза)
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

      // MA-7 — фиолетовый (НЕ оранжевый, чтобы не конфликтовать с VOC)
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

      for (let i = 1; i <= forecastPoints; i++) {
        const forecastDate = new Date(lastDate.getTime() + i * 3600000)
        forecastLabels.push(
          forecastDate.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' }) + ' (прогноз)'
        )
        const rawValue = slope * (n + i - 1) + intercept
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

  // ИСПРАВЛЕНО: УБРАНЫ все callbacks (убираем state_snapshot_uncloneable)
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
        min: yRange?.min,
        max: yRange?.max,
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
print('  • Убраны все callbacks (убираем state_snapshot_uncloneable)')
print('  • MA-7 теперь фиолетовый (#8b5cf6)')
print('  • Прогноз ограничен пределами yRange (clip)')

# ============================================================================
# 2. AnalyticsPanel.svelte — читаем, находим и добавляем yRange
# ============================================================================
panel_path = PROJECT_ROOT / 'frontend/src/components/analytics/AnalyticsPanel.svelte'
content = panel_path.read_text(encoding='utf-8')

# Физические границы
y_ranges = {
    'temperature': (0, 50),
    'humidity': (0, 100),
    'co2': (300, 2000),
    'pressure': (700, 800),
    'voc': (0, 1),
}

# Паттерн: ищем каждый вызов TrendChart и добавляем yRange
for param, (y_min, y_max) in y_ranges.items():
    # Ищем паттерн: trend={{ ... }}  /> для этого параметра
    old = f'''trend={{{{ slope_per_day: data.trends['{param}'].slope_per_day, r_squared: data.trends['{param}'].r_squared, direction: data.trends['{param}'].direction }}}}
                />'''
    
    new = f'''trend={{{{ slope_per_day: data.trends['{param}'].slope_per_day, r_squared: data.trends['{param}'].r_squared, direction: data.trends['{param}'].direction }}}}
                  yRange={{{{ min: {y_min}, max: {y_max} }}}}
                />'''
    
    if old in content:
        content = content.replace(old, new)
        print(f'✓ {param}: добавлен yRange min={y_min}, max={y_max}')
    elif 'yRange=' in content:
        print(f'ℹ {param}: yRange уже добавлен')
    else:
        # Показываем реальный паттерн
        import re
        match = re.search(f"trend=.*?{param}.*?/>", content, re.DOTALL)
        if match:
            print(f'⚠ {param}: точный паттерн не найден')
            print(f'  Реальный код: {match.group(0)[:150]}')

panel_path.write_text(content, encoding='utf-8', newline='\n')

print()
print('=' * 60)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 60)
print()
print('1. state_snapshot_uncloneable:')
print('   • Убраны ВСЕ callbacks из chartOptions')
print('   • scales.x.ticks и scales.y.ticks больше не содержат функций')
print()
print('2. Цвета MA-7:')
print('   • Было: #f59e0b (оранжевый) — конфликт с VOC')
print('   • Стало: #8b5cf6 (фиолетовый)')
print()
print('3. Пределы оси Y:')
print('   • temperature: 0..50 °C')
print('   • humidity: 0..100 %')
print('   • co2: 300..2000 ppm')
print('   • pressure: 700..800 мм рт. ст.')
print('   • voc: 0..1 мг/м³')
print()
print('4. Прогноз ограничен пределами:')
print('   • clip() функция обрезает значения прогноза')
print('   • График не будет выходить за физические границы')
print()
print('Frontend перезагрузится автоматически (Vite HMR).')
print()
print('Проверка:')
print('  1. DevTools Console: НЕ должно быть state_snapshot_uncloneable')
print('  2. Все графики: правильные пределы оси Y')
print('  3. VOC график: MA-7 фиолетовый (не оранжевый)')
print('  4. Прогноз: не выходит за физические границы')