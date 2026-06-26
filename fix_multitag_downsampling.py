#!/usr/bin/env python3
"""
fix_multitag_downsampling.py — step-based downsampling для multi-tag
"""
from pathlib import Path

print('=' * 80)
print('ФИКС: Step-based downsampling для multi-tag (вместо min-max)')
print('=' * 80)
print()

cs_path = Path('backend/modules/deep_analysis/visualizers/chart_specs.py')
content = cs_path.read_text(encoding='utf-8')

# Находим блок downsampling в create_multitag_time_series_spec
old_downsampling = '''    # Downsampling
    need_downsample = len(common_timestamps) > max_points

    if need_downsample:
        # ВНИМАНИЕ: downsample_time_series возвращает (values, timestamps)
        _, ds_timestamps = downsample_time_series(
            list(range(len(common_timestamps))),
            common_timestamps,
            max_points
        )
        ds_timestamps = [t for t in ds_timestamps if t is not None]
    else:
        ds_timestamps = common_timestamps'''

new_downsampling = '''    # Downsampling: step-based (равномерный) для multi-tag
    # Это гарантирует что все теги имеют одинаковые timestamps
    need_downsample = len(common_timestamps) > max_points

    if need_downsample:
        # Step-based: берём каждые N-ные точки
        step = max(1, len(common_timestamps) // max_points)
        ds_indices = list(range(0, len(common_timestamps), step))[:max_points]
        ds_timestamps = [common_timestamps[i] for i in ds_indices]
    else:
        ds_indices = list(range(len(common_timestamps)))
        ds_timestamps = common_timestamps'''

if old_downsampling in content:
    content = content.replace(old_downsampling, new_downsampling)
    print('✅ Downsampling заменён на step-based')
else:
    print('⚠️  Блок downsampling не найден')

# Теперь нужно обновить блок где добавляются линии для каждого тега
old_lines = '''    # 1. Добавляем линии для каждого тега (с downsampling)
    for i, (tag_name, tag_data) in enumerate(tags_data.items()):
        aligned_values = tag_data.get('aligned_values', [])
        color = tag_colors[i % len(tag_colors)]

        if need_downsample:
            ds_values, _ = downsample_time_series(aligned_values, common_timestamps, max_points)
        else:
            ds_values = aligned_values'''

new_lines = '''    # 1. Добавляем линии для каждого тега (с downsampling)
    for i, (tag_name, tag_data) in enumerate(tags_data.items()):
        aligned_values = tag_data.get('aligned_values', [])
        color = tag_colors[i % len(tag_colors)]

        if need_downsample:
            # Step-based: берём те же индексы что и для timestamps
            ds_values = [
                aligned_values[idx] if idx < len(aligned_values) else None
                for idx in ds_indices
            ]
        else:
            ds_values = aligned_values'''

if old_lines in content:
    content = content.replace(old_lines, new_lines)
    print('✅ Downsampled values теперь используют те же индексы что и timestamps')
else:
    print('⚠️  Блок lines не найден')

cs_path.write_text(content, encoding='utf-8', newline='\n')

print()
print('=' * 80)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 80)
print()
print('Было (min-max downsampling):')
print('  • Для тега A: downsample_time_series(values_A, timestamps)')
print('    → ds_timestamps_A = [t1, t5, t8, ...]')
print('  • Для тега B: downsample_time_series(values_B, timestamps)')
print('    → ds_timestamps_B = [t2, t4, t9, ...] (ДРУГИЕ точки!)')
print('  • ts_to_index создаётся для ds_timestamps (от первого тега)')
print('  • Маппинг аномалий для тега B использует ts_to_index от тега A')
print('  • Результат: смещение (разное для разных тегов)')
print()
print('Стало (step-based downsampling):')
print('  • ds_indices = [0, step, 2*step, 3*step, ...]')
print('  • ds_timestamps = [common_timestamps[i] for i in ds_indices]')
print('  • Для каждого тега: ds_values = [aligned_values[i] for i in ds_indices]')
print('  • ВСЕ теги используют ОДИНАКОВЫЕ индексы')
print('  • ts_to_index работает правильно для всех тегов')
print('  • Результат: НЕТ смещения')
print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Перезапусти backend')
print()
print('2. Запусти анализ с 2+ тегами')
print()
print('3. Проверь multi-tag график:')
print('   • Точки аномалий должны быть на правильных местах')
print('   • НЕ должно быть разного смещения для разных тегов')
print('   • Все аномалии точно на своих позициях')