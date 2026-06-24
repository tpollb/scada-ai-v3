#!/usr/bin/env python3
"""
fix_drift_thresholds.py — ослабляем пороги для drift + диагностика
"""
from pathlib import Path

print('=' * 80)
print('ФИКС: Ослабление порогов для drift/spike')
print('=' * 80)
print()

# ============================================================================
# 1. Ослабляем пороги в anomalies.py
# ============================================================================
anom_path = Path('backend/modules/deep_analysis/analyzers/anomalies.py')
anom_content = anom_path.read_text(encoding='utf-8')

changes = []

# 1a. Drift: duration >= 5 → 3, r_squared > 0.6 → 0.4, relative_change > 0.05 → 0.03
old_drift = '''elif (duration >= 5 
                  and monotonic 
                  and r_squared > 0.6 
                  and relative_change > 0.05):
                # НАСТОЯЩИЙ дрейф: монотонный + линейный + реальное изменение
                event_type = "drift"'''

new_drift = '''elif (duration >= 3 
                  and monotonic 
                  and r_squared > 0.4 
                  and relative_change > 0.03):
                # Дрейф: монотонное смещение с линейным трендом
                event_type = "drift"'''

if old_drift in anom_content:
    anom_content = anom_content.replace(old_drift, new_drift)
    changes.append('Drift: duration 5→3, R² 0.6→0.4, change 5%→3%')

# 1b. Spike/Dip: abs_deviation > 2.5 → 2.0 (везде где встречается)
count_25 = anom_content.count('abs_deviation > 2.5')
anom_content = anom_content.replace('abs_deviation > 2.5', 'abs_deviation > 2.0')
if count_25 > 0:
    changes.append(f'Spike/Dip: z-score 2.5 → 2.0 (замен {count_25})')

anom_path.write_text(anom_content, encoding='utf-8', newline='\n')

for c in changes:
    print(f'✅ {c}')

# ============================================================================
# 2. Расширяем диагностику — показываем "почти drift" события
# ============================================================================
api_path = Path('backend/modules/deep_analysis/api.py')
api_content = api_path.read_text(encoding='utf-8')

# Обновляем diagnose_weeks endpoint чтобы показывать near-drift события
old_diagnose = '''        # Полная детекция
        result = detect_anomalies_isolation_forest(
            data['raw_values'],
            data['raw_timestamps'],
            contamination=0.06,
            classify_types=True
        )'''

new_diagnose = '''        # Полная детекция
        result = detect_anomalies_isolation_forest(
            data['raw_values'],
            data['raw_timestamps'],
            contamination=0.06,
            classify_types=True
        )
        
        # Ищем события которые БЛИЗКИ к дрейфу, но не прошли критерии
        # Это помогает понять — математика слишком строгая или дрейфов реально нет
        from modules.deep_analysis.analyzers.anomalies import (
            group_anomaly_events,
            _is_monotonic,
            _is_plateau,
            _compute_linear_trend,
            _compute_relative_change,
        )
        
        events = group_anomaly_events(result['anomaly_indices'], max_gap=2)
        near_drift = []
        for event in events:
            indices = event["indices"]
            duration = event["duration"]
            if duration < 3:
                continue
            event_values = [data['raw_values'][i] for i in indices if data['raw_values'][i] is not None]
            if len(event_values) < 3:
                continue
            
            monotonic = _is_monotonic(event_values)
            is_flat = _is_plateau(event_values)
            r_squared = _compute_linear_trend(event_values)
            rel_change = _compute_relative_change(event_values)
            
            # Показываем события которые: длинные + монотонные + не плато
            if duration >= 3 and monotonic and not is_flat:
                ts_start = data['raw_timestamps'][event["start_idx"]].isoformat() if event["start_idx"] < len(data['raw_timestamps']) else None
                ts_end = data['raw_timestamps'][event["end_idx"]].isoformat() if event["end_idx"] < len(data['raw_timestamps']) else None
                
                # Определяем текущий тип
                current_type = None
                for i, idx in enumerate(result['anomaly_indices']):
                    if idx in indices:
                        current_type = result['anomaly_types'][i]
                        break
                
                near_drift.append({
                    "start": ts_start,
                    "end": ts_end,
                    "duration": duration,
                    "monotonic": monotonic,
                    "r_squared": round(r_squared, 3),
                    "relative_change": round(rel_change, 3),
                    "current_type": current_type,
                    "values_sample": [float(v) for v in event_values[:5]],
                })
        
        # Сортируем по r_squared (наиболее линейные первыми)
        near_drift.sort(key=lambda x: x['r_squared'], reverse=True)'''

if old_diagnose in api_content:
    api_content = api_content.replace(old_diagnose, new_diagnose)
    print('✅ diagnose_weeks расширен: показывает near-drift события')

# Обновляем return блок чтобы включить near_drift
old_return = '''        return {
            "tag_name": tag_name,
            "period": f"{start_date.isoformat()} - {end_date.isoformat()}",
            "total_anomalies": result['total_anomalies'],
            "type_counts": result['type_counts'],
            "anomaly_rate": result['anomaly_rate'],
            "by_week": weeks
        }'''

new_return = '''        return {
            "tag_name": tag_name,
            "period": f"{start_date.isoformat()} - {end_date.isoformat()}",
            "total_anomalies": result['total_anomalies'],
            "type_counts": result['type_counts'],
            "anomaly_rate": result['anomaly_rate'],
            "by_week": weeks,
            "near_drift_events": near_drift[:20],  # топ-20 кандидатов в дрейфы
        }'''

if old_return in api_content:
    api_content = api_content.replace(old_return, new_return)
    print('✅ diagnose_weeks: возвращает top-20 near_drift событий')

api_path.write_text(api_content, encoding='utf-8', newline='\n')

print()
print('=' * 80)
print('ИТОГО ИЗМЕНЕНИЙ:')
print('=' * 80)
print()
print('Drift теперь детектируется при:')
print('  • duration >= 3 точек (было 5)')
print('  • monotonic = True (>75% в одну сторону)')
print('  • r_squared > 0.4 (было 0.6)')
print('  • relative_change > 3% (было 5%)')
print('  • НЕ плато')
print()
print('Spike/Dip теперь при:')
print('  • abs_deviation > 2.0 std (было 2.5)')
print()
print('Новое поле near_drift_events в diagnose_weeks показывает:')
print('  • Длинные монотонные события которые близко к дрейфу')
print('  • r_squared (качество линейного тренда)')
print('  • relative_change (% изменения)')
print('  • current_type — как они сейчас классифицируются')
print('  • values_sample — первые 5 значений для визуальной проверки')
print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Перезапусти backend')
print()
print('2. Запусти диагностику:')
print('   curl -s http://localhost:8081/api/v1/deep_analysis/diagnose_weeks/R001-CO2?period=30 \\')
print('     | python -m json.tool | head -80')
print()
print('3. Ожидаемый результат:')
print('   • type_counts теперь: {spike: N, dip: N, drift: N, noise: N}')
print('     (drift должно быть > 0 если в данных есть монотонные смещения)')
print('   • near_drift_events: массив событий близких к дрейфу')
print()
print('4. Если drift всё ещё = 0, но near_drift_events показывает')
print('   события с r_squared ~0.3-0.4 — снизим порог до 0.3')
print()
print('5. Открой фронтенд и проверь:')
print('   • Дрейфы — пунктирные оранжевые линии')
print('   • Пики — красные точки (их должно стать больше)')
print('   • Провалы — синие точки')
print('   • Шум — серые точки')