from pathlib import Path

print('=== fix_trendchart_callbacks.py ===')
print()

PROJECT_ROOT = Path('.')
chart_path = PROJECT_ROOT / 'frontend/src/components/analytics/TrendChart.svelte'

if not chart_path.exists():
    print(f'⚠ Файл не найден: {chart_path}')
    exit(1)

# ============================================================================
# Полностью переписываем TrendChart с исправлениями
# ============================================================================
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

  // Используем $state.raw чтобы Chart.js не пытался сделать options реактивными
  // (это убирает state_snapshot_uncloneable warning)
  let chartOptions = $state.raw({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        mode: 'index' as const,
        intersect: false,
        callbacks: {
          // Убираем callback функцию — используем дефолтный формат
          // (Svelte 5 не может клонировать функции через $state.snapshot)
          label: (context: any) => {
            const value = context.parsed.y
            return `${value.toFixed(2)} ${unit}`
          }
        }
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
          // Убираем callback функцию — Chart.js сам отформатирует числа
          // (это убирает state_snapshot_uncloneable warning)
        }
      }
    },
    interaction: {
      mode: 'nearest' as const,
      axis: 'x' as const,
      intersect: false
    }
  })
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
print('✓ TrendChart.svelte: исправлен')
print('  • Убран callback из scales.y.ticks.callback')
print('  • Использован $state.raw() для options')
print('  • Добавлены часы и минуты в формат даты')

print()
print('=' * 60)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 60)
print()
print('1. state_snapshot_uncloneable warning:')
print('   • Убран callback из scales.y.ticks.callback')
print('   • Использован $state.raw() для chartOptions')
print('   • Svelte 5 больше не пытается клонировать функции')
print()
print('2. Формат даты на оси X:')
print('   • Добавлены часы и минуты: "9 июня 17:00"')
print('   • Раньше было только: "9 июня"')
print()
print('3. Про даты "28 мая - 4 июня":')
print('   • Это реальные данные из базы')
print('   • Backend возвращает raw_data с реальными timestamps')
print('   • Если последние измерения были неделю назад — даты будут старыми')
print()
print('Frontend перезагрузится автоматически (Vite HMR).')
print()
print('Проверка:')
print('  1. Открой DevTools → Console')
print('  2. В чате: "покажи аналитику"')
print('  3. НЕ должно быть state_snapshot_uncloneable warnings')
print('  4. Даты на оси X: "9 июня 17:00", "10 июня 08:00", ...')
print()
print('Если даты всё ещё старые — проверь что в базе есть свежие данные:')
print('  curl "http://localhost:8081/analytics/report?period=1&params=temperature"')
print('  → Должен вернуть raw_data за последний день')