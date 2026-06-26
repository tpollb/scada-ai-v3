#!/usr/bin/env python3
"""
fix_api_multitag_timestamps.py — передаём реальные timestamps в detect_anomalies
"""
from pathlib import Path

print('=' * 80)
print('ФИКС: Реальные timestamps для multi-tag в api.py')
print('=' * 80)
print()

api_path = Path('backend/modules/deep_analysis/api.py')
content = api_path.read_text(encoding='utf-8')

# Находим проблемный блок
old_block = '''            for tag_name in request.tags:
                tag_data = data['tags'].get(tag_name, {})
                aligned_values = tag_data.get('aligned_values', [])

                # Фильтруем None значения
                valid_values = [v for v in aligned_values if v is not None]

                if len(valid_values) >= 10:
                    adaptive_contamination = min(0.15, max(0.08, 200 / max(len(valid_values), 1)))
                    tag_anomalies = detect_anomalies_isolation_forest(
                        valid_values,
                        list(range(len(valid_values))),
                        contamination=adaptive_contamination,  # псевдо-timestamps (индексы)
                        classify_types=True
                    )
                    anomalies_per_tag[tag_name] = tag_anomalies
                    total_anomalies += tag_anomalies['total_anomalies']'''

new_block = '''            for tag_name in request.tags:
                tag_data = data['tags'].get(tag_name, {})
                aligned_values = tag_data.get('aligned_values', [])

                # Фильтруем None значения И соответствующие timestamps
                valid_values = []
                valid_timestamps = []
                for idx, v in enumerate(aligned_values):
                    if v is not None:
                        valid_values.append(v)
                        if idx < len(data['common_timestamps']):
                            valid_timestamps.append(data['common_timestamps'][idx])
                        else:
                            valid_timestamps.append(idx)  # fallback

                if len(valid_values) >= 10:
                    adaptive_contamination = min(0.15, max(0.08, 200 / max(len(valid_values), 1)))
                    tag_anomalies = detect_anomalies_isolation_forest(
                        valid_values,
                        valid_timestamps,  # ← РЕАЛЬНЫЕ timestamps из common_timestamps
                        contamination=adaptive_contamination,
                        classify_types=True
                    )
                    anomalies_per_tag[tag_name] = tag_anomalies
                    total_anomalies += tag_anomalies['total_anomalies']'''

if old_block in content:
    content = content.replace(old_block, new_block)
    api_path.write_text(content, encoding='utf-8', newline='\n')
    print('✅ api.py обновлён')
else:
    print('❌ Блок не найден')
    exit(1)

print()
print('Что исправлено:')
print('  Было: list(range(len(valid_values))) — индексы 0, 1, 2, ...')
print('  Стало: valid_timestamps — реальные datetime из common_timestamps')
print()
print('Теперь anomaly_timestamps будут содержать реальные datetime объекты,')
print('и create_time_series_spec сможет их правильно сопоставить.')
print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Backend перезагрузится сам')
print('2. Запусти анализ с 2+ тегами')
print('3. Точки аномалий должны появиться на графике')
print('4. Точки должны быть на правильных местах')