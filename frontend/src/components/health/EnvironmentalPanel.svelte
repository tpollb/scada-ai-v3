<script lang="ts">
  import { ChevronRight, TrendingUp, TrendingDown, Minus, AlertTriangle } from 'lucide-svelte'
  import api from '../../lib/api'

  interface Props {
    data: any
  }
  let { data }: Props = $props()

  interface EnvDetail {
    param: string
    label: string
    unit: string
    norms: any
    validator: any
    count: number
    outliers_count: number
    history: any[]
    hourly: any[]
    tags_last_values: any[]
    outliers: any[]
    error?: string
  }

  let selectedParam = $state<string | null>(null)
  let detail = $state<EnvDetail | null>(null)
  let loading = $state(false)
  let error = $state<string | null>(null)
  let activeTab = $state<'history' | 'tags' | 'outliers'>('history')
  let expandedOutliers = $state<Record<number, boolean>>({})

  const paramConfigs = [
    { key: 'temperature', label: 'Температура', unit: '°C', norm: '18-24°C' },
    { key: 'humidity', label: 'Влажность', unit: '%', norm: '30-60%' },
    { key: 'co2', label: 'CO2', unit: 'ppm', norm: '400-800' },
    { key: 'pressure', label: 'Давление', unit: 'мм рт.ст.', norm: '720-780' },
    { key: 'voc', label: 'VOC', unit: 'мг/м³', norm: '< 0.3' },
  ]

  const STATUS_RU: Record<string, string> = {
    'OK': 'Норма',
    'WARNING': 'Внимание',
    'CRITICAL': 'Критично',
    'NO_DATA': 'Нет данных',
  }

  function statusRu(status: string): string {
    return STATUS_RU[status] || status
  }

  function statusColor(status: string): string {
    if (status === 'CRITICAL') return 'text-red-600 bg-red-50 border-red-200'
    if (status === 'WARNING') return 'text-amber-600 bg-amber-50 border-amber-200'
    return 'text-green-700 bg-green-50 border-green-200'
  }

  function trendIcon(trend: string) {
    if (trend === 'rising') return TrendingUp
    if (trend === 'falling') return TrendingDown
    return Minus
  }

  async function openDetail(paramKey: string) {
    selectedParam = paramKey
    activeTab = 'history'
    loading = true
    error = null
    detail = null
    expandedOutliers = {}
    
    try {
      console.log('[EnvironmentalPanel] Loading', paramKey)
      const resp = await api.get(`health/environmental/${paramKey}?period_hours=24`, {
        timeout: 30000,
      }).json<EnvDetail>()
      
      console.log('[EnvironmentalPanel] Loaded', paramKey, resp)
      
      if (resp?.error) {
        error = resp.error
        detail = null
      } else {
        detail = resp
        if (detail?.outliers?.length > 0) {
          activeTab = 'outliers'
        }
      }
    } catch (e: any) {
      console.error('[EnvironmentalPanel] Error:', e)
      error = e?.message || 'Ошибка загрузки данных'
      detail = null
    } finally {
      loading = false
    }
  }

  function closeDetail() {
    selectedParam = null
    detail = null
    error = null
  }

  let selectedParamConfig = $derived(paramConfigs.find(p => p.key === selectedParam))
</script>

<div class="bg-white border border-neutral-200 rounded">
  <div class="px-4 py-3 border-b border-neutral-200">
    <h3 class="text-sm font-semibold text-neutral-900 uppercase tracking-wide">
      Параметры жизнедеятельности
    </h3>
  </div>

  <div class="p-4 grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-3">
    {#each paramConfigs as p}
      {@const d = data?.[p.key]}
      {#if d}
        {@const Icon = trendIcon(d.trend || 'stable')}
        {@const hasOutliers = (d.outliers_count || 0) > 0}
        <button
          type="button"
          onclick={() => openDetail(p.key)}
          class="text-left p-4 border rounded hover:border-neutral-400 hover:shadow-sm transition cursor-pointer {statusColor(d.status || 'OK')}"
        >
          <div class="flex items-center justify-between mb-2">
            <span class="text-xs font-semibold uppercase tracking-wide">{p.label}</span>
            <span class="text-xs px-2 py-0.5 rounded font-medium">{statusRu(d.status || 'OK')}</span>
          </div>
          <div class="text-3xl font-bold mb-1 tabular-nums">
            {d.avg ?? '—'}<span class="text-lg font-normal ml-1">{p.unit}</span>
          </div>
          <div class="text-xs text-neutral-600 tabular-nums">
            мин {d.min ?? '—'} / макс {d.max ?? '—'}
          </div>
          <div class="flex items-center justify-between mt-2 text-xs">
            <span class="text-neutral-500">Норма: {p.norm}</span>
            <Icon size={14} class="text-neutral-500" />
          </div>
          {#if hasOutliers}
            <div class="mt-2 text-xs text-red-700 font-medium flex items-center gap-1">
              <AlertTriangle size={12} />
              Битых: {d.outliers_count}
            </div>
          {/if}
          {#if d.deviations_count > 0 && !hasOutliers}
            <div class="mt-2 text-xs text-amber-700 font-medium">
              Отклонений: {d.deviations_count}
            </div>
          {/if}
          <div class="mt-2 text-xs text-neutral-500 flex items-center gap-1">
            Подробнее <ChevronRight size={12} />
          </div>
        </button>
      {:else}
        <div class="p-4 border border-neutral-100 rounded bg-neutral-50">
          <div class="text-xs font-semibold uppercase tracking-wide text-neutral-400">{p.label}</div>
          <div class="text-sm text-neutral-500 mt-2">Нет данных</div>
        </div>
      {/if}
    {/each}
  </div>
</div>

<!-- Модалка drilldown -->
{#if selectedParam}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded shadow-xl w-full max-w-5xl max-h-[90vh] flex flex-col">
      <div class="px-6 py-4 border-b border-neutral-200 flex items-center justify-between">
        <div>
          <h3 class="text-lg font-semibold text-neutral-900">
            {selectedParamConfig?.label}: детальный анализ
          </h3>
          {#if detail}
            <p class="text-xs text-neutral-500 mt-1">
              Период: 24 часа | Точек данных: {detail.count ?? 0} | Норма: {detail.norms?.opt_min}..{detail.norms?.opt_max} {detail.unit}
            </p>
          {/if}
        </div>
        <button type="button" onclick={closeDetail} class="text-neutral-500 hover:text-neutral-700 text-xl">x</button>
      </div>

      <!-- Табы (только если данные загружены) -->
      {#if detail}
        <div class="px-6 py-2 border-b border-neutral-200 bg-neutral-50 flex gap-1">
          <button
            type="button"
            onclick={() => activeTab = 'history'}
            class="px-3 py-1.5 text-xs font-medium rounded transition {activeTab === 'history' ? 'bg-white shadow-sm text-neutral-900' : 'text-neutral-600 hover:text-neutral-900'}"
          >
            Динамика по часам
          </button>
          <button
            type="button"
            onclick={() => activeTab = 'tags'}
            class="px-3 py-1.5 text-xs font-medium rounded transition {activeTab === 'tags' ? 'bg-white shadow-sm text-neutral-900' : 'text-neutral-600 hover:text-neutral-900'}"
          >
            Теги ({detail.tags_last_values?.length ?? 0})
          </button>
          {#if detail.outliers_count > 0}
            <button
              type="button"
              onclick={() => activeTab = 'outliers'}
              class="px-3 py-1.5 text-xs font-medium rounded transition {activeTab === 'outliers' ? 'bg-red-600 text-white' : 'bg-red-50 text-red-700 hover:bg-red-100'}"
            >
              Битые датчики ({detail.outliers_count})
            </button>
          {/if}
        </div>
      {/if}

      <div class="flex-1 overflow-y-auto p-6">
        {#if loading}
          <div class="flex flex-col items-center justify-center py-12 text-neutral-500">
            <div class="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mb-3"></div>
            <div>Загрузка данных {selectedParamConfig?.label}...</div>
            <div class="text-xs text-neutral-400 mt-1">Это может занять до 30 секунд</div>
          </div>
        {:else if error}
          <div class="text-center py-12">
            <div class="text-red-600 mb-3">
              <AlertTriangle size={48} class="mx-auto" />
            </div>
            <div class="text-red-700 font-semibold mb-2">Ошибка загрузки</div>
            <div class="text-sm text-red-600 mb-4 font-mono bg-red-50 p-3 rounded max-w-lg mx-auto break-words">
              {error}
            </div>
            <div class="text-xs text-neutral-500 mb-4">
              Проверьте консоль браузера (F12) и логи backend для деталей.
            </div>
            <div class="flex gap-2 justify-center">
              <button
                type="button"
                onclick={() => openDetail(selectedParam!)}
                class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition text-sm"
              >
                Попробовать снова
              </button>
              <button
                type="button"
                onclick={closeDetail}
                class="px-4 py-2 border border-neutral-300 rounded hover:bg-neutral-50 transition text-sm"
              >
                Закрыть
              </button>
            </div>
          </div>
        {:else if !detail}
          <div class="text-center py-8 text-neutral-500">Нет данных</div>
        {:else if activeTab === 'history'}
          {#if detail.hourly.length === 0}
            <div class="text-center py-8 text-neutral-500">
              Нет данных для отображения.<br>
              <span class="text-xs">Найдено точек: {detail.count}, валидных: {detail.hourly.length}</span>
            </div>
          {:else}
            <div class="bg-neutral-50 border border-neutral-200 rounded p-4 overflow-x-auto">
              <table class="w-full text-xs">
                <thead>
                  <tr class="text-neutral-500 uppercase tracking-wide">
                    <th class="text-left py-1 pr-3">Час</th>
                    <th class="text-right py-1 px-3">Min</th>
                    <th class="text-right py-1 px-3">Avg</th>
                    <th class="text-right py-1 px-3">Max</th>
                    <th class="text-right py-1 pl-3">Отклонение</th>
                  </tr>
                </thead>
                <tbody>
                  {#each detail.hourly as h}
                    {@const isWarning = h.avg < detail.norms.opt_min || h.avg > detail.norms.opt_max}
                    {@const isCritical = h.avg < detail.norms.crit_min || h.avg > detail.norms.crit_max}
                    <tr class="border-t border-neutral-200 {isCritical ? 'bg-red-50' : isWarning ? 'bg-amber-50' : ''}">
                      <td class="py-1.5 pr-3 font-mono text-neutral-600">{h.hour}</td>
                      <td class="text-right py-1.5 px-3 tabular-nums">{h.min}</td>
                      <td class="text-right py-1.5 px-3 tabular-nums font-semibold">{h.avg}</td>
                      <td class="text-right py-1.5 px-3 tabular-nums">{h.max}</td>
                      <td class="text-right py-1.5 pl-3 tabular-nums {isCritical ? 'text-red-700 font-semibold' : isWarning ? 'text-amber-700' : 'text-neutral-500'}">
                        {isCritical ? '!!!' : isWarning ? '!' : 'OK'}
                      </td>
                    </tr>
                  {/each}
                </tbody>
              </table>
            </div>
          {/if}
        {:else if activeTab === 'tags'}
          {@const tags = detail.tags_last_values || []}
          {@const validTags = tags.filter(t => t.is_valid)}
          {@const brokenTags = tags.filter(t => !t.is_valid)}
          <div class="mb-3 flex items-center gap-4 text-xs">
            <div class="flex items-center gap-1.5">
              <span class="w-2 h-2 rounded-full bg-green-600"></span>
              <span class="text-neutral-700">Валидных: <span class="font-bold">{validTags.length}</span></span>
            </div>
            <div class="flex items-center gap-1.5">
              <span class="w-2 h-2 rounded-full bg-red-600"></span>
              <span class="text-neutral-700">Битых: <span class="font-bold">{brokenTags.length}</span></span>
            </div>
            <div class="text-neutral-500">Всего тегов: <span class="font-bold">{tags.length}</span></div>
          </div>
          {#if tags.length === 0}
            <div class="text-center py-8 text-neutral-500">Нет данных по тегам</div>
          {:else}
            <div class="bg-neutral-50 border border-neutral-200 rounded overflow-hidden">
              <div class="max-h-[60vh] overflow-y-auto">
                <table class="w-full text-sm">
                  <thead class="bg-white border-b border-neutral-200 sticky top-0">
                    <tr>
                      <th class="text-left px-3 py-2 text-xs font-semibold text-neutral-700 uppercase tracking-wide">Тег</th>
                      <th class="text-right px-3 py-2 text-xs font-semibold text-neutral-700 uppercase tracking-wide">Последнее</th>
                      <th class="text-right px-3 py-2 text-xs font-semibold text-neutral-700 uppercase tracking-wide">Время</th>
                      <th class="text-center px-3 py-2 text-xs font-semibold text-neutral-700 uppercase tracking-wide">Статус</th>
                    </tr>
                  </thead>
                  <tbody>
                    {#each tags as tag}
                      <tr class="border-t border-neutral-100 {tag.is_valid ? '' : 'bg-red-50'}">
                        <td class="px-3 py-2 font-mono text-neutral-900 break-all">{tag.tag_name}</td>
                        <td class="text-right px-3 py-2 tabular-nums {tag.is_valid ? 'text-neutral-900' : 'text-red-700 font-bold'}">
                          {typeof tag.last_value === 'number' ? tag.last_value.toFixed(2) : tag.last_value ?? '—'} {detail.unit}
                        </td>
                        <td class="text-right px-3 py-2 font-mono text-xs text-neutral-600 whitespace-nowrap">
                          {tag.timestamp ? new Date(tag.timestamp).toLocaleTimeString('ru-RU', {hour: '2-digit', minute: '2-digit'}) : '—'}
                        </td>
                        <td class="text-center px-3 py-2">
                          {#if tag.is_valid}
                            <span class="text-xs px-2 py-0.5 rounded bg-green-100 text-green-800 font-medium">OK</span>
                          {:else}
                            <span class="text-xs px-2 py-0.5 rounded bg-red-100 text-red-800 font-medium">БИТЫЙ</span>
                          {/if}
                        </td>
                      </tr>
                    {/each}
                  </tbody>
                </table>
              </div>
            </div>
          {/if}
        {:else if activeTab === 'outliers'}
          {@const outliers = detail.outliers || []}
          {@const groupedByTag = outliers.reduce((acc: any, o: any) => {
            if (!acc[o.tag_name]) acc[o.tag_name] = [];
            acc[o.tag_name].push(o);
            return acc;
          }, {})}
          {@const tagGroups = Object.entries(groupedByTag).sort((a: any, b: any) => b[1].length - a[1].length)}
          <div class="mb-4 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-900">
            <div class="font-semibold mb-1">Обнаружено аномальных значений: {outliers.length}</div>
            <div class="text-xs">
              Уникальных датчиков с аномалиями: {tagGroups.length}.
              Рекомендуется заменить или откалибровать соответствующие датчики.
            </div>
          </div>
          {#if tagGroups.length === 0}
            <div class="text-center py-8 text-neutral-500">Аномальных значений не обнаружено</div>
          {:else}
            <div class="space-y-2">
              {#each tagGroups as [tagName, occurrences], idx}
                {@const last = (occurrences as any[])[0]}
                {@const uniqueValues = [...new Set((occurrences as any[]).map((o: any) => o.value))]}
                {@const minVal = Math.min(...(occurrences as any[]).map((o: any) => o.value))}
                {@const maxVal = Math.max(...(occurrences as any[]).map((o: any) => o.value))}
                {@const isExpanded = expandedOutliers[idx] === true}
                <div class="bg-red-50 border border-red-200 rounded p-3">
                  <div class="flex items-start justify-between gap-3 mb-2">
                    <div class="flex-1 min-w-0">
                      <div class="font-mono text-sm font-semibold text-red-900 break-all">{tagName}</div>
                      <div class="text-xs text-red-700 mt-1">
                        Аномальных значений: <span class="font-bold">{(occurrences as any[]).length}</span>
                        {#if uniqueValues.length > 1}
                          <span class="ml-2">Диапазон: {minVal.toFixed(2)} — {maxVal.toFixed(2)} {detail.unit}</span>
                        {:else}
                          <span class="ml-2">Значение: {uniqueValues[0].toFixed(2)} {detail.unit}</span>
                        {/if}
                      </div>
                    </div>
                    <div class="text-right flex-shrink-0">
                      <div class="text-xs text-red-700">Норма</div>
                      <div class="text-xs font-mono text-red-900">{last.threshold}</div>
                    </div>
                  </div>
                  {#if (occurrences as any[]).length > 1}
                    <button
                      type="button"
                      onclick={() => expandedOutliers[idx] = !isExpanded}
                      class="mt-2 flex items-center gap-1 text-xs text-red-700 hover:text-red-900 font-medium transition"
                    >
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="transform: rotate({isExpanded ? 180 : 0}deg); transition: transform 0.2s">
                        <polyline points="6 9 12 15 18 9"></polyline>
                      </svg>
                      {isExpanded ? 'Скрыть' : 'Показать'} все срабатывания ({(occurrences as any[]).length})
                    </button>
                    {#if isExpanded}
                      <div class="mt-2 max-h-48 overflow-y-auto bg-white border border-red-200 rounded p-2 space-y-1">
                        {#each occurrences as o}
                          <div class="flex items-center justify-between text-xs py-0.5 hover:bg-red-50 px-1 rounded">
                            <span class="font-mono text-neutral-600">
                              {o.timestamp ? new Date(o.timestamp).toLocaleString('ru-RU') : '—'}
                            </span>
                            <span class="font-mono font-bold text-red-700 tabular-nums">
                              {typeof o.value === 'number' ? o.value.toFixed(2) : o.value} {detail.unit}
                            </span>
                          </div>
                        {/each}
                      </div>
                    {/if}
                  {/if}
                </div>
              {/each}
            </div>
          {/if}
        {/if}
      </div>
    </div>
  </div>
{/if}
