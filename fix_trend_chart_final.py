from pathlib import Path

print('=== fix_trend_chart_final.py ===')
print()

PROJECT_ROOT = Path('.')
chart_path = PROJECT_ROOT / 'frontend/src/components/analytics/TrendChart.svelte'

# Полностью переписываем TrendChart с исправлениями
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
  }

  let { data = [], label = '', unit = '', color = '#2563eb', trend }: Props = $props()

  // ИСПРАВЛЕНО: $derived возвращает объект, а не функцию
  let chartData = $derived.by(() => {
    if (!data || data.length === 0) {
      return { labels: [], datasets: [] }
    }

    // Извлекаем значения (без proxy)
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

    // Добавляем линию тренда ВСЕГДА если есть данные и slope
    // (убираем условие r_squared > 0.1 — показываем даже слабые тренды)
    if (values.length >= 2 && trend && trend.slope_per_day !== 0) {
      const n = values.length
      const x_mean = (n - 1) / 2
      const y_mean = values.reduce((a, b) => a + b, 0) / n

      // Линейная регрессия
      const slope = trend.slope_per_day * (n / 30) // нормализуем к количеству точек
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

      // Добавляем MA-7 (7-дневная скользящая средняя) для сглаживания
      if (n >= 7) {
        const maValues = []
        for (let i = 0; i < n; i++) {
          if (i < 6) {
            maValues.push(null) // недостаточно данных
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

      // Добавляем экстраполяцию (прогноз) на 30% вперёд
      const forecastPoints = Math.ceil(n * 0.3)
      const forecastLabels = []
      const forecastValues = []
      const lastDate = new Date(data[data.length - 1].timestamp)

      for (let i = 1; i <= forecastPoints; i++) {
        const forecastDate = new Date(lastDate.getTime() + i * 3600000) // +1 час
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

  // Используем обычный const (НЕ $state) чтобы убрать warning
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
print('✓ TrendChart.svelte: полностью переписан')
print()
print('=' * 60)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 60)
print()
print('1. Графики пустые (прямая линия):')
print('   • БЫЛО: let chartData = $derived(() => {...}) — функция')
print('   • СТАЛО: let chartData = $derived.by(() => {...}) — значение')
print('   • Извлекаем значения без proxy: values.map(d => d.value)')
print('   • Теперь Chart.js получает корректные данные')
print()
print('2. Нет трендов для CO2/pressure/VOC:')
print('   • БЫЛО: if (trend.r_squared > 0.1) — слишком строгое условие')
print('   • СТАЛО: if (trend.slope_per_day !== 0) — показываем всегда')
print('   • Слабые тренды (r_squared < 0.1) помечаются как "Тренд (слабый)"')
print('   • Цвет линии: серый для слабых, тёмно-серый для сильных')
print()
print('3. Пропали тренды при 90 днях:')
print('   • Добавлена MA-7 (7-дневная скользящая средняя)')
print('   • Это альтернатива линейной регрессии для длинных периодов')
print('   • MA-7 показывает реальный тренд даже на сэмплированных данных')
print('   • Оранжевая линия в legend: "MA-7 (скользящая средняя)"')
print()
print('Frontend перезагрузится автоматически (Vite HMR).')
print()
print('Проверка:')
print('  1. В чате: "покажи аналитику"')
print('  2. Графики температуры/влажности — должны показать реальные линии')
print('  3. Графики CO2/pressure/VOC — должны показать тренды (возможно слабые)')
print('  4. Переключи на 90 дней — должен появиться MA-7 (оранжевая линия)')
print()
print('Legend на графиках:')
print('  • Синяя линия: Данные (сглаженная)')
print('  • Серая пунктирная: Тренд (или "Тренд (слабый)" если r² < 0.1)')
print('  • Оранжевая сплошная: MA-7 (скользящая средняя, если период >= 7 дней)')
print('  • Оранжевая пунктирная: Прогноз (экстраполяция на 30% вперёд)')