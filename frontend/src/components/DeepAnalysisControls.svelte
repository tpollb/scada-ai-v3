<script lang="ts">
  import { Play, Activity, X } from 'lucide-svelte'

  interface Props {
    tags: any[]
    selectedTag: string
    period: number
    isAnalyzing: boolean
    error: string | null
    onTagChange: (tag: string) => void
    onPeriodChange: (period: number) => void
    onRunAnalysis: () => void
    onClose: () => void
  }

  let { 
    tags, 
    selectedTag, 
    period, 
    isAnalyzing, 
    error,
    onTagChange, 
    onPeriodChange, 
    onRunAnalysis,
    onClose
  }: Props = $props()
</script>

<div class="w-[350px] h-full bg-white dark:bg-neutral-900 border-r border-neutral-200 dark:border-neutral-700 flex flex-col overflow-hidden transition-colors">
  <div class="flex items-center justify-between px-4 py-3 border-b border-neutral-200 dark:border-neutral-700 flex-shrink-0">
    <div class="flex items-center gap-2">
      <Activity size={18} class="text-blue-500" />
      <h2 class="text-base font-semibold text-neutral-900 dark:text-neutral-100">
        Deep Analysis
      </h2>
    </div>
    <button
      type="button"
      onclick={onClose}
      class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition"
      title="Закрыть"
    >
      <X size={16} class="text-neutral-500" />
    </button>
  </div>

  <div class="flex-1 overflow-y-auto px-4 py-3 space-y-3">
    <div>
      <label class="block text-xs font-medium text-neutral-600 dark:text-neutral-400 mb-1">
        Тег
      </label>
      <select
        value={selectedTag}
        onchange={(e) => onTagChange(e.currentTarget.value)}
        class="w-full px-3 py-1.5 text-sm border border-neutral-300 dark:border-neutral-600 rounded bg-white dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        {#each tags as tag}
          <option value={tag.tag_name}>
            {tag.tag_name}
            {#if tag.zone_name}({tag.zone_name}){/if}
          </option>
        {/each}
      </select>
    </div>

    <div>
      <label class="block text-xs font-medium text-neutral-600 dark:text-neutral-400 mb-1">
        Период
      </label>
      <div class="flex gap-1">
        {#each [7, 30, 120, 365] as p}
          <button
            type="button"
            onclick={() => onPeriodChange(p)}
            class="flex-1 px-2 py-1 text-xs rounded transition {period === p
              ? 'bg-blue-500 text-white'
              : 'bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 hover:bg-neutral-200 dark:hover:bg-neutral-700'}"
          >
            {p}д
          </button>
        {/each}
      </div>
    </div>

    <button
      type="button"
      onclick={onRunAnalysis}
      disabled={isAnalyzing || !selectedTag}
      class="w-full px-4 py-2 bg-blue-500 hover:bg-blue-600 disabled:bg-neutral-300 dark:disabled:bg-neutral-700 text-white text-sm font-medium rounded transition flex items-center justify-center gap-2"
    >
      {#if isAnalyzing}
        <div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
        Анализ...
      {:else}
        <Play size={14} />
        Запустить анализ
      {/if}
    </button>

    {#if error}
      <div class="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded text-sm text-red-700 dark:text-red-300">
        {error}
      </div>
    {/if}
  </div>
</div>
