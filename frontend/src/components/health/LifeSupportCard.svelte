<script lang="ts">
  import { Info } from 'lucide-svelte'
  
  interface Props {
    data: {
      score: number
      status: string
      status_ru?: string
      params: Record<string, any>
      problems?: string[]
    }
  }
  let { data }: Props = $props()
  let showFormula = $state(false)
  
  let score = $derived(data?.score ?? 0)
  let status = $derived(data?.status ?? 'NO_DATA')
  let statusDisplay = $derived(data?.status_ru || status)
  let params = $derived(data?.params ?? {})
  let problems = $derived(data?.problems ?? [])
  
  let color = $derived(
    status === 'NO_DATA' ? '#a3a3a3' :
    score < 30 ? '#dc2626' : 
    score < 60 ? '#d97706' : 
    score < 85 ? '#2563eb' : '#16a34a'
  )
  let circumference = 2 * Math.PI * 80
  let offset = $derived(circumference - (score / 100) * circumference)
  
  // Формируем строку детализации: "CO2 30 + Температура 25 + VOC 3 + Влажность 15 + Давление 10"
  function breakdown(): string {
    const weights: Record<string, number> = {
      co2: 30,
      temperature: 25,
      voc: 20,
      humidity: 15,
      pressure: 10,
    }
    const labels: Record<string, string> = {
      co2: 'CO2',
      temperature: 'Темп',
      voc: 'VOC',
      humidity: 'Влажн',
      pressure: 'Давл',
    }
    const parts: string[] = []
    for (const key of ['co2', 'temperature', 'voc', 'humidity', 'pressure']) {
      const p = params[key]
      if (p) {
        const s = p.score ?? 0
        const w = weights[key] ?? 0
        const contrib = Math.round(s * w / 100)
        parts.push(`${labels[key]} ${contrib}`)
      }
    }
    return parts.length > 0 ? parts.join(' + ') : ''
  }

  
  const paramLabels: Record<string, { label: string; unit: string; weight: number }> = {
    co2: { label: 'CO2', unit: 'ppm', weight: 30 },
    temperature: { label: 'Температура', unit: '°C', weight: 25 },
    voc: { label: 'VOC', unit: 'мг/м³', weight: 20 },
    humidity: { label: 'Влажность', unit: '%', weight: 15 },
    pressure: { label: 'Давление', unit: 'мм рт.ст.', weight: 10 },
  }
  
  const paramOrder = ['co2', 'temperature', 'voc', 'humidity', 'pressure']
  
  function paramStatusColor(s: string): string {
    // Поддерживаем и английские и русские статусы
    if (s === 'CRITICAL' || s === 'Критично') return '#dc2626'
    if (s === 'WARNING' || s === 'Внимание') return '#d97706'
    if (s === 'OK' || s === 'Норма') return '#16a34a'
    return '#a3a3a3'
  }
</script>

<div class="bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-lg p-6 h-full flex flex-col transition-colors">
  <div class="flex items-center justify-between mb-4">
    <div class="text-sm font-semibold text-neutral-600 dark:text-neutral-300 uppercase tracking-wide">
      Индекс жизнеобеспечения
    </div>
    <button
      type="button"
      onclick={() => showFormula = !showFormula}
      class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-700 transition text-neutral-500 dark:text-neutral-400 hover:text-neutral-700 dark:hover:text-neutral-200"
      title={showFormula ? 'Скрыть формулу' : 'Показать формулу'}
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
      <div class="font-semibold text-neutral-900 dark:text-neutral-100 mb-2">Формула расчёта</div>
      <div class="p-3 bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-700 rounded font-mono text-xs mb-4 leading-relaxed">
        score = взвешенная сумма статусов 5 параметров:<br>
        <span class="text-blue-700 dark:text-blue-400 font-semibold">0.30</span>×CO2 + 
        <span class="text-blue-700 dark:text-blue-400 font-semibold">0.25</span>×Темп + 
        <span class="text-blue-700 dark:text-blue-400 font-semibold">0.20</span>×VOC + 
        <span class="text-blue-700 dark:text-blue-400 font-semibold">0.15</span>×Влажн + 
        <span class="text-blue-700 dark:text-blue-400 font-semibold">0.10</span>×Давл
      </div>

      <div class="font-semibold text-neutral-900 dark:text-neutral-100 mb-2">Статусы параметров</div>
      <div class="border border-neutral-200 dark:border-neutral-700 rounded overflow-hidden mb-4">
        <table class="w-full text-xs">
          <thead class="bg-neutral-50 dark:bg-neutral-900 border-b border-neutral-200 dark:border-neutral-700">
            <tr>
              <th class="text-left px-2 py-2 font-semibold text-neutral-700 dark:text-neutral-300">Параметр</th>
              <th class="text-right px-2 py-2 font-semibold text-neutral-700 dark:text-neutral-300">Статус → Балл</th>
            </tr>
          </thead>
          <tbody>
            <tr class="border-t border-neutral-100 dark:border-neutral-700"><td class="px-2 py-1.5 text-green-700 dark:text-green-400 font-medium">Норма</td><td class="text-right px-2 py-1.5 font-mono font-semibold">100 баллов</td></tr>
            <tr class="border-t border-neutral-100 dark:border-neutral-700"><td class="px-2 py-1.5 text-amber-700 dark:text-amber-400 font-medium">Внимание</td><td class="text-right px-2 py-1.5 font-mono font-semibold">55 баллов</td></tr>
            <tr class="border-t border-neutral-100 dark:border-neutral-700"><td class="px-2 py-1.5 text-red-700 dark:text-red-400 font-medium">Критично</td><td class="text-right px-2 py-1.5 font-mono font-semibold">15 баллов</td></tr>
          </tbody>
        </table>
      </div>

      <div class="font-semibold text-neutral-900 dark:text-neutral-100 mb-2">Текущие компоненты</div>
      <div class="border border-neutral-200 dark:border-neutral-700 rounded overflow-hidden mb-4">
        <table class="w-full text-xs">
          <thead class="bg-neutral-50 dark:bg-neutral-900 border-b border-neutral-200 dark:border-neutral-700">
            <tr>
              <th class="text-left px-2 py-2 font-semibold text-neutral-700 dark:text-neutral-300">Параметр</th>
              <th class="text-center px-2 py-2 font-semibold text-neutral-700 dark:text-neutral-300">Вес</th>
              <th class="text-center px-2 py-2 font-semibold text-neutral-700 dark:text-neutral-300">Статус</th>
              <th class="text-right px-2 py-2 font-semibold text-neutral-700 dark:text-neutral-300">Балл</th>
              <th class="text-right px-2 py-2 font-semibold text-neutral-700 dark:text-neutral-300">Вклад</th>
            </tr>
          </thead>
          <tbody>
            {#each paramOrder as key}
              {@const cfg = paramLabels[key]}
              {@const p = params[key]}
              {@const paramLabel = p?.label_ru || cfg.label}
              {#if p && cfg}
                {@const pStatus = p.status_ru || p.status || 'NO_DATA'}
                {@const pScore = p.score ?? 0}
                {@const contribution = (pScore * cfg.weight / 100).toFixed(1)}
                <tr class="border-t border-neutral-100 dark:border-neutral-700">
                  <td class="px-2 py-1.5 text-neutral-700 dark:text-neutral-300 font-medium">{paramLabel}</td>
                  <td class="text-center px-2 py-1.5 font-mono text-neutral-600 dark:text-neutral-400">{cfg.weight}%</td>
                  <td class="text-center px-2 py-1.5">
                    <span class="text-xs px-1.5 py-0.5 rounded font-medium" style="background: {paramStatusColor(pStatus)}20; color: {paramStatusColor(pStatus)}">{pStatus}</span>
                  </td>
                  <td class="text-right px-2 py-1.5 font-mono font-semibold" style="color: {paramStatusColor(pStatus)}">{pScore}</td>
                  <td class="text-right px-2 py-1.5 font-mono text-neutral-700 dark:text-neutral-300">+{contribution}</td>
                </tr>
              {/if}
            {/each}
          </tbody>
        </table>
      </div>

      <div class="text-xs text-neutral-500 dark:text-neutral-400">
        <div class="font-semibold text-neutral-700 dark:text-neutral-300 mb-2">Шкала итогового статуса:</div>
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
