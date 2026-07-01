<script lang="ts">
  import { Play, Activity, X, Search, CheckSquare, Square, ArrowRightLeft } from 'lucide-svelte'
  import ABComparisonModal from './ABComparisonModal.svelte'

  interface Props {
    tags: any[]
    selectedTags: string[]
    period: number
    isAnalyzing: boolean
    error: string | null
    onTagsChange: (tags: string[]) => void
    onPeriodChange: (period: number) => void
    onRunAnalysis: () => void
    onClose: () => void
    onABResult?: (result: any) => void
  }

  let { 
    tags, 
    selectedTags, 
    period, 
    isAnalyzing, 
    error,
    onTagsChange, 
    onPeriodChange, 
    onRunAnalysis,
    onClose,
    onABResult
  }: Props = $props()

  let abModalOpen = $state(false)
  let searchQuery = $state('')

  // Фильтруем теги по поиску
  let filteredTags = $derived(
    tags.filter(tag => 
      tag.tag_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (tag.zone_name || '').toLowerCase().includes(searchQuery.toLowerCase())
    )
  )

  function toggleTag(tagName: string) {
    const newSelection = selectedTags.includes(tagName)
      ? selectedTags.filter(t => t !== tagName)
      : [...selectedTags, tagName]
    onTagsChange(newSelection)
  }

  function selectAll() {
    onTagsChange(filteredTags.map(t => t.tag_name))
  }

  function clearAll() {
    onTagsChange([])
  }
</script>

<div class="w-[350px] h-full bg-white dark:bg-neutral-900 border-r border-neutral-200 dark:border-neutral-700 flex flex-col overflow-hidden transition-colors">
  <!-- Header -->
  <div class="flex items-center justify-between px-4 py-3 border-b border-neutral-200 dark:border-neutral-700 flex-shrink-0">
    <div class="flex items-center gap-2">
      <Activity size={18} class="text-blue-500" />
      <h2 class="text-base font-semibold leading-6 text-neutral-900 dark:text-neutral-100 my-0">
        Deep Analysis
      </h2>
    </div>
    <button
      type="button"
      onclick={onClose}
      class="p-1 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition"
      title="Закрыть"
    >
      <X size={16} class="text-neutral-500" />
    </button>
  </div>

  <div class="flex-1 overflow-y-auto px-4 py-3 space-y-3">
    <!-- Period selector -->
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

    <!-- Tags selector with search -->
    <div>
      <label class="block text-xs font-medium text-neutral-600 dark:text-neutral-400 mb-1">
        Теги (выбрано: {selectedTags.length})
      </label>
      
      <!-- Search input -->
      <div class="relative mb-2">
        <Search size={14} class="absolute left-2 top-1/2 -translate-y-1/2 text-neutral-400" />
        <input
          type="text"
          placeholder="Поиск тегов..."
          bind:value={searchQuery}
          class="w-full pl-7 pr-3 py-1.5 text-sm border border-neutral-300 dark:border-neutral-600 rounded bg-white dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <!-- Select all / Clear -->
      <div class="flex gap-2 mb-2">
        <button
          type="button"
          onclick={selectAll}
          class="flex-1 px-2 py-1 text-xs bg-neutral-100 dark:bg-neutral-800 hover:bg-neutral-200 dark:hover:bg-neutral-700 text-neutral-700 dark:text-neutral-300 rounded transition flex items-center justify-center gap-1"
        >
          <CheckSquare size={12} />
          Выбрать все
        </button>
        <button
          type="button"
          onclick={clearAll}
          class="flex-1 px-2 py-1 text-xs bg-neutral-100 dark:bg-neutral-800 hover:bg-neutral-200 dark:hover:bg-neutral-700 text-neutral-700 dark:text-neutral-300 rounded transition flex items-center justify-center gap-1"
        >
          <Square size={12} />
          Очистить
        </button>
      </div>

      <!-- Tags list -->
      <div class="max-h-60 overflow-y-auto border border-neutral-200 dark:border-neutral-700 rounded">
        {#each filteredTags as tag}
          <button
            type="button"
            onclick={() => toggleTag(tag.tag_name)}
            class="w-full px-2 py-1.5 text-xs text-left hover:bg-neutral-100 dark:hover:bg-neutral-800 transition flex items-center gap-2 border-b border-neutral-100 dark:border-neutral-800 last:border-0 {selectedTags.includes(tag.tag_name) ? 'bg-blue-50 dark:bg-blue-900/20' : ''}"
          >
            {#if selectedTags.includes(tag.tag_name)}
              <CheckSquare size={14} class="text-blue-500 flex-shrink-0" />
            {:else}
              <Square size={14} class="text-neutral-400 flex-shrink-0" />
            {/if}
            <div class="flex-1 min-w-0">
              <div class="truncate text-neutral-900 dark:text-neutral-100">{tag.tag_name}</div>
              {#if tag.zone_name}
                <div class="text-[10px] text-neutral-500 dark:text-neutral-400 truncate">{tag.zone_name}</div>
              {/if}
            </div>
          </button>
        {/each}
        
        {#if filteredTags.length === 0}
          <div class="px-2 py-4 text-xs text-center text-neutral-400">
            Теги не найдены
          </div>
        {/if}
      </div>

      <div class="text-[10px] text-neutral-500 dark:text-neutral-400 mt-1">
        1 тег = статистика + аномалии · 2+ тега = корреляции
      </div>
    </div>

    <!-- Run button -->
    <button
      type="button"
      onclick={onRunAnalysis}
      disabled={isAnalyzing || selectedTags.length === 0}
      class="w-full px-4 py-2 bg-blue-500 hover:bg-blue-600 disabled:bg-neutral-300 dark:disabled:bg-neutral-700 text-white text-sm font-medium rounded transition flex items-center justify-center gap-2"
    >
      {#if isAnalyzing}
        <div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
        Анализ...
      {:else}
        <Play size={14} />
        Запустить анализ ({selectedTags.length} {selectedTags.length === 1 ? 'тег' : 'тегов'})
      {/if}
    </button>

    <!-- A/B сравнение -->
    <button
      type="button"
      onclick={() => abModalOpen = true}
      disabled={selectedTags.length === 0}
      class="w-full mt-2 px-4 py-2 bg-neutral-100 dark:bg-neutral-800 hover:bg-neutral-200 dark:hover:bg-neutral-700 disabled:opacity-50 text-neutral-700 dark:text-neutral-300 text-sm font-medium rounded transition flex items-center justify-center gap-2"
    >
      <ArrowRightLeft size={14} />
      Сравнить периоды (A/B)
    </button>

    {#if error}
      <div class="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded text-sm text-red-700 dark:text-red-300">
        {error}
      </div>
    {/if}
  </div>

  <!-- A/B Comparison Modal -->
  <ABComparisonModal
    isOpen={abModalOpen}
    availableTags={tags.map((t: any) => t.tag_name)}
    defaultTag={selectedTags[0]}
    onClose={() => abModalOpen = false}
    onResult={(result) => {
      if (onABResult) onABResult(result)
    }}
  />
</div>
