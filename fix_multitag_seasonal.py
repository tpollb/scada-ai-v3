#!/usr/bin/env python3
"""
fix_multitag_seasonal.py — добавляем вычисление seasonal_analysis для multi-tag
"""
from pathlib import Path

print('=' * 80)
print('ФИКС: Добавляем seasonal_analysis для multi-tag')
print('=' * 80)
print()

api_path = Path('backend/modules/deep_analysis/api.py')
content = api_path.read_text(encoding='utf-8')

# Ищем точное место перед "results = {" в multi-tag блоке
print('【1】Ищем маркер "results = {" в multi-tag блоке')
print('-' * 80)

# Маркер который есть только в multi-tag блоке (после create_multitag_time_series_spec)
marker = '''            # Формируем результаты
            results = {
                "correlation_matrix": correlation_matrix,
                "pair_analysis": pair_analysis,
            }'''

seasonal_block = '''            # Сезонный анализ для каждого тега
            seasonal_analysis = {}
            for tag_name in request.tags:
                tag_data = data['tags'].get(tag_name, {})
                aligned_values = tag_data.get('aligned_values', [])
                
                if len(aligned_values) >= 50:
                    try:
                        periods_result = detect_dominant_periods(
                            aligned_values,
                            data['common_timestamps']
                        )
                        
                        decomp_result = None
                        pattern_result = None
                        
                        if periods_result.get('detected_periods'):
                            main_period = periods_result['detected_periods'][0]['period']
                            decomp_result = decompose_seasonal(aligned_values, period=main_period)
                            pattern_result = get_seasonal_pattern(aligned_values, period=main_period)
                        
                        seasonal_analysis[tag_name] = {
                            "periods": periods_result,
                            "decomposition": decomp_result,
                            "pattern": pattern_result,
                        }
                    except Exception as e:
                        log.warning("Seasonal analysis failed", tag=tag_name, error=str(e))
                        seasonal_analysis[tag_name] = {"error": str(e)}

            # Формируем результаты
            results = {
                "correlation_matrix": correlation_matrix,
                "pair_analysis": pair_analysis,
                "seasonal_analysis": seasonal_analysis,
            }'''

if marker in content:
    content = content.replace(marker, seasonal_block)
    api_path.write_text(content, encoding='utf-8', newline='\n')
    print('✅ Блок seasonal анализа добавлен для multi-tag')
    print('✅ seasonal_analysis теперь вычисляется для каждого тега')
    print('✅ Добавлен в словарь results')
else:
    print('⚠️  Маркер не найден')

print()
print('=' * 80)
print('ЧТО СДЕЛАНО:')
print('=' * 80)
print()
print('Добавлен блок вычисления seasonal_analysis для multi-tag:')
print('  • Для каждого тега из request.tags')
print('  • Вызывается detect_dominant_periods с aligned_values')
print('  • Если найдены периоды - decompose_seasonal и get_seasonal_pattern')
print('  • Результаты сохраняются в словарь seasonal_analysis[tag_name]')
print('  • Добавляется в results как "seasonal_analysis": seasonal_analysis')
print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Backend перезагрузится сам')
print('2. Запусти анализ для multi-tag через UI')
print('3. Должен вернуться корректный ответ с seasonal_analysis для каждого тега')