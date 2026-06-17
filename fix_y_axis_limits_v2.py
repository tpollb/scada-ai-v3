from pathlib import Path

print('=== fix_y_axis_limits_v2.py ===')
print()

PROJECT_ROOT = Path('.')

# ============================================================================
# 1. TrendChart.svelte — уже обновлён в предыдущем шаге
# ============================================================================
print('✓ TrendChart.svelte: уже содержит prop yRange')

# ============================================================================
# 2. AnalyticsPanel.svelte — добавляем yRange для каждого параметра
# ============================================================================
panel_path = PROJECT_ROOT / 'frontend/src/components/analytics/AnalyticsPanel.svelte'
content = panel_path.read_text(encoding='utf-8')

# Физические границы для параметров
y_ranges = {
    'temperature': {'min': 0, 'max': 50},
    'humidity': {'min': 0, 'max': 100},
    'co2': {'min': 300, 'max': 2000},
    'pressure': {'min': 700, 'max': 800},
    'voc': {'min': 0, 'max': 1000},
}

# Обновляем каждый вызов TrendChart
for param, y_range in y_ranges.items():
    min_val = y_range['min']
    max_val = y_range['max']
    
    # Ищем паттерн: <TrendChart ... trend={...} />
    # и добавляем yRange={{ min: X, max: Y }} перед закрывающим />
    old_pattern = f'''trend={{{{ slope_per_day: data.trends['{param}'].slope_per_day, r_squared: data.trends['{param}'].r_squared, direction: data.trends['{param}'].direction }}}}
                />'''
    
    new_pattern = f'''trend={{{{ slope_per_day: data.trends['{param}'].slope_per_day, r_squared: data.trends['{param}'].r_squared, direction: data.trends['{param}'].direction }}}}
                  yRange={{{{ min: {min_val}, max: {max_val} }}}}
                />'''
    
    if old_pattern in content:
        content = content.replace(old_pattern, new_pattern)
        print(f'✓ {param}: добавлен yRange min={min_val}, max={max_val}')
    else:
        print(f'⚠ {param}: паттерн не найден')

panel_path.write_text(content, encoding='utf-8', newline='\n')

print()
print('=' * 60)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 60)
print()
print('Добавлены фиксированные пределы для оси Y:')
print('  • temperature: 0..50 °C')
print('  • humidity: 0..100 %')
print('  • co2: 300..2000 ppm')
print('  • pressure: 700..800 мм рт. ст.')
print('  • voc: 0..1000 мг/м³')
print()
print('Теперь графики не будут масштабироваться до нереалистичных значений')
print('(-400..+300) из-за экстраполяции тренда.')
print()
print('Frontend перезагрузится автоматически (Vite HMR).')
print()
print('Проверка:')
print('  1. В чате: "покажи аналитику"')
print('  2. Все графики должны показывать реалистичные пределы оси Y')
print('  3. Экстраполяция прогноза может выходить за пределы (это нормально)')