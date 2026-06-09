<script lang="ts">
  import { Info } from 'lucide-svelte'

  interface Props {
    data: { score: number; status: string; status_ru?: string; sub_scores?: any }
  }
  let { data }: Props = $props()
  let showFormula = $state(false)

  let score = $derived(data?.score ?? 0)
  let status = $derived(data?.status ?? 'UNKNOWN')
  let statusDisplay = $derived(data?.status_ru || status)
  let color = $derived(score < 30 ? '#dc2626' : score < 60 ? '#d97706' : score < 85 ? '#2563eb' : '#16a34a')
  let circumference = 2 * Math.PI * 80
  let offset = $derived(circumference - (score / 100) * circumference)

  let subScores = $derived(data?.sub_scores ?? {})
  
  // Формируем строку детализации: "Аварии (40%) + Среда (35%) + Оборудование (25%)"
  function breakdown(): string {
    if (!subScores || Object.keys(subScores).length === 0) return ''
    
    const labels: Record<string, string> = {
      alarms: 'Аварии',
      environmental: 'Среда',
      equipment: 'Оборудование',
    }
    
    const parts: string[] = []
    for (const key of ['alarms', 'environmental', 'equipment']) {
      const sub = subScores[key]
      if (sub && typeof sub === 'object') {
        const w = sub.weight ?? 25
        parts.push(`${labels[key] || key} (${w}%)`)
      }
    }
    return parts.length > 0 ? parts.join(' + ') : ''
  }

</script>

<div class="bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-lg p-6 relative h-full flex flex-col transition-colors">
  <div class="flex items-center justify-between mb-4">
    <div class="text-sm font-semibold text-neutral-600 dark:text-neutral-300 uppercase tracking-wide">
      Индекс здоровья системы
    </div>
    <button
      type="button"
      onclick={() => showFormula = !showFormula}
      class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-700 transition text-neutral-500 dark:text-neutral-400 hover:text-neutral-700 dark:hover:text-neutral-200"
      title={showFormula ? 'Скрыть формулу' : 'Показать формулу расчёта'}
    >
      <Info size={16} />
    </button>
  </div>

  {#if !showFormula}
    <div class="flex items-center justify-center relative mb-4 flex-1">
      <svg width="200" height="200" viewBox="0 0 200 200">
        <circle cx="100" cy="100" r="80" fill="none" stroke="currentColor" class="text-neutral-200 dark:text-neutral-700" stroke-width="14" />
        <circle
          cx="100" cy="100" r="80" fill="none" stroke={color} stroke-width="14"
          stroke-linecap="round"
          stroke-dasharray={circumference}
          stroke-dashoffset={offset}
          transform="rotate(-90 100 100)"
          style="transition: stroke-dashoffset 1s ease-out"
        />
      </svg>
      <div class="absolute inset-0 flex flex-col items-center justify-center">
        <div class="text-6xl font-bold" style="color: {color}">{score}</div>
        <div class="text-sm text-neutral-500 dark:text-neutral-400 mt-1">из 100</div>
      </div>
    </div>
    <div class="text-center mb-2">
      <span class="inline-block px-4 py-1.5 text-xs font-semibold uppercase rounded" style="background: {color}; color: white">
        {statusDisplay}
      </span>
    </div>
    {#if breakdown() && !showFormula}
      <div class="text-center mb-4 text-[11px] text-neutral-400 dark:text-neutral-500 font-mono tabular-nums px-2">
        {score} = {breakdown()}
      </div>
    {/if}
  {:else}
    <div class="text-sm text-neutral-700 dark:text-neutral-300 flex-1 overflow-y-auto">
      <div class="font-semibold text-neutral-900 dark:text-neutral-100 mb-2">Композитная формула</div>
      <div class="p-3 bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-700 rounded font-mono text-xs mb-4">
        score = <span class="text-blue-700 dark:text-blue-400 font-semibold">0.40</span>×Аварии + <span class="text-blue-700 dark:text-blue-400 font-semibold">0.35</span>×Среда + <span class="text-blue-700 dark:text-blue-400 font-semibold">0.25</span>×Оборуд
      </div>

      <div class="font-semibold text-neutral-900 dark:text-neutral-100 mb-2">Штрафы внутри под-индексов</div>
      <div class="border border-neutral-200 dark:border-neutral-700 rounded overflow-hidden mb-4">
        <table class="w-full text-xs">
          <thead class="bg-neutral-50 dark:bg-neutral-900 border-b border-neutral-200 dark:border-neutral-700">
            <tr>
              <th class="text-left px-2 py-2 font-semibold text-neutral-700 dark:text-neutral-300">Категория</th>
              <th class="text-right px-2 py-2 font-semibold text-neutral-700 dark:text-neutral-300">Штраф</th>
            </tr>
          </thead>
          <tbody>
            <tr class="border-t border-neutral-100 dark:border-neutral-700"><td class="px-2 py-1.5 text-neutral-700 dark:text-neutral-300">Авария высокого приоритета (крит.)</td><td class="text-right px-2 py-1.5 font-mono text-red-700 dark:text-red-400 font-semibold">-15 (макс -50)</td></tr>
            <tr class="border-t border-neutral-100 dark:border-neutral-700"><td class="px-2 py-1.5 text-neutral-700 dark:text-neutral-300">Авария среднего приоритета</td><td class="text-right px-2 py-1.5 font-mono text-red-700 dark:text-red-400 font-semibold">-4 (макс -25)</td></tr>
            <tr class="border-t border-neutral-100 dark:border-neutral-700"><td class="px-2 py-1.5 text-neutral-700 dark:text-neutral-300">Авария низкого приоритета</td><td class="text-right px-2 py-1.5 font-mono text-red-700 dark:text-red-400 font-semibold">-0.5 (макс -10)</td></tr>
            <tr class="border-t border-neutral-100 dark:border-neutral-700"><td class="px-2 py-1.5 text-neutral-700 dark:text-neutral-300">Битый датчик</td><td class="text-right px-2 py-1.5 font-mono text-red-700 dark:text-red-400 font-semibold">до -40</td></tr>
            <tr class="border-t border-neutral-100 dark:border-neutral-700"><td class="px-2 py-1.5 text-neutral-700 dark:text-neutral-300">Офлайн тег</td><td class="text-right px-2 py-1.5 font-mono text-red-700 dark:text-red-400 font-semibold">до -30</td></tr>
            <tr class="border-t border-neutral-100 dark:border-neutral-700"><td class="px-2 py-1.5 text-neutral-700 dark:text-neutral-300">Критичный параметр</td><td class="text-right px-2 py-1.5 font-mono text-red-700 dark:text-red-400 font-semibold">score=15</td></tr>
            <tr class="border-t border-neutral-100 dark:border-neutral-700"><td class="px-2 py-1.5 text-neutral-700 dark:text-neutral-300">Параметр с отклонением</td><td class="text-right px-2 py-1.5 font-mono text-red-700 dark:text-red-400 font-semibold">score=55</td></tr>
          </tbody>
        </table>
      </div>

      <div class="text-xs text-neutral-500 dark:text-neutral-400">
        <div class="font-semibold text-neutral-700 dark:text-neutral-300 mb-2">Шкала статуса:</div>
        <div class="grid grid-cols-2 gap-1.5">
          <div><span class="inline-block w-2 h-2 rounded-full bg-red-600 mr-1.5"></span>&lt;30: Критично</div>
          <div><span class="inline-block w-2 h-2 rounded-full bg-amber-600 mr-1.5"></span>30-59: Внимание</div>
          <div><span class="inline-block w-2 h-2 rounded-full bg-blue-600 mr-1.5"></span>60-84: Хорошо</div>
          <div><span class="inline-block w-2 h-2 rounded-full bg-green-600 mr-1.5"></span>≥85: Отлично</div>
        </div>
      </div>
    </div>
  {/if}
</div>
