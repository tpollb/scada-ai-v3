from pathlib import Path
import os

print('=== cleanup_health_widgets.py ===')
print()

ROOT = Path('.')

# ============================================================================
# 1. Удаляем EnergyPanel.svelte
# ============================================================================
ep_path = ROOT / 'frontend/src/components/health/EnergyPanel.svelte'
if ep_path.exists():
    ep_path.unlink()
    print('✓ Удалён: EnergyPanel.svelte')

# ============================================================================
# 2. WidgetRouter: убираем импорт и case для energy_panel
# ============================================================================
wr_path = ROOT / 'frontend/src/components/WidgetRouter.svelte'
if wr_path.exists():
    wr = wr_path.read_text(encoding='utf-8')
    changed = False
    
    # Убираем импорт EnergyPanel
    if "import EnergyPanel from './health/EnergyPanel.svelte'" in wr:
        wr = wr.replace("  import EnergyPanel from './health/EnergyPanel.svelte'\n", '')
        changed = True
        print('✓ WidgetRouter: убран импорт EnergyPanel')
    
    # Убираем из componentMap
    if "'energy_panel': EnergyPanel," in wr:
        wr = wr.replace("    'energy_panel': EnergyPanel,\n", '')
        changed = True
        print('✓ WidgetRouter: убран energy_panel из componentMap')
    
    if changed:
        wr_path.write_text(wr, encoding='utf-8', newline='\n')

# ============================================================================
# 3. renderers.py: убираем добавление energy_panel в виджеты
# ============================================================================
rend_path = ROOT / 'backend/modules/health/renderers.py'
if rend_path.exists():
    rend = rend_path.read_text(encoding='utf-8')
    
    # Ищем блок: energy = report.energy or {}; if energy: widgets.append(...)
    energy_block = '''    energy = report.energy or {}
    if energy:
        widgets.append({"type": "energy_panel", "data": energy, "size": "wide"})

'''
    if energy_block in rend:
        rend = rend.replace(energy_block, '')
        rend_path.write_text(rend, encoding='utf-8', newline='\n')
        print('✓ renderers.py: убран блок energy_panel')
    elif 'energy_panel' in rend:
        # Альтернативный вариант - одна строка
        for line in rend.split('\n'):
            if 'energy_panel' in line:
                rend = rend.replace(line + '\n', '')
                rend_path.write_text(rend, encoding='utf-8', newline='\n')
                print('✓ renderers.py: убрана строка с energy_panel')
                break

# ============================================================================
# 4. EnvironmentalPanel: делаем сворачиваемым
# ============================================================================
env_path = ROOT / 'frontend/src/components/health/EnvironmentalPanel.svelte'
if env_path.exists():
    env = env_path.read_text(encoding='utf-8')
    
    # Добавляем импорт ChevronDown/ChevronUp если нет
    if 'ChevronDown' not in env:
        env = env.replace(
            "import { ChevronRight, TrendingUp, TrendingDown, Minus, AlertTriangle } from 'lucide-svelte'",
            "import { ChevronRight, ChevronDown, ChevronUp, TrendingUp, TrendingDown, Minus, AlertTriangle } from 'lucide-svelte'"
        )
    
    # Добавляем collapsed state (после let selectedParam)
    if 'let collapsed = $state(true)' not in env:
        env = env.replace(
            '  let selectedParam = $state<string | null>(null)',
            '  let collapsed = $state(true)\n  let selectedParam = $state<string | null>(null)'
        )
    
    # Заменяем заголовок на кнопку
    old_header = '''  <div class="px-4 py-3 border-b border-neutral-200">
    <h3 class="text-sm font-semibold text-neutral-900 uppercase tracking-wide">
      Параметры жизнедеятельности
    </h3>
  </div>'''
    
    new_header = '''  <button
    type="button"
    onclick={() => collapsed = !collapsed}
    class="w-full px-4 py-3 border-b border-neutral-200 flex items-center justify-between hover:bg-neutral-50 transition"
  >
    <h3 class="text-sm font-semibold text-neutral-900 uppercase tracking-wide text-left">
      Параметры жизнедеятельности
    </h3>
    <div class="flex items-center gap-2">
      {#if collapsed}
        <ChevronDown size={16} class="text-neutral-400" />
      {:else}
        <ChevronUp size={16} class="text-neutral-400" />
      {/if}
    </div>
  </button>'''
    
    if old_header in env:
        env = env.replace(old_header, new_header)
    
    # Оборачиваем контент в {#if !collapsed}
    # Контент начинается с <div class="p-4 grid ...
    # И заканчивается перед <!-- Модалка drilldown -->
    if '{#if !collapsed}' not in env:
        env = env.replace(
            '  <div class="p-4 grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-3">',
            '  {#if !collapsed}\n  <div class="p-4 grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-3">'
        )
        env = env.replace(
            '<!-- Модалка drilldown -->',
            '  {/if}\n\n<!-- Модалка drilldown -->'
        )
    
    env_path.write_text(env, encoding='utf-8', newline='\n')
    print('✓ EnvironmentalPanel: сворачиваемый (по умолчанию свёрнут)')

# ============================================================================
# 5. AlarmsPanel: делаем сворачиваемым
# ============================================================================
al_path = ROOT / 'frontend/src/components/health/AlarmsPanel.svelte'
if al_path.exists():
    al = al_path.read_text(encoding='utf-8')
    
    # Добавляем импорты
    if 'ChevronDown' not in al:
        al = al.replace(
            "import { ChevronRight, X, AlertTriangle } from 'lucide-svelte'",
            "import { ChevronRight, ChevronDown, ChevronUp, X, AlertTriangle } from 'lucide-svelte'"
        )
    
    # Добавляем collapsed state
    if 'let collapsed = $state(true)' not in al:
        al = al.replace(
            '  let showDetail = $state(false)',
            '  let collapsed = $state(true)\n  let showDetail = $state(false)'
        )
    
    # Заменяем заголовок на кнопку
    old_header = '''  <div class="px-4 py-3 border-b border-neutral-200 flex items-center justify-between">
    <h3 class="text-sm font-semibold text-neutral-900 uppercase tracking-wide">Аварии</h3>
    <div class="flex items-center gap-3 text-xs">
      <span class="text-neutral-500">Всего: <span class="font-bold tabular-nums text-neutral-900">{total}</span></span>
      <span class="text-neutral-500">Активных: <span class="font-bold tabular-nums text-neutral-900">{active}</span></span>
    </div>
  </div>'''
    
    new_header = '''  <button
    type="button"
    onclick={() => collapsed = !collapsed}
    class="w-full px-4 py-3 border-b border-neutral-200 flex items-center justify-between hover:bg-neutral-50 transition"
  >
    <h3 class="text-sm font-semibold text-neutral-900 uppercase tracking-wide text-left">Аварии</h3>
    <div class="flex items-center gap-3">
      <div class="flex items-center gap-3 text-xs">
        <span class="text-neutral-500">Всего: <span class="font-bold tabular-nums text-neutral-900">{total}</span></span>
        <span class="text-neutral-500">Активных: <span class="font-bold tabular-nums text-neutral-900">{active}</span></span>
      </div>
      {#if collapsed}
        <ChevronDown size={16} class="text-neutral-400" />
      {:else}
        <ChevronUp size={16} class="text-neutral-400" />
      {/if}
    </div>
  </button>'''
    
    if old_header in al:
        al = al.replace(old_header, new_header)
    
    # Оборачиваем контент
    if '{#if !collapsed}' not in al:
        al = al.replace(
            '  <div class="p-4">\n    <div class="grid grid-cols-3 gap-2 mb-4">',
            '  {#if !collapsed}\n  <div class="p-4">\n    <div class="grid grid-cols-3 gap-2 mb-4">'
        )
        al = al.replace(
            '<!-- Модалка с журналом аварий -->',
            '  {/if}\n\n<!-- Модалка с журналом аварий -->'
        )
    
    al_path.write_text(al, encoding='utf-8', newline='\n')
    print('✓ AlarmsPanel: сворачиваемый (по умолчанию свёрнут)')

# ============================================================================
# 6. IssuesList: делаем сворачиваемым
# ============================================================================
il_path = ROOT / 'frontend/src/components/health/IssuesList.svelte'
if il_path.exists():
    il = il_path.read_text(encoding='utf-8')
    
    # Добавляем импорты
    if 'ChevronDown' not in il:
        il = il.replace(
            '<script lang="ts">',
            '<script lang="ts">\n  import { ChevronDown, ChevronUp } from \'lucide-svelte\''
        )
    
    # Добавляем collapsed state
    if 'let collapsed = $state(true)' not in il:
        il = il.replace(
            '  let issues = $derived(data?.issues ?? [])',
            '  let collapsed = $state(true)\n\n  let issues = $derived(data?.issues ?? [])'
        )
    
    # Заменяем заголовок
    old_header = '''  <div class="px-4 py-3 border-b border-neutral-200 dark:border-neutral-700 flex items-center justify-between">
    <h3 class="text-sm font-semibold text-neutral-900 dark:text-neutral-100">
      Обнаруженные проблемы
    </h3>
    <span class="text-xs text-neutral-500 dark:text-neutral-400 tabular-nums">{issues.length}</span>
  </div>'''
    
    new_header = '''  <button
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
  </button>'''
    
    if old_header in il:
        il = il.replace(old_header, new_header)
    
    # Оборачиваем контент
    if '{#if !collapsed}' not in il:
        il = il.replace(
            '  {#if issues.length === 0}',
            '  {#if !collapsed}\n  {#if issues.length === 0}'
        )
        # Закрываем {#if !collapsed} перед самым концом компонента (перед последним </div>)
        last_div = il.rfind('</div>')
        if last_div > 0:
            il = il[:last_div] + '  {/if}\n\n' + il[last_div:]
    
    il_path.write_text(il, encoding='utf-8', newline='\n')
    print('✓ IssuesList: сворачиваемый (по умолчанию свёрнут)')

# ============================================================================
# 7. HealthScoreCard: добавляем детализацию под статусом
# ============================================================================
hs_path = ROOT / 'frontend/src/components/health/HealthScoreCard.svelte'
if hs_path.exists():
    hs = hs_path.read_text(encoding='utf-8')
    
    # Обновляем Props чтобы принимать sub_scores
    if 'sub_scores?: any' not in hs:
        hs = hs.replace(
            'data: { score: number; status: string; status_ru?: string }',
            'data: { score: number; status: string; status_ru?: string; sub_scores?: any }'
        )
    
    # Добавляем переменные для расчёта
    calc_vars = '''
  let subScores = $derived(data?.sub_scores ?? {})
  
  // Формируем строку детализации: "Аварии 18 + Среда 22 + Оборудование 12 + Энергия 3"
  let breakdown = $derived(() => {
    const labels: Record<string, string> = {
      alarms: 'Аварии',
      environmental: 'Среда',
      equipment: 'Оборудование',
      energy: 'Энергия',
    }
    const weights: Record<string, number> = {
      alarms: 35,
      environmental: 30,
      equipment: 25,
      energy: 10,
    }
    const parts: string[] = []
    for (const key of ['alarms', 'environmental', 'equipment', 'energy']) {
      const sub = subScores[key]
      if (sub) {
        const s = sub.score ?? 75
        const w = weights[key] ?? 25
        const contrib = Math.round(s * w / 100)
        parts.push(`${labels[key]} ${contrib}`)
      }
    }
    return parts.length > 0 ? parts.join(' + ') : ''
  })
'''
    
    if 'let subScores = $derived' not in hs:
        hs = hs.replace(
            '  let offset = $derived(circumference - (score / 100) * circumference)',
            '  let offset = $derived(circumference - (score / 100) * circumference)\n' + calc_vars
        )
    
    # Добавляем детализацию ПОД плашкой статуса (перед {:else})
    old_status_block = '''    <div class="text-center mb-4">
      <span class="inline-block px-4 py-1.5 text-xs font-semibold uppercase rounded" style="background: {color}; color: white">
        {statusDisplay}
      </span>
    </div>
  {:else}'''
    
    new_status_block = '''    <div class="text-center mb-2">
      <span class="inline-block px-4 py-1.5 text-xs font-semibold uppercase rounded" style="background: {color}; color: white">
        {statusDisplay}
      </span>
    </div>
    {#if breakdown() && !showFormula}
      <div class="text-center mb-4 text-[11px] text-neutral-400 dark:text-neutral-500 font-mono tabular-nums px-2">
        {score} = {breakdown()}
      </div>
    {/if}
  {:else}'''
    
    if old_status_block in hs:
        hs = hs.replace(old_status_block, new_status_block)
    
    hs_path.write_text(hs, encoding='utf-8', newline='\n')
    print('✓ HealthScoreCard: добавлена детализация расчёта под статусом')

# ============================================================================
# 8. LifeSupportCard: добавляем детализацию под статусом
# ============================================================================
ls_path = ROOT / 'frontend/src/components/health/LifeSupportCard.svelte'
if ls_path.exists():
    ls = ls_path.read_text(encoding='utf-8')
    
    # Добавляем переменные для расчёта
    calc_vars = '''
  
  // Формируем строку детализации: "CO2 30 + Температура 25 + VOC 3 + Влажность 15 + Давление 10"
  let breakdown = $derived(() => {
    const weights: Record<string, number> = {
      co2: 30,
      temperature: 25,
      voc: 20,
      humidity: 15,
      pressure: 10,
    }
    const labels: Record<string, string> = {
      co2: 'CO2',
      temperature: 'Темп',
      voc: 'VOC',
      humidity: 'Влажн',
      pressure: 'Давл',
    }
    const parts: string[] = []
    for (const key of ['co2', 'temperature', 'voc', 'humidity', 'pressure']) {
      const p = params[key]
      if (p) {
        const s = p.score ?? 0
        const w = weights[key] ?? 0
        const contrib = Math.round(s * w / 100)
        parts.push(`${labels[key]} ${contrib}`)
      }
    }
    return parts.length > 0 ? parts.join(' + ') : ''
  })
'''
    
    if 'let breakdown = $derived' not in ls:
        ls = ls.replace(
            '  let offset = $derived(circumference - (score / 100) * circumference)',
            '  let offset = $derived(circumference - (score / 100) * circumference)' + calc_vars
        )
    
    # Добавляем детализацию ПОД плашкой статуса
    old_status_block = '''    <div class="text-center mb-4">
      <span class="inline-block px-4 py-1.5 text-xs font-semibold uppercase rounded" style="background: {color}; color: white">
        {statusDisplay}
      </span>
    </div>


  {:else}'''
    
    new_status_block = '''    <div class="text-center mb-2">
      <span class="inline-block px-4 py-1.5 text-xs font-semibold uppercase rounded" style="background: {color}; color: white">
        {statusDisplay}
      </span>
    </div>
    {#if breakdown() && !showFormula}
      <div class="text-center mb-4 text-[11px] text-neutral-400 dark:text-neutral-500 font-mono tabular-nums px-2">
        {score} = {breakdown()}
      </div>
    {/if}
  {:else}'''
    
    if old_status_block in ls:
        ls = ls.replace(old_status_block, new_status_block)
    
    ls_path.write_text(ls, encoding='utf-8', newline='\n')
    print('✓ LifeSupportCard: добавлена детализация расчёта под статусом')

# ============================================================================
# 9. renderers.py: передаём sub_scores в health_score виджет
# ============================================================================
if rend_path.exists():
    rend = rend_path.read_text(encoding='utf-8')
    
    old_health_score = '''    widgets.append({
        "type": "health_score",
        "data": {
            "score": report.score,
            "status": report.status,
            "status_ru": translate_status(report.status),
            "sub_scores": report.sub_scores,
        },
        "size": "medium",
    })'''
    
    if old_health_score in rend:
        print('ℹ renderers.py: sub_scores уже передаётся в health_score')
    elif '"sub_scores": report.sub_scores' in rend:
        print('ℹ renderers.py: sub_scores уже есть')
    else:
        # Ищем блок health_score и добавляем sub_scores
        old_block = '''        "type": "health_score",
        "data": {
            "score": report.score,
            "status": report.status,
            "status_ru": translate_status(report.status),
        },'''
        new_block = '''        "type": "health_score",
        "data": {
            "score": report.score,
            "status": report.status,
            "status_ru": translate_status(report.status),
            "sub_scores": report.sub_scores,
        },'''
        if old_block in rend:
            rend = rend.replace(old_block, new_block)
            rend_path.write_text(rend, encoding='utf-8', newline='\n')
            print('✓ renderers.py: добавлен sub_scores в health_score виджет')

print()
print('=' * 60)
print('ЧТО СДЕЛАНО:')
print('=' * 60)
print()
print('1. УДАЛЕНО:')
print('   • EnergyPanel.svelte (файл)')
print('   • Упоминания в WidgetRouter и renderers.py')
print()
print('2. СВОРАЧИВАЕМЫЕ БЛОКИ (по умолчанию свёрнуты):')
print('   • EnvironmentalPanel (Параметры жизнедеятельности)')
print('   • AlarmsPanel (Аварии)')
print('   • IssuesList (Обнаруженные проблемы)')
print()
print('3. ДЕТАЛИЗАЦИЯ РАСЧЁТА:')
print('   • HealthScoreCard: под статусом серым моноширинным текстом')
print('     "55 = Аварии 18 + Среда 22 + Оборудование 12 + Энергия 3"')
print('   • LifeSupportCard: под статусом серым моноширинным текстом')
print('     "83 = CO2 30 + Темп 25 + VOC 3 + Влажн 15 + Давл 10"')
print()
print('Backend перезагрузится автоматически.')
print('Frontend подхватит через HMR.')
print()
print('Проверь:')
print('  • Энергоэффективность должна исчезнуть')
print('  • 3 блока должны быть свёрнуты с шевроном ▼')
print('  • Под статусами индексов — компактная формула расчёта')
print()
print('Когда ок — скажи "косметика ок" и коммитим v3.1.0')