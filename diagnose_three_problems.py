#!/usr/bin/env python3
"""
diagnose_three_problems.py — диагностика трёх проблем + точечные фиксы
"""
from pathlib import Path
import json

print('=' * 80)
print('ДИАГНОСТИКА: 3 проблемы')
print('=' * 80)
print()

# ============================================================================
# ФИКС 1: Увеличиваем dip_threshold с 2.0 до 3.0
# ============================================================================
print('【1】ФИКС: dip_threshold 2.0 → 3.0')
print('-' * 80)

config_path = Path('backend/modules/deep_analysis/config.yaml')
if config_path.exists():
    content = config_path.read_text(encoding='utf-8')
    
    if 'dip_threshold: 2' in content or 'dip_threshold: 2.0' in content:
        content = content.replace('dip_threshold: 2', 'dip_threshold: 3')
        content = content.replace('dip_threshold: 2.0', 'dip_threshold: 3.0')
        config_path.write_text(content, encoding='utf-8', newline='\n')
        print('  ✅ config.yaml: dip_threshold 2.0 → 3.0')
        print('     Порог провала: mean - 3*std (только явные провалы)')
    else:
        print('  ℹ️  dip_threshold уже изменён')

# Обновляем settings.py
settings_path = Path('backend/modules/deep_analysis/settings.py')
if settings_path.exists():
    content = settings_path.read_text(encoding='utf-8')
    if 'dip_threshold: float = Field(2.0' in content:
        content = content.replace(
            'dip_threshold: float = Field(2.0',
            'dip_threshold: float = Field(3.0'
        )
        settings_path.write_text(content, encoding='utf-8', newline='\n')
        print('  ✅ settings.py: dip_threshold 2.0 → 3.0')

print()

# ============================================================================
# ФИКС 2: Убираем stuck sensors из аномалий
# ============================================================================
print('【2】ФИКС: Исключаем stuck sensors (плато > 1 часа) из аномалий')
print('-' * 80)

anomalies_path = Path('backend/modules/deep_analysis/analyzers/anomalies.py')
if anomalies_path.exists():
    content = anomalies_path.read_text(encoding='utf-8')
    
    # Ищем классификатор и добавляем проверку на stuck sensor
    # В classify_anomaly_types после is_flat проверки
    
    stuck_sensor_code = '''
        # Проверка на stuck sensor: если все значения одинаковые и длительность > 60 мин
        # Это застывший датчик — НЕ аномалия, исключаем
        if is_flat and duration >= 12:  # 12 точек * 5 мин = 60 мин
            # Помечаем как noise (чтобы не засчитывалось как аномалия)
            for idx in indices:
                types_map[idx] = "noise"
            continue
'''
    
    # Находим место перед "if duration == 1:"
    marker = '        if duration == 1:'
    if marker in content and 'stuck sensor' not in content:
        content = content.replace(marker, stuck_sensor_code + '\n' + marker)
        anomalies_path.write_text(content, encoding='utf-8', newline='\n')
        print('  ✅ Добавлена проверка stuck sensors')
        print('     Плато > 60 мин → помечается как noise (не аномалия)')
    else:
        print('  ℹ️  Проверка stuck sensors уже есть или не найдена')

print()

# ============================================================================
# ФИКС 3: Ослабляем критерии дрейфа
# ============================================================================
print('【3】ФИКС: Ослабление критериев дрейфа')
print('-' * 80)

if config_path.exists():
    content = config_path.read_text(encoding='utf-8')
    
    changes = []
    
    # drift_min_r_squared: 0.4 → 0.3
    if 'drift_min_r_squared: 0.4' in content:
        content = content.replace('drift_min_r_squared: 0.4', 'drift_min_r_squared: 0.3')
        changes.append('drift_min_r_squared: 0.4 → 0.3')
    
    # drift_min_relative_change: 0.03 → 0.02
    if 'drift_min_relative_change: 0.03' in content:
        content = content.replace('drift_min_relative_change: 0.03', 'drift_min_relative_change: 0.02')
        changes.append('drift_min_relative_change: 3% → 2%')
    
    if changes:
        config_path.write_text(content, encoding='utf-8', newline='\n')
        print('  ✅ config.yaml:')
        for c in changes:
            print(f'     • {c}')
    else:
        print('  ℹ️  Критерии дрейфа уже ослаблены')

# Обновляем settings.py
if settings_path.exists():
    content = settings_path.read_text(encoding='utf-8')
    content = content.replace(
        'drift_min_r_squared: float = Field(0.4',
        'drift_min_r_squared: float = Field(0.3'
    )
    content = content.replace(
        'drift_min_relative_change: float = Field(0.03',
        'drift_min_relative_change: float = Field(0.02'
    )
    settings_path.write_text(content, encoding='utf-8', newline='\n')
    print('  ✅ settings.py обновлён')

print()

# ============================================================================
# Сбрасываем настройки через API
# ============================================================================
print('【4】Сброс настроек через API')
print('-' * 80)

import requests
try:
    r = requests.post('http://localhost:8081/config/modules/deep_analysis/settings/reset', timeout=10)
    if r.status_code == 200:
        result = r.json()
        ad = result.get('settings', {}).get('anomaly_detection', {})
        print(f'  ✅ Настройки сброшены')
        print(f'     dip_threshold: {ad.get("dip_threshold")}')
        print(f'     drift_min_r_squared: {ad.get("drift_min_r_squared")}')
        print(f'     drift_min_relative_change: {ad.get("drift_min_relative_change")}')
    else:
        print(f'  ⚠️  Ошибка: {r.status_code}')
except Exception as e:
    print(f'  ⚠️  {e}')

print()
print('=' * 80)
print('ЧТО ЭТИ ФИКСЫ ДАЮТ:')
print('=' * 80)
print()
print('1. Провалы 18.06 (511, 488):')
print('   • Было: dip_threshold = 2 std → 511 и 488 попадают как "провалы"')
print('   • Стало: dip_threshold = 3 std → только значения < 293 считаются провалами')
print('   • 511 и 488 больше не будут помечаться как провалы')
print()
print('2. Плато 409 (07.06 и 14.06):')
print('   • Было: плато помечалось как аномалия → классифицировалось как noise')
print('   • Стало: плато > 60 мин = stuck sensor → НЕ аномалия')
print('   • Точки 409, 409, 409 больше не будут вообще появляться в аномалиях')
print()
print('3. Дрейфы:')
print('   • Было: r² > 0.4, change > 3% — слишком строго')
print('   • Стало: r² > 0.3, change > 2% — ослаблено')
print('   • Больше монотонных смещений будут классифицированы как drift')
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
print('   • dip: значительно меньше (только реальные провалы < 293)')
print('   • noise: меньше (stuck sensors исключены)')
print('   • drift: может появиться (если есть монотонные смещения)')
print()
print('4. Визуально:')
print('   • 18.06 11:00-13:00 — не должно быть синих точек (провалов)')
print('   • 07.06 12:33-16:53 — не должно быть серых точек (плато 409)')
print('   • 14.06 08:52-17:47 — не должно быть серых точек (плато 409)')