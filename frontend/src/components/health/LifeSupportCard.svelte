<script lang="ts">
  import { Info } from 'lucide-svelte'
  
  interface Props {
    data: {
      score: number
      status: string
      params: Record<string, any>
      problems?: string[]
    }
  }
  let { data }: Props = $props()
  let showFormula = $state(false)
  
  let score = $derived(data?.score ?? 0)
  let status = $derived(data?.status ?? 'NO_DATA')
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
  
  const paramLabels: Record<string, { label: string; unit: string; weight: number }> = {
    co2: { label: 'CO2', unit: 'ppm', weight: 30 },
    temperature: { label: 'Температура', unit: '°C', weight: 25 },
    voc: { label: 'VOC', unit: 'мг/м³', weight: 20 },
    humidity: { label: 'Влажность', unit: '%', weight: 15 },
    pressure: { label: 'Давление', unit: 'мм рт.ст.', weight: 10 },
  }
  
  const paramOrder = ['co2', 'temperature', 'voc', 'humidity', 'pressure']
  
  function paramStatusColor(s: string): string {
    if (s === 'CRITICAL') return '#dc2626'
    if (s === 'WARNING') return '#d97706'
    if (s === 'OK') return '#16a34a'
    if (s === 'NO_DATA') return '#a3a3a3'
    return '#a3a3a3'
  }
</script>

<div class="bg-white border border-neutral-200 rounded-lg p-6 h-full flex flex-col">
  <div class="flex items-center justify-between mb-4">
    <div class="text-sm font-semibold text-neutral-600 uppercase tracking-wide">
      Индекс жизнеобеспечения
    </div>
    <button
      type="button"
      onclick={() => showFormula = !showFormula}
      class="p-1.5 rounded hover:bg-neutral-100 transition text-neutral-500 hover:text-neutral-700"
      title={showFormula ? 'Скрыть формулу' : 'Показать формулу расчёта'}
    >
      <Info size={16} />
    </button>
  </div>

  {#if !showFormula}
    <!-- Крупный круглый индекс -->
    <div class="flex items-center justify-center relative mb-4 flex-1">
      <svg width="200" height="200" viewBox="0 0 200 200">
        <circle cx="100" cy="100" r="80" fill="none" stroke="#e5e5e5" stroke-width="14" />
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
        <div class="text-sm text-neutral-500 mt-1">из 100</div>
      </div>
    </div>
    <div class="text-center mb-4">
      <span class="inline-block px-4 py-1.5 text-xs font-semibold uppercase rounded" style="background: {color}; color: white">
        {status}
      </span>
    </div>

    <!-- Проблемы (если есть) -->
    {#if problems.length > 0}
      <div class="pt-4 border-t border-neutral-200">
        <div class="text-xs text-red-700 font-semibold mb-2 uppercase tracking-wide">
          Проблемы ({problems.length})
        </div>
        <div class="space-y-1.5">
          {#each problems.slice(0, 4) as p}
            <div class="text-sm text-red-700 flex items-start gap-2">
              <span class="text-red-500 flex-shrink-0 mt-1">●</span>
              <span class="leading-snug">{p}</span>
            </div>
          {/each}
          {#if problems.length > 4}
            <div class="text-xs text-neutral-500 mt-1 pl-5">...и ещё {problems.length - 4}</div>
          {/if}
        </div>
      </div>
    {/if}
  {:else}
    <!-- Формула -->
    <div class="text-sm text-neutral-700 flex-1 overflow-y-auto">
      <div class="font-semibold text-neutral-900 mb-2">Формула расчёта</div>
      <div class="p-3 bg-neutral-50 border border-neutral-200 rounded font-mono text-xs mb-4 leading-relaxed">
        score = взвешенная сумма статусов 5 параметров:<br>
        <span class="text-blue-700 font-semibold">0.30</span>×CO2 + 
        <span class="text-blue-700 font-semibold">0.25</span>×Темп + 
        <span class="text-blue-700 font-semibold">0.20</span>×VOC + 
        <span class="text-blue-700 font-semibold">0.15</span>×Влажн + 
        <span class="text-blue-700 font-semibold">0.10</span>×Давл
      </div>

      <div class="font-semibold text-neutral-900 mb-2">Статусы параметров</div>
      <div class="border border-neutral-200 rounded overflow-hidden mb-4">
        <table class="w-full text-xs">
          <thead class="bg-neutral-50 border-b border-neutral-200">
            <tr>
              <th class="text-left px-2 py-2 font-semibold text-neutral-700">Параметр</th>
              <th class="text-right px-2 py-2 font-semibold text-neutral-700">Статус → Балл</th>
            </tr>
          </thead>
          <tbody>
            <tr class="border-t border-neutral-100"><td class="px-2 py-1.5 text-green-700 font-medium">OK</td><td class="text-right px-2 py-1.5 font-mono font-semibold">100 баллов</td></tr>
            <tr class="border-t border-neutral-100"><td class="px-2 py-1.5 text-amber-700 font-medium">WARNING</td><td class="text-right px-2 py-1.5 font-mono font-semibold">55 баллов</td></tr>
            <tr class="border-t border-neutral-100"><td class="px-2 py-1.5 text-red-700 font-medium">CRITICAL</td><td class="text-right px-2 py-1.5 font-mono font-semibold">15 баллов</td></tr>
          </tbody>
        </table>
      </div>

      <div class="font-semibold text-neutral-900 mb-2">Текущие компоненты</div>
      <div class="border border-neutral-200 rounded overflow-hidden mb-4">
        <table class="w-full text-xs">
          <thead class="bg-neutral-50 border-b border-neutral-200">
            <tr>
              <th class="text-left px-2 py-2 font-semibold text-neutral-700">Параметр</th>
              <th class="text-center px-2 py-2 font-semibold text-neutral-700">Вес</th>
              <th class="text-center px-2 py-2 font-semibold text-neutral-700">Статус</th>
              <th class="text-right px-2 py-2 font-semibold text-neutral-700">Балл</th>
              <th class="text-right px-2 py-2 font-semibold text-neutral-700">Вклад</th>
            </tr>
          </thead>
          <tbody>
            {#each paramOrder as key}
              {@const cfg = paramLabels[key]}
              {@const p = params[key]}
              {#if p && cfg}
                {@const pStatus = p.status ?? 'NO_DATA'}
                {@const pScore = p.score ?? 0}
                {@const contribution = (pScore * cfg.weight / 100).toFixed(1)}
                <tr class="border-t border-neutral-100">
                  <td class="px-2 py-1.5 text-neutral-700 font-medium">{cfg.label}</td>
                  <td class="text-center px-2 py-1.5 font-mono text-neutral-600">{cfg.weight}%</td>
                  <td class="text-center px-2 py-1.5">
                    <span class="text-xs px-1.5 py-0.5 rounded font-medium" style="background: {paramStatusColor(pStatus)}20; color: {paramStatusColor(pStatus)}">{pStatus}</span>
                  </td>
                  <td class="text-right px-2 py-1.5 font-mono font-semibold" style="color: {paramStatusColor(pStatus)}">{pScore}</td>
                  <td class="text-right px-2 py-1.5 font-mono text-neutral-700">+{contribution}</td>
                </tr>
              {/if}
            {/each}
          </tbody>
        </table>
      </div>

      <div class="text-xs text-neutral-500">
        <div class="font-semibold text-neutral-700 mb-2">Шкала итогового статуса:</div>
        <div class="grid grid-cols-2 gap-1.5">
          <div><span class="inline-block w-2 h-2 rounded-full bg-red-600 mr-1.5"></span>&lt;30: CRITICAL</div>
          <div><span class="inline-block w-2 h-2 rounded-full bg-amber-600 mr-1.5"></span>30-59: WARNING</div>
          <div><span class="inline-block w-2 h-2 rounded-full bg-blue-600 mr-1.5"></span>60-84: GOOD</div>
          <div><span class="inline-block w-2 h-2 rounded-full bg-green-600 mr-1.5"></span>≥85: EXCELLENT</div>
        </div>
      </div>
    </div>
  {/if}
</div>
