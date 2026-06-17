from pathlib import Path

print('=== fix_ma7_color.py ===')
print()

PROJECT_ROOT = Path('.')
chart_path = PROJECT_ROOT / 'frontend/src/components/analytics/TrendChart.svelte'

content = chart_path.read_text(encoding='utf-8')

# Меняем фиолетовый MA-7 на нейтральный серый
old_color = "borderColor: '#8b5cf6',"
new_color = "borderColor: '#6b7280',  // нейтральный серый (хорошо виден на обеих темах)"

if old_color in content:
    content = content.replace(old_color, new_color)
    chart_path.write_text(content, encoding='utf-8', newline='\n')
    print('✓ MA-7: #8b5cf6 (фиолетовый) → #6b7280 (нейтральный серый)')
else:
    print('⚠ Паттерн не найден')

print()
print('=' * 60)
print('ЦВЕТОВАЯ ПАЛИТРА ГРАФИКОВ:')
print('=' * 60)
print()
print('Данные (по параметрам):')
print('  • temperature: #ef4444 (красный)')
print('  • humidity: #3b82f6 (синий)')
print('  • co2: #22c55e (зелёный)')
print('  • pressure: #a855f7 (фиолетовый)')
print('  • voc: #f59e0b (оранжевый)')
print()
print('Дополнительные линии:')
print('  • Тренд (сильный, R²≥0.1): #64748b (тёмно-серый) пунктир')
print('  • Тренд (слабый, R²<0.1): #9ca3af (светло-серый) пунктир')
print('  • MA-7 (скользящая средняя): #6b7280 (нейтральный серый) сплошная')
print('  • Прогноз: #f97316 (оранжево-красный) пунктир')
print()
print('Frontend перезагрузится автоматически (Vite HMR).')
print()
print('Проверка:')
print('  1. В чате: "покажи аналитику"')
print('  2. MA-7 должен быть нейтрально-серым (не сливается с данными)')
print('  3. Хорошо читается на светлой и тёмной теме')