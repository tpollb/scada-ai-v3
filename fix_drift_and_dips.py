#!/usr/bin/env python3
"""
fix_drift_and_dips.py — финальный фикс визуализации дрейфа и провалов
"""
from pathlib import Path

print('=' * 80)
print('ФИНАЛЬНЫЙ ФИКС: Drift визуализация + Dip классификация')
print('=' * 80)
print()

# ============================================================================
# ФИКС 1: Drift рисуем точками (scatter), не линией
# ============================================================================
print('【1】ФИКС: Drift рисуем точками (scatter)')
print('-' * 80)

cs_path = Path('backend/modules/deep_analysis/visualizers/chart_specs.py')
if cs_path.exists():
    content = cs_path.read_text(encoding='utf-8')
    
    # Ищем блок где drift рисуется линией
    old_drift_block = '''            # Дрейф рисуем ЛИНИЕЙ (пунктир), остальные — точками
            if atype == "drift":
                datasets.append({
                    "label": color_info["label"],
                    "data": type_data,
                    "borderColor": color_info["color"],
                    "backgroundColor": color_info["color"],
                    "type": "line",
                    "borderWidth": 2,
                    "borderDash": [6, 3],
                    "pointRadius": 3,
                    "pointHoverRadius": 5,
                    "showLine": True,
                    "spanGaps": True,
                })'''
    
    new_drift_block = '''            # Все типы (включая drift) рисуем точками (scatter)
            # Это предотвращает соединение точек через весь график
            datasets.append({
                "label": color_info["label"],
                "data": type_data,
                "borderColor": color_info["color"],
                "backgroundColor": color_info["color"],
                "type": "scatter",
                "pointRadius": 6,
                "pointHoverRadius": 8,
                "showLine": False,
            })'''
    
    if old_drift_block in content:
        content = content.replace(old_drift_block, new_drift_block)
        cs_path.write_text(content, encoding='utf-8', newline='\n')
        print('  ✅ Drift теперь рисуется точками (scatter)')
        print('     Больше не будет линии через весь график')
    else:
        print('  ℹ️  Блок drift не найден или уже изменён')

print()

# ============================================================================
# ФИКС 2: Увеличиваем significant_dip_ratio с 0.30 до 0.50
# ============================================================================
print('【2】ФИКС: significant_dip_ratio 0.30 → 0.50')
print('-' * 80)

config_path = Path('backend/modules/deep_analysis/config.yaml')
if config_path.exists():
    content = config_path.read_text(encoding='utf-8')
    
    if 'significant_dip_ratio: 0.3' in content:
        content = content.replace('significant_dip_ratio: 0.3', 'significant_dip_ratio: 0.5')
        config_path.write_text(content, encoding='utf-8', newline='\n')
        print('  ✅ config.yaml: significant_dip_ratio 30% → 50%')
        print('     Только падения > 50% от локального среднего будут провалами')

settings_path = Path('backend/modules/deep_analysis/settings.py')
if settings_path.exists():
    content = settings_path.read_text(encoding='utf-8')
    if 'significant_dip_ratio: float = Field(0.3' in content:
        content = content.replace(
            'significant_dip_ratio: float = Field(0.3',
            'significant_dip_ratio: float = Field(0.5'
        )
        settings_path.write_text(content, encoding='utf-8', newline='\n')
        print('  ✅ settings.py: significant_dip_ratio 30% → 50%')

print()

# ============================================================================
# Сбрасываем настройки
# ============================================================================
print('【3】Сброс настроек через API')
print('-' * 80)

import requests
try:
    r = requests.post('http://localhost:8081/config/modules/deep_analysis/settings/reset', timeout=10)
    if r.status_code == 200:
        result = r.json()
        ad = result.get('settings', {}).get('anomaly_detection', {})
        print(f'  ✅ Настройки сброшены')
        print(f'     significant_dip_ratio: {ad.get("significant_dip_ratio")}')
    else:
        print(f'  ⚠️  Ошибка: {r.status_code}')
except Exception as e:
    print(f'  ⚠️  {e}')

print()
print('=' * 80)
print('ЧТО ЭТИ ФИКСЫ ДАЮТ:')
print('=' * 80)
print()
print('1. Drift визуализация:')
print('   • Было: type="line" + spanGaps=True → линия через весь график')
print('   • Стало: type="scatter" → только точки (без линий)')
print('   • 6 точек дрейфа будут видны как отдельные оранжевые точки')
print()
print('2. Dip классификация:')
print('   • Было: significant_dip_ratio=30% → падения > 30% = провал')
print('   • Стало: significant_dip_ratio=50% → падения > 50% = провал')
print('   • Значения 444-580 (при mean=505) больше не будут провалами')
print('   • Только реальные провалы (< 250 при mean=505) будут помечаться')
print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Перезапусти backend')
print()
print('2. Запусти анализ KITCHEN2-CO2:')
print('   curl -s -X POST http://localhost:8081/api/v1/deep_analysis/run \\')
print('     -H "Content-Type: application/json" \\')
print('     -d \'{"tags": ["KITCHEN2-CO2"], "period": 30}\' | \\')
print('     python -c "import sys,json; r=json.load(sys.stdin); print(r.get(\'anomalies\',{}).get(\'type_counts\'))"')
print()
print('3. Ожидаемый результат:')
print('   • dip: значительно меньше (только реальные провалы < 250)')
print('   • drift: 6 точек (как scatter, не линия)')
print()
print('4. Визуально:')
print('   • 18.06 11:00-13:00 — не должно быть синих точек (провалов)')
print('   • Дрейфы — оранжевые точки на 03.06 и 22.06 (НЕ линия через весь график)')
print('   • Плато 409 — не должно быть точек (stuck sensor detection)')