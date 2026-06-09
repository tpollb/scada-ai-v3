<script lang="ts">
  import { ChevronRight, ChevronDown, ChevronUp, X, AlertTriangle } from 'lucide-svelte'
  import api from '../../lib/api'

  interface Props {
    data: any
  }
  let { data }: Props = $props()

  interface Alarm {
    id: number
    name: string
    bound: string
    priority: number
    priority_label: string
    state: number
    is_active: boolean
    timestamp: string | null
    message: string | null
    zone: string | null
  }

  let collapsed = $state(true)
  let showDetail = $state(false)
  let alarms = $state<Alarm[]>([])
  let loading = $state(false)
  let error = $state<string | null>(null)
  let filter = $state<string>('all')
  let selectedAlarm = $state<Alarm | null>(null)

  const priorityConfig: Record<string, { label: string; color: string; bg: string }> = {
    high: { label: 'Высокий', color: 'text-red-700', bg: 'bg-red-50 border-red-200' },
    medium: { label: 'Средний', color: 'text-amber-700', bg: 'bg-amber-50 border-amber-200' },
    low: { label: 'Низкий', color: 'text-neutral-700', bg: 'bg-neutral-50 border-neutral-200' },
  }

  async function openDetail(priorityFilter: string = 'all') {
    filter = priorityFilter
    showDetail = true
    loading = true
    error = null
    alarms = []
    selectedAlarm = null
    
    try {
      console.log('[AlarmsPanel] Loading', priorityFilter)
      const resp = await api.get(`health/alarms?period_hours=24&priority=${priorityFilter}&limit=500`, {
        timeout: 30000,
      }).json<any>()
      
      console.log('[AlarmsPanel] Loaded', priorityFilter, 'count:', resp?.count)
      
      if (resp?.error) {
        error = resp.error
        alarms = []
      } else {
        alarms = resp.alarms || []
      }
    } catch (e: any) {
      console.error('[AlarmsPanel] Error:', e)
      error = e?.message || 'Ошибка загрузки аварий'
      alarms = []
    } finally {
      loading = false
    }
  }

  function closeDetail() {
    showDetail = false
    alarms = []
    selectedAlarm = null
    error = null
  }

  function selectAlarm(a: Alarm) {
    selectedAlarm = a
  }

  function closeAlarmModal() {
    selectedAlarm = null
  }

  let total = $derived(data?.total ?? 0)
  let active = $derived(data?.active ?? 0)
  let byPriority = $derived(data?.by_priority ?? {})
  let topIssues = $derived(data?.top_issues ?? [])
</script>

<div class="bg-white border border-neutral-200 rounded">
  <button
    type="button"
    onclick={() => collapsed = !collapsed}
    class="w-full px-4 py-3 border-b border-neutral-200 flex items-center justify-between hover:bg-neutral-50 transition"
  >
    <h3 class="text-sm font-semibold text-neutral-900 uppercase tracking-wide text-left">Аварии</h3>
    <div class="flex items-center gap-3">
      <div class="flex items-center gap-3 text-xs">
        <span class="text-neutral-500">Всего: <span class="font-bold tabular-nums text-neutral-900">{total}</span></span>
        <span class="text-neutral-500">Активных: <span class="font-bold tabular-nums text-neutral-900">{active}</span></span>
      </div>
      {#if collapsed}
        <ChevronDown size={16} class="text-neutral-400" />
      {:else}
        <ChevronUp size={16} class="text-neutral-400" />
      {/if}
    </div>
  </button>

  {#if !collapsed}
  <div class="p-4">
    <div class="grid grid-cols-3 gap-2 mb-4">
      {#each ['high', 'medium', 'low'] as p}
        {@const cfg = priorityConfig[p]}
        {@const count = byPriority[p] ?? 0}
        <button
          type="button"
          onclick={() => openDetail(p)}
          class="p-3 border rounded text-left transition cursor-pointer hover:shadow-sm {cfg.bg}"
        >
          <div class="text-xs font-semibold uppercase tracking-wide {cfg.color}">{cfg.label}</div>
          <div class="text-2xl font-bold tabular-nums mt-1 {cfg.color}">{count}</div>
        </button>
      {/each}
    </div>

    {#if topIssues.length > 0}
      <div>
        <div class="flex items-center justify-between mb-2">
          <h4 class="text-xs font-semibold text-neutral-700 uppercase tracking-wide">
            Топ повторяющихся
          </h4>
          <button
            type="button"
            onclick={() => openDetail('all')}
            class="text-xs text-blue-600 hover:text-blue-800 font-medium flex items-center gap-1"
          >
            Все аварии <ChevronRight size={12} />
          </button>
        </div>
        <div class="border border-neutral-200 rounded divide-y divide-neutral-100">
          {#each topIssues.slice(0, 5) as issue, i}
            <div class="px-3 py-2 flex items-center gap-3 text-sm">
              <span class="w-5 h-5 rounded-full bg-neutral-100 text-xs font-medium flex items-center justify-center text-neutral-700 flex-shrink-0">
                {i + 1}
              </span>
              <span class="flex-1 font-mono text-neutral-900 truncate">{issue.name}</span>
              <span class="text-xs text-neutral-500 tabular-nums flex-shrink-0">
                {issue.count} раз
              </span>
              <span class="text-xs px-2 py-0.5 rounded font-medium flex-shrink-0 {priorityConfig[issue.priority]?.bg || ''} {priorityConfig[issue.priority]?.color || ''}">
                {priorityConfig[issue.priority]?.label || issue.priority}
              </span>
            </div>
          {/each}
        </div>
      </div>
    {:else}
      <div class="text-center py-6 text-sm text-neutral-500">
        Аварий за период не обнаружено
      </div>
    {/if}
  </div>
  {/if}
</div>

<!-- Модалка с журналом аварий -->
{#if showDetail}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded shadow-xl w-full max-w-5xl max-h-[90vh] flex flex-col">
      <div class="px-6 py-4 border-b border-neutral-200 flex items-center justify-between">
        <div>
          <h3 class="text-lg font-semibold text-neutral-900">Детальный журнал аварий</h3>
          {#if !error && !loading}
            <p class="text-xs text-neutral-500 mt-1">
              Период: 24 часа | Фильтр: {filter === 'all' ? 'все' : filter.toUpperCase()} |
              Найдено: {alarms.length}
            </p>
          {/if}
        </div>
        <button type="button" onclick={closeDetail} class="text-neutral-500 hover:text-neutral-700">
          <X size={20} />
        </button>
      </div>

      <div class="px-6 py-3 border-b border-neutral-200 bg-neutral-50 flex gap-2">
        {#each ['all', 'high', 'medium', 'low'] as p}
          {@const label = p === 'all' ? 'Все' : priorityConfig[p].label}
          <button
            type="button"
            onclick={() => openDetail(p)}
            class="px-3 py-1.5 text-xs font-medium rounded border transition {filter === p ? 'bg-neutral-900 text-white border-neutral-900' : 'bg-white text-neutral-700 border-neutral-300 hover:border-neutral-400'}"
          >
            {label}
          </button>
        {/each}
      </div>

      <div class="flex-1 overflow-y-auto p-6">
        {#if loading}
          <div class="flex flex-col items-center justify-center py-12 text-neutral-500">
            <div class="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mb-3"></div>
            <div>Загрузка аварий...</div>
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
                onclick={() => openDetail(filter)}
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
        {:else if alarms.length === 0}
          <div class="text-center py-8 text-neutral-500">Аварий не найдено</div>
        {:else}
          <div class="text-xs text-neutral-500 mb-2 italic">Кликните по строке для просмотра деталей</div>
          <div class="border border-neutral-200 rounded overflow-hidden">
            <table class="w-full text-sm">
              <thead class="bg-neutral-50 border-b border-neutral-200 sticky top-0 z-10">
                <tr>
                  <th class="text-left px-3 py-2 text-xs font-semibold text-neutral-700 uppercase tracking-wide">Время</th>
                  <th class="text-left px-3 py-2 text-xs font-semibold text-neutral-700 uppercase tracking-wide">Название</th>
                  <th class="text-left px-3 py-2 text-xs font-semibold text-neutral-700 uppercase tracking-wide">Зона</th>
                  <th class="text-left px-3 py-2 text-xs font-semibold text-neutral-700 uppercase tracking-wide">Приоритет</th>
                  <th class="text-left px-3 py-2 text-xs font-semibold text-neutral-700 uppercase tracking-wide">Статус</th>
                  <th class="text-left px-3 py-2 text-xs font-semibold text-neutral-700 uppercase tracking-wide">Сообщение</th>
                </tr>
              </thead>
              <tbody>
                {#each alarms as a}
                  {@const cfg = priorityConfig[a.priority_label] || priorityConfig.low}
                  <tr
                    class="border-t border-neutral-100 hover:bg-blue-50 cursor-pointer transition"
                    onclick={() => selectAlarm(a)}
                    role="button"
                    tabindex="0"
                    onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); selectAlarm(a); }}}
                  >
                    <td class="px-3 py-2 font-mono text-xs text-neutral-600 whitespace-nowrap">
                      {a.timestamp ? new Date(a.timestamp).toLocaleString('ru-RU') : '—'}
                    </td>
                    <td class="px-3 py-2 font-mono text-neutral-900">{a.name}</td>
                    <td class="px-3 py-2 text-neutral-600 text-xs">{a.zone || '—'}</td>
                    <td class="px-3 py-2">
                      <span class="text-xs px-2 py-0.5 rounded font-medium {cfg.bg} {cfg.color}">
                        {cfg.label}
                      </span>
                    </td>
                    <td class="px-3 py-2">
                      {#if a.is_active}
                        <span class="text-xs px-2 py-0.5 rounded bg-red-100 text-red-800 font-medium">ACTIVE</span>
                      {:else}
                        <span class="text-xs px-2 py-0.5 rounded bg-neutral-100 text-neutral-700">CLOSED</span>
                      {/if}
                    </td>
                    <td class="px-3 py-2 text-xs text-neutral-600 max-w-xs truncate">
                      {a.message || '—'}
                    </td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        {/if}
      </div>
    </div>
  </div>
{/if}

<!-- Модалка с деталями конкретной аварии -->
{#if selectedAlarm}
  {@const cfg = priorityConfig[selectedAlarm.priority_label] || priorityConfig.low}
  <div class="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-[60] p-4">
    <div class="bg-white rounded shadow-xl w-full max-w-3xl max-h-[85vh] flex flex-col">
      <div class="px-6 py-4 border-b border-neutral-200 flex items-center justify-between bg-neutral-50">
        <div class="flex items-center gap-3">
          <span class="text-xs px-3 py-1 rounded font-bold {cfg.bg} {cfg.color}">
            {cfg.label}
          </span>
          <h3 class="text-lg font-semibold text-neutral-900">Детали аварии #{selectedAlarm.id}</h3>
        </div>
        <button type="button" onclick={closeAlarmModal} class="text-neutral-500 hover:text-neutral-700">
          <X size={20} />
        </button>
      </div>

      <div class="flex-1 overflow-y-auto p-6 space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <div>
            <div class="text-xs text-neutral-500 uppercase tracking-wide mb-1">Название тега</div>
            <div class="font-mono text-neutral-900 break-all">{selectedAlarm.name}</div>
          </div>
          <div>
            <div class="text-xs text-neutral-500 uppercase tracking-wide mb-1">Зона</div>
            <div class="text-neutral-900">{selectedAlarm.zone || 'Не определена'}</div>
          </div>
          <div>
            <div class="text-xs text-neutral-500 uppercase tracking-wide mb-1">Уставка срабатывания</div>
            <div class="font-mono text-neutral-700">{selectedAlarm.bound || '—'}</div>
          </div>
          <div>
            <div class="text-xs text-neutral-500 uppercase tracking-wide mb-1">Числовой приоритет</div>
            <div class="font-mono text-neutral-700">{selectedAlarm.priority}</div>
          </div>
          <div>
            <div class="text-xs text-neutral-500 uppercase tracking-wide mb-1">Статус</div>
            <div>
              {#if selectedAlarm.is_active}
                <span class="inline-flex items-center gap-2 px-3 py-1 rounded bg-red-100 text-red-800 font-medium">
                  <span class="w-2 h-2 rounded-full bg-red-600 animate-pulse"></span>
                  АКТИВНА
                </span>
              {:else}
                <span class="inline-flex items-center gap-2 px-3 py-1 rounded bg-neutral-100 text-neutral-700 font-medium">
                  <span class="w-2 h-2 rounded-full bg-neutral-500"></span>
                  УСТРАНЕНА
                </span>
              {/if}
            </div>
          </div>
          <div>
            <div class="text-xs text-neutral-500 uppercase tracking-wide mb-1">Состояние (state)</div>
            <div class="font-mono text-neutral-700">{selectedAlarm.state}</div>
          </div>
          <div class="col-span-2">
            <div class="text-xs text-neutral-500 uppercase tracking-wide mb-1">Время возникновения</div>
            <div class="font-mono text-neutral-900">
              {selectedAlarm.timestamp ? new Date(selectedAlarm.timestamp).toLocaleString('ru-RU', {
                year: 'numeric', month: 'long', day: 'numeric',
                hour: '2-digit', minute: '2-digit', second: '2-digit'
              }) : '—'}
            </div>
          </div>
        </div>

        <div class="pt-4 border-t border-neutral-200">
          <div class="text-xs text-neutral-500 uppercase tracking-wide mb-2">Сообщение системы</div>
          <div class="p-4 bg-neutral-50 border border-neutral-200 rounded font-mono text-sm text-neutral-900 whitespace-pre-wrap break-words">
            {selectedAlarm.message || 'Сообщение отсутствует'}
          </div>
        </div>

        <div class="pt-4 border-t border-neutral-200">
          <div class="text-xs text-neutral-500 uppercase tracking-wide mb-2">Рекомендации</div>
          <div class="p-4 rounded {cfg.bg}">
            {#if selectedAlarm.priority_label === 'high'}
              <p class="text-sm text-red-900 font-medium mb-1">Критическая авария</p>
              <ul class="text-sm text-red-800 list-disc list-inside space-y-1">
                <li>Немедленно проверить связанное оборудование</li>
                <li>При необходимости — остановить технологический процесс</li>
                <li>Уведомить ответственного инженера</li>
                <li>Зафиксировать время обнаружения и принятые меры</li>
              </ul>
            {:else if selectedAlarm.priority_label === 'medium'}
              <p class="text-sm text-amber-900 font-medium mb-1">Авария среднего приоритета</p>
              <ul class="text-sm text-amber-800 list-disc list-inside space-y-1">
                <li>Запланировать диагностику в ближайшее время</li>
                <li>Проверить историю срабатываний данного тега</li>
                <li>Внести замечание в журнал обслуживания</li>
              </ul>
            {:else}
              <p class="text-sm text-neutral-800 font-medium mb-1">Информационное событие</p>
              <ul class="text-sm text-neutral-700 list-disc list-inside space-y-1">
                <li>Зафиксировать для анализа трендов</li>
                <li>Проверить при очередном осмотре</li>
              </ul>
            {/if}
          </div>
        </div>
      </div>

      <div class="px-6 py-4 border-t border-neutral-200 bg-neutral-50 flex justify-end">
        <button
          type="button"
          onclick={closeAlarmModal}
          class="px-4 py-2 bg-neutral-900 text-white rounded hover:bg-neutral-800 transition text-sm font-medium"
        >
          Закрыть
        </button>
      </div>
    </div>
  </div>
{/if}
