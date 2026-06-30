#!/usr/bin/env python3
"""
fix_json_inf.py - убирает inf/nan из результатов A/B анализа
"""
from pathlib import Path

print('=' * 80)
print('ФИКС: JSON сериализация (inf/nan)')
print('=' * 80)
print()

# ============================================================================
# 1. Исправляем compare_snapshots — убираем float('inf')
# ============================================================================
ab_path = Path('backend/modules/deep_analysis/analyzers/ab.py')
content = ab_path.read_text(encoding='utf-8')

# Находим проблемный блок с delta
old_delta = '''    # Разница в процентах
    delta = {}
    for key in ['mean', 'median', 'std', 'min', 'max', 'range']:
        val_a = stats_a.get(key, 0)
        val_b = stats_b.get(key, 0)
        
        if val_a != 0:
            delta[key] = ((val_b - val_a) / abs(val_a)) * 100
        else:
            delta[key] = 0 if val_b == 0 else float('inf')'''

new_delta = '''    # Разница в процентах (с защитой от inf/nan)
    delta = {}
    for key in ['mean', 'median', 'std', 'min', 'max', 'range']:
        val_a = stats_a.get(key, 0)
        val_b = stats_b.get(key, 0)
        
        if val_a != 0 and abs(val_a) > 1e-10:
            delta_val = ((val_b - val_a) / abs(val_a)) * 100
            # Защита от inf/nan
            if delta_val != delta_val or abs(delta_val) > 1e6:  # isnan или очень большое
                delta[key] = 9999.0 if delta_val > 0 else -9999.0
            else:
                delta[key] = float(delta_val)
        else:
            delta[key] = 0.0 if val_b == 0 else 9999.0'''

if old_delta in content:
    content = content.replace(old_delta, new_delta)
    print('✅ Исправлен расчёт delta (убран inf)')
else:
    print('⚠️  Блок delta не найден')

# Также исправляем cohens_d и другие float значения
old_sig = '''    return {
        "statistics": {
            "a": stats_a,
            "b": stats_b,
            "delta": delta
        },
        "significance": {
            "t_stat": float(t_stat),
            "p_value": float(p_value),
            "cohens_d": float(cohens_d),
            "interpretation": significance_interp
        }
    }'''

new_sig = '''    # Защита от inf/nan в significance
    def safe_float(v, default=0.0):
        if v is None:
            return default
        v = float(v)
        if v != v or abs(v) > 1e10:  # isnan или слишком большое
            return default
        return v
    
    return {
        "statistics": {
            "a": stats_a,
            "b": stats_b,
            "delta": delta
        },
        "significance": {
            "t_stat": safe_float(t_stat),
            "p_value": safe_float(p_value, 1.0),
            "cohens_d": safe_float(cohens_d),
            "interpretation": significance_interp
        }
    }'''

if old_sig in content:
    content = content.replace(old_sig, new_sig)
    print('✅ Исправлен return significance (защита от inf/nan)')

# ============================================================================
# 2. Добавляем JSONResponse с обработкой ошибок в endpoint
# ============================================================================
print()
print('【2】Оборачиваем endpoint в try/except')
print('-' * 80)

api_path = Path('backend/modules/deep_analysis/api.py')
api_content = api_path.read_text(encoding='utf-8')

# Добавляем import JSONResponse если нет
if 'JSONResponse' not in api_content:
    api_content = api_content.replace(
        'from fastapi import APIRouter, HTTPException, Query, Request',
        'from fastapi import APIRouter, HTTPException, Query, Request\nfrom fastapi.responses import JSONResponse'
    )
    print('✅ Добавлен import JSONResponse')

# Оборачиваем endpoint в try/except
# Находим начало функции
endpoint_start_marker = '@router.post("/ab")\nasync def ab_analysis(request: Request):'

if endpoint_start_marker in api_content and 'import traceback' not in api_content:
    # Добавляем traceback в начало файла
    if 'import traceback' not in api_content:
        api_content = api_content.replace(
            'from datetime import datetime',
            'from datetime import datetime\nimport traceback'
        )
        print('✅ Добавлен import traceback')

# Добавляем try/except в конец функции (перед return result)
old_return = '''    if pattern_comparison:
        result["pattern_comparison"] = pattern_comparison
    
    return result'''

new_return = '''    if pattern_comparison:
        result["pattern_comparison"] = pattern_comparison
    
    return result'''

# Теперь оборачиваем всю функцию в try/except
# Ищем маркер начала функции
if 'try:' not in api_content.split('async def ab_analysis')[1].split('async def ')[0][:200]:
    # Оборачиваем тело функции
    old_body_start = '''    body = await request.json()
    
    snapshot_a = body.get('snapshot_a', {})'''
    
    new_body_start = '''    try:
        body = await request.json()
        
        snapshot_a = body.get('snapshot_a', {})'''
    
    if old_body_start in api_content:
        api_content = api_content.replace(old_body_start, new_body_start, 1)
        
        # Добавляем except в самый конец (перед следующим @router или в конце файла)
        # Ищем конец функции (следующий @router или конец файла)
        ab_func_start = api_content.find('async def ab_analysis(request: Request):')
        if ab_func_start != -1:
            # Ищем следующее async def или @router после ab_analysis
            next_func = api_content.find('\n@router.', ab_func_start + 100)
            if next_func == -1:
                next_func = len(api_content)
            
            # Находим return result внутри функции
            return_pos = api_content.rfind('return result', ab_func_start, next_func)
            if return_pos != -1:
                # Вставляем except после return result (отступ)
                except_block = '''
    except Exception as e:
        log.error("A/B analysis failed", error=str(e), traceback=traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={
                "error": str(e),
                "detail": "A/B analysis failed",
                "traceback": traceback.format_exc().split('\\n')[-5:]
            }
        )
'''
                # Находим позицию после 'return result\n'
                insert_pos = api_content.find('\n', return_pos) + 1
                api_content = api_content[:insert_pos] + except_block + api_content[insert_pos:]
                print('✅ Endpoint обёрнут в try/except')

api_path.write_text(api_content, encoding='utf-8')
ab_path.write_text(content, encoding='utf-8')

print()
print('=' * 80)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 80)
print()
print('1. В compare_snapshots:')
print('   • float("inf") заменён на 9999.0')
print('   • Добавлена функция safe_float() для защиты significance')
print('   • NaN проверяется через v != v (idiomatic Python)')
print()
print('2. В endpoint ab_analysis:')
print('   • Тело обёрнуто в try/except')
print('   • При ошибке возвращается JSONResponse с traceback')
print('   • Теперь curl увидит ЧТО СЛОМАЛОСЬ, а не пустой ответ')
print()
print('=' * 80)
print('ТЕСТИРОВАНИЕ:')
print('=' * 80)
print()
print('1. Перезапусти backend')
print('2. Попробуй curl снова')
print('3. Если будут ошибки — увидишь их в ответе')