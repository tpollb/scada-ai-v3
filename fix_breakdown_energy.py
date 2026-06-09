from pathlib import Path

print('=== fix_breakdown_energy.py ===')
print()

# ============================================================================
# 1. analysis.py: убираем "energy" из sub_scores, меняем веса
# ============================================================================
analysis_path = Path('backend/modules/health/analysis.py')
if analysis_path.exists():
    content = analysis_path.read_text(encoding='utf-8')
    
    old_sub_scores = '''        sub_scores={
            "alarms": {"score": alarm_idx, "weight": 35},
            "environmental": {"score": env_idx, "weight": 30},
            "equipment": {"score": equip_idx, "weight": 25},
            "energy": {"score": energy_idx, "weight": 10},
        },'''
    
    new_sub_scores = '''        sub_scores={
            "alarms": {"score": alarm_idx, "weight": 40},
            "environmental": {"score": env_idx, "weight": 35},
            "equipment": {"score": equip_idx, "weight": 25},
        },'''
    
    if old_sub_scores in content:
        content = content.replace(old_sub_scores, new_sub_scores)
        analysis_path.write_text(content, encoding='utf-8', newline='\n')
        print('✓ analysis.py: убрана "Энергия" из sub_scores')
        print('  Веса: 35+30+25+10 → 40+35+25')
    else:
        print('⚠ Точный паттерн sub_scores не найден')

# ============================================================================
# 2. HealthScoreCard: убираем "Энергия" из breakdown, показываем веса
# ============================================================================
hs_path = Path('frontend/src/components/health/HealthScoreCard.svelte')
if hs_path.exists():
    hs = hs_path.read_text(encoding='utf-8')
    
    old_breakdown = '''  // Формируем строку детализации: "Аварии 18 + Среда 22 + Оборудование 12 + Энергия 3"
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
    
    new_breakdown = '''  // Формируем строку детализации: "Аварии (40%) + Среда (35%) + Оборудование (25%)"
  function breakdown(): string {
    if (!subScores || Object.keys(subScores).length === 0) return ''
    
    const labels: Record<string, string> = {
      alarms: 'Аварии',
      environmental: 'Среда',
      equipment: 'Оборудование',
    }
    
    const parts: string[] = []
    for (const key of ['alarms', 'environmental', 'equipment']) {
      const sub = subScores[key]
      if (sub && typeof sub === 'object') {
        const w = sub.weight ?? 25
        parts.push(`${labels[key] || key} (${w}%)`)
      }
    }
    return parts.length > 0 ? parts.join(' + ') : ''
  }'''
    
    if old_breakdown in hs:
        hs = hs.replace(old_breakdown, new_breakdown)
        print('✓ HealthScoreCard: breakdown обновлён')
        print('  • Убрана "Энергия"')
        print('  • Показываем веса: "Аварии (40%) + Среда (35%) + Оборудование (25%)"')
    else:
        print('⚠ Точный паттерн breakdown не найден')
    
    # Обновляем формулу в showFormula
    old_formula = 'score = <span class="text-blue-700 dark:text-blue-400 font-semibold">0.35</span>×Аварии + <span class="text-blue-700 dark:text-blue-400 font-semibold">0.30</span>×Среда + <span class="text-blue-700 dark:text-blue-400 font-semibold">0.25</span>×Оборуд + <span class="text-blue-700 dark:text-blue-400 font-semibold">0.10</span>×Энергия'
    
    new_formula = 'score = <span class="text-blue-700 dark:text-blue-400 font-semibold">0.40</span>×Аварии + <span class="text-blue-700 dark:text-blue-400 font-semibold">0.35</span>×Среда + <span class="text-blue-700 dark:text-blue-400 font-semibold">0.25</span>×Оборуд'
    
    if old_formula in hs:
        hs = hs.replace(old_formula, new_formula)
        print('✓ HealthScoreCard: формула в showFormula обновлена')
    else:
        print('⚠ Точный паттерн формулы не найден')
    
    hs_path.write_text(hs, encoding='utf-8', newline='\n')

print()
print('=' * 60)
print('ИЗМЕНЕНИЯ:')
print('=' * 60)
print()
print('1. analysis.py:')
print('   • Убрана "Энергия" из sub_scores')
print('   • Веса: 35+30+25+10=100 → 40+35+25=100')
print()
print('2. HealthScoreCard:')
print('   • breakdown() показывает веса вместо вкладов')
print('   • Было: "65 = Аварии 5 + Среда 25 + Оборудование 5 + Энергия 5"')
print('   • Стало: "65 = Аварии (40%) + Среда (35%) + Оборудование (25%)"')
print('   • Формула в showFormula: убрана "Энергия"')
print()
print('Backend перезагрузится, frontend подхватит через HMR.')
print('Напиши "покажи здоровье здания" — проверь детализацию.')
print()
print('Когда ок — скажи "breakdown ок" и коммитим v3.1.0')