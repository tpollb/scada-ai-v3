#!/usr/bin/env python3
"""
fix_dips_logic.py — исправление логики провалов
"""
from pathlib import Path

print('=' * 80)
print('ФИКС: Логика детекции провалов')
print('=' * 80)
print()

anom_path = Path('backend/modules/deep_analysis/analyzers/anomalies.py')
content = anom_path.read_text(encoding='utf-8')
changes = []

# ============================================================================
# ФИКС 1: Убираем hardcoded drop_ratio=0.30 (строка 185)
# ============================================================================
print('【1】ФИКС: Убираем hardcoded drop_ratio=0.30')
print('-' * 80)

old_line = 'sig_dips = detect_significant_dips(values, timestamps, drop_ratio=0.30, min_duration=2)'
new_line = 'sig_dips = detect_significant_dips(values, timestamps, drop_ratio=None, min_duration=2)  # None = читать из конфига'

if old_line in content:
    content = content.replace(old_line, new_line)
    changes.append('Убран hardcoded drop_ratio=0.30 → None (читается из конфига)')
    print(f'  ✅ {changes[-1]}')
else:
    print('  ℹ️  Строка не найдена или уже изменена')

print()

# ============================================================================
# ФИКС 2: Добавляем глобальную проверку в detect_significant_dips
# ============================================================================
print('【2】ФИКС: Глобальная проверка в detect_significant_dips')
print('-' * 80)

# Ищем начало функции detect_significant_dips и добавляем глобальную проверку
old_sig_dips_start = '''    # Читаем из конфига если не передан
    if drop_ratio is None:
        settings = load_dda_settings()
        drop_ratio = settings.anomaly_detection.significant_dip_ratio

    max_duration = max(min_duration, int(len(values) * max_duration_ratio))

    events = []
    i = 0'''

new_sig_dips_start = '''    # Читаем из конфига если не передан
    if drop_ratio is None:
        settings = load_dda_settings()
        drop_ratio = settings.anomaly_detection.significant_dip_ratio

    # ГЛОБАЛЬНАЯ ПРОВЕРКА: вычисляем глобальное среднее и std
    # Если "провал" выше (global_mean - 2*global_std) — это НЕ провал, а нормальное колебание
    valid_all = [v for v in values if v is not None]
    if valid_all:
        import numpy as np
        global_mean = np.mean(valid_all)
        global_std = np.std(valid_all)
        global_dip_threshold = global_mean - 2 * global_std  # только ниже этого — реальный провал
    else:
        global_dip_threshold = -float('inf')
    
    max_duration = max(min_duration, int(len(values) * max_duration_ratio))

    events = []
    i = 0'''

if old_sig_dips_start in content:
    content = content.replace(old_sig_dips_start, new_sig_dips_start)
    changes.append('Добавлена глобальная проверка (global_mean - 2*std)')
    print(f'  ✅ {changes[-1]}')
else:
    print('  ⚠️  Стартовый блок detect_significant_dips не найден')

# Теперь ищем место где событие добавляется в events и добавляем проверку
# Ищем паттерн: events.append({...
old_events_append_pattern = '''                        events.append({
                            "start_idx": start,
                            "end_idx": j - 1,
                            "duration": j - start,
                            "values": [values[k] for k in range(start, j)],
                            "drop_ratio": actual_drop,
                        })'''

new_events_append_pattern = '''                        # ГЛОБАЛЬНАЯ ПРОВЕРКА: минимальное значение в событии должно быть ниже global_dip_threshold
                        min_val_in_event = min(v for v in [values[k] for k in range(start, j)] if v is not None)
                        if min_val_in_event < global_dip_threshold:
                            events.append({
                                "start_idx": start,
                                "end_idx": j - 1,
                                "duration": j - start,
                                "values": [values[k] for k in range(start, j)],
                                "drop_ratio": actual_drop,
                            })
                        # Иначе: "провал" выше порога — это нормальное колебание, пропускаем'''

if old_events_append_pattern in content:
    content = content.replace(old_events_append_pattern, new_events_append_pattern)
    changes.append('События sig_dips фильтруются по глобальному порогу')
    print(f'  ✅ {changes[-1]}')
else:
    print('  ⚠️  Паттерн events.append не найден, ищем альтернативно...')
    # Показываем контекст для ручной правки
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        if 'events.append' in line and 'detect_significant' in '\n'.join(lines[max(0,i-50):i]):
            print(f'  Строка {i}: {line.strip()}')
            # Показываем 10 строк вокруг
            for j in range(max(0, i-5), min(len(lines), i+10)):
                marker = '>>>' if j == i-1 else '   '
                print(f'  {marker} {j+1}: {lines[j]}')
            break

anom_path.write_text(content, encoding='utf-8', newline='\n')

print()
print('=' * 80)
print('ЧТО ЭТИ ФИКСЫ ДАЮТ:')
print('=' * 80)
print()
print('Было:')
print('  • drop_ratio = 0.30 (hardcoded, конфиг игнорируется)')
print('  • Локальное среднее = 650 → значение 444 = падение 32% → "значительный провал"')
print('  • Приоритет 1 → ВСЕГДА становится "dip"')
print('  • Результат: значения 444-580 помечаются как провалы')
print()
print('Стало:')
print('  • drop_ratio читается из конфига (сейчас 0.50)')
print('  • Глобальный порог: mean - 2*std = 505 - 212 = 293')
print('  • Только значения < 293 считаются реальными провалами')
print('  • Значения 444-580 фильтруются как "нормальные колебания"')
print()
print('Ожидаемый результат:')
print('  • dip: только реальные провалы (< 293 или значения близкие к 0)')
print('  • Значения 444-580 больше НЕ будут провалами')
print('  • Конфигуратор работает (можно менять significant_dip_ratio через UI)')
print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Перезапусти backend')
print()
print('2. Запусти анализ:')
print('   curl -s -X POST http://localhost:8081/api/v1/deep_analysis/run \\')
print('     -H "Content-Type: application/json" \\')
print('     -d \'{"tags": ["KITCHEN2-CO2"], "period": 30}\' | \\')
print('     python -c "import sys,json; r=json.load(sys.stdin); print(r.get(\'anomalies\',{}).get(\'type_counts\'))"')
print()
print('3. Ожидаемый результат:')
print('   • dip: значительно меньше (только реальные провалы < 293)')
print('   • spike: без изменений')
print('   • drift: без изменений')
print('   • noise: может немного увеличиться (т.к. sig_dips теперь noise)')
print()
print('4. Визуально:')
print('   • 18.06 11:00-13:00 — не должно быть синих точек (значения 444-580)')
print('   • Только реальные провалы (близкие к 0 или < 293) должны быть синими')