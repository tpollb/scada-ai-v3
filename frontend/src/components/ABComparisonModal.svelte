<script lang="ts">
  import { X, Calendar, ArrowRightLeft, Loader2, AlertCircle, TrendingUp, TrendingDown, Minus } from 'lucide-svelte'
  import api from '../lib/api'

  interface Props {
    isOpen: boolean
    availableTags: string[]
    defaultTag?: string
    onClose: () => void
    onResult?: (result: any) => void
  }

  let { isOpen, availableTags, defaultTag, onClose, onResult }: Props = $props()

  // === State ===
  let mode = $state<'before_after' | 'equipment_comparison'>('before_after')
  let tagA = $state<string>(defaultTag || '')
  let tagB = $state<string>(defaultTag || '')
  
  // Периоды (по умолчанию: последние 7 дней vs предыдущие 7 дней)
  let startA = $state<string>('')
  let endA = $state<string>('')
  let startB = $state<string>('')
  let endB = $state<string>('')

  let isLoading = $state(false)
  let error = $state<string | null>(null)
  let result = $state<any>(null)

  // Инициализация дат при открытии
  $effect(() => {
    if (isOpen) {
      const now = new Date()
      const end = now.toISOString().split('T')[0]
      
      const start7 = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
      const start14 = new Date(now.getTime() - 14 * 24 * 60 * 60 * 1000)
      
      startA = start14.toISOString().split('T')[0]
      endA = start7.toISOString().split('T')[0]
      startB = start7.toISOString().split('T')[0]
      endB = end
    }
  })

  // Автозаполнение tagB при смене режима
  $effect(() => {
    if (mode === 'before_after' && tagA) {
      tagB = tagA
    }
  })

  async function runComparison() {
    if (!tagA || !tagB || !startA || !endA || !startB || !endB) {
      error = 'Заполните все поля'
      return
    }

    isLoading = true
    error = null
    result = null

    try {
      const response = await fetch('http://localhost:8081/api/v1/deep_analysis/ab', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          snapshot_a: { tag: tagA, start: startA, end: endA },
          snapshot_b: { tag: tagB, start: startB, end: endB }
        })
      })

      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || err.error || 'Ошибка A/B анализа')
      }

      result = await response.json()
      
      // Если есть callback — передаём результат
      if (onResult) {
        onResult(result)
      }
    } catch (e: any) {
      error = e.message || 'Не удалось выполнить сравнение'
    } finally {
      isLoading = false
    }
  }

  function formatDelta(value: number | null | undefined): string {
    if (value === null || value === undefined) return 'N/A'
    if (Number.isNaN(value)) return 'N/A'
    // Бэк уже возвращает % (не долю), поэтому просто форматируем
    const v = Number(value)
    if (!Number.isFinite(v)) return 'N/A'
    // Капирование: если |v| > 999% — показываем ">999%"
    if (Math.abs(v) > 999) {
      return v > 0 ? '>+999%' : '<-999%'
    }
    if (v > 0) return `+${v.toFixed(1)}%`
    return `${v.toFixed(1)}%`
  }

  function formatPercent(value: number | null | undefined): string {
    if (value === null || value === undefined) return 'N/A'
    if (Number.isNaN(value)) return 'N/A'
    const v = Number(value)
    if (!Number.isFinite(v)) return 'N/A'
    return `${v.toFixed(1)}%`
  }

  function getSeverityColor(severity: string): string {
    const colors: Record<string, string> = {
      'info': 'text-blue-600 bg-blue-50 dark:bg-blue-900/20 dark:text-blue-400',
      'warning': 'text-yellow-600 bg-yellow-50 dark:bg-yellow-900/20 dark:text-yellow-400',
      'critical': 'text-red-600 bg-red-50 dark:bg-red-900/20 dark:text-red-400'
    }
    return colors[severity] || 'text-neutral-600 bg-neutral-50'
  }

  // Закрываем по Escape
  $effect(() => {
    if (!isOpen) return
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  })
</script>

{#if isOpen}
  <!-- Overlay -->
  <div class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onclick={onClose}>
    
    <!-- Modal -->
    <div 
      class="bg-white dark:bg-neutral-800 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"
      onclick={(e) => e.stopPropagation()}
    >
      <!-- Header -->
      <div class="flex items-center justify-between p-4 border-b border-neutral-200 dark:border-neutral-700">
        <h3 class="text-lg font-semibold text-neutral-900 dark:text-neutral-100 flex items-center gap-2">
          <ArrowRightLeft size={18} class="text-purple-500" />
          A/B Сравнение
        </h3>
        <button onclick={onClose} class="p-1 hover:bg-neutral-100 dark:hover:bg-neutral-700 rounded">
          <X size={20} />
        </button>
      </div>

      <!-- Body -->
      <div class="p-4 space-y-6">
        
        <!-- Режим сравнения -->
        <div>
          <label class="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
            Режим сравнения
          </label>
          <div class="flex gap-2">
            <button
              type="button"
              onclick={() => mode = 'before_after'}
              class="flex-1 px-3 py-2 text-sm rounded border transition {mode === 'before_after' ? 'border-purple-500 bg-purple-50 dark:bg-purple-900/20 text-purple-700 dark:text-purple-400' : 'border-neutral-300 dark:border-neutral-600 hover:bg-neutral-50 dark:hover:bg-neutral-700'}"
            >
              <div class="flex items-center justify-center gap-1">
                <Calendar size={14} />
                До/После
              </div>
              <div class="text-[10px] text-neutral-500 mt-1">Один тег, разные периоды</div>
            </button>
            <button
              type="button"
              onclick={() => mode = 'equipment_comparison'}
              class="flex-1 px-3 py-2 text-sm rounded border transition {mode === 'equipment_comparison' ? 'border-purple-500 bg-purple-50 dark:bg-purple-900/20 text-purple-700 dark:text-purple-400' : 'border-neutral-300 dark:border-neutral-600 hover:bg-neutral-50 dark:hover:bg-neutral-700'}"
            >
              <div class="flex items-center justify-center gap-1">
                <ArrowRightLeft size={14} />
                Оборудование
              </div>
              <div class="text-[10px] text-neutral-500 mt-1">Два тега, один период</div>
            </button>
          </div>
        </div>

        <!-- Snapshot A -->
        <div class="p-3 bg-neutral-50 dark:bg-neutral-900/30 rounded border border-neutral-200 dark:border-neutral-700">
          <h4 class="text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-3">Snapshot A</h4>
          
          <div class="space-y-3">
            <div>
              <label class="block text-xs text-neutral-500 mb-1">Тег</label>
              <select 
                bind:value={tagA}
                class="w-full px-3 py-2 text-sm bg-white dark:bg-neutral-800 border border-neutral-300 dark:border-neutral-600 rounded focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              >
                {#each availableTags as tag}
                  <option value={tag}>{tag}</option>
                {/each}
              </select>
            </div>
            
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs text-neutral-500 mb-1">Начало</label>
                <input 
                  type="date"
                  bind:value={startA}
                  class="w-full px-3 py-2 text-sm bg-white dark:bg-neutral-800 border border-neutral-300 dark:border-neutral-600 rounded"
                />
              </div>
              <div>
                <label class="block text-xs text-neutral-500 mb-1">Конец</label>
                <input 
                  type="date"
                  bind:value={endA}
                  class="w-full px-3 py-2 text-sm bg-white dark:bg-neutral-800 border border-neutral-300 dark:border-neutral-600 rounded"
                />
              </div>
            </div>
          </div>
        </div>

        <!-- Snapshot B -->
        <div class="p-3 bg-neutral-50 dark:bg-neutral-900/30 rounded border border-neutral-200 dark:border-neutral-700">
          <h4 class="text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-3">Snapshot B</h4>
          
          <div class="space-y-3">
            <div>
              <label class="block text-xs text-neutral-500 mb-1">Тег</label>
              <select 
                bind:value={tagB}
                disabled={mode === 'before_after'}
                class="w-full px-3 py-2 text-sm bg-white dark:bg-neutral-800 border border-neutral-300 dark:border-neutral-600 rounded focus:ring-2 focus:ring-purple-500 focus:border-transparent {mode === 'before_after' ? 'opacity-50 cursor-not-allowed' : ''}"
              >
                {#each availableTags as tag}
                  <option value={tag}>{tag}</option>
                {/each}
              </select>
            </div>
            
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs text-neutral-500 mb-1">Начало</label>
                <input 
                  type="date"
                  bind:value={startB}
                  class="w-full px-3 py-2 text-sm bg-white dark:bg-neutral-800 border border-neutral-300 dark:border-neutral-600 rounded"
                />
              </div>
              <div>
                <label class="block text-xs text-neutral-500 mb-1">Конец</label>
                <input 
                  type="date"
                  bind:value={endB}
                  class="w-full px-3 py-2 text-sm bg-white dark:bg-neutral-800 border border-neutral-300 dark:border-neutral-600 rounded"
                />
              </div>
            </div>
          </div>
        </div>

        <!-- Кнопка запуска -->
        <button
          type="button"
          onclick={runComparison}
          disabled={isLoading}
          class="w-full py-2.5 bg-purple-600 hover:bg-purple-700 disabled:bg-purple-400 text-white rounded font-medium flex items-center justify-center gap-2 transition"
        >
          {#if isLoading}
            <Loader2 size={16} class="animate-spin" />
            Анализ...
          {:else}
            <ArrowRightLeft size={16} />
            Сравнить
          {/if}
        </button>

        <!-- Ошибка -->
        {#if error}
          <div class="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded">
            <div class="flex items-start gap-2">
              <AlertCircle size={16} class="text-red-500 mt-0.5" />
              <p class="text-sm text-red-900 dark:text-red-100">{error}</p>
            </div>
          </div>
        {/if}

        <!-- Результаты -->
        {#if result}
          <div class="space-y-4">
            
            <!-- Verdict -->
            {#if result.verdict}
              <div class="p-4 rounded border {getSeverityColor(result.verdict.severity)}">
                <div class="flex items-center gap-2 mb-2">
                  {#if result.verdict.severity === 'critical'}
                    <TrendingUp size={16} />
                  {:else if result.verdict.severity === 'warning'}
                    <TrendingDown size={16} />
                  {:else}
                    <Minus size={16} />
                  {/if}
                  <span class="font-semibold uppercase text-sm">{result.verdict.severity}</span>
                </div>
                <p class="text-sm">{result.verdict.summary}</p>
              </div>
            {/if}

            <!-- Statistics -->
            {#if result.comparison?.statistics?.delta && Object.keys(result.comparison.statistics.delta).length > 0}
              <div>
                <h4 class="text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">Изменение статистик (B vs A)</h4>
                <div class="grid grid-cols-2 gap-2 text-sm">
                  {#each Object.entries(result.comparison.statistics.delta) as [key, value]}
                    <div class="p-2 bg-neutral-50 dark:bg-neutral-900/30 rounded">
                      <div class="text-xs text-neutral-500">{key}</div>
                      {#if value !== null && value !== undefined && Number.isFinite(Number(value)) && Number(value) !== 0}
                        <div class="font-mono {Number(value) > 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}">
                          {formatDelta(value)}
                        </div>
                      {:else}
                        <div class="font-mono text-neutral-400">{formatDelta(value)}</div>
                      {/if}
                    </div>
                  {/each}
                </div>
                {#if result.comparison.statistics.a && Object.keys(result.comparison.statistics.a).length > 0}
                  <details class="mt-2">
                    <summary class="text-xs text-neutral-500 cursor-pointer hover:text-neutral-700 dark:hover:text-neutral-300">
                      Показать абсолютные значения
                    </summary>
                    <div class="mt-2 grid grid-cols-2 gap-2 text-xs">
                      <div class="p-2 bg-blue-50 dark:bg-blue-900/20 rounded">
                        <div class="font-medium text-neutral-600 dark:text-neutral-400 mb-1">Период A</div>
                        {#each Object.entries(result.comparison.statistics.a) as [k, v]}
                          <div><span class="text-neutral-500">{k}:</span> <span class="font-mono">{typeof v === 'number' ? v.toFixed(2) : v}</span></div>
                        {/each}
                      </div>
                      <div class="p-2 bg-orange-50 dark:bg-orange-900/20 rounded">
                        <div class="font-medium text-neutral-600 dark:text-neutral-400 mb-1">Период B</div>
                        {#each Object.entries(result.comparison.statistics.b) as [k, v]}
                          <div><span class="text-neutral-500">{k}:</span> <span class="font-mono">{typeof v === 'number' ? v.toFixed(2) : v}</span></div>
                        {/each}
                      </div>
                    </div>
                  </details>
                {/if}
              </div>
            {:else if result.comparison?.significance?.interpretation === 'insufficient_data'}
              <div class="p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded text-sm">
                <p class="text-yellow-800 dark:text-yellow-200">⚠ Недостаточно данных для сравнения</p>
                {#if result.comparison.significance.reason}
                  <p class="text-xs text-yellow-700 dark:text-yellow-300 mt-1">{result.comparison.significance.reason}</p>
                {/if}
              </div>
            {/if}

            <!-- Significance -->
            {#if result.comparison?.significance}
              <div>
                <h4 class="text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">Значимость</h4>
                <div class="p-2 bg-neutral-50 dark:bg-neutral-900/30 rounded text-sm">
                  <div>p-value: <span class="font-mono">{result.comparison.significance.p_value}</span></div>
                  <div>Интерпретация: {result.comparison.significance.interpretation}</div>
                </div>
              </div>
            {/if}

            <!-- Pattern comparison -->
            {#if result.pattern_comparison?.comparison}
              <div>
                <h4 class="text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">Сравнение паттернов</h4>
                <div class="p-2 bg-neutral-50 dark:bg-neutral-900/30 rounded text-sm space-y-1">
                  {#if result.pattern_comparison.comparison.pattern_correlation != null}
                    {@const corr = result.pattern_comparison.comparison.pattern_correlation}
                    <div>
                      Корреляция суточных паттернов:
                      <span class="font-mono {corr > 0.7 ? 'text-green-600 dark:text-green-400' : corr > 0.3 ? 'text-yellow-600 dark:text-yellow-400' : 'text-red-600 dark:text-red-400'}">
                        {formatPercent(corr * 100)}
                      </span>
                    </div>
                  {:else}
                    <div class="text-neutral-500 italic">Корреляция паттернов не определена (данные слишком однородные)</div>
                  {/if}

                  <div>
                    Совпадение периодов:
                    {#if result.pattern_comparison.comparison.period_match}
                      <span class="text-green-600 dark:text-green-400">✓ Да ({result.pattern_comparison.a?.period || '?'} точек)</span>
                    {:else}
                      <span class="text-yellow-600 dark:text-yellow-400">✗ Различаются ({result.pattern_comparison.a?.period} vs {result.pattern_comparison.b?.period})</span>
                    {/if}
                  </div>

                  {#if result.pattern_comparison.comparison.delta_amplitude_pct != null}
                    <div>
                      Изменение амплитуды:
                      <span class="font-mono">
                        {formatDelta(result.pattern_comparison.comparison.delta_amplitude_pct)}
                      </span>
                    </div>
                  {/if}
                </div>
              </div>
            {/if}

          </div>
        {/if}

      </div>

      <!-- Footer -->
      <div class="flex justify-end gap-2 p-4 border-t border-neutral-200 dark:border-neutral-700">
        <button
          type="button"
          onclick={onClose}
          class="px-4 py-2 text-sm bg-neutral-100 dark:bg-neutral-700 hover:bg-neutral-200 dark:hover:bg-neutral-600 rounded"
        >
          Закрыть
        </button>
        {#if result && onResult}
          <button
            type="button"
            onclick={() => {
              onResult(result)
              // Закрываем модалку
              onClose()
            }}
            class="px-4 py-2 text-sm bg-purple-600 hover:bg-purple-700 text-white rounded"
          >
            Использовать в анализе
          </button>
        {/if}
      </div>

    </div>
  </div>
{/if}
