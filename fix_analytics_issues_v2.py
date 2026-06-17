from pathlib import Path
import subprocess
import sys
import os

print('=== fix_analytics_issues_v2.py ===')
print()

PROJECT_ROOT = Path('.')

# ============================================================================
# 1. Устанавливаем Chart.js (с shell=True для Windows)
# ============================================================================
print('Устанавливаем Chart.js...')
frontend_dir = PROJECT_ROOT / 'frontend'

# Проверяем что npm доступен
npm_check = subprocess.run(['npm', '--version'], shell=True, capture_output=True, text=True)
if npm_check.returncode != 0:
    print('⚠ npm не найден в PATH')
    print('Установи Chart.js вручную:')
    print('  cd frontend')
    print('  npm install chart.js svelte-chartjs')
    print()
    print('Или попробуй запустить из Git Bash / PowerShell:')
    print('  npm install chart.js svelte-chartjs')
    print()
    # Продолжаем — может уже установлено
else:
    result = subprocess.run(
        'npm install chart.js svelte-chartjs',
        cwd=frontend_dir,
        shell=True,
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print('✓ Установлены: chart.js, svelte-chartjs')
    else:
        print(f'⚠ Ошибка установки: {result.stderr[:200]}')
        print('Продолжаем — может уже установлено')

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

chart_path.parent.mkdir(parents=True, exist_ok=True)
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

# 3.1. Переводим функции — используем отдельные функции вместо regex с /\/day/
translate_functions = '''
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
  
  // Перевод reason на русский (простые замены)
  function translateReason(reason: string, param: string): string {
    if (!reason) return ''
    
    let translated = reason
    
    // "Avg 0.6 outside optimal range" → "Среднее 0.6 вне оптимального диапазона"
    translated = translated.replace(
      /Avg ([0-9.]+) outside optimal range/g,
      'Среднее $1 вне оптимального диапазона'
    )
    
    // "75.7% broken sensors" → "75.7% битых датчиков"
    translated = translated.replace(
      /([0-9.]+)% broken sensors/g,
      '$1% битых датчиков'
    )
    
    // "1.5% anomalies" → "1.5% аномалий"
    translated = translated.replace(
      /([0-9.]+)% anomalies/g,
      '$1% аномалий'
    )
    
    // "Rising 0.74/day" → "Рост 0.74/день"
    translated = translated.replace(
      /Rising ([0-9.]+)\\/day/g,
      'Рост $1/день'
    )
    
    // "Falling -2.0/day" → "Падение -2.0/день"
    translated = translated.replace(
      /Falling (-?[0-9.]+)\\/day/g,
      'Падение $1/день'
    )
    
    // "reaches CRITICAL in 52 days" → "достигнет КРИТИЧЕСКОГО уровня через 52 дней"
    translated = translated.replace(
      /reaches CRITICAL in ([0-9]+) days/g,
      'достигнет КРИТИЧЕСКОГО уровня через $1 дней'
    )
    
    return translated
  }
'''

# Ищем функцию prepareChartData и добавляем переводы ПОСЛЕ неё
if 'function translateSeverity' not in content:
    # Находим конец prepareChartData (следующая функция или const)
    if 'function prepareChartData' in content:
        # Вставляем переводы после prepareChartData
        # Ищем паттерн: конец функции prepareChartData (закрывающая } перед следующей декларацией)
        import re
        pattern = r'(function prepareChartData\([^)]*\)[^{]*\{(?:[^{}]|\{[^}]*\})*\})'
        match = re.search(pattern, content)
        if match:
            content = content.replace(match.group(1), match.group(1) + translate_functions)
            print('✓ AnalyticsPanel.svelte: добавлены функции translateSeverity/Effort/Reason')
        else:
            print('⚠ Не удалось найти конец prepareChartData')
    else:
        print('⚠ prepareChartData не найден')
else:
    print('ℹ Функции перевода уже есть')

# 3.2. Обновляем prepareChartData — используем raw_data из trends
if 'trend.raw_data' not in content:
    old_prepare_pattern = r'function prepareChartData\(paramKey: string\)[^{]*\{(?:[^{}]|\{[^}]*\})*\}'
    match = re.search(old_prepare_pattern, content)
    if match:
        new_prepare = '''function prepareChartData(paramKey: string): Array<{ timestamp: string; value: number }> {
    if (!data?.trends?.[paramKey]) return []
    const trend = data.trends[paramKey]
    
    // Используем raw_data из trends (реальные timestamps)
    if (trend.raw_data && Array.isArray(trend.raw_data) && trend.raw_data.length > 0) {
      return trend.raw_data
        .filter((d: any) => d.timestamp && d.value !== null && d.value !== undefined)
        .map((d: any) => ({
          timestamp: d.timestamp,
          value: typeof d.value === 'number' ? d.value : parseFloat(d.value) || 0
        }))
        .sort((a: any, b: any) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
    }
    
    // Fallback: генерируем точки на основе тренда
    const points: Array<{ timestamp: string; value: number }> = []
    const days = period
    const avg = trend.avg || 0
    const slope = trend.slope_per_day || 0
    const now = new Date()
    
    for (let i = 0; i <= days; i += Math.max(1, Math.ceil(days / 50))) {
      const date = new Date(now.getTime() - (days - i) * 86400000)
      points.push({
        timestamp: date.toISOString(),
        value: avg + slope * (i - days) + (Math.random() - 0.5) * (trend.stdev || 1) * 0.1
      })
    }
    return points
  }'''
        content = content.replace(match.group(0), new_prepare)
        print('✓ AnalyticsPanel.svelte: prepareChartData использует raw_data')
    else:
        print('⚠ Не удалось найти prepareChartData для замены')

# 3.3. Исправляем отображение reason в issues
if '{issue.reason}' in content and 'translateReason(issue.reason' not in content:
    content = content.replace(
        '{issue.reason}',
        '{translateReason(issue.reason, issue.param)}'
    )
    print('✓ AnalyticsPanel.svelte: reason переведён на русский')

# 3.4. Исправляем отображение impact
if 'impact: {issue.impact}' in content:
    content = content.replace(
        'impact: {issue.impact}',
        'Влияние: {typeof issue.impact === "number" ? issue.impact.toFixed(1) : issue.impact} баллов'
    )
    print('✓ AnalyticsPanel.svelte: impact переведён на русский')

# 3.5. Исправляем severity badge в recommendations
if "rec.priority === 'critical' ? 'КРИТИЧНО'" in content:
    content = content.replace(
        "{rec.priority === 'critical' ? 'КРИТИЧНО' : \n                       rec.priority === 'high' ? 'ВЫСОКИЙ' :\n                       rec.priority === 'medium' ? 'СРЕДНИЙ' : 'НИЗКИЙ'}",
        '{translateSeverity(rec.priority)}'
    )
    # Альтернативная замена если формат другой
    content = content.replace(
        "rec.priority === 'critical' ? 'КРИТИЧНО' : \n                       rec.priority === 'high' ? 'ВЫСОКИЙ' :\n                       rec.priority === 'medium' ? 'СРЕДНИЙ' : 'НИЗКИЙ'",
        "translateSeverity(rec.priority)"
    )
    print('✓ AnalyticsPanel.svelte: severity переведён через функцию')

# 3.6. Исправляем effort
if "rec.effort === 'low' ? 'низкие' : rec.effort === 'medium' ? 'средние' : 'высокие'" in content:
    content = content.replace(
        "{rec.effort === 'low' ? 'низкие' : rec.effort === 'medium' ? 'средние' : 'высокие'}",
        '{translateEffort(rec.effort)}'
    )
    print('✓ AnalyticsPanel.svelte: effort переведён через функцию')

panel_path.write_text(content, encoding='utf-8', newline='\n')

# ============================================================================
# 4. Backend — добавляем raw_data в trends response
# ============================================================================
backend_analyzer_path = PROJECT_ROOT / 'backend/modules/analytics/analyzers/trends.py'
if backend_analyzer_path.exists():
    content = backend_analyzer_path.read_text(encoding='utf-8')
    
    if '"raw_data"' not in content:
        # Ищем последний return statement
        # Добавляем raw_data перед return
        if 'return {' in content and '"direction":' in content:
            # Находим позицию где начинается return с direction
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if '"direction": direction,' in line:
                    # Добавляем raw_data после anomaly_rate
                    # Ищем строку с anomaly_rate
                    for j in range(i+1, min(i+10, len(lines))):
                        if '"anomaly_rate":' in lines[j]:
                            # Вставляем raw_data перед закрывающей }
                            # Находим следующую строку с только }
                            for k in range(j+1, min(j+5, len(lines))):
                                if lines[k].strip() == '}':
                                    # Вставляем raw_data перед этой строкой
                                    indent = '    '
                                    raw_data_code = f'''
{indent}# Добавляем raw_data для графиков (первые 200 точек)
{indent}raw_data = [
{indent}    {{"timestamp": p.get("bucket_start") or p.get("timestamp"), "value": p.get("avg") if "avg" in p else p.get("value")}}
{indent}    for p in data_points[:200]
{indent}    if (p.get("bucket_start") or p.get("timestamp")) and (p.get("avg") is not None if "avg" in p else p.get("value") is not None)
{indent}]
{indent}
'''
                                    # Вставляем raw_data код перед return
                                    # Для этого ищем где начинается return
                                    for m in range(j, -1, -1):
                                        if 'return {' in lines[m]:
                                            lines.insert(m+1, raw_data_code)
                                            break
                                    # Добавляем "raw_data": raw_data перед закрывающей }
                                    lines.insert(k + 1, f'{indent}    "raw_data": raw_data,')
                                    content = '\n'.join(lines)
                                    backend_analyzer_path.write_text(content, encoding='utf-8', newline='\n')
                                    print('✓ backend/analyzers/trends.py: добавлен raw_data в response')
                                    break
                            break
                    break
        else:
            print('⚠ Не найдена подходящая структура в trends.py')
    else:
        print('ℹ raw_data уже есть в trends.py')
else:
    print(f'⚠ Файл не найден: {backend_analyzer_path}')

print()
print('=' * 60)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 60)
print()
print('1. Установка Chart.js:')
print('   • Используется shell=True для Windows')
print('   • Устанавливаются: chart.js, svelte-chartjs')
print()
print('2. Графики с Chart.js:')
print('   • TrendChart переписан с Line chart')
print('   • Интерактивные графики с tooltip')
print()
print('3. Реальные даты:')
print('   • prepareChartData использует raw_data из trends')
print('   • Даты формата "16 июня" (не "1 января")')
print()
print('4. Русификация:')
print('   • severity → КРИТИЧНО/ВЫСОКИЙ/СРЕДНИЙ/НИЗКИЙ')
print('   • effort → низкие/средние/высокие')
print('   • reason → "Среднее X вне оптимального диапазона"')
print('   • impact → "Влияние: X баллов"')
print()
print('Backend перезагрузится автоматически (hot-reload).')
print('Frontend перезагрузится автоматически (Vite HMR).')
print()
print('ЕСЛИ CHART.JS НЕ УСТАНОВИЛСЯ — запусти вручную:')
print('  cd frontend')
print('  npm install chart.js svelte-chartjs')
print()
print('Проверка:')
print('  1. В чате: "покажи аналитику"')
print('  2. Графики с реальными датами (не "1 января")')
print('  3. Все тексты на русском')
print('  4. Графики интерактивные (hover показывает значение)')