#!/usr/bin/env python3
"""
integrate_seasonal_into_api.py — добавляем сезонный анализ в API DDA
"""
from pathlib import Path

print('=' * 80)
print('ИНТЕГРАЦИЯ: Сезонный анализ в API DDA')
print('=' * 80)
print()

api_path = Path('backend/modules/deep_analysis/api.py')
content = api_path.read_text(encoding='utf-8')

# 1. Добавляем импорт seasonal анализаторов
print('【1】Добавляем импорты seasonal анализаторов')
print('-' * 80)

old_imports = '''from modules.deep_analysis.analyzers.anomalies import (
    detect_anomalies_isolation_forest,
    classify_anomalies,
    AnomalyType,
)'''

new_imports = '''from modules.deep_analysis.analyzers.anomalies import (
    detect_anomalies_isolation_forest,
    classify_anomalies,
    AnomalyType,
)
from modules.deep_analysis.analyzers.seasonal import (
    detect_dominant_periods,
    decompose_seasonal,
    get_seasonal_pattern,
)'''

if old_imports in content:
    content = content.replace(old_imports, new_imports)
    print('✅ Импорты добавлены')
else:
    print('⚠️  Блок импортов не найден')

print()

# 2. Добавляем вызов seasonal анализа в функцию run_analysis
print('【2】Добавляем вызов seasonal анализа в run_analysis')
print('-' * 80)

# Находим место где возвращаем результаты
old_return = '''    return {
        "anomalies": {
            "total": total_anomalies,
            "per_tag": anomalies_per_tag,
            "type_counts": total_type_counts,
        },
        "correlation_matrix": correlation_matrix,
        "pair_analysis": pair_analysis,
    }'''

new_return = '''    # Сезонный анализ для каждого тега
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
    
    return {
        "anomalies": {
            "total": total_anomalies,
            "per_tag": anomalies_per_tag,
            "type_counts": total_type_counts,
        },
        "correlation_matrix": correlation_matrix,
        "pair_analysis": pair_analysis,
        "seasonal_analysis": seasonal_analysis,  # ← НОВОЕ
    }'''

if old_return in content:
    content = content.replace(old_return, new_return)
    print('✅ Seasonal анализ добавлен в run_analysis')
else:
    print('⚠️  Блок return не найден')

api_path.write_text(content, encoding='utf-8', newline='\n')

print()
print('=' * 80)
print('ЧТО ДОБАВЛЕНО:')
print('=' * 80)
print()
print('В response теперь есть поле "seasonal_analysis":')
print()
print('{')
print('  "anomalies": {...},')
print('  "correlation_matrix": {...},')
print('  "pair_analysis": {...},')
print('  "seasonal_analysis": {')
print('    "KITCHEN2-CO2": {')
print('      "periods": {')
print('        "detected_periods": [')
print('          {"period": 293, "confidence": 0.207, ...}')
print('        ]')
print('      },')
print('      "decomposition": {')
print('        "trend": [...],')
print('        "seasonal": [...],')
print('        "residual": [...]')
print('      },')
print('      "pattern": {')
print('        "pattern": [620.71, 583.86, ...],')
print('        "std": [170.03, 125.56, ...]')
print('      }')
print('    }')
print('  }')
print('}')
print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Backend перезагрузится сам')
print('2. Запусти анализ через API:')
print('   curl -X POST http://localhost:8081/api/v1/deep_analysis/run \\')
print('     -H "Content-Type: application/json" \\')
print('     -d \'{"tags": ["KITCHEN2-CO2"], "period": "7d"}\' | jq .results.seasonal_analysis')
print()
print('3. Должен вернуться seasonal_analysis с detected_periods')