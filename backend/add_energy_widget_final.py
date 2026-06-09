from pathlib import Path

print('=== add_energy_widget_final.py ===')
print()

renderers_path = Path('modules/health/renderers.py')
content = renderers_path.read_text(encoding='utf-8')

# Точный паттерн из файла (начало функции render_visual)
old_pattern = '''async def render_visual(report: HealthReport) -> dict:
    """Виджеты для Workspace — ГАРАНТИРОВАННО life_support + компактный health_score"""

    # 1. Индекс здоровья (компактный)
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

new_pattern = '''async def render_visual(report: HealthReport) -> dict:
    """Виджеты для Workspace — ГАРАНТИРОВАННО life_support + компактный health_score"""

    # === Виджет энергозатрат (async fetch) ===
    energy_data = None
    try:
        from modules.energy_electricity.tools import calculate_electricity_cost
        energy_data = await calculate_electricity_cost()
        log.info("Energy data fetched for widget", 
                 current_cost=energy_data.get("current_month", {}).get("cost_rub"),
                 last_cost=energy_data.get("last_month", {}).get("cost_rub"))
    except Exception as e:
        log.warning("Failed to get energy data for widget", error=str(e))

    widgets = []

    # Виджет энергозатрат — в начало списка (первый слева)
    if energy_data:
        widgets.append({
            "type": "energy_cost_card",
            "data": energy_data,
            "size": "medium",
        })
        log.info("energy_cost_card widget added")

    # 1. Индекс здоровья (компактный)
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

if old_pattern in content:
    content = content.replace(old_pattern, new_pattern)
    renderers_path.write_text(content, encoding='utf-8', newline='\n')
    print('✓ Паттерн найден и заменён')
    print('✓ energy_cost_card будет добавляться в начало списка виджетов')
else:
    print('⚠ Точный паттерн не найден!')
    print('Показываю первые строки render_visual:')
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'async def render_visual' in line:
            for j in range(i, min(i+20, len(lines))):
                print(f'{j+1}: {lines[j]}')
            break

print()
print('=' * 60)
print('СЛЕДУЮЩИЙ ШАГ:')
print('=' * 60)
print('1. Перезапусти backend: Ctrl+C, uvicorn main:app --port 8081')
print('2. Напиши в чате: "покажи здоровье здания"')
print('3. В логах должны появиться:')
print('   • "Energy data fetched for widget current_cost=... last_cost=..."')
print('   • "energy_cost_card widget added"')
print('   • types=[\'energy_cost_card\', \'health_score\', ...]')
print()
print('4. В UI должен появиться виджет "Энергозатраты"')
print('   с большой цифрой текущей стоимости')