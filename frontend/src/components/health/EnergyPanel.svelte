<script lang="ts">
  import { Sun, Moon, Lightbulb, LightbulbOff, MapPinned, Clock } from 'lucide-svelte'
  
  interface Props {
    data: any
  }
  let { data }: Props = $props()
  
  const statusConfig: Record<string, { color: string; bg: string; label: string }> = {
    EXCELLENT: { color: 'text-green-700', bg: 'bg-green-50 border-green-200', label: 'Отличная' },
    GOOD: { color: 'text-blue-700', bg: 'bg-blue-50 border-blue-200', label: 'Хорошая' },
    WARNING: { color: 'text-amber-700', bg: 'bg-amber-50 border-amber-200', label: 'Требует внимания' },
    CRITICAL: { color: 'text-red-700', bg: 'bg-red-50 border-red-200', label: 'Критическая' },
    NO_DATA: { color: 'text-neutral-600', bg: 'bg-neutral-50 border-neutral-200', label: 'Нет данных' },
  }
  
  // Все вычисления через $derived (вместо {@const} в шаблоне)
  let status = $derived(data?.status || 'NO_DATA')
  let cfg = $derived(statusConfig[status] || statusConfig.NO_DATA)
  let byZone = $derived(data?.by_zone || {})
  let zoneEntries = $derived(Object.entries(byZone))
  let timeCtx = $derived(data?.time_context || {})
  let isDay = $derived(timeCtx.is_day ?? true)
  
  // Геолокация и время
  let city = $derived(data?.city || timeCtx.city || 'Не указан')
  let hour = $derived(data?.hour ?? timeCtx.hour ?? null)
  let lat = $derived(data?.latitude ?? data?.time_context?.latitude ?? null)
  let lon = $derived(data?.longitude ?? data?.time_context?.longitude ?? null)
  let timezone = $derived(data?.timezone || data?.time_context?.timezone || timeCtx.timezone || 'UTC')
  
  // Значения для освещения
  let scoreValue = $derived(data?.score ?? '—')
  let onCount = $derived(data?.lighting_on ?? data?.on ?? 0)
  let totalCount = $derived(data?.lighting_total ?? data?.total_fixtures ?? 0)
  let pct = $derived(totalCount > 0 ? Math.round((onCount / totalCount) * 100) : 0)
  
  let expandedZone = $state<string | null>(null)
</script>

<div class="bg-white border border-neutral-200 rounded">
  <div class="px-4 py-3 border-b border-neutral-200">
    <h3 class="text-sm font-semibold text-neutral-900 uppercase tracking-wide">
      Энергоэффективность
    </h3>
  </div>

  <div class="p-4">
    <!-- Header: статус + геолокация + время -->
    <div class="flex items-start justify-between mb-4 gap-3">
      <div class="flex items-center gap-3 flex-shrink-0">
        <div class="text-4xl font-bold tabular-nums text-neutral-900">
          {scoreValue}<span class="text-lg font-normal text-neutral-500">/100</span>
        </div>
        <span class="text-xs px-2 py-1 rounded font-medium border {cfg.bg} {cfg.color}">
          {cfg.label}
        </span>
      </div>
      <div class="text-right text-xs text-neutral-600 space-y-1 min-w-0">
        <div class="flex items-center justify-end gap-1" title={lat != null && lon != null ? `${lat.toFixed(4)}, ${lon.toFixed(4)} | ${timezone}` : `timezone: ${timezone}`}>
          <MapPinned size={12} class="flex-shrink-0" />
          <span class="font-medium truncate">{city}</span>
        </div>
        {#if lat != null && lon != null}
          <div class="font-mono text-[10px] text-neutral-400 tabular-nums" title="Координаты">
            {lat.toFixed(2)}°, {lon.toFixed(2)}°
          </div>
        {:else if city !== 'Не указан'}
          <div class="text-[10px] text-neutral-400 italic">координаты не заданы</div>
        {/if}
        <div class="flex items-center justify-end gap-1">
          <Clock size={12} class="flex-shrink-0" />
          {#if hour != null}
            <span class="font-mono tabular-nums">{String(hour).padStart(2, '0')}:00</span>
            {#if isDay}
              <Sun size={12} class="text-amber-500" title="Дневное время" />
            {:else}
              <Moon size={12} class="text-blue-600" title="Ночное время" />
            {/if}
            <span class="font-medium">{timeCtx.period || (isDay ? 'день' : 'ночь')}</span>
          {:else}
            <span class="text-neutral-400">—</span>
          {/if}
        </div>
      </div>
    </div>
    
    <!-- Основная метрика: включено/всего -->
    <div class="mb-4 p-3 border border-neutral-200 rounded bg-neutral-50">
      <div class="flex items-center justify-between mb-2">
        <div class="text-xs font-semibold text-neutral-700 uppercase tracking-wide">
          Освещение
        </div>
        <div class="text-xs text-neutral-500">
          {totalCount > 0 ? pct + '% включено' : 'нет данных'}
        </div>
      </div>
      <div class="flex items-center gap-4">
        <div class="flex-1">
          <div class="flex items-center gap-3 mb-2">
            <div class="flex items-center gap-1.5 text-green-700">
              <Lightbulb size={16} />
              <span class="text-2xl font-bold tabular-nums">{onCount}</span>
              <span class="text-xs">вкл</span>
            </div>
            <div class="text-neutral-400">/</div>
            <div class="flex items-center gap-1.5 text-neutral-600">
              <LightbulbOff size={16} />
              <span class="text-2xl font-bold tabular-nums">{totalCount}</span>
              <span class="text-xs">всего</span>
            </div>
          </div>
          <!-- Progress bar -->
          <div class="h-2 bg-neutral-200 rounded-full overflow-hidden">
            <div
              class="h-full transition-all duration-500"
              style="width: {pct}%; background: {isDay ? '#16a34a' : '#2563eb'}"
            ></div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Рекомендация -->
    {#if data?.recommendation}
      <div class="mb-4 p-3 {cfg.bg} border rounded text-sm {cfg.color}">
        {data.recommendation}
      </div>
    {/if}
    
    <!-- По зонам (если есть) -->
    {#if zoneEntries.length > 0}
      <div>
        <div class="text-xs font-semibold text-neutral-700 uppercase tracking-wide mb-2">
          По зонам ({zoneEntries.length})
        </div>
        <div class="border border-neutral-200 rounded overflow-hidden">
          {#each zoneEntries as [zoneName, zoneData]}
            {@const zonePct = zoneData.total > 0 ? Math.round(zoneData.on / zoneData.total * 100) : 0}
            <button
              type="button"
              onclick={() => expandedZone = expandedZone === zoneName ? null : zoneName}
              class="w-full text-left px-3 py-2 hover:bg-neutral-50 transition border-t border-neutral-100 first:border-t-0"
            >
              <div class="flex items-center justify-between">
                <div class="flex-1 min-w-0">
                  <div class="text-sm font-medium text-neutral-900 truncate">{zoneName}</div>
                  <div class="text-xs text-neutral-500 mt-0.5">
                    {zoneData.on} вкл / {zoneData.total} всего
                  </div>
                </div>
                <div class="flex items-center gap-2 flex-shrink-0">
                  <div class="w-16 h-1.5 bg-neutral-200 rounded-full overflow-hidden">
                    <div class="h-full" style="width: {zonePct}%; background: {isDay ? '#16a34a' : '#2563eb'}"></div>
                  </div>
                  <span class="text-xs font-mono text-neutral-700 tabular-nums w-10 text-right">{zonePct}%</span>
                </div>
              </div>
            </button>
          {/each}
        </div>
      </div>
    {/if}
    
    {#if status === 'NO_DATA'}
      <div class="text-xs text-neutral-500 mt-3 p-3 bg-neutral-50 rounded border border-neutral-200">
        Для оценки энергоэффективности требуются теги освещения (light, свет, лампа).
      </div>
    {/if}
  </div>
</div>
