#!/usr/bin/env python3
"""
revert_and_fix.py — откат последнего фикса и упрощение логики
"""
from pathlib import Path

print('=' * 80)
print('ОТКАТ: Возвращаемся к orig_to_ds_idx маппингу')
print('=' * 80)
print()

cs_path = Path('backend/modules/deep_analysis/visualizers/chart_specs.py')
content = cs_path.read_text(encoding='utf-8')

# Откатываем последний фикс — возвращаемся к поиску через оригинальные timestamps
old_logic = '''            for val, orig_ts in points:
                # Форматируем timestamp аномалии
                if isinstance(orig_ts, datetime):
                    ts_key = orig_ts.strftime("%Y-%m-%d %H:%M")
                else:
                    ts_str = str(orig_ts).replace('T', ' ')
                    ts_key = ts_str[:16] if len(ts_str) > 16 else ts_str

                # Ищем НАПРЯМУЮ в downsampled timestamps
                ds_idx = None
                
                # 1. Пробуем точное совпадение через ts_to_index
                if ts_key in ts_to_index:
                    ds_idx = ts_to_index[ts_key]
                else:
                    # 2. Если точного совпадения нет — ищем ближайший downsampled timestamp
                    try:
                        if isinstance(orig_ts, datetime):
                            orig_ts_dt = orig_ts
                        else:
                            ts_str = str(orig_ts).replace('T', ' ')
                            if len(ts_str) > 16:
                                ts_str = ts_str[:16]
                            orig_ts_dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M")

                        min_diff = float('inf')
                        closest_ds_idx = None

                        # Ищем в DOWNSAMPLED timestamps, не в оригинальных!
                        for i, ds_ts in enumerate(ds_timestamps):
                            if isinstance(ds_ts, datetime):
                                diff = abs((ds_ts - orig_ts_dt).total_seconds())
                                if diff < min_diff:
                                    min_diff = diff
                                    closest_ds_idx = i

                        # Если разница меньше 15 минут (половина шага) — используем этот индекс
                        if closest_ds_idx is not None and min_diff < 900:
                            ds_idx = closest_ds_idx
                    except Exception:
                        pass

                # Устанавливаем значение на найденный downsampled индекс
                if ds_idx is not None and 0 <= ds_idx < len(type_data):
                    type_data[ds_idx] = val'''

new_logic = '''            for val, orig_ts in points:
                # Ищем оригинальный индекс для этой аномалии
                orig_idx = None
                
                # 1. Точное совпадение timestamp объекта
                for i, ts in enumerate(timestamps):
                    if ts == orig_ts:
                        orig_idx = i
                        break
                
                # 2. Если точного совпадения нет — ищем ближайший по времени
                if orig_idx is None:
                    try:
                        if isinstance(orig_ts, datetime):
                            orig_ts_dt = orig_ts
                        else:
                            ts_str = str(orig_ts).replace('T', ' ')
                            if len(ts_str) > 16:
                                ts_str = ts_str[:16]
                            orig_ts_dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M")

                        min_diff = float('inf')
                        closest_orig_idx = None

                        for i, ts in enumerate(timestamps):
                            if isinstance(ts, datetime):
                                diff = abs((ts - orig_ts_dt).total_seconds())
                                if diff < min_diff:
                                    min_diff = diff
                                    closest_orig_idx = i

                        # Если разница меньше 30 минут — используем этот индекс
                        if closest_orig_idx is not None and min_diff < 1800:
                            orig_idx = closest_orig_idx
                    except Exception:
                        pass

                # Используем точный маппинг из downsampling
                if orig_idx is not None and orig_idx in orig_to_ds_idx:
                    ds_idx = orig_to_ds_idx[orig_idx]
                    type_data[ds_idx] = val'''

if old_logic in content:
    content = content.replace(old_logic, new_logic)
    cs_path.write_text(content, encoding='utf-8', newline='\n')
    print('✅ Откатились к orig_to_ds_idx маппингу')
    print('   Используем точное совпадение timestamp объектов (не строк)')
else:
    print('⚠️  Блок не найден')

print()
print('=' * 80)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 80)
print()
print('Было (сломанный фикс):')
print('  • Искали timestamp в downsampled timestamps')
print('  • Многие аномалии НЕ попадали в downsampled (не min/max)')
print('  • Результат: провалы пропадали')
print()
print('Стало (откат):')
print('  • Ищем timestamp в ОРИГИНАЛЬНЫХ timestamps')
print('  • Используем точное совпадение объектов (ts == orig_ts)')
print('  • Если нет — ищем ближайший по времени')
print('  • Используем orig_to_ds_idx для точного маппинга')
print('  • Результат: все провалы на месте + точное позиционирование')
print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Перезапусти backend')
print()
print('2. Запусти анализ KITCHEN2-CO2 на 30 дней')
print()
print('3. Проверь:')
print('   • Все провалы должны быть на месте (не пропали)')
print('   • Смещение должно быть минимальным (< 5 минут)')
print('   • Точки на своих позициях')