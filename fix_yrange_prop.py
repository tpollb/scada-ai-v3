from pathlib import Path

print('=== fix_yrange_prop.py ===')
print()

PROJECT_ROOT = Path('.')
panel_path = PROJECT_ROOT / 'frontend/src/components/analytics/AnalyticsPanel.svelte'

content = panel_path.read_text(encoding='utf-8')

# Физические границы для каждого параметра
y_ranges = {
    'temperature': (0, 50),
    'humidity': (0, 100),
    'co2': (300, 2000),
    'pressure': (700, 800),
    'voc': (0, 1),
}

# Для каждого параметра добавляем yRange prop
for param, (y_min, y_max) in y_ranges.items():
    # Ищем точный паттерн вызова TrendChart для этого параметра
    old_pattern = f'''<TrendChart
                  data={{prepareChartData('{param}')}}
                  unit={{'{param}' === 'temperature' ? '°C' : '{param}' === 'humidity' ? '%' : '{param}' === 'co2' ? 'ppm' : '{param}' === 'pressure' ? 'мм' : 'мг/м³'}}
                  color={{paramColors['{param}'] || '#64748b'}}
                  trend={{{{ slope_per_day: data.trends['{param}'].slope_per_day, r_squared: data.trends['{param}'].r_squared, direction: data.trends['{param}'].direction }}}}
                />'''
    
    new_pattern = f'''<TrendChart
                  data={{prepareChartData('{param}')}}
                  unit={{'{param}' === 'temperature' ? '°C' : '{param}' === 'humidity' ? '%' : '{param}' === 'co2' ? 'ppm' : '{param}' === 'pressure' ? 'мм' : 'мг/м³'}}
                  color={{paramColors['{param}'] || '#64748b'}}
                  trend={{{{ slope_per_day: data.trends['{param}'].slope_per_day, r_squared: data.trends['{param}'].r_squared, direction: data.trends['{param}'].direction }}}}
                  yRange={{{{ min: {y_min}, max: {y_max} }}}}
                />'''
    
    if old_pattern in content:
        content = content.replace(old_pattern, new_pattern)
        print(f'✓ {param}: добавлен yRange min={y_min}, max={y_max}')
    else:
        print(f'⚠ {param}: паттерн не найден')

panel_path.write_text(content, encoding='utf-8', newline='\n')

print()
print('=' * 60)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 60)
print()
print('Добавлен prop yRange для каждого TrendChart:')
print('  • temperature: yRange={{ min: 0, max: 50 }}')
print('  • humidity: yRange={{ min: 0, max: 100 }}')
print('  • co2: yRange={{ min: 300, max: 2000 }}')
print('  • pressure: yRange={{ min: 700, max: 800 }}')
print('  • voc: yRange={{ min: 0, max: 1 }}')
print()
print('Теперь TrendChart получит yRange prop и применит его к chartOptions:')
print('  scales.y.min = yRange?.min')
print('  scales.y.max = yRange?.max')
print()
print('Frontend перезагрузится автоматически (Vite HMR).')
print()
print('Проверка:')
print('  1. В чате: "покажи аналитику"')
print('  2. Все графики должны иметь фиксированные пределы оси Y')
print('  3. Температура: 0..50 °C (не -400..+300)')
print('  4. Влажность: 0..100 %')
print('  5. CO₂: 300..2000 ppm')