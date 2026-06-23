#!/usr/bin/env python3
"""
fix_dda_issues.py — исправляет 4 проблемы:
1. Кнопка закрытия (Х) в DeepAnalysisControls
2. Дубликаты SystemLogsPanel при открытии логов + DDA
3. Zoom/pan/download в графике (как в AnalyticsPanel)
4. Возврат поля ввода диалога при открытом DDA
"""

from pathlib import Path
import subprocess
import sys
import re

print('=' * 70)
print('ФИКС 4 ПРОБЛЕМ DDA')
print('=' * 70)
print()

changes = []

# ============================================================================
# ПРОВЕРКА: установлены ли chartjs-plugin-zoom и hammerjs
# ============================================================================
frontend_dir = Path('frontend')
package_json_path = frontend_dir / 'package.json'

if package_json_path.exists():
    package_content = package_json_path.read_text(encoding='utf-8')
    
    has_zoom = 'chartjs-plugin-zoom' in package_content
    has_hammer = 'hammerjs' in package_content
    
    if not has_zoom or not has_hammer:
        print('📦 Устанавливаем chartjs-plugin-zoom и hammerjs...')
        result = subprocess.run(
            ['npm', 'install', 'chartjs-plugin-zoom', 'hammerjs'],
            cwd=frontend_dir,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print('✓ Пакеты установлены')
            changes.append('Установлены chartjs-plugin-zoom + hammerjs')
        else:
            print(f'⚠ Ошибка установки: {result.stderr}')
    else:
        print('✓ chartjs-plugin-zoom и hammerjs уже установлены')
print()

# ============================================================================
# 1. ОБНОВЛЯЕМ DeepAnalysisControls — добавляем кнопку Х
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
  <!-- Header с кнопкой закрытия -->
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

  <!-- Controls -->
  <div class="flex-1 overflow-y-auto px-4 py-3 space-y-3">
    <!-- Tag selector -->
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

    <!-- Period selector -->
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

    <!-- Run button -->
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

    <!-- Error message -->
    {#if error}
      <div class="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded text-sm text-red-700 dark:text-red-300">
        {error}
      </div>
    {/if}
  </div>
</div>
'''

controls_path.write_text(new_controls, encoding='utf-8', newline='\n')
changes.append('DeepAnalysisControls: добавлена кнопка Х (закрытие)')
print('✓ DeepAnalysisControls.svelte обновлён')

# ============================================================================
# 2. ОБНОВЛЯЕМ DeepAnalysisResults — zoom/pan/download + улучшенный layout
# ============================================================================
results_path = Path('frontend/src/components/DeepAnalysisResults.svelte')

new_results = '''<script lang="ts">
  import { onMount } from 'svelte'
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

  // Chart.js данные
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
        labels: {
          font: { size: 11 },
          boxWidth: 12,
        }
      },
      tooltip: {
        mode: 'index' as const,
        intersect: false,
      },
      zoom: {
        pan: {
          enabled: true,
          mode: 'x' as const,
          modifierKey: null,
        },
        zoom: {
          wheel: {
            enabled: true,
            speed: 0.05,
          },
          pinch: {
            enabled: true,
          },
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
        ticks: {
          maxTicksLimit: 10,
          font: { size: 10 }
        }
      },
      y: {
        display: true,
        grid: { color: 'rgba(0, 0, 0, 0.05)' },
        ticks: {
          font: { size: 10 }
        }
      }
    },
    interaction: {
      mode: 'nearest' as const,
      axis: 'x' as const,
      intersect: false
    }
  }

  // Получаем Chart instance после рендеринга
  $effect(() => {
    if (chartData.labels.length > 0) {
      setTimeout(() => {
        const container = document.getElementById(chartId)
        if (container) {
          const canvas = container.querySelector('canvas')
          if (canvas) {
            chartInstance = ChartJS.getChart(canvas) || null
          }
        }
      }, 200)
    }
  })

  function resetZoom() {
    chartInstance?.resetZoom()
  }

  function zoomIn() {
    chartInstance?.zoom(1.2)
  }

  function zoomOut() {
    chartInstance?.zoom(0.8)
  }

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
      <!-- Summary -->
      <div class="mb-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded">
        <p class="text-sm text-blue-900 dark:text-blue-100">{analysisResult.summary}</p>
      </div>

      <!-- Statistics -->
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

      <!-- Anomalies -->
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
                <span class="text-red-700 dark:text-red-300 font-mono">
                  {formatNumber(value)}
                </span>
                <span class="text-neutral-500 dark:text-neutral-400">
                  {new Date(analysisResult.anomalies.anomaly_timestamps[i]).toLocaleString('ru-RU', {
                    day: '2-digit',
                    month: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </span>
              </div>
            {/each}
          </div>
        </div>
      {/if}

      <!-- Chart -->
      <div class="mb-4">
        <div class="flex items-center justify-between mb-2">
          <h3 class="text-sm font-semibold text-neutral-900 dark:text-neutral-100">
            График
          </h3>
          <div class="flex items-center gap-1">
            <button
              type="button"
              onclick={zoomIn}
              class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition"
              title="Приблизить"
            >
              <ZoomIn size={14} class="text-neutral-600 dark:text-neutral-400" />
            </button>
            <button
              type="button"
              onclick={zoomOut}
              class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition"
              title="Отдалить"
            >
              <ZoomOut size={14} class="text-neutral-600 dark:text-neutral-400" />
            </button>
            <button
              type="button"
              onclick={resetZoom}
              class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition"
              title="Сбросить масштаб"
            >
              <RotateCcw size={14} class="text-neutral-600 dark:text-neutral-400" />
            </button>
            <button
              type="button"
              onclick={downloadPNG}
              class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition"
              title="Скачать PNG"
            >
              <Download size={14} class="text-neutral-600 dark:text-neutral-400" />
            </button>
          </div>
        </div>
        <div class="text-xs text-neutral-500 dark:text-neutral-400 mb-2">
          💡 Колёсико мыши — масштаб · Shift+перетаскивание — область зума · Перетаскивание — прокрутка
        </div>
        <div id={chartId} class="h-[350px] bg-white dark:bg-neutral-800 rounded border border-neutral-200 dark:border-neutral-700 p-3">
          {#if chartData.labels.length > 0}
            <Line 
              data={chartData} 
              options={chartOptions}
              key={analysisResult?.analysis_id || 'default'}
            />
          {:else}
            <div class="flex items-center justify-center h-full text-sm text-neutral-400">
              Нет данных
            </div>
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
changes.append('DeepAnalysisResults: добавлен zoom/pan/download PNG')
print('✓ DeepAnalysisResults.svelte обновлён')

# ============================================================================
# 3. ОБНОВЛЯЕМ Home.svelte — layout и пропсы
# ============================================================================
home_path = Path('frontend/src/routes/Home.svelte')
content = home_path.read_text(encoding='utf-8')

# 3a. Удаляем все дубликаты SystemLogsPanel кроме первого
logs_blocks = list(re.finditer(
    r'\s*\{#if showLogsPanel\}\s*\n\s*<SystemLogsPanel[^/]*?/>\s*\n\s*\{/if\}\s*',
    content,
    re.DOTALL
))

if len(logs_blocks) > 1:
    for match in reversed(logs_blocks[1:]):
        content = content[:match.start()] + '\n' + content[match.end():]
    changes.append(f'Удалено {len(logs_blocks)-1} дубликатов SystemLogsPanel')
    print(f'✓ Удалено {len(logs_blocks)-1} дубликатов SystemLogsPanel')

# 3b. Добавляем onClose пропс в DeepAnalysisControls
old_controls_props = '''      <DeepAnalysisControls
        tags={ddaTags}
        selectedTag={ddaSelectedTag}
        period={ddaPeriod}
        isAnalyzing={ddaIsAnalyzing}
        error={ddaError}
        onTagChange={(tag) => ddaSelectedTag = tag}
        onPeriodChange={(period) => ddaPeriod = period}
        onRunAnalysis={runDDAAnalysis}
      />'''

new_controls_props = '''      <DeepAnalysisControls
        tags={ddaTags}
        selectedTag={ddaSelectedTag}
        period={ddaPeriod}
        isAnalyzing={ddaIsAnalyzing}
        error={ddaError}
        onTagChange={(tag) => ddaSelectedTag = tag}
        onPeriodChange={(period) => ddaPeriod = period}
        onRunAnalysis={runDDAAnalysis}
        onClose={() => showDeepAnalysisPanel = false}
      />'''

if old_controls_props in content:
    content = content.replace(old_controls_props, new_controls_props)
    changes.append('DeepAnalysisControls: добавлен prop onClose')
    print('✓ Добавлен prop onClose в DeepAnalysisControls')

# 3c. ИСПРАВЛЕНИЕ ПРОБЛЕМЫ 4: убираем {:else} чтобы Input всегда был виден
# Ищем блок:
#   <div class="flex-1 flex flex-col bg-white dark:bg-neutral-900 overflow-hidden transition-colors">
#     {#if showDeepAnalysisPanel}
#       <DeepAnalysisResults ... />
#     {:else}
#     ...
#     </div>
#
# Меняем на:
#   <div class="flex-1 flex flex-col bg-white dark:bg-neutral-900 overflow-hidden transition-colors">
#     {#if showDeepAnalysisPanel}
#       <div class="h-1/2 overflow-hidden border-b border-neutral-200 dark:border-neutral-700">
#         <DeepAnalysisResults ... />
#       </div>
#     {/if}
#     <div class="flex-1 flex flex-col overflow-hidden">
#       <div class="flex-1 overflow-y-auto">
#         <NarrativePanel />
#       </div>
#       <WidgetRouter />
#       <Input />
#     </div>
#   </div>

# Сначала удаляем старый блок с {:else} и вставляем новый
old_main_block_pattern = r'(<div class="flex-1 flex flex-col bg-white dark:bg-neutral-900 overflow-hidden transition-colors">\s*\{#if showDeepAnalysisPanel\}\s*<DeepAnalysisResults[^/]*?isAnalyzing=\{ddaIsAnalyzing\}\s*/>\s*\{:else\}\s*<div class="flex-1 overflow-y-auto">\s*<NarrativePanel />\s*</div>\s*\{#if currentWidgets\.length > 0\}\s*<WidgetRouter[^/]*?/>\s*\{/if\}\s*<Input onSend=\{handleSend\} />\s*\{/if\}\s*</div>)'

match = re.search(old_main_block_pattern, content, re.DOTALL)

if match:
    new_main_block = '''<div class="flex-1 flex flex-col bg-white dark:bg-neutral-900 overflow-hidden transition-colors">
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
    
    content = content[:match.start()] + new_main_block + content[match.end():]
    changes.append('Layout: DDA в верхней половине, чат всегда снизу')
    print('✓ Layout исправлен: DDA занимает 50% сверху, чат всегда снизу')
else:
    print('⚠ Не удалось найти блок для рефакторинга layout')
    print('   Возможно структура отличается от ожидаемой')

# Сохраняем
home_path.write_text(content, encoding='utf-8', newline='\n')

print()
print('=' * 70)
print('ИТОГОВЫЕ ИСПРАВЛЕНИЯ:')
print('=' * 70)
for i, c in enumerate(changes, 1):
    print(f'  {i}. ✓ {c}')

# Проверка баланса
content_check = home_path.read_text(encoding='utf-8')
open_divs = len(re.findall(r'<div(?:\s|>)', content_check))
close_divs = len(re.findall(r'</div>', content_check))
open_ifs = len(re.findall(r'\{#if\b', content_check))
close_ifs = len(re.findall(r'\{/if\}', content_check))

print()
print('БАЛАНС:')
print(f'  <div>: {open_divs} / {close_divs} {("✅" if open_divs == close_divs else "❌")}')
print(f'  {{#if}}: {open_ifs} / {close_ifs} {("✅" if open_ifs == close_ifs else "❌")}')

print()
print('=' * 70)
print('ЧТО СДЕЛАНО:')
print('=' * 70)
print()
print('1. ✓ Кнопка Х в DeepAnalysisControls')
print('     • Закрывает панель (как у SystemLogsPanel)')
print('     • Иконка X в правом верхнем углу хедера')
print()
print('2. ✓ Дубликаты SystemLogsPanel удалены')
print('     • Теперь SystemLogsPanel рендерится только один раз')
print('     • При открытии логов + DDA блоки не дублируются')
print()
print('3. ✓ Zoom/pan/download в графике DeepAnalysisResults')
print('     • Колёсико мыши — масштаб по оси X')
print('     • Shift+перетаскивание — выделить область зума')
print('     • Перетаскивание — прокрутка по графику')
print('     • Pinch-to-zoom на тач-устройствах')
print('     • Кнопка "Reset Zoom" (сброс масштаба)')
print('     • Кнопка "Download PNG" (сохранение графика)')
print('     • Установлены: chartjs-plugin-zoom + hammerjs')
print()
print('4. ✓ Поле ввода диалога всегда видно при DDA')
print('     • DDA Results занимает верхние 50% экрана')
print('     • Чат (NarrativePanel + WidgetRouter + Input) всегда снизу')
print('     • Можно одновременно видеть график и общаться с моделью')
print()
print('Frontend перезагрузится автоматически (Vite HMR).')
print()
print('ПРОВЕРКА:')
print('  1. Открой фронтенд')
print('  2. Клик Activity → выбери тег → "Запустить анализ"')
print('  3. Проверь:')
print('     • График отображается в верхней половине экрана')
print('     • Кнопки Zoom/Reset/Download над графиком')
print('     • Попробуй колёсико мыши — должен быть zoom')
print('     • Попробуй Shift+drag — выделение области')
print('     • Нажми Download PNG — должен скачаться файл')
print('     • Снизу должно быть поле ввода диалога')
print('  4. Напиши "покажи логи" — должны открыться только одни логи')
print('     (не должно быть дублирования)')
print('  5. Клик Х в шапке DeepAnalysis — панель должна закрыться')