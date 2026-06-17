<script lang="ts">
  interface Props {
    value: number
    onValueChange?: (v: number) => void
  }

  let { value = 30, onValueChange }: Props = $props()

  const periods = [
    { label: '7д', value: 7 },
    { label: '30д', value: 30 },
    { label: '90д', value: 90 },
    { label: '365д', value: 365 },
  ]

  function select(v: number) {
    if (onValueChange) onValueChange(v)
  }
</script>

<div class="flex items-center gap-1 bg-neutral-100 dark:bg-neutral-800 rounded-lg p-1">
  {#each periods as p}
    <button
      type="button"
      onclick={() => select(p.value)}
      class="px-3 py-1 text-xs font-medium rounded-md transition-colors
        {value === p.value 
          ? 'bg-white dark:bg-neutral-700 text-neutral-900 dark:text-neutral-100 shadow-sm' 
          : 'text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-200'}"
    >
      {p.label}
    </button>
  {/each}
</div>
