#!/usr/bin/env python3
"""
fix_histogram_keyerror.py — диагностика + фикс KeyError в гистограмме
"""
from pathlib import Path
import re

print('=' * 80)
print('ФИКС: KeyError в create_histogram_spec')
print('=' * 80)
print()

# 1. Смотрим что возвращает compute_histogram
stats_path = Path('backend/modules/deep_analysis/analyzers/statistics.py')
if stats_path.exists():
    content = stats_path.read_text(encoding='utf-8')
    
    # Ищем функцию compute_histogram
    match = re.search(r'def compute_histogram.*?(?=\n\ndef|\Z)', content, re.DOTALL)
    if match:
        print('【1】Текущая реализация compute_histogram:')
        print('-' * 80)
        print(match.group(0)[:500])
        print()
        
        # Проверяем что возвращается
        if "'counts':" in match.group(0) or '"counts":' in match.group(0):
            print('✅ compute_histogram возвращает "counts"')
        elif "'histogram':" in match.group(0) or '"histogram":' in match.group(0):
            print('❌ compute_histogram возвращает "histogram" вместо "counts"')
        elif 'return np.histogram' in match.group(0) or 'return counts, bin_edges' in match.group(0):
            print('ℹ️  compute_histogram возвращает tuple (counts, bin_edges)')
    else:
        print('⚠️  Функция compute_histogram не найдена')
else:
    print('⚠️  statistics.py не найден')

print()

# 2. Смотрим create_histogram_spec
chart_specs_path = Path('backend/modules/deep_analysis/visualizers/chart_specs.py')
cs_content = chart_specs_path.read_text(encoding='utf-8')

print('【2】Текущая реализация create_histogram_spec:')
print('-' * 80)
match = re.search(r'def create_histogram_spec.*?(?=\n\ndef|\Z)', cs_content, re.DOTALL)
if match:
    print(match.group(0)[:800])
print()

# 3. ФИКС: Делаем create_histogram_spec устойчивым к разным форматам
old_histogram = '''def create_histogram_spec(
    histogram_data: dict,
    tag_name: str,
) -> dict:
    """Создаёт JSON-спецификацию для гистограммы распределения."""
    spec = {
        "type": "bar",
        "data": {
            "labels": [f"{edge:.2f}" for edge in histogram_data['bin_edges'][:-1]],
            "datasets": [{
                "label": f"Распределение {tag_name}",
                "data": histogram_data['counts'],
                "backgroundColor": "rgba(59, 130, 246, 0.5)",
                "borderColor": "rgba(59, 130, 246, 1)",
                "borderWidth": 1,
            }]
        },
        "options": {
            "responsive": True,
            "maintainAspectRatio": False,
            "plugins": {
                "legend": {"display": False},
            },
            "scales": {
                "x": {"title": {"display": True, "text": "Значение"}},
                "y": {"title": {"display": True, "text": "Частота"}},
            },
        },
    }

    return spec'''

new_histogram = '''def create_histogram_spec(
    histogram_data: dict,
    tag_name: str,
) -> dict:
    """Создаёт JSON-спецификацию для гистограммы распределения.
    
    Поддерживает разные форматы данных:
    - {'counts': [...], 'bin_edges': [...]}
    - {'histogram': [...], 'bin_edges': [...]}
    - tuple (counts, bin_edges) — результат np.histogram
    """
    # Извлекаем данные в зависимости от формата
    if isinstance(histogram_data, tuple) and len(histogram_data) == 2:
        # np.histogram возвращает (counts, bin_edges)
        counts, bin_edges = histogram_data
    elif isinstance(histogram_data, dict):
        # Пробуем разные ключи
        counts = histogram_data.get('counts') or histogram_data.get('histogram') or histogram_data.get('values', [])
        bin_edges = histogram_data.get('bin_edges') or histogram_data.get('bins') or histogram_data.get('edges', [])
    else:
        # Fallback
        counts, bin_edges = [], []
    
    # Если counts пустой — возвращаем пустой график
    if not counts or not bin_edges:
        counts = [0] * 10
        bin_edges = [0] * 11
    
    spec = {
        "type": "bar",
        "data": {
            "labels": [f"{edge:.2f}" for edge in bin_edges[:-1]],
            "datasets": [{
                "label": f"Распределение {tag_name}",
                "data": list(counts),
                "backgroundColor": "rgba(59, 130, 246, 0.5)",
                "borderColor": "rgba(59, 130, 246, 1)",
                "borderWidth": 1,
            }]
        },
        "options": {
            "responsive": True,
            "maintainAspectRatio": False,
            "plugins": {
                "legend": {"display": False},
            },
            "scales": {
                "x": {"title": {"display": True, "text": "Значение"}},
                "y": {"title": {"display": True, "text": "Частота"}},
            },
        },
    }

    return spec'''

if old_histogram in cs_content:
    cs_content = cs_content.replace(old_histogram, new_histogram)
    chart_specs_path.write_text(cs_content, encoding='utf-8', newline='\n')
    print('✅ 3. create_histogram_spec обновлена — поддерживает разные форматы')
    print('   • dict с "counts" или "histogram"')
    print('   • tuple (counts, bin_edges) от np.histogram')
    print('   • fallback на пустой график если данных нет')
else:
    # Пробуем альтернативный паттерн
    if "histogram_data['counts']" in cs_content:
        # Заменяем через regex
        pattern = r'"data": histogram_data\[\'counts\'\]'
        replacement = '"data": list(histogram_data.get(\'counts\', histogram_data.get(\'histogram\', histogram_data.get(\'values\', []))))'
        cs_content = re.sub(pattern, replacement, cs_content)
        
        # Также обновляем labels
        pattern2 = r'"labels": \[f"\{edge:.2f\}" for edge in histogram_data\[\'bin_edges\'\]\[:-1\]\]'
        replacement2 = '"labels": [f"{edge:.2f}" for edge in (histogram_data.get(\'bin_edges\') or histogram_data.get(\'bins\') or histogram_data.get(\'edges\', []))[:-1]]'
        cs_content = re.sub(pattern2, replacement2, cs_content)
        
        chart_specs_path.write_text(cs_content, encoding='utf-8', newline='\n')
        print('✅ 3. create_histogram_spec обновлена (через regex)')
    else:
        print('⚠️  Не удалось найти паттерн для замены')

print()
print('=' * 80)
print('ФИНАЛЬНАЯ ДИАГНОСТИКА')
print('=' * 80)
print()

# Проверяем что исправлено
cs_check = chart_specs_path.read_text(encoding='utf-8')
if "histogram_data.get('counts')" in cs_check or 'isinstance(histogram_data, tuple)' in cs_check:
    print('✅ create_histogram_spec теперь устойчива к разным форматам')
else:
    print('❌ create_histogram_spec всё ещё использует прямой доступ к [\'counts\']')

print()
print('=' * 80)
print('ЧТО РАБОТАЕТ (по логам):')
print('=' * 80)
print()
print('✅ Провалы детектируются: dip: 3 (было 0)')
print('✅ Плато 409,409,409 больше НЕ drift: drift: 0')
print('✅ Шум правильно классифицирован: noise: 745')
print('✅ Пики работают: spike: 6')
print('✅ Zero dips детектируются: zero_dips=1')
print('✅ Teги все возвращаются: 1527 в БД, все доступны')
print()
print('=' * 80)
print('СЛЕДУЮЩИЙ ШАГ:')
print('=' * 80)
print()
print('Перезапусти backend и повтори проверку:')
print()
print('  curl -s -X POST http://localhost:8081/api/v1/deep_analysis/run \\')
print('    -H "Content-Type: application/json" \\')
print('    -d \'{"tags": ["R001-CO2"], "period": 30}\' | \\')
print('    python -c "import sys,json; r=json.load(sys.stdin); print(r.get(\'anomalies\', {}).get(\'type_counts\'))"')
print()
print('Должно вернуть: {"dip": 3, "noise": 745, "spike": 6} (без KeyError)')