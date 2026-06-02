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
    <div class="bg-white dark:bg-neutral-800 border rounded p-4 transition-colors {isAlert ? 'border-red-300 dark:border-red-700 bg-red-50 dark:bg-red-900/20' : 'border-neutral-200 dark:border-neutral-700'}">
      <div class="text-xs text-neutral-500 dark:text-neutral-400 uppercase tracking-wide mb-2">
        {card.label}
      </div>
      <div class="text-3xl font-bold tabular-nums {isAlert ? 'text-red-700 dark:text-red-400' : 'text-neutral-900 dark:text-neutral-100'}">{value}</div>
    </div>
  {/each}
</div>
