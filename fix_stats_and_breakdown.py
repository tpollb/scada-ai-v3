from pathlib import Path

print('=== fix_stats_and_breakdown.py ===')
print()

# ============================================================================
# 1. Удаляем stats_cards из renderers.py
# ============================================================================
rend_path = Path('backend/modules/health/renderers.py')
if rend_path.exists():
    rend = rend_path.read_text(encoding='utf-8')
    
    # Ищем блок stats_cards
    stats_block = '''    if report.stats:
        widgets.append({"type": "stats_cards", "data": report.stats, "size": "wide"})

'''
    
    if stats_block in rend:
        rend = rend.replace(stats_block, '')
        rend_path.write_text(rend, encoding='utf-8', newline='\n')
        print('✓ renderers.py: удалён блок stats_cards')
    else:
        # Пробуем альтернативный паттерн
        for line in rend.split('\n'):
            if 'stats_cards' in line:
                rend = rend.replace(line + '\n', '')
                rend_path.write_text(rend, encoding='utf-8', newline='\n')
                print('✓ renderers.py: удалена строка со stats_cards')
                break

# ============================================================================
# 2. Удаляем stats_cards из WidgetRouter.svelte
# ============================================================================
wr_path = Path('frontend/src/components/WidgetRouter.svelte')
if wr_path.exists():
    wr = wr_path.read_text(encoding='utf-8')
    changed = False
    
    # Убираем импорт
    if "import StatsCards from './health/StatsCards.svelte'" in wr:
        wr = wr.replace("  import StatsCards from './health/StatsCards.svelte'\n", '')
        changed = True
        print('✓ WidgetRouter: убран импорт StatsCards')
    
    # Убираем из componentMap
    if "'stats_cards': StatsCards," in wr:
        wr = wr.replace("    'stats_cards': StatsCards,\n", '')
        changed = True
        print('✓ WidgetRouter: убран stats_cards из componentMap')
    
    if changed:
        wr_path.write_text(wr, encoding='utf-8', newline='\n')

# ============================================================================
# 3. Удаляем StatsCards.svelte
# ============================================================================
sc_path = Path('frontend/src/components/health/StatsCards.svelte')
if sc_path.exists():
    sc_path.unlink()
    print('✓ Удалён файл: StatsCards.svelte')

# ============================================================================
# 4. Починить breakdown в HealthScoreCard
# ============================================================================
hs_path = Path('frontend/src/components/health/HealthScoreCard.svelte')
if hs_path.exists():
    hs = hs_path.read_text(encoding='utf-8')
    
    # Заменяем $derived(() => {...}) на обычную функцию
    old_breakdown = '''  // Формируем строку детализации: "Аварии 18 + Среда 22 + Оборудование 12 + Энергия 3"
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
  })'''
    
    new_breakdown = '''  // Формируем строку детализации: "Аварии 18 + Среда 22 + Оборудование 12 + Энергия 3"
  function breakdown(): string {
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
  }'''
    
    if old_breakdown in hs:
        hs = hs.replace(old_breakdown, new_breakdown)
        hs_path.write_text(hs, encoding='utf-8', newline='\n')
        print('✓ HealthScoreCard: breakdown заменён на обычную функцию')
    elif '$derived(() =>' in hs:
        # Альтернативный фикс
        hs = hs.replace('let breakdown = $derived(() => {', 'function breakdown(): string {')
        hs = hs.replace("    return parts.length > 0 ? parts.join(' + ') : ''\n  })", 
                       "    return parts.length > 0 ? parts.join(' + ') : ''\n  }")
        hs_path.write_text(hs, encoding='utf-8', newline='\n')
        print('✓ HealthScoreCard: breakdown исправлен (альтернативный метод)')

# ============================================================================
# 5. Починить breakdown в LifeSupportCard
# ============================================================================
ls_path = Path('frontend/src/components/health/LifeSupportCard.svelte')
if ls_path.exists():
    ls = ls_path.read_text(encoding='utf-8')
    
    # Заменяем $derived(() => {...}) на обычную функцию
    old_breakdown = '''  
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
  })'''
    
    new_breakdown = '''  
  // Формируем строку детализации: "CO2 30 + Температура 25 + VOC 3 + Влажность 15 + Давление 10"
  function breakdown(): string {
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
  }'''
    
    if old_breakdown in ls:
        ls = ls.replace(old_breakdown, new_breakdown)
        ls_path.write_text(ls, encoding='utf-8', newline='\n')
        print('✓ LifeSupportCard: breakdown заменён на обычную функцию')
    elif '$derived(() =>' in ls:
        # Альтернативный фикс
        ls = ls.replace('let breakdown = $derived(() => {', 'function breakdown(): string {')
        ls = ls.replace("    return parts.length > 0 ? parts.join(' + ') : ''\n  })", 
                       "    return parts.length > 0 ? parts.join(' + ') : ''\n  }")
        ls_path.write_text(ls, encoding='utf-8', newline='\n')
        print('✓ LifeSupportCard: breakdown исправлен (альтернативный метод)')

print()
print('=' * 60)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 60)
print()
print('1. УДАЛЕНО:')
print('   • stats_cards виджет из renderers.py')
print('   • StatsCards из WidgetRouter (импорт + componentMap)')
print('   • Файл StatsCards.svelte')
print()
print('2. ПОЧИНЕН breakdown:')
print('   • HealthScoreCard: $derived(() =>) → function breakdown()')
print('   • LifeSupportCard: $derived(() =>) → function breakdown()')
print()
print('Backend перезагрузится автоматически.')
print('Frontend подхватит через HMR.')
print()
print('Ожидаемый результат:')
print('  • Блок "Аварии за 24ч" исчезнет')
print('  • Под статусом HealthScoreCard:')
print('    "55 = Аварии 18 + Среда 22 + Оборудование 12 + Энергия 3"')
print('  • Под статусом LifeSupportCard:')
print('    "83 = CO2 30 + Темп 25 + VOC 3 + Влажн 15 + Давл 10"')
print()
print('Когда всё работает — скажи "финальная косметика ок" и коммитим v3.1.0')