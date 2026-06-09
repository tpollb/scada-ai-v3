from pathlib import Path

print('=== fix_energy_widget.py (гарантированный патч) ===')
print()

renderers_path = Path('modules/health/renderers.py')
content = renderers_path.read_text(encoding='utf-8')

# Проверяем что уже есть
if 'energy_cost_card' in content:
    print('ℹ energy_cost_card уже есть в renderers.py')
    exit(0)

# Точный паттерн из grep (строки 144-156)
old_code = '''    # 1. Индекс здоровья (компактный)
    widgets = [
        {
            "type": "health_score",
            "data": {
                "score": report.score,
                "status": report.status,
                "status_ru": translate_status(report.status),
                "sub_scores": report.sub_scores,
            },
            "size": "medium",
        },
    ]'''

new_code = '''    # === Виджет энергозатрат ===
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
        log.info("energy_cost_card widget added")

    widgets.append({
        "type": "health_score",
        "data": {
            "score": report.score,
            "status": report.status,
            "status_ru": translate_status(report.status),
            "sub_scores": report.sub_scores,
        },
        "size": "medium",
    })'''

if old_code in content:
    content = content.replace(old_code, new_code)
    renderers_path.write_text(content, encoding='utf-8', newline='\n')
    print('✓ Паттерн найден и заменён')
    print('✓ energy_cost_card будет добавляться в начало списка виджетов')
    print()
    print('Проверяю результат...')
    # Проверяем что замена произошла
    if 'energy_cost_card' in content:
        print('✓ Подтверждено: energy_cost_card теперь в файле')
    else:
        print('❌ ОШИБКА: замена не произошла!')
else:
    print('❌ Точный паттерн не найден!')
    print('Показываю строки 140-160 для ручной проверки:')
    lines = content.split('\n')
    for i in range(140, min(160, len(lines))):
        print(f'{i+1}: {lines[i]}')
    exit(1)

print()
print('=' * 60)
print('ПРОВЕРКА WidgetRouter:')
print('=' * 60)

router_path = Path('../frontend/src/components/WidgetRouter.svelte')
if router_path.exists():
    router = router_path.read_text(encoding='utf-8')
    if "'energy_cost_card'" in router or '"energy_cost_card"' in router:
        print('✓ WidgetRouter поддерживает energy_cost_card')
    else:
        print('❌ WidgetRouter НЕ поддерживает energy_cost_card!')
        print('Добавляю поддержку...')
        # Ищем где добавить
        if 'HealthScoreCard' in router and 'EnergyCostCard' not in router:
            # Добавляем импорт
            router = router.replace(
                "import HealthScoreCard",
                "import EnergyCostCard from './health/EnergyCostCard.svelte'\n  import HealthScoreCard"
            )
            # Добавляем case
            router = router.replace(
                "{#if widget.type === 'health_score'}",
                "{#if widget.type === 'energy_cost_card'}\n          <EnergyCostCard data={widget.data} />\n        {:else if widget.type === 'health_score'}"
            )
            router_path.write_text(router, encoding='utf-8', newline='\n')
            print('✓ WidgetRouter обновлён')

print()
print('=' * 60)
print('СЛЕДУЮЩИЙ ШАГ:')
print('=' * 60)
print('1. Backend перезагрузится автоматически (hot-reload)')
print('2. Напиши в чате: "покажи здоровье здания"')
print('3. В логах должны появиться:')
print('   • "Energy data fetched for widget current_cost=..."')
print('   • "energy_cost_card widget added"')
print('   • types=[\'energy_cost_card\', \'health_score\', ...]')
print('4. В UI должен появиться виджет "Энергозатраты"')