#!/usr/bin/env python3
"""
apply_seasonal_integration.py — применяет интеграцию seasonal анализа в api.py
"""
from pathlib import Path

print("=" * 80)
print("ПРИМЕНЕНИЕ: Интеграция seasonal анализа в api.py")
print("=" * 80)
print()

api_path = Path('backend/modules/deep_analysis/api.py')
content = api_path.read_text(encoding='utf-8')
original_len = len(content)

changes_made = []

# 1. Добавляем импорт после строки с import anomalies
print("【1】Добавляем импорт seasonal функций:")
import_marker = "from modules.deep_analysis.analyzers.anomalies import detect_anomalies_isolation_forest"
if import_marker in content:
    # Ищем строку где импортируется correlations (следующий импорт)
    next_import = "from modules.deep_analysis.analyzers.correlations import compute_correlation_matrix"
    if next_import in content:
        # Вставляем наш импорт ПЕРЕД correlations
        new_import = "from modules.deep_analysis.analyzers.seasonal import detect_dominant_periods, decompose_seasonal, get_seasonal_pattern\n"
        content = content.replace(next_import, new_import + next_import)
        changes_made.append("Импорт seasonal функций добавлен")
        print("   ✅ Добавлен импорт после anomalies, перед correlations")
    else:
        # Вставляем просто после anomalies
        new_import = "\nfrom modules.deep_analysis.analyzers.seasonal import detect_dominant_periods, decompose_seasonal, get_seasonal_pattern"
        content = content.replace(import_marker, import_marker + new_import)
        changes_made.append("Импорт seasonal функций добавлен")
        print("   ✅ Добавлен импорт после anomalies")
else:
    print("   ❌ Маркер импорта не найден!")

# 2. Находим блок results = { для multi-tag и добавляем seasonal_analysis
print()
print("【2】Ищем блок results = { для multi-tag:")

# Ищем характерный паттерн: results = { после correlation_matrix
results_marker = 'results = {\n                "correlation_matrix": correlation_matrix,\n                "pair_analysis": pair_analysis,\n            }'

if results_marker in content:
    print("   ✅ Найден точный блок results = {")
    
    # Добавляем блок seasonal анализа ПЕРЕД results = {
    seasonal_block = '''
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

'''
    
    # Вставляем блок перед results = {
    content = content.replace(
        '            # Формируем результаты\n            results = {',
        seasonal_block + '            # Формируем результаты\n            results = {'
    )
    
    # Также добавляем seasonal_analysis в results
    content = content.replace(
        'results = {\n                "correlation_matrix": correlation_matrix,\n                "pair_analysis": pair_analysis,\n            }',
        'results = {\n                "correlation_matrix": correlation_matrix,\n                "pair_analysis": pair_analysis,\n                "seasonal_analysis": seasonal_analysis,\n            }'
    )
    
    changes_made.append("Блок seasonal анализа добавлен")
    print("   ✅ Блок seasonal анализа добавлен перед results = {")
    print("   ✅ seasonal_analysis добавлен в results")
else:
    print("   ⚠️  Точный блок не найден — показываю контекст вокруг 'results = {':")
    import re
    for match in re.finditer(r'results = \{', content):
        start = max(0, match.start() - 200)
        end = min(len(content), match.end() + 200)
        print("   ---")
        print(content[start:end])
        print("   ---")

# 3. Изменяем seasonality=None на seasonality=seasonal_analysis
print()
print("【3】Изменяем seasonality=None в AnalysisResponse для multi-tag:")

# Ищем блок multi-tag response
multitag_response_marker = '''        else:
            # Мульти-тег
            response = AnalysisResponse('''

if multitag_response_marker in content:
    print("   ✅ Найден блок мульти-тег response")
    # Ищем seasonality=None внутри этого блока и заменяем на seasonality=seasonal_analysis
    # Берём контекст после маркера
    start_idx = content.find(multitag_response_marker)
    end_idx = content.find('        log.info("Analysis completed"', start_idx)
    
    if end_idx > start_idx:
        block = content[start_idx:end_idx]
        if 'seasonality=None' in block:
            block = block.replace('seasonality=None', 'seasonality=seasonal_analysis')
            content = content[:start_idx] + block + content[end_idx:]
            changes_made.append("seasonality=None → seasonality=seasonal_analysis")
            print("   ✅ seasonality=None изменён на seasonality=seasonal_analysis")
        else:
            print("   ⚠️  seasonality=None не найден в блоке")
    else:
        print("   ⚠️  Не удалось найти границы блока")
else:
    print("   ❌ Блок мульти-тег response не найден")

# Сохраняем
print()
print("【4】Сохраняем файл:")
if changes_made:
    api_path.write_text(content, encoding='utf-8', newline='\n')
    new_len = len(content)
    print(f"   ✅ Файл сохранён")
    print(f"   Размер: {original_len} → {new_len} символов (+{new_len - original_len})")
    print()
    print("Внесённые изменения:")
    for i, change in enumerate(changes_made, 1):
        print(f"   {i}. {change}")
else:
    print("   ❌ Изменений не внесено")

print()
print("=" * 80)
print("ПРОВЕРКА:")
print("=" * 80)
print()
print("1. Backend должен перезагрузиться автоматически (если включён --reload)")
print("2. Проверим логи:")
print("   tail -f backend/logs/*.log | grep -i 'seasonal\\|periodic'")
print()
print("3. Запустим анализ и проверим seasonality:")
print("   curl -s -X POST http://localhost:8081/api/v1/deep_analysis/run \\")
print("     -H 'Content-Type: application/json' \\")
print("     -d '{\"tags\": [\"KITCHEN2-CO2\", \"R001-CO2\"], \"period\": 7}' | \\")
print("     python -c \"import sys, json; data=json.load(sys.stdin); print(json.dumps(data.get('seasonality', {}), indent=2, default=str))\"")
print()
print("Ожидаемый результат:")
print('  {')
print('    "KITCHEN2-CO2": {')
print('      "periods": {')
print('        "detected_periods": [')
print('          {"period": 293, "frequency": 0.0034, "confidence": 0.207}')
print('        ]')
print('      }')
print('    }')
print('  }')