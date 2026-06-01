<script lang="ts">
  interface Props {
    data: { issues: any[] }
  }
  let { data }: Props = $props()

  let issues = $derived(data?.issues ?? [])

  const severityColors: Record<string, string> = {
    critical: 'border-l-red-600',
    major: 'border-l-amber-600',
    warning: 'border-l-blue-600',
    info: 'border-l-neutral-400',
  }
</script>

<div class="bg-white border border-neutral-200 rounded">
  <div class="px-4 py-3 border-b border-neutral-200 flex items-center justify-between">
    <h3 class="text-sm font-semibold text-neutral-900">
      Обнаруженные проблемы
    </h3>
    <span class="text-xs text-neutral-500 tabular-nums">{issues.length}</span>
  </div>

  {#if issues.length === 0}
    <div class="p-8 text-center text-neutral-500 text-sm">
      Проблем не обнаружено
    </div>
  {:else}
    <div class="divide-y divide-neutral-100">
      {#each issues as issue}
        <div class="p-4 border-l-4 {severityColors[issue.severity] || 'border-l-neutral-400'}">
          <div class="flex items-start gap-3">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-1">
                <span class="text-xs font-semibold uppercase text-neutral-500">
                  {issue.category}
                </span>
                <span class="text-xs px-2 py-0.5 bg-neutral-100 text-neutral-700 rounded font-medium">
                  {issue.severity}
                </span>
              </div>
              <h4 class="font-semibold text-neutral-900 mb-1">{issue.title}</h4>
              <p class="text-sm text-neutral-700 mb-2">{issue.details}</p>
              <div class="text-sm text-neutral-600 bg-neutral-50 rounded p-2">
                <span class="font-medium">Рекомендация:</span> {issue.recommendation}
              </div>
            </div>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>
