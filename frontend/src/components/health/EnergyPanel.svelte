<script lang="ts">
  import { Sun, Moon, Lightbulb, LightbulbOff, MapPinned, Clock } from 'lucide-svelte'
  
  interface Props {
    data: any
  }
  let { data }: Props = $props()
  
  const statusConfig: Record<string, { color: string; bg: string; label: string }> = {
    EXCELLENT: { color: 'text-green-700 dark:text-green-400', bg: 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800/40', label: 'Отличная' },
    GOOD: { color: 'text-blue-700 dark:text-blue-400', bg: 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800/40', label: 'Хорошая' },
    WARNING: { color: 'text-amber-700 dark:text-amber-400', bg: 'bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800/40', label: 'Требует внимания' },
    CRITICAL: { color: 'text-red-700 dark:text-red-400', bg: 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800/40', label: 'Критическая' },
    NO_DATA: { color: 'text-neutral-600 dark:text-neutral-400', bg: 'bg-neutral-50 dark:bg-neutral-800 border-neutral-200 dark:border-neutral-700', label: 'Нет данных' },
  }
  
  let status = $derived(data?.status || 'NO_DATA')
  let cfg = $derived(statusConfig[status] || statusConfig.NO_DATA)
  let byZone = $derived(data?.by_zone || {})
  let zoneEntries = $derived(Object.entries(byZone))
  let timeCtx = $derived(data?.time_context || {})
  let isDay = $derived(timeCtx.is_day ?? true)
  
  let city = $derived(data?.city || timeCtx.city || 'Не указан')
  let hour = $derived(data?.hour ?? timeCtx.hour ?? null)
  let lat = $derived(data?.latitude ?? data?.time_context?.latitude ?? timeCtx.latitude ?? null)
  let lon = $derived(data?.longitude ?? data?.time_context?.longitude ?? timeCtx.longitude ?? null)
  let timezone = $derived(data?.timezone || data?.time_context?.timezone || timeCtx.timezone || 'UTC')
  
  let scoreValue = $derived(data?.score ?? '—')
  let onCount = $derived(data?.lighting_on ?? data?.on ?? 0)
  let totalCount = $derived(data?.lighting_total ?? data?.total_fixtures ?? 0)
  let pct = $derived(totalCount > 0 ? Math.round((onCount / totalCount) * 100) : 0)
  
  let expandedZone = $state<string | null>(null)
</script>

<div class="bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded transition-colors">
  <div class="px-4 py-3 border-b border-neutral-200 dark:border-neutral-700">
    <h3 class="text-sm font-semibold text-neutral-900 dark:text-neutral-100 uppercase tracking-wide">
      Энергоэффективность
    </h3>
  </div>

  <div class="p-4">
    <div class="flex items-start justify-between mb-4 gap-3">
      <div class="flex items-center gap-3 flex-shrink-0">
        <div class="text-4xl font-bold tabular-nums text-neutral-900 dark:text-neutral-100">
          {scoreValue}<span class="text-lg font-normal text-neutral-500 dark:text-neutral-400">/100</span>
        </div>
        <span class="text-xs px-2 py-1 rounded font-medium border {cfg.bg} {cfg.color}">
          {cfg.label}
        </span>
      </div>
      <div class="text-right text-xs text-neutral-600 dark:text-neutral-400 space-y-1 min-w-0">
        <div class="flex items-center justify-end gap-1" title={lat != null && lon != null ? `${lat.toFixed(4)}, ${lon.toFixed(4)} | ${timezone}` : `timezone: ${timezone}`}>
          <MapPinned size={12} class="flex-shrink-0" />
          <span class="font-medium truncate">{city}</span>
        </div>
        {#if lat != null && lon != null}
          <div class="font-mono text-[10px] text-neutral-400 dark:text-neutral-500 tabular-nums" title="Координаты">
            {lat.toFixed(2)}°, {lon.toFixed(2)}°
          </div>
        {:else if city !== 'Не указан'}
          <div class="text-[10px] text-neutral-400 dark:text-neutral-500 italic">координаты не заданы</div>
        {/if}
        <div class="flex items-center justify-end gap-1">
          <Clock size={12} class="flex-shrink-0" />
          {#if hour != null}
            <span class="font-mono tabular-nums">{String(hour).padStart(2, '0')}:00</span>
            {#if isDay}
              <Sun size={12} class="text-amber-500" title="Дневное время" />
            {:else}
              <Moon size={12} class="text-blue-400 dark:text-blue-300" title="Ночное время" />
            {/if}
            <span class="font-medium">{timeCtx.period || (isDay ? 'день' : 'ночь')}</span>
          {:else}
            <span class="text-neutral-400">—</span>
          {/if}
        </div>
      </div>
    </div>
    
    <div class="mb-4 p-3 border border-neutral-200 dark:border-neutral-700 rounded bg-neutral-50 dark:bg-neutral-900">
      <div class="flex items-center justify-between mb-2">
        <div class="text-xs font-semibold text-neutral-700 dark:text-neutral-300 uppercase tracking-wide">
          Освещение
        </div>
        <div class="text-xs text-neutral-500 dark:text-neutral-400">
          {totalCount > 0 ? pct + '% включено' : 'нет данных'}
        </div>
      </div>
      <div class="flex items-center gap-4">
        <div class="flex-1">
          <div class="flex items-center gap-3 mb-2">
            <div class="flex items-center gap-1.5 text-green-700 dark:text-green-400">
              <Lightbulb size={16} />
              <span class="text-2xl font-bold tabular-nums">{onCount}</span>
              <span class="text-xs">вкл</span>
            </div>
            <div class="text-neutral-400 dark:text-neutral-500">/</div>
            <div class="flex items-center gap-1.5 text-neutral-600 dark:text-neutral-400">
              <LightbulbOff size={16} />
              <span class="text-2xl font-bold tabular-nums">{totalCount}</span>
              <span class="text-xs">всего</span>
            </div>
          </div>
          <div class="h-2 bg-neutral-200 dark:bg-neutral-700 rounded-full overflow-hidden">
            <div
              class="h-full transition-all duration-500"
              style="width: {pct}%; background: {isDay ? '#16a34a' : '#2563eb'}"
            ></div>
          </div>
        </div>
      </div>
    </div>
    
    {#if data?.recommendation}
      <div class="mb-4 p-3 {cfg.bg} border rounded text-sm {cfg.color}">
        {data.recommendation}
      </div>
    {/if}
    
    {#if zoneEntries.length > 0}
      <div>
        <div class="text-xs font-semibold text-neutral-700 dark:text-neutral-300 uppercase tracking-wide mb-2">
          По зонам ({zoneEntries.length})
        </div>
        <div class="border border-neutral-200 dark:border-neutral-700 rounded overflow-hidden">
          {#each zoneEntries as [zoneName, zoneData]}
            {@const zonePct = zoneData.total > 0 ? Math.round(zoneData.on / zoneData.total * 100) : 0}
            <button
              type="button"
              onclick={() => expandedZone = expandedZone === zoneName ? null : zoneName}
              class="w-full text-left px-3 py-2 hover:bg-neutral-50 dark:hover:bg-neutral-700 transition border-t border-neutral-100 dark:border-neutral-700 first:border-t-0"
            >
              <div class="flex items-center justify-between">
                <div class="flex-1 min-w-0">
                  <div class="text-sm font-medium text-neutral-900 dark:text-neutral-100 truncate">{zoneName}</div>
                  <div class="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">
                    {zoneData.on} вкл / {zoneData.total} всего
                  </div>
                </div>
                <div class="flex items-center gap-2 flex-shrink-0">
                  <div class="w-16 h-1.5 bg-neutral-200 dark:bg-neutral-700 rounded-full overflow-hidden">
                    <div class="h-full" style="width: {zonePct}%; background: {isDay ? '#16a34a' : '#2563eb'}"></div>
                  </div>
                  <span class="text-xs font-mono text-neutral-700 dark:text-neutral-300 tabular-nums w-10 text-right">{zonePct}%</span>
                </div>
              </div>
            </button>
          {/each}
        </div>
      </div>
    {/if}
    
    {#if status === 'NO_DATA'}
      <div class="text-xs text-neutral-500 dark:text-neutral-400 mt-3 p-3 bg-neutral-50 dark:bg-neutral-900 rounded border border-neutral-200 dark:border-neutral-700">
        Для оценки энергоэффективности требуются теги освещения (light, свет, лампа).
      </div>
    {/if}
  </div>
</div>
