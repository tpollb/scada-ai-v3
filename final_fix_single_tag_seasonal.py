#!/usr/bin/env python3
"""
final_fix_single_tag_seasonal.py — точечный фикс seasonal для single-tag
"""
from pathlib import Path

print('=' * 80)
print('ФИНАЛЬНЫЙ ФИКС: Seasonal анализ для single-tag')
print('=' * 80)
print()

api_path = Path('backend/modules/deep_analysis/api.py')
content = api_path.read_text(encoding='utf-8')

# 1. Добавляем блок seasonal анализа после histogram_spec
print('【1】Добавляем блок seasonal анализа после histogram_spec')
print('-' * 80)

old_block = '''            histogram_spec = create_histogram_spec(histogram, tag_name)

            # Формируем результат
            results = {
                "statistics": stats,
                "histogram": histogram,
                "anomalies": anomalies_result,
            }'''

new_block = '''            histogram_spec = create_histogram_spec(histogram, tag_name)

            # Сезонный анализ для single-tag
            seasonal_analysis = {}
            if len(data['raw_values']) >= 50:
                try:
                    periods_result = detect_dominant_periods(
                        data['raw_values'],
                        data['raw_timestamps']
                    )
                    
                    decomp_result = None
                    pattern_result = None
                    
                    if periods_result.get('detected_periods'):
                        main_period = periods_result['detected_periods'][0]['period']
                        decomp_result = decompose_seasonal(data['raw_values'], period=main_period)
                        pattern_result = get_seasonal_pattern(data['raw_values'], period=main_period)
                    
                    seasonal_analysis = {
                        "periods": periods_result,
                        "decomposition": decomp_result,
                        "pattern": pattern_result,
                    }
                except Exception as e:
                    log.warning("Seasonal analysis failed", tag=tag_name, error=str(e))
                    seasonal_analysis = {"error": str(e)}

            # Формируем результат
            results = {
                "statistics": stats,
                "histogram": histogram,
                "anomalies": anomalies_result,
                "seasonal_analysis": seasonal_analysis,
            }'''

if old_block in content:
    content = content.replace(old_block, new_block)
    print('✅ Блок seasonal анализа добавлен для single-tag')
    print('✅ seasonal_analysis добавлен в results')
else:
    print('⚠️  Блок не найден в ожидаемом виде')

api_path.write_text(content, encoding='utf-8', newline='\n')

print()
print('=' * 80)
print('ЧТО СДЕЛАНО:')
print('=' * 80)
print()
print('1. Добавлен блок вычисления seasonal_analysis для single-tag')
print('2. Добавлен ключ "seasonal_analysis" в словарь results')
print('3. seasonality=seasonal_analysis уже есть в AnalysisResponse (из предыдущего фикса)')
print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Backend перезагрузится сам')
print('2. Запусти анализ для single-tag:')
print()
print('   curl -s -X POST http://localhost:8081/api/v1/deep_analysis/run \\')
print('     -H "Content-Type: application/json" \\')
print('     -d \'{"tags": ["KITCHEN2-CO2"], "period": 7}\' | \\')
print('     python -c "import sys, json; data=json.load(sys.stdin); s=data.get(\'seasonality\', {}); print(json.dumps(s, indent=2, default=str)[:1000])"')
print()
print('3. Должен вернуться seasonal_analysis с detected_periods и variance_explained')
print('4. В логах должны появиться записи "Detected periodic patterns"')