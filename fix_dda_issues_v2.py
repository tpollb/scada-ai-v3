#!/usr/bin/env python3
"""
fix_dda_issues_v2.py — без subprocess, все 4 проблемы
"""

from pathlib import Path
import re

print('=' * 70)
print('ФИКС 4 ПРОБЛЕМ DDA (v2)')
print('=' * 70)
print()

changes = []

# Проверим что пакеты установлены
package_path = Path('frontend/package.json')
if package_path.exists():
    pkg = package_path.read_text(encoding='utf-8')
    if 'chartjs-plugin-zoom' in pkg:
        print('✓ chartjs-plugin-zoom установлен')
    else:
        print('⚠ chartjs-plugin-zoom НЕ установлен!')
        print('  Запусти: cd frontend && npm install chartjs-plugin-zoom hammerjs')
        print()
if 'hammerjs' in (pkg if package_path.exists() else ''):
    print('✓ hammerjs установлен')

print()

# ============================================================================
# 1. DeepAnalysisControls — добавляем кнопку Х
# ============================================================================
controls_path = Path('frontend/src/components/DeepAnalysisControls.svelte')

new_controls = '''<script lang="ts">
  import { Play, Activity, X } from 'lucide-svelte'

  interface Props {
    tags: any[]
    selectedTag: string
    period: number
    isAnalyzing: boolean
    error: string | null
    onTagChange: (tag: string) => void
    onPeriodChange: (period: number) => void
    onRunAnalysis: () => void
    onClose: () => void
  }

  let { 
    tags, 
    selectedTag, 
    period, 
    isAnalyzing, 
    error,
    onTagChange, 
    onPeriodChange, 
    onRunAnalysis,
    onClose
  }: Props = $props()
</script>

<div class="w-[350px] h-full bg-white dark:bg-neutral-900 border-r border-neutral-200 dark:border-neutral-700 flex flex-col overflow-hidden transition-colors">
  <div class="flex items-center justify-between px-4 py-3 border-b border-neutral-200 dark:border-neutral-700 flex-shrink-0">
    <div class="flex items-center gap-2">
      <Activity size={18} class="text-blue-500" />
      <h2 class="text-base font-semibold text-neutral-900 dark:text-neutral-100">
        Deep Analysis
      </h2>
    </div>
    <button
      type="button"
      onclick={onClose}
      class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition"
      title="Закрыть"
    >
      <X size={16} class="text-neutral-500" />
    </button>
  </div>

  <div class="flex-1 overflow-y-auto px-4 py-3 space-y-3">
    <div>
      <label class="block text-xs font-medium text-neutral-600 dark:text-neutral-400 mb-1">
        Тег
      </label>
      <select
        value={selectedTag}
        onchange={(e) => onTagChange(e.currentTarget.value)}
        class="w-full px-3 py-1.5 text-sm border border-neutral-300 dark:border-neutral-600 rounded bg-white dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        {#each tags as tag}
          <option value={tag.tag_name}>
            {tag.tag_name}
            {#if tag.zone_name}({tag.zone_name}){/if}
          </option>
        {/each}
      </select>
    </div>

    <div>
      <label class="block text-xs font-medium text-neutral-600 dark:text-neutral-400 mb-1">
        Период
      </label>
      <div class="flex gap-1">
        {#each [7, 30, 120, 365] as p}
          <button
            type="button"
            onclick={() => onPeriodChange(p)}
            class="flex-1 px-2 py-1 text-xs rounded transition {period === p
              ? 'bg-blue-500 text-white'
              : 'bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 hover:bg-neutral-200 dark:hover:bg-neutral-700'}"
          >
            {p}д
          </button>
        {/each}
      </div>
    </div>

    <button
      type="button"
      onclick={onRunAnalysis}
      disabled={isAnalyzing || !selectedTag}
      class="w-full px-4 py-2 bg-blue-500 hover:bg-blue-600 disabled:bg-neutral-300 dark:disabled:bg-neutral-700 text-white text-sm font-medium rounded transition flex items-center justify-center gap-2"
    >
      {#if isAnalyzing}
        <div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
        Анализ...
      {:else}
        <Play size={14} />
        Запустить анализ
      {/if}
    </button>

    {#if error}
      <div class="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded text-sm text-red-700 dark:text-red-300">
        {error}
      </div>
    {/if}
  </div>
</div>
'''

controls_path.write_text(new_controls, encoding='utf-8', newline='\n')
changes.append('DeepAnalysisControls: добавлена кнопка Х')
print('✓ DeepAnalysisControls.svelte обновлён')

# ============================================================================
# 2. DeepAnalysisResults — zoom/pan/download
# ============================================================================
results_path = Path('frontend/src/components/DeepAnalysisResults.svelte')

new_results = '''<script lang="ts">
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
    ScatterController,
  } from 'chart.js'
  import zoomPlugin from 'chartjs-plugin-zoom'
  import { TrendingUp, AlertTriangle, Activity, Download, RotateCcw, ZoomIn, ZoomOut } from 'lucide-svelte'

  ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    ScatterController,
    zoomPlugin
  )

  interface Props {
    analysisResult: any
    isAnalyzing: boolean
  }

  let { analysisResult, isAnalyzing }: Props = $props()

  let chartInstance: ChartJS | null = $state(null)
  const chartId = `dda-chart-${Math.random().toString(36).slice(2, 9)}`

  let chartData = $derived(
    analysisResult?.visualizations?.time_series?.data || { labels: [], datasets: [] }
  )

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'top' as const,
        labels: { font: { size: 11 }, boxWidth: 12 }
      },
      tooltip: { mode: 'index' as const, intersect: false },
      zoom: {
        pan: { enabled: true, mode: 'x' as const, modifierKey: null },
        zoom: {
          wheel: { enabled: true, speed: 0.05 },
          pinch: { enabled: true },
          drag: {
            enabled: true,
            modifierKey: 'shift' as const,
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            borderColor: 'rgba(59, 130, 246, 0.5)',
            borderWidth: 1,
          },
          mode: 'x' as const,
        },
      },
    },
    scales: {
      x: {
        display: true,
        grid: { display: false },
        ticks: { maxTicksLimit: 10, font: { size: 10 } }
      },
      y: {
        display: true,
        grid: { color: 'rgba(0, 0, 0, 0.05)' },
        ticks: { font: { size: 10 } }
      }
    },
    interaction: { mode: 'nearest' as const, axis: 'x' as const, intersect: false }
  }

  $effect(() => {
    if (chartData.labels.length > 0) {
      setTimeout(() => {
        const container = document.getElementById(chartId)
        if (container) {
          const canvas = container.querySelector('canvas')
          if (canvas) chartInstance = ChartJS.getChart(canvas) || null
        }
      }, 200)
    }
  })

  function resetZoom() { chartInstance?.resetZoom() }
  function zoomIn() { chartInstance?.zoom(1.2) }
  function zoomOut() { chartInstance?.zoom(0.8) }
  function downloadPNG() {
    if (!chartInstance) return
    const canvas = chartInstance.canvas
    const link = document.createElement('a')
    const tagName = analysisResult?.tags?.[0] || 'analysis'
    const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-')
    link.download = `scada_ai_analysis_${tagName}_${timestamp}.png`
    link.href = canvas.toDataURL('image/png', 1.0)
    link.click()
  }

  function formatNumber(value: number, decimals: number = 2): string {
    return value.toFixed(decimals)
  }
</script>

<div class="flex-1 flex flex-col bg-white dark:bg-neutral-900 overflow-hidden transition-colors">
  {#if isAnalyzing}
    <div class="flex-1 flex items-center justify-center">
      <div class="flex flex-col items-center text-center text-neutral-400 dark:text-neutral-500">
        <div class="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-3"></div>
        <p class="text-sm">Анализируем данные...</p>
      </div>
    </div>
  {:else if analysisResult}
    <div class="flex-1 overflow-y-auto px-6 py-4">
      <div class="mb-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded">
        <p class="text-sm text-blue-900 dark:text-blue-100">{analysisResult.summary}</p>
      </div>

      {#if analysisResult?.statistics && analysisResult.statistics.count > 0}
      <div class="mb-4">
        <h3 class="text-sm font-semibold text-neutral-900 dark:text-neutral-100 mb-2 flex items-center gap-2">
          <TrendingUp size={16} />
          Статистика
        </h3>
        <div class="grid grid-cols-4 gap-2">
          <div class="p-2 bg-neutral-50 dark:bg-neutral-800 rounded">
            <div class="text-xs text-neutral-500 dark:text-neutral-400 mb-1">Среднее</div>
            <div class="text-base font-semibold text-neutral-900 dark:text-neutral-100">
              {formatNumber(analysisResult.statistics.mean)}
            </div>
          </div>
          <div class="p-2 bg-neutral-50 dark:bg-neutral-800 rounded">
            <div class="text-xs text-neutral-500 dark:text-neutral-400 mb-1">Std Dev</div>
            <div class="text-base font-semibold text-neutral-900 dark:text-neutral-100">
              {formatNumber(analysisResult.statistics.std)}
            </div>
          </div>
          <div class="p-2 bg-neutral-50 dark:bg-neutral-800 rounded">
            <div class="text-xs text-neutral-500 dark:text-neutral-400 mb-1">Min</div>
            <div class="text-base font-semibold text-neutral-900 dark:text-neutral-100">
              {formatNumber(analysisResult.statistics.min)}
            </div>
          </div>
          <div class="p-2 bg-neutral-50 dark:bg-neutral-800 rounded">
            <div class="text-xs text-neutral-500 dark:text-neutral-400 mb-1">Max</div>
            <div class="text-base font-semibold text-neutral-900 dark:text-neutral-100">
              {formatNumber(analysisResult.statistics.max)}
            </div>
          </div>
        </div>
      </div>
      {/if}

      {#if analysisResult?.anomalies?.total_anomalies > 0}
        <div class="mb-4">
          <h3 class="text-sm font-semibold text-neutral-900 dark:text-neutral-100 mb-2 flex items-center gap-2">
            <AlertTriangle size={16} class="text-red-500" />
            Аномалии ({analysisResult.anomalies.total_anomalies})
          </h3>
          <div class="text-xs text-neutral-600 dark:text-neutral-400 mb-2">
            Обнаружено {analysisResult.anomalies.total_anomalies} аномальных точек
            ({(analysisResult.anomalies.anomaly_rate * 100).toFixed(1)}% от общего числа)
          </div>
          <div class="space-y-1 max-h-40 overflow-y-auto">
            {#each analysisResult.anomalies.anomaly_values.slice(0, 20) as value, i}
              <div class="flex items-center justify-between p-2 bg-red-50 dark:bg-red-900/20 rounded text-xs">
                <span class="text-red-700 dark:text-red-300 font-mono">{formatNumber(value)}</span>
                <span class="text-neutral-500 dark:text-neutral-400">
                  {new Date(analysisResult.anomalies.anomaly_timestamps[i]).toLocaleString('ru-RU', {
                    day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit'
                  })}
                </span>
              </div>
            {/each}
          </div>
        </div>
      {/if}

      <div class="mb-4">
        <div class="flex items-center justify-between mb-2">
          <h3 class="text-sm font-semibold text-neutral-900 dark:text-neutral-100">График</h3>
          <div class="flex items-center gap-1">
            <button type="button" onclick={zoomIn} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Приблизить">
              <ZoomIn size={14} class="text-neutral-600 dark:text-neutral-400" />
            </button>
            <button type="button" onclick={zoomOut} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Отдалить">
              <ZoomOut size={14} class="text-neutral-600 dark:text-neutral-400" />
            </button>
            <button type="button" onclick={resetZoom} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Сбросить масштаб">
              <RotateCcw size={14} class="text-neutral-600 dark:text-neutral-400" />
            </button>
            <button type="button" onclick={downloadPNG} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Скачать PNG">
              <Download size={14} class="text-neutral-600 dark:text-neutral-400" />
            </button>
          </div>
        </div>
        <div class="text-xs text-neutral-500 dark:text-neutral-400 mb-2">
          💡 Колёсико — zoom · Shift+drag — область · Drag — прокрутка
        </div>
        <div id={chartId} class="h-[350px] bg-white dark:bg-neutral-800 rounded border border-neutral-200 dark:border-neutral-700 p-3">
          {#if chartData.labels.length > 0}
            <Line data={chartData} options={chartOptions} key={analysisResult?.analysis_id || 'default'} />
          {:else}
            <div class="flex items-center justify-center h-full text-sm text-neutral-400">Нет данных</div>
          {/if}
        </div>
      </div>
    </div>
  {:else}
    <div class="flex-1 flex items-center justify-center">
      <div class="flex flex-col items-center text-center text-neutral-400 dark:text-neutral-500">
        <Activity size={48} class="mb-3 opacity-50" />
        <p class="text-sm mb-1">Выберите тег и запустите анализ</p>
        <p class="text-xs">Результаты появятся здесь</p>
      </div>
    </div>
  {/if}
</div>
'''

results_path.write_text(new_results, encoding='utf-8', newline='\n')
changes.append('DeepAnalysisResults: zoom/pan/download')
print('✓ DeepAnalysisResults.svelte обновлён')

# ============================================================================
# 3. Home.svelte — удаляем дубликат + добавляем onClose + layout 50/50
# ============================================================================
home_path = Path('frontend/src/routes/Home.svelte')
lines = home_path.read_text(encoding='utf-8').split('\n')

# 3a. Удаляем блок дубликата на строках 286-288
# Блок: {#if showLogsPanel} + <SystemLogsPanel.../> + {/if}
# Ищем второй (строка 287)
log_block_indices = []
for i, line in enumerate(lines):
    if '<SystemLogsPanel' in line and 'onClose' in line:
        log_block_indices.append(i)

print(f'Найдено SystemLogsPanel: {len(log_block_indices)} раз на строках {[i+1 for i in log_block_indices]}')

if len(log_block_indices) >= 2:
    # Второй — строка 287 (индекс 286). Удаляем весь блок с ним.
    # Ищем открывающий {#if} перед ним и закрывающий {/if} после
    second_idx = log_block_indices[1]
    
    # Ищем {#if showLogsPanel} перед
    if_start = second_idx
    while if_start > 0 and '{#if showLogsPanel}' not in lines[if_start]:
        if_start -= 1
    
    # Ищем {/if} после
    if_end = second_idx
    while if_end < len(lines) and '{/if}' not in lines[if_end]:
        if_end += 1
    
    print(f'Удаляем блок строк {if_start+1}-{if_end+1}')
    
    # Удаляем строки (включая пустые до блока)
    # Находим начало (первая непустая до if_start)
    block_start = if_start
    while block_start > 0 and lines[block_start - 1].strip() == '':
        block_start -= 1
    
    # Конец — после {/if} (убираем trailing пустую строку)
    block_end = if_end + 1
    if block_end < len(lines) and lines[block_end].strip() == '':
        block_end += 1
    
    # Вырезаем
    lines = lines[:block_start] + lines[block_end:]
    changes.append(f'Удалён дубликат SystemLogsPanel (строки {if_start+1}-{if_end+1})')
    print(f'✓ Удалены строки {block_start+1}-{block_end}')

content = '\n'.join(lines)

# 3b. Добавляем onClose в DeepAnalysisControls
old_controls = '''        onRunAnalysis={runDDAAnalysis}
      />'''

new_controls = '''        onRunAnalysis={runDDAAnalysis}
        onClose={() => showDeepAnalysisPanel = false}
      />'''

if old_controls in content and 'onClose={() => showDeepAnalysisPanel = false}' not in content:
    # Заменяем только первый (у DeepAnalysisControls)
    # Ищем блок DeepAnalysisControls и заменяем внутри
    controls_block_start = content.find('<DeepAnalysisControls')
    if controls_block_start >= 0:
        controls_block_end = content.find('/>', controls_block_start) + 2
        controls_block = content[controls_block_start:controls_block_end]
        new_controls_block = controls_block.replace(
            'onRunAnalysis={runDDAAnalysis}\n      />',
            'onRunAnalysis={runDDAAnalysis}\n        onClose={() => showDeepAnalysisPanel = false}\n      />'
        )
        content = content[:controls_block_start] + new_controls_block + content[controls_block_end:]
        changes.append('DeepAnalysisControls: добавлен prop onClose')
        print('✓ Добавлен onClose в DeepAnalysisControls')

# 3c. Меняем layout — DDA сверху (50%), чат снизу (всегда)
# Ищем старый блок:
#   <div class="flex-1 flex flex-col bg-white dark:bg-neutral-900 overflow-hidden transition-colors">
#     {#if showDeepAnalysisPanel}
#       <DeepAnalysisResults ...
#       />
#     {:else}
#   ...
#     </div>

old_layout = '''    <div class="flex-1 flex flex-col bg-white dark:bg-neutral-900 overflow-hidden transition-colors">
      {#if showDeepAnalysisPanel}
        <DeepAnalysisResults
          analysisResult={ddaAnalysisResult}
          isAnalyzing={ddaIsAnalyzing}
        />
      {:else}

      <div class="flex-1 overflow-y-auto">
        <NarrativePanel />
      </div>
      {#if currentWidgets.length > 0}
        <WidgetRouter widgets={currentWidgets} onClose={handleCloseWidgets} />
      {/if}
      <Input onSend={handleSend} />
    </div>'''

new_layout = '''    <div class="flex-1 flex flex-col bg-white dark:bg-neutral-900 overflow-hidden transition-colors">
      {#if showDeepAnalysisPanel}
        <div class="h-1/2 overflow-hidden border-b border-neutral-200 dark:border-neutral-700">
          <DeepAnalysisResults
            analysisResult={ddaAnalysisResult}
            isAnalyzing={ddaIsAnalyzing}
          />
        </div>
      {/if}
      <div class="flex-1 flex flex-col overflow-hidden">
        <div class="flex-1 overflow-y-auto">
          <NarrativePanel />
        </div>
        {#if currentWidgets.length > 0}
          <WidgetRouter widgets={currentWidgets} onClose={handleCloseWidgets} />
        {/if}
        <Input onSend={handleSend} />
      </div>
    </div>'''

if old_layout in content:
    content = content.replace(old_layout, new_layout)
    changes.append('Layout: DDA 50% сверху, чат снизу всегда')
    print('✓ Layout исправлен')
else:
    print('⚠ Не найден старый layout блок (возможно структура изменилась)')
    # Попробуем найти и показать текущую структуру
    if 'showDeepAnalysisPanel' in content and '{:else}' in content:
        idx = content.find('{:else}')
        context = content[max(0, idx-200):idx+400]
        print()
        print('Текущая структура вокруг {:else}:')
        print('-' * 60)
        print(context)
        print('-' * 60)

# Сохраняем
home_path.write_text(content, encoding='utf-8', newline='\n')

# Финальная проверка
content_check = home_path.read_text(encoding='utf-8')
open_divs = len(re.findall(r'<div(?:\s|>)', content_check))
close_divs = len(re.findall(r'</div>', content_check))
open_ifs = len(re.findall(r'\{#if\b', content_check))
close_ifs = len(re.findall(r'\{/if\}', content_check))

print()
print('=' * 70)
print('ИТОГ:')
print('=' * 70)
for i, c in enumerate(changes, 1):
    print(f'  {i}. ✓ {c}')

print()
print(f'Баланс <div>: {open_divs}/{close_divs} {"✅" if open_divs == close_divs else "❌"}')
print(f'Баланс {{#if}}: {open_ifs}/{close_ifs} {"✅" if open_ifs == close_ifs else "❌"}')

if open_divs == close_divs and open_ifs == close_ifs:
    print()
    print('✅ БАЛАНС OK — ошибка компиляции не должна возникнуть!')
else:
    print()
    print('⚠ Есть дисбаланс, запусти:')
    print('  sed -n "268,310p" frontend/src/routes/Home.svelte')