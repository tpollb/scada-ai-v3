<script lang="ts">
  import HealthScoreCard from './health/HealthScoreCard.svelte'
  import StatsCards from './health/StatsCards.svelte'
  import IssuesList from './health/IssuesList.svelte'
  import EnvironmentalPanel from './health/EnvironmentalPanel.svelte'
  import AlarmsPanel from './health/AlarmsPanel.svelte'
  import EnergyPanel from './health/EnergyPanel.svelte'
  import LifeSupportCard from './health/LifeSupportCard.svelte'
  import { ChevronDown, ChevronUp, X } from 'lucide-svelte'

  interface Props {
    widgets: any[]
    onClose?: () => void
  }

  let { widgets = [], onClose }: Props = $props()
  let collapsed = $state(false)

  const componentMap: Record<string, any> = {
    'health_score': HealthScoreCard,
    'life_support_card': LifeSupportCard,
    'stats_cards': StatsCards,
    'issues_list': IssuesList,
    'environmental_panel': EnvironmentalPanel,
    'alarms_panel': AlarmsPanel,
    'energy_panel': EnergyPanel,
  }

  function handleClose() {
    if (onClose) onClose()
  }

  function toggleCollapse() {
    collapsed = !collapsed
  }

  // Debug: логируем что пришло
  $effect(() => {
    console.log('[WidgetRouter] widgets received:', widgets.length, widgets.map(w => ({ type: w.type, size: w.size })))
  })

  // Выделяем первые два medium виджета для grid (health_score + life_support)
  let mediumWidgets = $derived(widgets.filter(w => w.size === 'medium'))
  let otherWidgets = $derived(widgets.filter(w => w.size !== 'medium'))
</script>

{#if widgets && widgets.length > 0}
  <div class="border-t border-neutral-200 bg-neutral-50">
    <div class="flex items-center justify-between px-4 py-2 bg-white border-b border-neutral-200 sticky top-0 z-10">
      <button type="button" onclick={toggleCollapse} class="flex items-center gap-2 text-sm font-semibold text-neutral-700 hover:text-neutral-900 transition">
        {#if collapsed}<ChevronDown size={16} />{:else}<ChevronUp size={16} />{/if}
        Визуализация ({widgets.length} {widgets.length === 1 ? 'виджет' : widgets.length < 5 ? 'виджета' : 'виджетов'})
      </button>
      <button type="button" onclick={handleClose} class="p-1 rounded hover:bg-neutral-100 transition text-neutral-500 hover:text-neutral-700" title="Закрыть виджеты">
        <X size={18} />
      </button>
    </div>

    {#if !collapsed}
      <div class="space-y-4 p-4 max-h-[75vh] overflow-y-auto">
        <!-- Medium виджеты в grid 2 колонки (health_score + life_support) -->
        {#if mediumWidgets.length > 0}
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            {#each mediumWidgets as widget}
              {@const Component = componentMap[widget.type]}
              {#if Component}
                <div class="min-w-0">
                  <Component data={widget.data} />
                </div>
              {:else}
                <div class="bg-yellow-50 border border-yellow-200 rounded p-3 text-sm text-yellow-800">
                  Виджет не найден: {widget.type}
                </div>
              {/if}
            {/each}
          </div>
        {/if}
        
        <!-- Остальные виджеты (wide) -->
        {#each otherWidgets as widget}
          {@const Component = componentMap[widget.type]}
          {#if Component}
            <div class="w-full">
              <Component data={widget.data} />
            </div>
          {:else}
            <div class="bg-yellow-50 border border-yellow-200 rounded p-3 text-sm text-yellow-800">
              Виджет не найден: {widget.type}
            </div>
          {/if}
        {/each}
      </div>
    {/if}
  </div>
{/if}
