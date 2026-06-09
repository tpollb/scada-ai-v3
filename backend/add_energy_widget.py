from pathlib import Path

print('=== add_energy_widget.py ===')
print()

renderers_path = Path('modules/health/renderers.py')
content = renderers_path.read_text(encoding='utf-8')

# Проверяем есть ли уже блок energy_cost_card
if 'energy_cost_card' in content:
    print('ℹ Блок energy_cost_card уже есть в renderers.py')
else:
    # Ищем место где создаётся widgets list
    if 'widgets: list = []' in content:
        # Вставляем блок ПЕРЕД созданием widgets
        energy_block = '''    # === Виджет энергозатрат (async fetch) ===
    try:
        from modules.energy_electricity.tools import calculate_electricity_cost
        energy_data = await calculate_electricity_cost()
        log.info("Energy data fetched for widget", 
                 current_cost=energy_data.get("current_month", {}).get("cost_rub"),
                 last_cost=energy_data.get("last_month", {}).get("cost_rub"))
    except Exception as e:
        log.warning("Failed to get energy data for widget", error=str(e))
        energy_data = None

    widgets: list = []

    # Добавляем виджет энергозатрат в начало (если данные есть)
    if energy_data:
        widgets.append({
            "type": "energy_cost_card",
            "data": energy_data,
            "size": "medium",
        })
        log.info("energy_cost_card widget added")

'''
        content = content.replace(
            '    widgets: list = []',
            energy_block
        )
        renderers_path.write_text(content, encoding='utf-8', newline='\n')
        print('✓ Добавлен блок energy_cost_card в renderers.py')
        print('  • Виджет добавляется в начало списка')
        print('  • Данные берутся из calculate_electricity_cost()')
        print('  • Добавлен debug logging')
    else:
        print('⚠ Не нашёл "widgets: list = []" в renderers.py')
        print('Покажи текущее состояние файла:')
        for i, line in enumerate(content.split('\n')[120:140], 121):
            print(f'{i}: {line}')

print()
print('=' * 60)
print('ПРОВЕРКА WIDGETROUTER:')
print('=' * 60)

# Проверяем WidgetRouter.svelte
router_path = Path('../frontend/src/components/WidgetRouter.svelte')
if router_path.exists():
    router = router_path.read_text(encoding='utf-8')
    
    widget_types = [
        'health_score',
        'life_support_card', 
        'environmental_panel',
        'alarms_panel',
        'energy_panel',
        'energy_cost_card',
    ]
    
    print('WidgetRouter.svelte — поддержка виджетов:')
    for wtype in widget_types:
        if f"'{wtype}'" in router or f'"{wtype}"' in router:
            print(f'  ✓ {wtype}')
        else:
            print(f'  ✗ {wtype} — НЕ НАЙДЕН!')
else:
    print('⚠ WidgetRouter.svelte не найден')

print()
print('=' * 60)
print('СЛЕДУЮЩИЙ ШАГ:')
print('=' * 60)
print('1. Перезапусти backend: Ctrl+C, uvicorn main:app --port 8081')
print('2. Напиши в чате: "покажи здоровье здания"')
print('3. Проверь логи — должны быть:')
print('   • "Energy data fetched for widget"')
print('   • "energy_cost_card widget added"')
print('   • "render_visual widgets" с types=[...energy_cost_card...]')
print()
print('Когда ок — скажи "виджет ок" и коммитим')