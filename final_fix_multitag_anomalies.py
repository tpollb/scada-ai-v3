#!/usr/bin/env python3
"""
final_fix_multitag_anomalies.py — передаём реальные timestamps для multi-tag
"""
from pathlib import Path

print('=' * 80)
print('ФИНАЛЬНЫЙ ФИКС: Реальные timestamps для multi-tag')
print('=' * 80)
print()

api_path = Path('backend/modules/deep_analysis/api.py')
lines = api_path.read_text(encoding='utf-8').split('\n')

# Находим строку 234 и контекст вокруг
print('【1】Находим проблемное место')
print('-' * 80)

for i, line in enumerate(lines[220:240], 221):
    if 'list(range(len(valid_values)))' in line:
        print(f'Найдена строка {i}:')
        print(f'  {line}')
        
        # Заменяем эту строку
        indent = '                        '
        new_lines = [
            indent + '[data["common_timestamps"][j] for j in range(len(aligned_values)) if j < len(aligned_values) and aligned_values[j] is not None],',
        ]
        
        # Заменяем строку
        lines[i-1] = new_lines[0]
        print()
        print('✅ Заменено на:')
        print(f'  {new_lines[0]}')
        break

api_path.write_text('\n'.join(lines), encoding='utf-8', newline='\n')

print()
print('=' * 80)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 80)
print()
print('Было:')
print('  list(range(len(valid_values)))')
print('  → индексы [0, 1, 2, 3, ...]')
print()
print('Стало:')
print('  [data["common_timestamps"][j] for j in range(len(aligned_values))')
print('   if j < len(aligned_values) and aligned_values[j] is not None]')
print('  → реальные datetime объекты из common_timestamps')
print()
print('Теперь detect_anomalies_isolation_forest получит реальные timestamps,')
print('и create_time_series_spec сможет правильно сопоставить аномалии с графиком.')
print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Backend перезагрузится сам (--reload)')
print('2. Запусти анализ с 2+ тегами (например, KITCHEN2-CO2 + R001-CO2)')
print('3. Должны появиться точки аномалий (пики/провалы/дрейфы/шум)')
print('4. Точки должны быть на правильных местах (не в случайных позициях)')