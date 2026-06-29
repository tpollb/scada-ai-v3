#!/usr/bin/env python3
"""
add_seasonal_single_tag.py — добавляем seasonal анализ для single-tag
"""
from pathlib import Path

print('=' * 80)
print('ФИКС: Добавляем seasonal анализ для single-tag')
print('=' * 80)
print()

api_path = Path('backend/modules/deep_analysis/api.py')
content = api_path.read_text(encoding='utf-8')

# Находим single-tag блок results = {
print('【1】Добавляем seasonal анализ для single-tag')
print('-' * 80)

old_single_tag_results = '''            histogram_spec = create_histogram_spec(histogram, tag_name)

            # Формируем результат
            results = {
                "statistics": stats,
                "histogram": histogram,
                "anomalies": anomalies_result,
            }'''

new_single_tag_results = '''            histogram_spec = create_histogram_spec(histogram, tag_name)

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

if old_single_tag_results in content:
    content = content.replace(old_single_tag_results, new_single_tag_results)
    print('✅ Seasonal анализ добавлен для single-tag')
else:
    print('⚠️  Блок не найден')

# Изменяем seasonality=None для single-tag в AnalysisResponse
print()
print('【2】Изменяем seasonality=None для single-tag в AnalysisResponse')
print('-' * 80)

old_single_response = '''            # Один тег
            response = AnalysisResponse(
                analysis_id=analysis_id,
                status="completed",
                created_at=datetime.now().isoformat(),
                tags=request.tags,
                period=period_str,
                summary=summary,
                statistics=stats,
                anomalies=anomalies_result,
                correlations=None,
                seasonality=None,'''

new_single_response = '''            # Один тег
            response = AnalysisResponse(
                analysis_id=analysis_id,
                status="completed",
                created_at=datetime.now().isoformat(),
                tags=request.tags,
                period=period_str,
                summary=summary,
                statistics=stats,
                anomalies=anomalies_result,
                correlations=None,
                seasonality=seasonal_analysis,'''

if old_single_response in content:
    content = content.replace(old_single_response, new_single_response)
    print('✅ seasonality=None → seasonality=seasonal_analysis для single-tag')
else:
    print('⚠️  Блок не найден')

api_path.write_text(content, encoding='utf-8', newline='\n')

print()
print('=' * 80)
print('ЧТО СДЕЛАНО:')
print('=' * 80)
print()
print('1. Добавлен блок seasonal анализа для single-tag')
print('2. seasonality=None изменён на seasonality=seasonal_analysis')
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
print('     python -c "import sys, json; data=json.load(sys.stdin); print(json.dumps(data.get(\'seasonality\', {}), indent=2, default=str))"')
print()
print('3. Должен вернуться seasonal_analysis с detected_periods и variance_explained')