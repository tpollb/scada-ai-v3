from pathlib import Path

print('=== fix_ma7_color_v2.py ===')
print()

PROJECT_ROOT = Path('.')
chart_path = PROJECT_ROOT / 'frontend/src/components/analytics/TrendChart.svelte'

content = chart_path.read_text(encoding='utf-8')

# Меняем на светло-серый (хорошо читается на обеих темах)
old_color = "borderColor: '#6b7280',  // нейтральный серый (хорошо виден на обеих темах)"
new_color = "borderColor: '#9ca3af',  // светло-серый (читается на светлой и тёмной теме)"

if old_color in content:
    content = content.replace(old_color, new_color)
    chart_path.write_text(content, encoding='utf-8', newline='\n')
    print('✓ MA-7: #6b7280 → #9ca3af (светло-серый, хорошо читается на обеих темах)')
else:
    print('⚠ Паттерн не найден')

print()
print('=' * 60)
print('ФИНАЛЬНАЯ ПАЛИТРА:')
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
print('  • MA-7 (скользящая средняя): #9ca3af (светло-серый) сплошная 2px')
print('  • Прогноз: #f97316 (оранжево-красный) пунктир')
print()
print('Frontend перезагрузится автоматически (Vite HMR).')
print()
print('Проверка:')
print('  1. Переключи тему (светлая/тёмная)')
print('  2. MA-7 должен хорошо читаться на обеих темах')
print('  3. Не сливается с данными (ярко-цветными)')