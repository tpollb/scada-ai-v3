#!/usr/bin/env python3
"""
ensure_chart_modal_exists.py — проверка и создание ChartModal.svelte
"""
from pathlib import Path

print('=' * 80)
print('ПРОВЕРКА: ChartModal.svelte')
print('=' * 80)
print()

# Правильный путь
modal_path = Path('frontend/src/components/ChartModal.svelte')

# Проверяем существование
if modal_path.exists():
    size = modal_path.stat().st_size
    print(f'✅ Файл существует: {modal_path}')
    print(f'   Размер: {size} байт')
    
    # Проверяем что файл не пустой
    if size < 100:
        print('⚠️  Файл слишком маленький — возможно повреждён')
        print('   Пересоздаю...')
    else:
        print('   Файл в порядке')
        exit(0)
else:
    print(f'❌ Файл НЕ СУЩЕСТВУЕТ: {modal_path}')
    print('   Создаю...')

# Создаём/пересоздаём файл
modal_path.parent.mkdir(parents=True, exist_ok=True)

modal_content = '''<script lang="ts">
  import { onMount, onDestroy } from 'svelte'
  import { X, Download, ZoomIn, ZoomOut, RotateCcw } from 'lucide-svelte'
  import { Line, Bar } from 'svelte-chartjs'
  import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    Title,
    Tooltip,
    Legend,
    TimeScale
  } from 'chart.js'
  import zoomPlugin from 'chartjs-plugin-zoom'

  ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    Title,
    Tooltip,
    Legend,
    TimeScale,
    zoomPlugin
  )

  interface Props {
    isOpen: boolean
    title: string
    chartType: 'line' | 'bar'
    chartData: any
    chartOptions: any
    onClose: () => void
  }

  let { isOpen, title, chartType, chartData, chartOptions, onClose }: Props = $props()

  let chartInstance = $state<any>(null)
  let chartId = $state(`chart-modal-${Math.random().toString(36).substr(2, 9)}`)

  // Закрытие по Esc
  function handleKeydown(event: KeyboardEvent) {
    if (event.key === 'Escape' && isOpen) {
      onClose()
    }
  }

  onMount(() => {
    if (typeof window !== 'undefined') {
      window.addEventListener('keydown', handleKeydown)
    }
  })

  onDestroy(() => {
    if (typeof window !== 'undefined') {
      window.removeEventListener('keydown', handleKeydown)
    }
  })

  // Zoom функции
  function zoomIn() {
    if (chartInstance) {
      chartInstance.zoom(1.2)
    }
  }

  function zoomOut() {
    if (chartInstance) {
      chartInstance.zoom(0.8)
    }
  }

  function resetZoom() {
    if (chartInstance) {
      chartInstance.resetZoom()
    }
  }

  // Скачать PNG
  function downloadPNG() {
    if (!chartInstance) return
    const link = document.createElement('a')
    link.download = `${title.replace(/\\s+/g, '_').toLowerCase()}_${new Date().toISOString().split('T')[0]}.png`
    link.href = chartInstance.toBase64Image()
    link.click()
  }

  // Обработчик клика на фон
  function handleBackdropClick(event: MouseEvent) {
    if (event.target === event.currentTarget) {
      onClose()
    }
  }
</script>

{#if isOpen}
  <div
    class="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4"
    onclick={handleBackdropClick}
    role="dialog"
    aria-modal="true"
    aria-label={title}
  >
    <div class="bg-white dark:bg-neutral-900 rounded-lg shadow-2xl w-full h-full max-w-[95vw] max-h-[95vh] flex flex-col">
      <!-- Header -->
      <div class="flex items-center justify-between p-4 border-b border-neutral-200 dark:border-neutral-700">
        <h2 class="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
          {title}
        </h2>
        <div class="flex items-center gap-2">
          <button
            type="button"
            onclick={zoomIn}
            class="p-2 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition"
            title="Приблизить"
          >
            <ZoomIn size={18} class="text-neutral-600 dark:text-neutral-400" />
          </button>
          <button
            type="button"
            onclick={zoomOut}
            class="p-2 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition"
            title="Отдалить"
          >
            <ZoomOut size={18} class="text-neutral-600 dark:text-neutral-400" />
          </button>
          <button
            type="button"
            onclick={resetZoom}
            class="p-2 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition"
            title="Сбросить zoom"
          >
            <RotateCcw size={18} class="text-neutral-600 dark:text-neutral-400" />
          </button>
          <button
            type="button"
            onclick={downloadPNG}
            class="p-2 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition"
            title="Скачать PNG"
          >
            <Download size={18} class="text-neutral-600 dark:text-neutral-400" />
          </button>
          <div class="w-px h-6 bg-neutral-300 dark:bg-neutral-600 mx-1"></div>
          <button
            type="button"
            onclick={onClose}
            class="p-2 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition"
            title="Закрыть (Esc)"
          >
            <X size={18} class="text-neutral-600 dark:text-neutral-400" />
          </button>
        </div>
      </div>

      <!-- Chart -->
      <div class="flex-1 p-6 overflow-hidden">
        <div class="w-full h-full">
          {#if chartType === 'line'}
            <Line
              bind:chartInstance
              data={chartData}
              options={chartOptions}
            />
          {:else if chartType === 'bar'}
            <Bar
              bind:chartInstance
              data={chartData}
              options={chartOptions}
            />
          {/if}
        </div>
      </div>

      <!-- Footer -->
      <div class="p-3 border-t border-neutral-200 dark:border-neutral-700 text-xs text-neutral-500 dark:text-neutral-400">
        Колёсико мыши — zoom · Shift+drag — выделение области · Drag — прокрутка · Esc — закрыть
      </div>
    </div>
  </div>
{/if}
'''

modal_path.write_text(modal_content, encoding='utf-8', newline='\n')

print()
print(f'✅ Файл создан: {modal_path.absolute()}')
print(f'   Размер: {modal_path.stat().st_size} байт')

print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Vite автоматически перезагрузит страницу')
print('2. Ошибка "Failed to resolve import" должна исчезнуть')
print('3. Кнопка ⛶ (Maximize) должна работать')
print()
print('Если Vite всё ещё ругается:')
print('  • Перезапусти dev сервер: Ctrl+C и npm run dev заново')
print('  • Или обнови страницу с hard refresh: Ctrl+Shift+R')