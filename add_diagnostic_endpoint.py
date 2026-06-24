#!/usr/bin/env python3
"""
add_diagnostic_endpoint.py — добавляем диагностический endpoint в api.py
"""
from pathlib import Path

print('=' * 80)
print('ДОБАВЛЕНИЕ ДИАГНОСТИЧЕСКОГО ENDPOINT')
print('=' * 80)
print()

api_path = Path('backend/modules/deep_analysis/api.py')
content = api_path.read_text(encoding='utf-8')

diagnostic_endpoint = '''

@router.get("/diagnose/{tag_name}")
async def diagnose_tag(tag_name: str, period: int = 30):
    """
    Диагностический endpoint — показывает детальную информацию о теге.
    
    Возвращает:
    - Количество точек в БД по диапазонам
    - Последние 20 точек с датами
    - Все аномалии с датами и значениями
    - Плато (повторяющиеся значения)
    """
    from datetime import datetime, timedelta
    from core.db import fetch
    
    log.info("Running diagnostics", tag=tag_name, period=period)
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=period)
    
    try:
        # 1. Диапазон данных
        range_query = """
            SELECT 
                MIN(tv.date_created) as first_ts,
                MAX(tv.date_created) as last_ts,
                COUNT(*) as total
            FROM tags_value tv
            JOIN tags_dict td ON td.tag_id = tv.tag_id
            WHERE td.tag_name = $1
              AND tv.date_created >= $2
              AND tv.date_created <= $3
        """
        range_result = await fetch(range_query, tag_name, start_date, end_date)
        
        # 2. Распределение по неделям
        weeks = []
        for week in range(4):
            w_start = start_date + timedelta(weeks=week)
            w_end = w_start + timedelta(weeks=1)
            
            week_query = """
                SELECT COUNT(*) as cnt
                FROM tags_value tv
                JOIN tags_dict td ON td.tag_id = tv.tag_id
                WHERE td.tag_name = $1
                  AND tv.date_created >= $2
                  AND tv.date_created < $3
            """
            week_result = await fetch(week_query, tag_name, w_start, w_end)
            weeks.append({
                "start": w_start.isoformat(),
                "end": w_end.isoformat(),
                "count": week_result[0]['cnt'] if week_result else 0
            })
        
        # 3. Последние 20 точек
        last_query = """
            SELECT tv.date_created, tv.value
            FROM tags_value tv
            JOIN tags_dict td ON td.tag_id = tv.tag_id
            WHERE td.tag_name = $1
            ORDER BY tv.date_created DESC
            LIMIT 20
        """
        last_result = await fetch(last_query, tag_name)
        last_points = [
            {
                "timestamp": r['date_created'].isoformat(),
                "value": float(r['value']) if r['value'] is not None else None
            }
            for r in last_result
        ]
        
        # 4. Низкие значения (< 200)
        low_query = """
            SELECT tv.date_created, tv.value
            FROM tags_value tv
            JOIN tags_dict td ON td.tag_id = tv.tag_id
            WHERE td.tag_name = $1
              AND tv.date_created >= $2
              AND tv.date_created <= $3
              AND tv.value < 200
            ORDER BY tv.date_created ASC
            LIMIT 50
        """
        low_result = await fetch(low_query, tag_name, start_date, end_date)
        low_points = [
            {
                "timestamp": r['date_created'].isoformat(),
                "value": float(r['value'])
            }
            for r in low_result
        ]
        
        # 5. Запускаем анализ аномалий
        from modules.deep_analysis.collectors.data_fetcher import fetch_tag_data
        from modules.deep_analysis.analyzers.anomalies import (
            detect_anomalies_isolation_forest,
            detect_zero_dips,
            detect_significant_dips,
        )
        
        data = await fetch_tag_data(tag_name, start_date, end_date)
        
        # Zero dips
        zd = detect_zero_dips(data['raw_values'], data['raw_timestamps'])
        zero_dips_events = []
        for e in zd['events'][:10]:
            ts_start = data['raw_timestamps'][e['start_idx']] if e['start_idx'] < len(data['raw_timestamps']) else None
            ts_end = data['raw_timestamps'][e['end_idx']] if e['end_idx'] < len(data['raw_timestamps']) else None
            zero_dips_events.append({
                "start": ts_start.isoformat() if ts_start else None,
                "end": ts_end.isoformat() if ts_end else None,
                "duration": e['duration'],
                "min_value": e['min_value']
            })
        
        # Significant dips
        sd = detect_significant_dips(data['raw_values'], data['raw_timestamps'])
        sig_dips_events = []
        for e in sd['events'][:10]:
            ts_start = data['raw_timestamps'][e['start_idx']] if e['start_idx'] < len(data['raw_timestamps']) else None
            ts_end = data['raw_timestamps'][e['end_idx']] if e['end_idx'] < len(data['raw_timestamps']) else None
            sig_dips_events.append({
                "start": ts_start.isoformat() if ts_start else None,
                "end": ts_end.isoformat() if ts_end else None,
                "duration": e['duration'],
                "drop_percent": e.get('drop_percent', 0),
                "min_value": e['min_value'],
                "mean_before": e.get('local_mean_before', 0)
            })
        
        # Полная детекция
        result = detect_anomalies_isolation_forest(
            data['raw_values'],
            data['raw_timestamps'],
            contamination=0.10,
            classify_types=True
        )
        
        # Детали по типам
        type_details = {}
        for atype in ['spike', 'dip', 'drift', 'noise']:
            indices = [
                i for i, t in zip(result['anomaly_indices'], result['anomaly_types'])
                if t == atype
            ]
            
            points = []
            for idx in indices[:10]:
                if idx < len(data['raw_timestamps']) and idx < len(data['raw_values']):
                    points.append({
                        "idx": idx,
                        "timestamp": data['raw_timestamps'][idx].isoformat(),
                        "value": float(data['raw_values'][idx]) if data['raw_values'][idx] is not None else None
                    })
            
            type_details[atype] = {
                "count": len(indices),
                "sample": points
            }
        
        # Плато
        plateaus = []
        current_val = None
        current_count = 0
        current_start = None
        
        for i, val in enumerate(data['raw_values']):
            if val == current_val:
                current_count += 1
            else:
                if current_count >= 5:
                    ts_start = data['raw_timestamps'][current_start] if current_start < len(data['raw_timestamps']) else None
                    ts_end = data['raw_timestamps'][i-1] if i-1 < len(data['raw_timestamps']) else None
                    
                    # Типы в этом плато
                    types_in_plateau = set()
                    for j in range(current_start, i):
                        if j in result['anomaly_indices']:
                            idx_in_list = result['anomaly_indices'].index(j)
                            types_in_plateau.add(result['anomaly_types'][idx_in_list])
                    
                    plateaus.append({
                        "start": ts_start.isoformat() if ts_start else None,
                        "end": ts_end.isoformat() if ts_end else None,
                        "count": current_count,
                        "value": float(current_val) if current_val is not None else None,
                        "types": list(types_in_plateau)
                    })
                current_val = val
                current_count = 1
                current_start = i
        
        return {
            "tag_name": tag_name,
            "period": f"{start_date.isoformat()} - {end_date.isoformat()}",
            "db_range": {
                "first_ts": range_result[0]['first_ts'].isoformat() if range_result and range_result[0]['first_ts'] else None,
                "last_ts": range_result[0]['last_ts'].isoformat() if range_result and range_result[0]['last_ts'] else None,
                "total_in_period": range_result[0]['total'] if range_result else 0
            },
            "distribution_by_weeks": weeks,
            "last_20_points": last_points,
            "low_values_under_200": {
                "count": len(low_points),
                "sample": low_points
            },
            "anomalies": {
                "total": result['total_anomalies'],
                "type_counts": result['type_counts'],
                "zero_dips_events": zero_dips_events,
                "sig_dips_events": sig_dips_events,
                "by_type": type_details
            },
            "plateaus_5plus": plateaus[:10]
        }
    
    except Exception as e:
        log.error("Diagnostics failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

'''

# Вставляем endpoint перед последним @router (например, перед /tags)
if '@router.get("/diagnose/' not in content:
    # Находим @router.get("/tags"
    marker = '@router.get("/tags"'
    if marker in content:
        content = content.replace(marker, diagnostic_endpoint + '\n\n' + marker)
        api_path.write_text(content, encoding='utf-8', newline='\n')
        print('✅ Диагностический endpoint добавлен')
        print('   GET /api/v1/deep_analysis/diagnose/{tag_name}')
    else:
        print('❌ Не удалось найти место для вставки')
else:
    print('ℹ️  Endpoint уже существует')

print()
print('=' * 80)
print('ИСПОЛЬЗОВАНИЕ:')
print('=' * 80)
print()
print('Перезапусти backend, затем выполни:')
print()
print('  curl -s http://localhost:8081/api/v1/deep_analysis/diagnose/R001-CO2?period=30 \\')
print('    | python -m json.tool')
print()
print('Или сохрани в файл для удобного просмотра:')
print()
print('  curl -s http://localhost:8081/api/v1/deep_analysis/diagnose/R001-CO2?period=30 \\')
print('    > diag_R001-CO2.json')
print()
print('  cat diag_R001-CO2.json | python -m json.tool | head -100')
print()
print('Что покажет endpoint:')
print('  • db_range.first_ts / last_ts — реальные даты в БД')
print('  • distribution_by_weeks — сколько точек в каждой неделе')
print('  • last_20_points — последние записи с датами')
print('  • low_values_under_200 — точки со значением < 200')
print('  • zero_dips_events — падения в ноль (с датами)')
print('  • sig_dips_events — падения >30% (с датами и %)')
print('  • by_type.spike/dip/drift/noise — примеры по 10 точек каждого типа')
print('  • plateaus_5plus — плато из 5+ одинаковых значений (с типами)')
print()
print('Это покажет КОРЕНЬ проблемы:')
print('  • Если db_range.last_ts = 2026-06-08 → в БД НЕТ данных после этой даты')
print('  • Если distribution_by_weeks показывает 0 после 08.06 → то же самое')
print('  • Если last_20_points заканчивается на 08.06 → SCADA не пишет')
print('  • Если plateaus показывает 409,409,409 с типом drift → баг в _is_plateau')
print('  • Если sig_dips_events показывает "нормальные" колебания как dips → порог слишком низкий')