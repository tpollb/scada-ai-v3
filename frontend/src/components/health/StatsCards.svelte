<script lang="ts">
  interface Props {
    data: Record<string, number>
  }
  let { data }: Props = $props()

  const cards = [
    { key: 'total_alarms_24h', label: 'Аварий за 24ч' },
    { key: 'high_alarms', label: 'High приоритет' },
    { key: 'broken_sensors', label: 'Битых датчиков' },
    { key: 'chattering_tags', label: 'Дребезг тегов' },
    { key: 'online_tags', label: 'Активных тегов' },
    { key: 'offline_tags', label: 'Оффлайн тегов' },
  ]
</script>

<div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
  {#each cards as card}
    {@const value = data?.[card.key] ?? 0}
    {@const isAlert = (card.key === 'high_alarms' && value > 0) || (card.key === 'broken_sensors' && value > 0)}
    <div class="bg-white border rounded p-4 {isAlert ? 'border-red-300 bg-red-50' : 'border-neutral-200'}">
      <div class="text-xs text-neutral-500 uppercase tracking-wide mb-2">
        {card.label}
      </div>
      <div class="text-3xl font-bold tabular-nums {isAlert ? 'text-red-700' : 'text-neutral-900'}">{value}</div>
    </div>
  {/each}
</div>
