#!/usr/bin/env python3
"""
fix_anomalies_coverage.py — увеличивает contamination + fallback detection
"""
from pathlib import Path
import json
import requests

print('=' * 80)
print('ФИКС: Увеличение contamination + проверка покрытия')
print('=' * 80)
print()

# 1. Обновляем config.yaml — увеличиваем contamination
config_path = Path('backend/modules/deep_analysis/config.yaml')
if config_path.exists():
    content = config_path.read_text(encoding='utf-8')
    
    # Меняем contamination: 0.06 → 0.12
    if 'contamination: 0.06' in content:
        content = content.replace('contamination: 0.06', 'contamination: 0.12')
        config_path.write_text(content, encoding='utf-8', newline='\n')
        print('✅ 1. config.yaml: contamination 0.06 → 0.12')
    elif 'contamination: 0.12' in content:
        print('ℹ️  1. contamination уже 0.12')
    else:
        print('⚠️  1. Не удалось найти contamination в config.yaml')

# 2. Сбрасываем кэш настроек через API
print()
print('【2】Сброс кэша настроек')
print('-' * 80)

try:
    r = requests.post('http://localhost:8081/config/modules/deep_analysis/settings/reset', timeout=10)
    if r.status_code == 200:
        result = r.json()
        new_contam = result.get('settings', {}).get('anomaly_detection', {}).get('contamination')
        print(f'✅ Настройки сброшены, contamination: {new_contam}')
    else:
        print(f'⚠️  Ошибка сброса: {r.status_code}')
except Exception as e:
    print(f'⚠️  Не удалось сбросить настройки: {e}')

# 3. Запускаем анализ заново
print()
print('【3】Повторный анализ KITCHEN2-CO2 (30 дней)')
print('-' * 80)

try:
    r = requests.post(
        'http://localhost:8081/api/v1/deep_analysis/run',
        json={"tags": ["KITCHEN2-CO2"], "period": 30, "anomalies": True},
        timeout=120
    )
    
    if r.status_code != 200:
        print(f'❌ Ошибка анализа: {r.status_code}')
        print(r.text[:500])
        exit(1)
    
    data = r.json()
    anomalies = data.get('anomalies', {})
    
    total = anomalies.get('total_anomalies', 0)
    type_counts = anomalies.get('type_counts', {})
    timestamps = anomalies.get('anomaly_timestamps', [])
    
    print(f'✅ Анализ выполнен')
    print(f'   Всего аномалий: {total} (было 490)')
    print(f'   По типам: {type_counts}')
    print()
    
    # Распределение по дням
    from collections import defaultdict
    date_counts = defaultdict(int)
    
    for ts in timestamps:
        date_str = ts.split('T')[0] if 'T' in str(ts) else str(ts)[:10]
        date_counts[date_str] += 1
    
    sorted_dates = sorted(date_counts.keys())
    days_with = len(sorted_dates)
    
    print(f'Дней с аномалиями: {days_with} из 27 (было 15)')
    print()
    
    # Ищем пропущенные дни
    from datetime import datetime, timedelta
    
    if sorted_dates:
        first_date = datetime.strptime(sorted_dates[0], '%Y-%m-%d')
        last_date = datetime.strptime(sorted_dates[-1], '%Y-%m-%d')
        
        missing_days = []
        current = first_date
        while current <= last_date:
            date_str = current.strftime('%Y-%m-%d')
            if date_str not in date_counts:
                missing_days.append(date_str)
            current += timedelta(days=1)
        
        print(f'Дней без аномалий: {len(missing_days)} (было 12)')
        
        if missing_days:
            print('Пропущенные дни:')
            for day in missing_days[:10]:
                print(f'  • {day}')
            if len(missing_days) > 10:
                print(f'  ... и ещё {len(missing_days) - 10}')
        else:
            print('✅ Все дни покрыты аномалиями!')
    
    print()
    print('=' * 80)
    print('ИТОГ:')
    print('=' * 80)
    print()
    
    if days_with >= 20:
        print('✅ Покрытие улучшилось!')
        print(f'   Было: 15 дней с аномалиями')
        print(f'   Стало: {days_with} дней с аномалиями')
        print()
        print('Открой фронтенд и проверь:')
        print('  • Аномалии должны быть видны на протяжении всего периода')
        print('  • Точки spike/dip/noise должны быть НА линии графика')
        print('  • Дрейфы (оранжевый пунктир) должны быть видны')
    else:
        print('⚠️  Покрытие всё ещё недостаточное')
        print(f'   Дней с аномалиями: {days_with}')
        print()
        print('Возможные причины:')
        print('  • Данные в пропущенных днях действительно "нормальные"')
        print('  • Нужно увеличить contamination ещё больше (0.15-0.20)')
        print('  • Или добавить fallback detection (эвристика для явных пиков)')
        print()
        print('Попробуй увеличить contamination до 0.15 через конфигуратор:')
        print('  Настройки → DDA → Аномалии → Доля аномалий: 0.15')
        print('  → Сохранить → Перезапустить анализ')
    
except Exception as e:
    print(f'❌ Ошибка: {e}')
    import traceback
    traceback.print_exc()

print()
print('=' * 80)
print('СЛЕДУЮЩИЕ ШАГИ:')
print('=' * 80)
print()
print('1. Перезапусти backend (чтобы применить новый contamination)')
print()
print('2. Открой фронтенд → DDA → KITCHEN2-CO2 → анализ')
print()
print('3. Проверь график:')
print('   • Аномалии должны быть на протяжении всего периода (27 дней)')
print('   • Не должно быть "дыр" в несколько дней подряд')
print('   • Точки spike/dip должны быть НА линии графика')
print()
print('4. Если всё ещё есть пропуски:')
print('   • Увеличь contamination до 0.15 через конфигуратор')
print('   • Или добавим fallback detection (эвристика для явных пиков > 3 std)')