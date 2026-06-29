#!/usr/bin/env python3
"""
fix_numpy_serialization.py — чиним сериализацию numpy типов в seasonal.py
"""
from pathlib import Path

print('=' * 80)
print('ФИКС: Сериализация numpy типов в seasonal.py')
print('=' * 80)
print()

seasonal_path = Path('backend/modules/deep_analysis/analyzers/seasonal.py')
content = seasonal_path.read_text(encoding='utf-8')

changes = []

# 1. Исправляем significant: numpy.bool → bool
print('【1】Исправляем numpy.bool в _compute_autocorrelation')
print('-' * 80)

old_significant = '''                peaks.append({
                    "lag": int(lag),
                    "correlation": float(autocorr[lag]),
                    "significant": autocorr[lag] > 2 * significance,
                })'''

new_significant = '''                peaks.append({
                    "lag": int(lag),
                    "correlation": float(autocorr[lag]),
                    "significant": bool(autocorr[lag] > 2 * significance),  # numpy.bool → bool
                })'''

if old_significant in content:
    content = content.replace(old_significant, new_significant)
    changes.append('significant: numpy.bool → bool')
    print('✅ Исправлено')
else:
    print('⚠️  Паттерн не найден')

print()

# 2. Добавляем явную конвертацию в _merge_period_candidates
print('【2】Добавляем явную конвертацию типов в _merge_period_candidates')
print('-' * 80)

old_merge = '''    # Фильтруем по confidence и significance
    result = []
    for period, data in candidates.items():
        if data['confidence'] >= significance_threshold:
            result.append({
                "period": data['period'],
                "frequency": data['frequency'],
                "power": data['fft_power'],
                "autocorrelation": data['autocorr'],
                "confidence": round(data['confidence'], 3),
            })'''

new_merge = '''    # Фильтруем по confidence и significance
    result = []
    for period, data in candidates.items():
        if data['confidence'] >= significance_threshold:
            result.append({
                "period": int(data['period']),
                "frequency": float(data['frequency']),
                "power": float(data['fft_power']),
                "autocorrelation": float(data['autocorr']) if data['autocorr'] is not None else None,
                "confidence": round(float(data['confidence']), 3),
            })'''

if old_merge in content:
    content = content.replace(old_merge, new_merge)
    changes.append('_merge_period_candidates: явная конвертация типов')
    print('✅ Исправлено')
else:
    print('⚠️  Паттерн не найден')

print()

# 3. Добавляем обработку numpy типов в storage.py json_serializer
print('【3】Улучшаем json_serializer в storage.py для numpy типов')
print('-' * 80)

storage_path = Path('backend/modules/deep_analysis/history/storage.py')
if storage_path.exists():
    storage_content = storage_path.read_text(encoding='utf-8')
    
    old_serializer = '''def json_serializer(obj):
    """Кастомный сериализатор для JSON."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, date):
        return obj.isoformat()
    if isinstance(obj, set):
        return list(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")'''
    
    new_serializer = '''def json_serializer(obj):
    """Кастомный сериализатор для JSON."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, date):
        return obj.isoformat()
    if isinstance(obj, set):
        return list(obj)
    # Обработка numpy типов
    if hasattr(obj, 'item'):  # numpy scalar types (bool_, int64, float64, etc.)
        return obj.item()
    if hasattr(obj, 'tolist'):  # numpy arrays
        return obj.tolist()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")'''
    
    if old_serializer in storage_content:
        storage_content = storage_content.replace(old_serializer, new_serializer)
        storage_path.write_text(storage_content, encoding='utf-8', newline='\n')
        changes.append('json_serializer: добавлена обработка numpy типов')
        print('✅ Исправлено')
    else:
        print('⚠️  Паттерн не найден — возможно уже улучшен')
        if 'hasattr(obj, \'item\')' in storage_content:
            print('ℹ️  Обработка numpy уже есть')
else:
    print('⚠️  storage.py не найден')

seasonal_path.write_text(content, encoding='utf-8', newline='\n')

print()
print('=' * 80)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 80)
for change in changes:
    print(f'  • {change}')
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
print('3. Ожидаемый результат:')
print('   {')
print('     "KITCHEN2-CO2": {')
print('       "periods": {')
print('         "detected_periods": [')
print('           {"period": 293, "frequency": 0.0034, "confidence": 0.207}')
print('         ]')
print('       }')
print('     }')
print('   }')