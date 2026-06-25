#!/usr/bin/env python3
"""
generate_anomalies_report.py — генерация отчёта по аномалиям
"""
import sys
sys.path.insert(0, 'backend')

from modules.deep_analysis.analyzers.anomalies import detect_anomalies_isolation_forest
from modules.deep_analysis.collectors.data_fetcher import fetch_tag_data
from datetime import datetime, timedelta
import json

async def generate():
    print("Генерация отчёта по аномалиям...")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    data = await fetch_tag_data('KITCHEN2-CO2', start_date, end_date)
    raw_values = data['raw_values']
    raw_timestamps = data['raw_timestamps']
    
    # Фильтруем None
    valid_indices = [i for i, v in enumerate(raw_values) if v is not None]
    valid_values = [raw_values[i] for i in valid_indices]
    
    result = detect_anomalies_isolation_forest(
        valid_values,
        [raw_timestamps[i] for i in valid_indices],
        classify_types=True
    )
    
    # Формируем отчёт
    report = {
        'tag': 'KITCHEN2-CO2',
        'period': f"{start_date.isoformat()} - {end_date.isoformat()}",
        'total_points': len(raw_values),
        'valid_points': len(valid_values),
        'none_points': len(raw_values) - len(valid_values),
        'anomalies': {
            'total': result['total_anomalies'],
            'by_type': result['type_counts'],
            'rate': result['anomaly_rate']
        },
        'samples': {
            'spike': [],
            'dip': [],
            'drift': [],
            'noise': []
        }
    }
    
    # Берём примеры каждого типа
    for idx, val, atype, ts in zip(
        result['anomaly_indices'],
        result['anomaly_values'],
        result['anomaly_types'],
        result['anomaly_timestamps']
    ):
        if len(report['samples'][atype]) < 5:
            report['samples'][atype].append({
                'index': idx,
                'value': val,
                'timestamp': ts.isoformat(),
                'original_index': valid_indices[idx]
            })
    
    # Сохраняем
    with open('anomalies_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Отчёт сохранён: anomalies_report.json")
    print()
    print("Сводка:")
    print(f"  Всего точек: {report['total_points']}")
    print(f"  Валидных: {report['valid_points']}")
    print(f"  None: {report['none_points']}")
    print(f"  Аномалий: {report['anomalies']['total']} ({report['anomalies']['rate']:.2%})")
    print(f"  По типам: {report['anomalies']['by_type']}")

import asyncio
asyncio.run(generate())
