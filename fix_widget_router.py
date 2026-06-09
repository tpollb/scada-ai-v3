from pathlib import Path

print('=== fix_widget_router.py ===')
print()

router_path = Path('frontend/src/components/WidgetRouter.svelte')
content = router_path.read_text(encoding='utf-8')

changes = []

# 1. Добавляем energy_cost_card в componentMap
if "'energy_cost_card': EnergyCostCard" in content:
    print('ℹ energy_cost_card уже есть в componentMap')
elif "'health_score': HealthScoreCard" in content:
    content = content.replace(
        "'health_score': HealthScoreCard,",
        "'energy_cost_card': EnergyCostCard,\n    'health_score': HealthScoreCard,"
    )
    changes.append("✓ Добавлен 'energy_cost_card' в componentMap")
else:
    print('⚠ Не нашёл health_score в componentMap')

# 2. Меняем grid с 2 колонок на 3
if 'md:grid-cols-3' in content:
    print('ℹ grid уже 3 колонки')
elif 'md:grid-cols-2' in content:
    content = content.replace('md:grid-cols-2', 'md:grid-cols-3')
    changes.append("✓ Изменён grid: md:grid-cols-2 → md:grid-cols-3")
else:
    print('⚠ Не нашёл md:grid-cols-2')

if changes:
    router_path.write_text(content, encoding='utf-8', newline='\n')
    print()
    for change in changes:
        print(f'  {change}')
    print()
    print('Vite подхватит через HMR.')
    print('Обнови страницу и напиши "покажи здоровье здания".')
    print()
    print('Ожидаемый результат:')
    print('  • Виджет "Энергозатраты" появится (не "не найден")')
    print('  • 3 виджета в ряд: Энергозатраты | Здоровье | Жизнеобеспечение')
else:
    print('ℹ Изменений не требуется')