#!/usr/bin/env python3
"""
add_downsampling_diagnosis.py — добавляем эндпоинт для диагностики downsampling
"""
from pathlib import Path

print('=' * 80)
print('ДОБАВЛЕНИЕ ЭНДПОИНТА ДИАГНОСТИКИ DOWNSAMPLING')
print('=' * 80)
print()

api_path = Path('backend/modules/deep_analysis/api.py')
content = api_path.read_text(encoding='utf-8')

diagnosis_endpoint = '''

# ============================================================================
# Расширенная диагностика downsampling и аномалий
# ============================================================================

@router.get("/diagnose/downsampling/{tag_name}")
async def diagnose_downsampling(tag_name: str, period: int = 30, max_points: int = 1500):
    """
    Показывает как downsampling влияет на аномалии:
    1. Сырые данные (с None)
    2. Отфильтрованные данные (без None) — на них работает Isolation Forest
    3. Downsampled данные — на них отображается график
    4. Сравнение аномалий в каждом из представлений
    """
    from datetime import datetime, timedelta
    from modules.deep_analysis.collectors.data_fetcher import fetch_tag_data
    from modules.deep_analysis.analyzers.anomalies import detect_anomalies_isolation_forest
    from modules.deep_analysis.visualizers.chart_specs import downsample_time_series
    import numpy as np
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=period)
    
    try:
        data = await fetch_tag_data(tag_name, start_date, end_date)
        raw_values = data['raw_values']
        raw_timestamps = data['raw_timestamps']
        
        # 1. Сырые данные
        total = len(raw_values)
        none_count = sum(1 for v in raw_values if v is None or (isinstance(v, float) and np.isnan(v)))
        valid_count = total - none_count
        
        # 2. Отфильтрованные данные
        valid_indices = [i for i, v in enumerate(raw_values) 
                        if v is not None and not (isinstance(v, float) and np.isnan(v))]
        valid_values = [raw_values[i] for i in valid_indices]
        valid_timestamps = [raw_timestamps[i] for i in valid_indices]
        
        # 3. Детекция аномалий на отфильтрованных данных
        if len(valid_values) >= 10:
            result = detect_anomalies_isolation_forest(
                valid_values, valid_timestamps, classify_types=True
            )
        else:
            result = {'anomaly_indices': [], 'anomaly_types': [], 'anomaly_values': [], 'type_counts': {}}
        
        # 4. Downsampling
        ds_values, ds_timestamps = downsample_time_series(raw_values, raw_timestamps, max_points)
        
        # 5. Маппинг аномалий на downsampled данные
        # ЭТО КРИТИЧЕСКАЯ ЧАСТЬ — смотрим как индексы маппятся
        anomaly_mapping = []
        bucket_size = total / max_points if total > max_points else 1.0
        
        for orig_idx, val, atype in zip(
            result['anomaly_indices'][:20],
            result['anomaly_values'][:20],
            result['anomaly_types'][:20]
        ):
            # Находим оригинальный индекс в raw_values
            raw_idx = valid_indices[orig_idx]
            
            # Приблизительный индекс в downsampled
            ds_idx_approx = int(raw_idx / bucket_size) if bucket_size > 0 else raw_idx
            ds_idx_approx = min(ds_idx_approx, len(ds_values) - 1)
            
            ds_val = ds_values[ds_idx_approx]
            ds_ts = ds_timestamps[ds_idx_approx] if ds_idx_approx < len(ds_timestamps) else None
            
            # Ищем реальное значение в bucket
            bucket_start = int(raw_idx / bucket_size) * int(bucket_size) if bucket_size > 1 else raw_idx
            bucket_end = min(bucket_start + int(bucket_size) + 1, total) if bucket_size > 1 else raw_idx + 1
            
            anomaly_mapping.append({
                'type': atype,
                'orig_idx': raw_idx,
                'orig_value': val,
                'orig_timestamp': raw_timestamps[raw_idx].isoformat() if raw_idx < len(raw_timestamps) else None,
                'ds_idx_approx': ds_idx_approx,
                'ds_value': float(ds_val) if ds_val is not None else None,
                'ds_timestamp': ds_ts.isoformat() if hasattr(ds_ts, 'isoformat') else str(ds_ts),
                'value_diff': abs(val - ds_val) if ds_val is not None else None,
                'bucket_range': [bucket_start, bucket_end],
            })
        
        # 6. Анализ дрейфов — ищем потенциальные дрейфы в данных
        potential_drifts = []
        window_size = 30
        for i in range(0, len(valid_values) - window_size, window_size // 2):
            window = valid_values[i:i+window_size]
            
            if None in window:
                continue
            
            try:
                x = np.arange(len(window))
                y = np.array(window)
                slope, intercept = np.polyfit(x, y, 1)
                y_pred = slope * x + intercept
                ss_res = np.sum((y - y_pred) ** 2)
                ss_tot = np.sum((y - np.mean(y)) ** 2)
                r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0
                
                # Монотонность
                increases = sum(1 for j in range(len(window)-1) if window[j+1] > window[j])
                decreases = sum(1 for j in range(len(window)-1) if window[j+1] < window[j])
                monotonic_ratio = max(increases, decreases) / (len(window) - 1)
                
                # Изменение
                change = abs(window[-1] - window[0]) / (abs(window[0]) + 1e-10)
                
                if r_squared > 0.5 and monotonic_ratio > 0.6 and change > 0.03:
                    potential_drifts.append({
                        'start_idx': i,
                        'end_idx': i + window_size,
                        'start_timestamp': valid_timestamps[i].isoformat(),
                        'end_timestamp': valid_timestamps[i + window_size - 1].isoformat(),
                        'start_value': float(window[0]),
                        'end_value': float(window[-1]),
                        'r_squared': float(r_squared),
                        'monotonic_ratio': float(monotonic_ratio),
                        'change_percent': float(change * 100),
                    })
            except Exception:
                continue
        
        # Сортируем по r_squared
        potential_drifts.sort(key=lambda x: x['r_squared'], reverse=True)
        
        return {
            'tag_name': tag_name,
            'period_days': period,
            'raw_data': {
                'total_points': total,
                'valid_points': valid_count,
                'null_points': none_count,
                'null_percent': round(none_count / total * 100, 2) if total > 0 else 0,
                'first_timestamp': raw_timestamps[0].isoformat() if raw_timestamps else None,
                'last_timestamp': raw_timestamps[-1].isoformat() if raw_timestamps else None,
            },
            'anomalies_detected': {
                'total': result.get('total_anomalies', 0),
                'type_counts': result.get('type_counts', {}),
                'rate': result.get('anomaly_rate', 0),
            },
            'downsampling': {
                'original_points': total,
                'downsampled_points': len(ds_values),
                'compression_ratio': round(total / len(ds_values), 2) if ds_values else 0,
                'bucket_size': round(bucket_size, 2),
            },
            'anomaly_mapping_sample': anomaly_mapping,
            'potential_drifts': potential_drifts[:20],
            'summary': {
                'null_affects_analysis': none_count > valid_count * 0.1,
                'downsampling_loses_anomalies': any(
                    m['value_diff'] is not None and m['value_diff'] > 50
                    for m in anomaly_mapping
                ),
                'drifts_found_but_not_classified': len(potential_drifts) > 0 and result.get('type_counts', {}).get('drift', 0) == 0,
            },
        }
    
    except Exception as e:
        log.error("Downsampling diagnosis failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

'''

# Добавляем endpoints если их нет
if '@router.get("/diagnose/downsampling/' not in content:
    content += diagnosis_endpoint
    api_path.write_text(content, encoding='utf-8', newline='\n')
    print('✅ Эндпоинт /diagnose/downsampling/{tag_name} добавлен')
    print()
    print('Что он показывает:')
    print('  • raw_data: общее количество точек, None/NaN, период')
    print('  • anomalies_detected: результат Isolation Forest')
    print('  • downsampling: степень сжатия, размер bucket')
    print('  • anomaly_mapping_sample: как индексы аномалий маппятся на downsampled данные')
    print('  • potential_drifts: потенциальные дрейфы (нашли по R², но классификатор не увидел)')
    print('  • summary: флаги проблем')
else:
    print('ℹ️  Эндпоинт уже существует')

print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Перезапусти backend')
print()
print('2. Запусти HTTP диагностику:')
print('   python diagnose_via_http.py')
print()
print('3. Запусти диагностику downsampling:')
print('   curl -s http://localhost:8081/api/v1/deep_analysis/diagnose/downsampling/KITCHEN2-CO2?period=30 \\')
print('     | python -m json.tool > downsampling_diag.json')
print()
print('4. Открой downsampling_diag.json и скинь секции:')
print('   • raw_data')
print('   • downsampling')
print('   • anomaly_mapping_sample (первые 3)')
print('   • potential_drifts (первые 3)')
print('   • summary')
print()
print('Это покажет КОРЕНЬ проблемы:')
print('  • Если null_percent > 10% — None режут данные')
print('  • Если value_diff большой — downsampling теряет аномалии')
print('  • Если potential_drifts есть, но drift=0 — проблема в классификаторе')