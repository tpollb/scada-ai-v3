<script lang="ts">
  import { ChevronDown, ChevronUp } from 'lucide-svelte'
  interface Props {
    data: { issues: any[] }
  }
  let { data }: Props = $props()

  let collapsed = $state(true)

  let issues = $derived(data?.issues ?? [])

  const severityColors: Record<string, string> = {
    critical: 'border-l-red-600',
    major: 'border-l-amber-600',
    warning: 'border-l-blue-600',
    info: 'border-l-neutral-400',
  }
</script>

<div class="bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded transition-colors">
  <button
    type="button"
    onclick={() => collapsed = !collapsed}
    class="w-full px-4 py-3 border-b border-neutral-200 dark:border-neutral-700 flex items-center justify-between hover:bg-neutral-50 dark:hover:bg-neutral-700 transition"
  >
    <h3 class="text-sm font-semibold text-neutral-900 dark:text-neutral-100 text-left">
      Обнаруженные проблемы
    </h3>
    <div class="flex items-center gap-3">
      <span class="text-xs text-neutral-500 dark:text-neutral-400 tabular-nums">{issues.length}</span>
      {#if collapsed}
        <ChevronDown size={16} class="text-neutral-400" />
      {:else}
        <ChevronUp size={16} class="text-neutral-400" />
      {/if}
    </div>
  </button>

  {#if !collapsed}
  {#if issues.length === 0}
    <div class="p-8 text-center text-neutral-500 dark:text-neutral-400 text-sm">
      Проблем не обнаружено
    </div>
  {:else}
    <div class="divide-y divide-neutral-100 dark:divide-neutral-700">
      {#each issues as issue}
        <div class="p-4 border-l-4 {severityColors[issue.severity] || 'border-l-neutral-400'}">
          <div class="flex items-start gap-3">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-1">
                <span class="text-xs font-semibold uppercase text-neutral-500 dark:text-neutral-400">
                  {issue.category}
                </span>
                <span class="text-xs px-2 py-0.5 bg-neutral-100 dark:bg-neutral-700 text-neutral-700 dark:text-neutral-300 rounded font-medium">
                  {issue.severity}
                </span>
              </div>
              <h4 class="font-semibold text-neutral-900 dark:text-neutral-100 mb-1">{issue.title}</h4>
              <p class="text-sm text-neutral-700 dark:text-neutral-300 mb-2">{issue.details}</p>
              <div class="text-sm text-neutral-600 dark:text-neutral-400 bg-neutral-50 dark:bg-neutral-900 rounded p-2">
                <span class="font-medium">Рекомендация:</span> {issue.recommendation}
              </div>
            </div>
          </div>
        </div>
      {/each}
    </div>
  {/if}
  {/if}

</div>
