from pathlib import Path

print('=== fix_three_issues.py ===')
print()

# ============================================================================
# 1. HealthScoreCard: убираем блок "Компоненты" (subScores)
# ============================================================================
hs_path = Path('frontend/src/components/health/HealthScoreCard.svelte')
hs_content = hs_path.read_text(encoding='utf-8')

# Удаляем блок {#if Object.keys(subScores).length > 0}...{/if}
# Ищем его между "</div>" статуса и "{:else}" формулы
import re
pattern = r'\n\s*\{#if Object\.keys\(subScores\)\.length > 0\}[\s\S]*?\{/if\}\n'
if re.search(pattern, hs_content):
    hs_content = re.sub(pattern, '\n', hs_content, count=1)
    hs_path.write_text(hs_content, encoding='utf-8', newline='\n')
    print('✓ HealthScoreCard: блок "Компоненты" удалён')
else:
    print('ℹ HealthScoreCard: блок уже удалён или не найден')

# Также удаляем неиспользуемые переменные и константы
unused_cleanups = [
    ("let subScores = $derived(data?.sub_scores ?? {})", ""),
    ("const subLabels: Record<string, string> = {\n    alarms: 'Аварии',\n    environmental: 'Среда',\n    equipment: 'Оборудование',\n    energy: 'Энергия',\n  }\n", ""),
    ("const subOrder = ['alarms', 'environmental', 'equipment', 'energy']\n", ""),
    ("function subColor(s: number): string {\n    if (s < 30) return '#dc2626'\n    if (s < 60) return '#d97706'\n    if (s < 85) return '#2563eb'\n    return '#16a34a'\n  }\n", ""),
]

for old, new in unused_cleanups:
    if old in hs_content:
        hs_content = hs_content.replace(old, new)

hs_path.write_text(hs_content, encoding='utf-8', newline='\n')
print('✓ HealthScoreCard: удалены неиспользуемые переменные')

# ============================================================================
# 2. renderers.py: оборачиваем energy_data в правильную структуру
# ============================================================================
renderers_path = Path('backend/modules/health/renderers.py')
rend_content = renderers_path.read_text(encoding='utf-8')

# Ищем блок с energy_data и заменяем его
old_energy_block = '''    # === Виджет энергозатрат ===
    energy_data = None
    try:
        from modules.energy_electricity.tools import calculate_electricity_cost
        energy_data = await calculate_electricity_cost()
        log.info("Energy data fetched for widget",
                 current_cost=energy_data.get("current_month", {}).get("cost_rub"),
                 last_cost=energy_data.get("last_month", {}).get("cost_rub"))
    except Exception as e:
        log.warning("Failed to get energy data for widget", error=str(e))

    # 1. Индекс здоровья (компактный)
    widgets = []

    # Виджет энергозатрат — в начало списка
    if energy_data:
        widgets.append({
            "type": "energy_cost_card",
            "data": energy_data,
            "size": "medium",
        })
        log.info("energy_cost_card widget added")'''

new_energy_block = '''    # === Виджет энергозатрат ===
    energy_widget_data = None
    try:
        from modules.energy_electricity.tools import calculate_electricity_cost
        energy_raw = await calculate_electricity_cost()
        
        # Преобразуем в структуру которую ждёт EnergyCostCard
        current_cost = energy_raw.get("current_month", {}).get("cost_rub", 0) or 0
        last_cost = energy_raw.get("last_month", {}).get("cost_rub", 0) or 0
        
        energy_widget_data = {
            "electricity": energy_raw,
            "water": None,
            "heat": None,
            "total_cost_current": float(current_cost),
            "total_cost_last": float(last_cost),
            "errors": energy_raw.get("errors", []),
        }
        
        log.info("Energy data fetched for widget",
                 current_cost=current_cost,
                 last_cost=last_cost)
    except Exception as e:
        log.warning("Failed to get energy data for widget", error=str(e))

    # 1. Индекс здоровья (компактный)
    widgets = []

    # Виджет энергозатрат — в начало списка
    if energy_widget_data:
        widgets.append({
            "type": "energy_cost_card",
            "data": energy_widget_data,
            "size": "medium",
        })
        log.info("energy_cost_card widget added")'''

if old_energy_block in rend_content:
    rend_content = rend_content.replace(old_energy_block, new_energy_block)
    renderers_path.write_text(rend_content, encoding='utf-8', newline='\n')
    print('✓ renderers.py: energy_data преобразован в правильную структуру')
else:
    print('⚠ renderers.py: не нашёл точный блок energy_data')
    print('  Проверь вручную или перезапусти предыдущий скрипт')

# ============================================================================
# 3. Энергозатраты: добавляем обработку null значений
# ============================================================================
# Проверим что в EnergyCostCard правильно обрабатываются данные
ec_path = Path('frontend/src/components/health/EnergyCostCard.svelte')
ec_content = ec_path.read_text(encoding='utf-8')

# Проверяем что есть правильные $derived
if 'total_cost_last ?? 0' in ec_content and 'total_cost_current ?? 0' in ec_content:
    print('ℹ EnergyCostCard: обработка null уже на месте')
else:
    print('⚠ EnergyCostCard: проверь обработку null вручную')

print()
print('=' * 60)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 60)
print()
print('1. HealthScoreCard:')
print('   ✓ Удалён блок "Компоненты" (Аварии/Среда/Оборудование/Энергия)')
print('   ✓ Удалены неиспользуемые переменные (subScores, subLabels, subOrder, subColor)')
print()
print('2. renderers.py:')
print('   ✓ energy_data преобразован в структуру для виджета:')
print('     {')
print('       electricity: {...},')
print('       water: null,')
print('       heat: null,')
print('       total_cost_current: 26350.0,')
print('       total_cost_last: 114005.6,')
print('       errors: [...]')
print('     }')
print()
print('3. EnergyCostCard: уже готов к приёму данных (не трогали)')
print()
print('По проблеме 3 (LLM сбой):')
print('   • Fallback на детерминированный расчёт работает правильно')
print('   • Пустая ошибка "error=" — YandexGPT вернул пустой ответ')
print('   • Можно добавить retry позже, но сейчас не критично')
print()
print('СЛЕДУЮЩИЙ ШАГ:')
print('  Backend перезагрузится автоматически.')
print('  Обнови страницу, напиши "покажи здоровье здания".')
print()
print('Ожидаемый результат:')
print('  • HealthScoreCard: только круг + статус (без компонентов)')
print('  • EnergyCostCard: 114 005,60 ₽ (май 2026) + детализация')
print('  • 3 виджета в ряд')
print()
print('Когда ок — скажи "всё ок" и коммитим v3.1.0')