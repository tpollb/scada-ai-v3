#!/usr/bin/env python3
"""
integrate_seasonal_correct.py — правильная интеграция seasonal в api.py
"""
from pathlib import Path

print('=' * 80)
print('ИНТЕГРАЦИЯ: Seasonal анализ в api.py (правильная версия)')
print('=' * 80)
print()

api_path = Path('backend/modules/deep_analysis/api.py')
content = api_path.read_text(encoding='utf-8')

# 1. Добавляем импорт seasonal функций
print('【1】Добавляем импорты seasonal')
print('-' * 80)

old_imports = '''from modules.deep_analysis.analyzers.anomalies import detect_anomalies_isolation_forest
from modules.deep_analysis.analyzers.correlations import compute_correlation_matrix, compute_pair_correlation'''

new_imports = '''from modules.deep_analysis.analyzers.anomalies import detect_anomalies_isolation_forest
from modules.deep_analysis.analyzers.correlations import compute_correlation_matrix, compute_pair_correlation
from modules.deep_analysis.analyzers.seasonal import detect_dominant_periods, decompose_seasonal, get_seasonal_pattern'''

if old_imports in content:
    content = content.replace(old_imports, new_imports)
    print('✅ Импорты добавлены')
else:
    print('⚠️  Блок импортов не найден — проверяем вручную')
    if 'detect_dominant_periods' in content:
        print('ℹ️  Импорты уже есть')

print()

# 2. Добавляем блок сезонного анализа перед формированием results
print('【2】Добавляем блок сезонного анализа')
print('-' * 80)

old_results_block = '''            )

            # Формируем результаты
            results = {
                "correlation_matrix": correlation_matrix,
                "pair_analysis": pair_analysis,
            }'''

new_results_block = '''            )

            # Сезонный анализ для каждого тега
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
    print('✅ Блок сезонного анализа добавлен')
else:
    print('⚠️  Блок не найден — показываю контекст вокруг строки 270')

api_path.write_text(content, encoding='utf-8', newline='\n')

print()
print('=' * 80)
print('ЧТО ДОБАВЛЕНО:')
print('=' * 80)
print()
print('1. Импорты:')
print('   from modules.deep_analysis.analyzers.seasonal import (')
print('       detect_dominant_periods, decompose_seasonal, get_seasonal_pattern')
print('   )')
print()
print('2. Блок сезонного анализа для каждого тега:')
print('   • detect_dominant_periods() — поиск периодов через FFT')
print('   • decompose_seasonal() — trend + seasonal + residual')
print('   • get_seasonal_pattern() — типичный паттерн')
print()
print('3. В response добавлен ключ "seasonal_analysis"')
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
print('     python -c "import sys, json; data=json.load(sys.stdin); print(json.dumps(data.get(\'results\', {}).get(\'seasonal_analysis\', {}), indent=2, default=str))"')
print()
print('3. Должен вернуться seasonal_analysis с detected_periods для каждого тега')