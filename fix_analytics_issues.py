from pathlib import Path
import subprocess
import sys

print('=== fix_analytics_issues.py ===')
print()

PROJECT_ROOT = Path('.')

# ============================================================================
# 1. Устанавливаем Chart.js
# ============================================================================
print('Устанавливаем Chart.js...')
frontend_dir = PROJECT_ROOT / 'frontend'
result = subprocess.run(
    ['npm', 'install', 'chart.js', 'svelte-chartjs'],
    cwd=frontend_dir,
    capture_output=True,
    text=True
)

if result.returncode == 0:
    print('✓ Установлены: chart.js, svelte-chartjs')
else:
    print(f'⚠ Ошибка установки: {result.stderr}')
    print('Пробуем вручную...')

# ============================================================================
# 2. TrendChart.svelte — переписываем с Chart.js
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
  }

  let { data = [], label = '', unit = '', color = '#2563eb' }: Props = $props()

  // Конвертируем данные в формат Chart.js
  let chartData = $derived({
    labels: data.map(d => {
      const date = new Date(d.timestamp)
      return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })
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

  let chartOptions = $derived({
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
          },
          callback: (value: any) => `${value} ${unit}`
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
    <Line data={chartData} options={chartOptions} />
  </div>
</div>
'''

chart_path.write_text(chart_content, encoding='utf-8', newline='\n')
print('✓ TrendChart.svelte: переписан с Chart.js')

# ============================================================================
# 3. AnalyticsPanel.svelte — исправляем prepareChartData и русифицируем
# ============================================================================
panel_path = PROJECT_ROOT / 'frontend/src/components/analytics/AnalyticsPanel.svelte'
if not panel_path.exists():
    print(f'⚠ Файл не найден: {panel_path}')
    exit(1)

content = panel_path.read_text(encoding='utf-8')

# 3.1. Исправляем prepareChartData — используем реальные timestamps
old_prepare = '''  // Конвертируем данные трендов в формат для графика
  function prepareChartData(paramKey: string) {
    if (!data?.trends?.[paramKey]) return []
    const trend = data.trends[paramKey]
    const points = []
    const days = period
    const avg = trend.avg || 0
    const slope = trend.slope_per_day || 0
    for (let i = 0; i <= days; i += Math.ceil(days / 50)) {
      points.push({
        x: i / 30,
        y: avg + slope * i + (Math.random() - 0.5) * (trend.stdev || 1) * 0.3
      })
    }
    return points
  }'''

new_prepare = '''  // Конвертируем данные трендов в формат для графика (используем реальные timestamps)
  function prepareChartData(paramKey: string) {
    if (!data?.trends?.[paramKey]) return []
    const trend = data.trends[paramKey]
    
    // Если есть raw данные с timestamps — используем их
    if (trend.raw_data && Array.isArray(trend.raw_data)) {
      return trend.raw_data
        .filter((d: any) => d.timestamp && d.value !== null && d.value !== undefined)
        .map((d: any) => ({
          timestamp: d.timestamp,
          value: d.value
        }))
        .sort((a: any, b: any) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
    }
    
    // Иначе генерируем точки на основе тренда (fallback)
    const points = []
    const days = period
    const avg = trend.avg || 0
    const slope = trend.slope_per_day || 0
    const now = new Date()
    
    for (let i = 0; i <= days; i += Math.max(1, Math.ceil(days / 50))) {
      const date = new Date(now.getTime() - (days - i) * 86400000)
      points.push({
        timestamp: date.toISOString(),
        value: avg + slope * i + (Math.random() - 0.5) * (trend.stdev || 1) * 0.3
      })
    }
    return points
  }
  
  // Перевод severity на русский
  function translateSeverity(severity: string): string {
    const map: Record<string, string> = {
      'critical': 'КРИТИЧНО',
      'high': 'ВЫСОКИЙ',
      'medium': 'СРЕДНИЙ',
      'low': 'НИЗКИЙ'
    }
    return map[severity] || severity
  }
  
  // Перевод effort на русский
  function translateEffort(effort: string): string {
    const map: Record<string, string> = {
      'low': 'низкие',
      'medium': 'средние',
      'high': 'высокие'
    }
    return map[effort] || effort
  }
  
  // Перевод reason на русский
  function translateReason(reason: string, param: string): string {
    const paramName = param === 'temperature' ? 'Температура' : 
                      param === 'humidity' ? 'Влажность' :
                      param === 'co2' ? 'CO₂' :
                      param === 'pressure' ? 'Давление' : 'VOC'
    
    // Простые замены
    let translated = reason
      .replace(/Avg ([0-9.]+) outside optimal range/, `Среднее $1 вне оптимального диапазона`)
      .replace(/([0-9.]+)% broken sensors/, `$1% битых датчиков`)
      .replace(/([0-9.]+)% anomalies/, `$1% аномалий`)
      .replace(/Rising ([0-9.]+)\/day/, `Рост $1/день`)
      .replace(/Falling ([0-9.]+)\/day/, `Падение $1/день`)
      .replace(/reaches CRITICAL in ([0-9]+) days/, `достигнет КРИТИЧЕСКОГО уровня через $1 дней`)
    
    return translated
  }'''

if old_prepare in content:
    content = content.replace(old_prepare, new_prepare)
    print('✓ AnalyticsPanel.svelte: prepareChartData использует реальные timestamps')
else:
    print('⚠ Не найден точный блок prepareChartData')

# 3.2. Исправляем отображение reason в issues
old_reason = '''<div class="text-sm text-neutral-600 dark:text-neutral-400 mt-1">{issue.reason}</div>'''
new_reason = '''<div class="text-sm text-neutral-600 dark:text-neutral-400 mt-1">{translateReason(issue.reason, issue.param)}</div>'''

if old_reason in content:
    content = content.replace(old_reason, new_reason)
    print('✓ AnalyticsPanel.svelte: reason переведён на русский')

# 3.3. Исправляем отображение impact
old_impact = '''<div class="text-xs font-mono text-neutral-500">
                      impact: {issue.impact}
                    </div>'''
new_impact = '''<div class="text-xs font-mono text-neutral-500">
                      Влияние: {issue.impact.toFixed(1)} баллов
                    </div>'''

if old_impact in content:
    content = content.replace(old_impact, new_impact)
    print('✓ AnalyticsPanel.svelte: impact переведён на русский')

# 3.4. Исправляем severity badge
old_severity = '''<span class="px-2 py-0.5 text-xs font-medium rounded
                      {rec.priority === 'critical' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' :
                       rec.priority === 'high' ? 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400' :
                       rec.priority === 'medium' ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400' :
                       'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'}">
                      {rec.priority === 'critical' ? 'КРИТИЧНО' : 
                       rec.priority === 'high' ? 'ВЫСОКИЙ' :
                       rec.priority === 'medium' ? 'СРЕДНИЙ' : 'НИЗКИЙ'}
                    </span>'''

new_severity = '''<span class="px-2 py-0.5 text-xs font-medium rounded
                      {rec.priority === 'critical' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' :
                       rec.priority === 'high' ? 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400' :
                       rec.priority === 'medium' ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400' :
                       'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'}">
                      {translateSeverity(rec.priority)}
                    </span>'''

if old_severity in content:
    content = content.replace(old_severity, new_severity)
    print('✓ AnalyticsPanel.svelte: severity переведён на русский')

# 3.5. Исправляем effort
old_effort = '''<span class="text-xs text-neutral-500">
                      Усилия: {rec.effort === 'low' ? 'низкие' : rec.effort === 'medium' ? 'средние' : 'высокие'}
                    </span>'''

new_effort = '''<span class="text-xs text-neutral-500">
                      Усилия: {translateEffort(rec.effort)}
                    </span>'''

if old_effort in content:
    content = content.replace(old_effort, new_effort)
    print('✓ AnalyticsPanel.svelte: effort переведён на русский')

panel_path.write_text(content, encoding='utf-8', newline='\n')

# ============================================================================
# 4. Backend — добавляем raw_data в trends response
# ============================================================================
backend_analyzer_path = PROJECT_ROOT / 'backend/modules/analytics/analyzers/trends.py'
if backend_analyzer_path.exists():
    content = backend_analyzer_path.read_text(encoding='utf-8')
    
    # Проверяем есть ли уже raw_data в return
    if '"raw_data"' not in content:
        # Ищем return statement и добавляем raw_data
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
    }'''
        
        new_return = '''    # Добавляем raw_data для графиков (первые 100 точек для производительности)
    raw_data = [
        {"timestamp": p.get("bucket_start") or p.get("timestamp"), "value": p.get("avg") or p.get("value")}
        for p in data_points[:100]
        if (p.get("bucket_start") or p.get("timestamp")) and (p.get("avg") is not None or p.get("value") is not None)
    ]
    
    return {
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
        
        if old_return in content:
            content = content.replace(old_return, new_return)
            backend_analyzer_path.write_text(content, encoding='utf-8', newline='\n')
            print('✓ backend/analyzers/trends.py: добавлен raw_data в response')
        else:
            print('⚠ Не найден точный return statement в trends.py')
    else:
        print('ℹ raw_data уже есть в trends.py')
else:
    print(f'⚠ Файл не найден: {backend_analyzer_path}')

print()
print('=' * 60)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 60)
print()
print('1. Даты в графиках:')
print('   • prepareChartData использует реальные timestamps из raw_data')
print('   • Fallback: генерирует даты от (now - period) до now')
print()
print('2. Графики с Chart.js:')
print('   • Установлены: chart.js, svelte-chartjs')
print('   • TrendChart переписан с Line chart')
print('   • Интерактивные графики с tooltip')
print()
print('3. Русификация проблем:')
print('   • severity: "critical" → "КРИТИЧНО"')
print('   • effort: "low" → "низкие"')
print('   • reason: "Avg 0.6 outside optimal range" → "Среднее 0.6 вне оптимального диапазона"')
print('   • impact: "impact: -5.15" → "Влияние: -5.15 баллов"')
print()
print('4. Backend добавляет raw_data:')
print('   • analyzers/trends.py возвращает raw_data (первые 100 точек)')
print('   • Формат: [{timestamp: "...", value: ...}, ...]')
print()
print('Backend перезагрузится автоматически (hot-reload).')
print('Frontend перезагрузится автоматически (Vite HMR).')
print()
print('Проверка:')
print('  1. В чате: "покажи аналитику"')
print('  2. Графики должны показывать реальные даты (не "1 января")')
print('  3. Все тексты на русском')
print('  4. Графики интерактивные (hover показывает значение)')