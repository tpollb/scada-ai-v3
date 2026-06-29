#!/usr/bin/env python3
"""
final_single_tag_fix.py — точечный фикс seasonal для single-tag (точная замена)
"""
from pathlib import Path

print('=' * 80)
print('ФИНАЛЬНЫЙ ТОЧЕЧНЫЙ ФИКС: Seasonal анализ для single-tag')
print('=' * 80)
print()

api_path = Path('backend/modules/deep_analysis/api.py')
content = api_path.read_text(encoding='utf-8')

# Точный паттерн из файла (строки 164-171)
old_block = '''            histogram_spec = create_histogram_spec(histogram, tag_name)

            # Формируем результат
            results = {
                "statistics": stats,
                "histogram": histogram,
                "anomalies": anomalies_result,
            }'''

# Новый блок с вычислением seasonal_analysis
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
    api_path.write_text(content, encoding='utf-8', newline='\n')
    print('✅ Блок seasonal анализа УСПЕШНО добавлен для single-tag')
    print('✅ seasonal_analysis теперь вычисляется перед использованием в AnalysisResponse')
else:
    print('❌ КРИТИЧНО: Блок не найден. Показываю что реально в файле:')
    print('-' * 80)
    # Ищем ближайший контекст
    idx = content.find('histogram_spec = create_histogram_spec(histogram, tag_name)')
    if idx != -1:
        print(content[idx:idx+400])
    print('-' * 80)

print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('Запусти анализ для single-tag:')
print()
print('curl -s -X POST http://localhost:8081/api/v1/deep_analysis/run \\')
print('  -H "Content-Type: application/json" \\')
print('  -d \'{"tags": ["KITCHEN2-CO2"], "period": 7}\' | \\')
print('  python -c "import sys, json; data=json.load(sys.stdin); print(json.dumps(data.get(\'seasonality\', {}), indent=2, default=str)[:2000])"')