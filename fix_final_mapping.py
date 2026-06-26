#!/usr/bin/env python3
"""
fix_final_mapping.py — финальный фикс: поиск в downsampled timestamps
"""
from pathlib import Path

print('=' * 80)
print('ФИНАЛЬНЫЙ ФИКС: Поиск аномалий в downsampled timestamps')
print('=' * 80)
print()

cs_path = Path('backend/modules/deep_analysis/visualizers/chart_specs.py')
content = cs_path.read_text(encoding='utf-8')

# Ищем блок маппинга аномалий и заменяем его на более точный
old_mapping_logic = '''            for val, orig_ts in points:
                # Форматируем timestamp аномалии
                if isinstance(orig_ts, datetime):
                    ts_key = orig_ts.strftime("%Y-%m-%d %H:%M")
                else:
                    ts_str = str(orig_ts).replace('T', ' ')
                    ts_key = ts_str[:16] if len(ts_str) > 16 else ts_str

                # Находим оригинальный индекс для этой аномалии
                orig_idx = None
                if ts_key in ts_to_orig_idx:
                    orig_idx = ts_to_orig_idx[ts_key]
                else:
                    # Если точного совпадения нет — ищем ближайший timestamp
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

new_mapping_logic = '''            for val, orig_ts in points:
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

if old_mapping_logic in content:
    content = content.replace(old_mapping_logic, new_mapping_logic)
    cs_path.write_text(content, encoding='utf-8', newline='\n')
    print('✅ Маппинг теперь ищет напрямую в downsampled timestamps')
else:
    print('⚠️  Блок маппинга не найден или уже изменён')

print()
print('=' * 80)
print('ЧТО ИЗМЕНИЛОСЬ:')
print('=' * 80)
print()
print('Было:')
print('  1. Ищем timestamp аномалии в ОРИГИНАЛЬНЫХ timestamps')
print('  2. Получаем orig_idx')
print('  3. Используем маппинг: ds_idx = orig_to_ds_idx[orig_idx]')
print('  Проблема: могут быть дубликаты, разница в секундах')
print()
print('Стало:')
print('  1. Ищем timestamp аномалии НАПРЯМУЮ в DOWNSAMPLED timestamps')
print('  2. Получаем ds_idx сразу (без промежуточного orig_idx)')
print('  3. Если точного совпадения нет — ищем ближайший downsampled timestamp')
print('  Преимущество: работаем с тем же набором точек что на графике')
print()
print('Ключевое отличие:')
print('  • Раньше: timestamps (оригинал) → orig_idx → orig_to_ds_idx → ds_idx')
print('  • Теперь: ds_timestamps → ds_idx напрямую')
print('  • Меньше промежуточных шагов → меньше ошибок')
print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Перезапусти backend')
print()
print('2. Запусти анализ KITCHEN2-CO2 на 30 дней')
print()
print('3. Проверь точки аномалий:')
print('   • Просадка 12.06 02:40 должна быть ТОЧНО на 12.06 02:40')
print('   • НЕ должно быть смещения на 10 минут')
print('   • Все точки на своих позициях')
print()
print('Это должно быть ФИНАЛЬНЫМ фиксом!')