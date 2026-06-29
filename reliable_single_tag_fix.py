#!/usr/bin/env python3
"""
reliable_single_tag_fix.py — надёжный фикс seasonal для single-tag
"""
from pathlib import Path
import re

print('=' * 80)
print('НАДЁЖНЫЙ ФИКС: Seasonal анализ для single-tag')
print('=' * 80)
print()

api_path = Path('backend/modules/deep_analysis/api.py')
content = api_path.read_text(encoding='utf-8')

# 1. Находим строку с histogram_spec
print('【1】Ищем histogram_spec = create_histogram_spec(histogram, tag_name)')
print('-' * 80)

marker = 'histogram_spec = create_histogram_spec(histogram, tag_name)'
if marker in content:
    print(f'✅ Найден маркер: {marker}')
    
    # 2. Находим позицию маркера
    marker_pos = content.find(marker)
    
    # 3. Ищем следующий блок "results = {"
    results_marker = 'results = {'
    results_pos = content.find(results_marker, marker_pos)
    
    if results_pos != -1:
        print(f'✅ Найден блок results = {{ на позиции {results_pos}')
        
        # 4. Находим закрывающую } этого блока
        # Ищем следующую строку с "}" которая закрывает словарь
        search_start = results_pos
        brace_count = 0
        found_opening = False
        closing_pos = -1
        
        for i in range(search_start, min(search_start + 500, len(content))):
            if content[i] == '{':
                brace_count += 1
                found_opening = True
            elif content[i] == '}':
                brace_count -= 1
                if found_opening and brace_count == 0:
                    closing_pos = i
                    break
        
        if closing_pos != -1:
            print(f'✅ Найдена закрывающая }} на позиции {closing_pos}')
            
            # 5. Вставляем блок seasonal анализа ПЕРЕД results = {
            seasonal_block = '''
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

'''
            
            # Вставляем seasonal_block перед results = {
            content = content[:results_pos] + seasonal_block + content[results_pos:]
            
            # 6. Теперь нужно добавить "seasonal_analysis": seasonal_analysis в словарь results
            # Находим позицию где мы только что вставили seasonal_block
            new_results_pos = results_pos + len(seasonal_block)
            
            # Ищем закрывающую } словаря results (она теперь сдвинулась)
            search_start = new_results_pos
            brace_count = 0
            found_opening = False
            closing_pos = -1
            
            for i in range(search_start, min(search_start + 500, len(content))):
                if content[i] == '{':
                    brace_count += 1
                    found_opening = True
                elif content[i] == '}':
                    brace_count -= 1
                    if found_opening and brace_count == 0:
                        closing_pos = i
                        break
            
            if closing_pos != -1:
                # Вставляем "seasonal_analysis": seasonal_analysis перед закрывающей }
                # Находим последнюю запятую перед }
                last_comma = content.rfind(',', search_start, closing_pos)
                
                if last_comma != -1:
                    # Вставляем после последней запятой
                    insertion = '\n                "seasonal_analysis": seasonal_analysis,'
                    content = content[:last_comma + 1] + insertion + content[last_comma + 1:]
                    print('✅ Добавлен "seasonal_analysis": seasonal_analysis в словарь results')
                else:
                    print('⚠️  Не найдена запятая перед закрывающей }')
            else:
                print('⚠️  Не найдена закрывающая } для словаря results')
            
            # 7. Сохраняем файл
            api_path.write_text(content, encoding='utf-8', newline='\n')
            print()
            print('✅ Файл успешно обновлён!')
            
        else:
            print('❌ Не найдена закрывающая } для блока results')
    else:
        print('❌ Не найден блок results = {')
else:
    print('❌ Маркер histogram_spec не найден')

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
print()
print('Ожидаемый результат:')
print('{')
print('  "periods": {')
print('    "detected_periods": [...]')
print('  },')
print('  "decomposition": {...},')
print('  "pattern": {...}')
print('}')