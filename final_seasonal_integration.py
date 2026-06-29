#!/usr/bin/env python3
"""
final_seasonal_integration.py — финальная интеграция seasonal в API
"""
from pathlib import Path

print('=' * 80)
print('ФИНАЛЬНАЯ ИНТЕГРАЦИЯ: Seasonal анализ в api.py')
print('=' * 80)
print()

api_path = Path('backend/modules/deep_analysis/api.py')
content = api_path.read_text(encoding='utf-8')

# 1. Добавляем блок seasonal анализа ПЕРЕД "results = {"
print('【1】Добавляем блок seasonal анализа')
print('-' * 80)

old_results_block = '''            # Формируем результаты
            results = {
                "correlation_matrix": correlation_matrix,
                "pair_analysis": pair_analysis,
            }'''

new_results_block = '''            # Сезонный анализ для каждого тега
            seasonal_analysis = {}
            for tag_name in request.tags:
                tag_data = data['tags'].get(tag_name, {})
                aligned_values = tag_data.get('aligned_values', [])
                
                if len(aligned_values) >= 50:  # минимум данных для анализа
                    try:
                        # Детекция доминирующих периодов
                        periods_result = detect_dominant_periods(
                            aligned_values,
                            data['common_timestamps']
                        )
                        
                        # Если нашли периоды — делаем декомпозицию
                        decomp_result = None
                        pattern_result = None
                        
                        if periods_result.get('detected_periods'):
                            main_period = periods_result['detected_periods'][0]['period']
                            
                            # Декомпозиция
                            decomp_result = decompose_seasonal(aligned_values, period=main_period)
                            
                            # Типичный паттерн
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

if old_results_block in content:
    content = content.replace(old_results_block, new_results_block)
    print('✅ Блок seasonal анализа добавлен')
else:
    print('⚠️  Блок не найден — показываю что есть:')
    # Ищем альтернативный паттерн
    if 'results = {' in content and 'correlation_matrix' in content:
        print('   Найден results = { с correlation_matrix')
        print('   Возможно форматирование отличается')

# 2. Изменяем seasonality=None на seasonality=seasonal_analysis в AnalysisResponse
print()
print('【2】Изменяем seasonality=None в AnalysisResponse')
print('-' * 80)

# Ищем блок multi-tag response
old_response = '''            # Мульти-тег
            response = AnalysisResponse(
                analysis_id=analysis_id,
                status="completed",
                created_at=datetime.now().isoformat(),
                tags=request.tags,
                period=period_str,
                summary=summary,
                statistics=None,
                anomalies=combined_anomalies,  # НОВОЕ: аномалии для мульти-тег
                correlations=correlation_matrix,
                seasonality=None,'''

new_response = '''            # Мульти-тег
            response = AnalysisResponse(
                analysis_id=analysis_id,
                status="completed",
                created_at=datetime.now().isoformat(),
                tags=request.tags,
                period=period_str,
                summary=summary,
                statistics=None,
                anomalies=combined_anomalies,  # НОВОЕ: аномалии для мульти-тег
                correlations=correlation_matrix,
                seasonality=seasonal_analysis,'''

if old_response in content:
    content = content.replace(old_response, new_response)
    print('✅ seasonality=None → seasonality=seasonal_analysis')
else:
    print('⚠️  Блок не найден')

api_path.write_text(content, encoding='utf-8', newline='\n')

print()
print('=' * 80)
print('ЧТО СДЕЛАНО:')
print('=' * 80)
print()
print('1. Добавлен блок seasonal анализа перед "results = {":')
print('   • Для каждого тега вызывается detect_dominant_periods()')
print('   • Если найдены периоды — делается decompose_seasonal()')
print('   • Строится get_seasonal_pattern()')
print('   • Результаты добавляются в словарь seasonal_analysis')
print()
print('2. В results добавлен ключ "seasonal_analysis"')
print()
print('3. В AnalysisResponse изменено:')
print('   seasonality=None → seasonality=seasonal_analysis')
print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Backend перезагрузится сам')
print('2. Запусти анализ:')
print()
print('   curl -s -X POST http://localhost:8081/api/v1/deep_analysis/run \\')
print('     -H "Content-Type: application/json" \\')
print('     -d \'{"tags": ["KITCHEN2-CO2", "R001-CO2"], "period": 7}\' | \\')
print('     python -c "import sys, json; data=json.load(sys.stdin); print(json.dumps(data.get(\'seasonality\', {}), indent=2, default=str))"')
print()
print('3. Должен вернуться seasonal_analysis с detected_periods')
print('4. В логах должны появиться записи "Detected periodic patterns"')