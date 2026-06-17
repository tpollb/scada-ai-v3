from pathlib import Path

print('=== fix_upgrade_bugs.py ===')
print()

PROJECT_ROOT = Path('.')

# ============================================================================
# 1. TrendChart.svelte — исправляем chartData и убираем callbacks
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
  }

  let { data = [], label = '', unit = '', color = '#2563eb', trend }: Props = $props()

  // ИСПРАВЛЕНО: chartData теперь объект, а не функция
  let chartData = $derived(() => {
    const labels = data.map(d => {
      const date = new Date(d.timestamp)
      return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
    })

    const datasets: any[] = [
      {
        label: 'Данные',
        data: data.map(d => d.value),
        borderColor: color,
        backgroundColor: color + '20',
        tension: 0.3,
        fill: true,
        pointRadius: 0,
        pointHoverRadius: 4,
        order: 2,
      }
    ]

    // Добавляем линию тренда если есть данные и тренд
    if (data.length >= 2 && trend && trend.r_squared > 0.1) {
      const values = data.map(d => d.value)
      const n = values.length
      const x_mean = (n - 1) / 2
      const y_mean = values.reduce((a, b) => a + b, 0) / n

      const slope = trend.slope_per_day * (n / 30)
      const intercept = y_mean - slope * x_mean

      const trendValues = values.map((_, i) => slope * i + intercept)

      datasets.push({
        label: 'Тренд',
        data: trendValues,
        borderColor: '#64748b',
        borderDash: [5, 5],
        borderWidth: 1.5,
        pointRadius: 0,
        fill: false,
        order: 1,
      })

      // Экстраполяция на 30% вперёд
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
        order: 0,
      })

      labels.push(...forecastLabels)
    }

    return { labels, datasets }
  })

  // ВАЖНО: обычный const (НЕ $state) + БЕЗ callbacks (убираем state_snapshot_uncloneable)
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
      <Line data={chartData()} options={chartOptions} />
    {:else}
      <div class="flex items-center justify-center h-full text-sm text-neutral-400">
        Нет данных для графика
      </div>
    {/if}
  </div>
</div>
'''

chart_path.write_text(chart_content, encoding='utf-8', newline='\n')
print('✓ TrendChart.svelte: исправлен chartData (функция вызывается), убраны callbacks')

# ============================================================================
# 2. Backend: добавляем norms в response trends.py
# ============================================================================
trends_path = PROJECT_ROOT / 'backend/modules/analytics/analyzers/trends.py'
content = trends_path.read_text(encoding='utf-8')

# Ищем return statement и добавляем norms
if '"norms":' not in content:
    old_return = '''    return {
        "param": param_key,
        "aggregation": aggregation,
        "bucket_count": len(data_points),
        "total_raw_count": total_raw_count,
        "outliers_count": outliers_count,
        "avg": round(avg, 2),
        "min": round(min_val, 2),
        "max": round(max_val, 2),
        "stdev": round(stdev, 2),
        "slope_per_day": round(slope_per_day, 4),
        "r_squared": round(r_squared, 3),
        "direction": direction,
        "anomalies": anomalies,
        "anomaly_rate": round(anomaly_rate, 4),
        "raw_data": raw_data,
    }'''
    
    new_return = '''    return {
        "param": param_key,
        "aggregation": aggregation,
        "bucket_count": len(data_points),
        "total_raw_count": total_raw_count,
        "outliers_count": outliers_count,
        "avg": round(avg, 2),
        "min": round(min_val, 2),
        "max": round(max_val, 2),
        "stdev": round(stdev, 2),
        "slope_per_day": round(slope_per_day, 4),
        "r_squared": round(r_squared, 3),
        "direction": direction,
        "anomalies": anomalies,
        "anomaly_rate": round(anomaly_rate, 4),
        "norms": param_data.get("norms", {}),
        "raw_data": raw_data,
    }'''
    
    if old_return in content:
        content = content.replace(old_return, new_return)
        trends_path.write_text(content, encoding='utf-8', newline='\n')
        print('✓ trends.py: добавлено поле norms в response')
    else:
        print('⚠ Не найден точный return statement')
else:
    print('ℹ norms уже есть в trends.py')

# ============================================================================
# 3. AnalyticsPanel.svelte — исправляем доступ к агрегации
# ============================================================================
panel_path = PROJECT_ROOT / 'frontend/src/components/analytics/AnalyticsPanel.svelte'
content = panel_path.read_text(encoding='utf-8')

# Исправляем строку с агрегацией
old_agg = '''<li>Агрегация: {data.aggregation}</li>'''
new_agg = '''<li>Агрегация: {data?.aggregation || 'auto'}</li>'''

if old_agg in content:
    content = content.replace(old_agg, new_agg)
    panel_path.write_text(content, encoding='utf-8', newline='\n')
    print('✓ AnalyticsPanel.svelte: исправлен доступ к агрегации')

print()
print('=' * 60)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 60)
print()
print('1. Графики пустые:')
print('   • chartData был функцией, теперь вызывается: <Line data={chartData()} />')
print()
print('2. state_snapshot_uncloneable warning:')
print('   • Убраны callbacks из scales.x.ticks и scales.y.ticks')
print('   • Chart.js сам отформатирует метки осей')
print()
print('3. Пустые нормы параметра:')
print('   • Backend теперь возвращает norms: param_data.get("norms", {})')
print('   • Frontend получит нормы из data.trends[param].norms')
print()
print('4. Пустая агрегация:')
print('   • Добавлен optional chaining: data?.aggregation || "auto"')
print()
print('Backend перезагрузится автоматически (hot-reload).')
print('Frontend перезагрузится автоматически (Vite HMR).')
print()
print('Проверка:')
print('  1. Графики должны отображаться с линией тренда')
print('  2. DevTools Console: НЕ должно быть state_snapshot_uncloneable')
print('  3. Вкладка "Проблемы" → раскрыть карточку → должны быть нормы')
print('  4. Вкладка "Рекомендации" → раскрыть карточку → агрегация: hourly')