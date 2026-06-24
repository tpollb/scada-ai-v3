#!/usr/bin/env python3
"""
fix_math_and_limits.py — комплексное исправление математики и SQL
"""
from pathlib import Path

print('=' * 70)
print('КОМПЛЕКСНЫЙ ФИКС: Математика + SQL + UI')
print('=' * 70)
print()

# ============================================================================
# 1. TAG_RESOLVER: убираем LIMIT 1000
# ============================================================================
resolver_path = Path('backend/modules/deep_analysis/collectors/tag_resolver.py')
if resolver_path.exists():
    content = resolver_path.read_text(encoding='utf-8')
    # Заменяем LIMIT 1000 на LIMIT 10000
    content = content.replace('LIMIT 1000', 'LIMIT 10000')
    resolver_path.write_text(content, encoding='utf-8', newline='\n')
    print('✅ 1. tag_resolver.py: LIMIT 1000 → LIMIT 10000')

# ============================================================================
# 2. DATA_FETCHER: убираем LIMIT 100000
# ============================================================================
fetcher_path = Path('backend/modules/deep_analysis/collectors/data_fetcher.py')
if fetcher_path.exists():
    content = fetcher_path.read_text(encoding='utf-8')
    # Убираем LIMIT полностью — БД должна вернуть всё за период
    # (period max 365 дней, при 1-мин частоте = 525600 точек — нормально для pandas)
    content = content.replace('        LIMIT 100000\n', '')
    content = content.replace('LIMIT 100000', '')
    fetcher_path.write_text(content, encoding='utf-8', newline='\n')
    print('✅ 2. data_fetcher.py: убран LIMIT 100000 (возвращаем все точки)')

# ============================================================================
# 3. ANOMALIES.PY: полная переделка математики
# ============================================================================
anomalies_path = Path('backend/modules/deep_analysis/analyzers/anomalies.py')
new_anomalies = '''"""Детекция и классификация аномалий (v2 — исправленная математика)"""
from typing import Optional, Literal
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.cluster import KMeans
from structlog import get_logger

log = get_logger()


AnomalyType = Literal["spike", "dip", "drift", "noise"]


def _compute_local_stats(values: list[float], idx: int, window: int = 24) -> tuple[float, float]:
    """Локальное среднее и std в окне (исключая центральную точку)."""
    half_w = window // 2
    start = max(0, idx - half_w)
    end = min(len(values), idx + half_w + 1)
    
    window_values = [values[i] for i in range(start, end) if i != idx and values[i] is not None]
    
    if len(window_values) < 3:
        return float(np.mean([v for v in values if v is not None])), float(np.std([v for v in values if v is not None]))
    
    local_mean = float(np.mean(window_values))
    local_std = float(np.std(window_values))
    return local_mean, max(local_std, 1e-10)


def _is_monotonic(values: list[float]) -> bool:
    """Проверяет монотонность (>75% изменений в одну сторону)."""
    if len(values) < 3:
        return False  # для 1-2 точек не считаем монотонным
    
    increases = sum(1 for i in range(len(values)-1) if values[i+1] > values[i])
    decreases = sum(1 for i in range(len(values)-1) if values[i+1] < values[i])
    equals = sum(1 for i in range(len(values)-1) if values[i+1] == values[i])
    
    total = len(values) - 1
    
    # Если большинство значений равны — это ПЛАТО, не монотонность
    if equals / total > 0.5:
        return False
    
    return max(increases, decreases) / total > 0.75


def _is_plateau(values: list[float], tolerance: float = 0.02) -> bool:
    """Проверяет является ли последовательность плато (значения почти одинаковые).
    
    Args:
        values: значения
        tolerance: допустимое отклонение в долях от среднего (2% по умолчанию)
    """
    if len(values) < 2:
        return False
    
    valid = [v for v in values if v is not None]
    if len(valid) < 2:
        return False
    
    mean_val = np.mean(valid)
    if abs(mean_val) < 1e-10:
        return False
    
    # Размах относительно среднего
    range_ratio = (max(valid) - min(valid)) / abs(mean_val)
    return range_ratio < tolerance


def _compute_linear_trend(values: list[float]) -> float:
    """Вычисляет R² линейной регрессии (качество линейного тренда)."""
    if len(values) < 3:
        return 0.0
    
    valid = [v for v in values if v is not None]
    if len(valid) < 3:
        return 0.0
    
    x = np.arange(len(valid))
    y = np.array(valid)
    
    try:
        slope, intercept = np.polyfit(x, y, 1)
        y_pred = slope * x + intercept
        
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        
        if ss_tot < 1e-10:
            return 0.0
        
        return float(1 - ss_res / ss_tot)
    except:
        return 0.0


def _compute_relative_change(values: list[float]) -> float:
    """Вычисляет относительное изменение (max-min)/mean."""
    valid = [v for v in values if v is not None]
    if len(valid) < 2:
        return 0.0
    
    mean_val = np.mean(valid)
    if abs(mean_val) < 1e-10:
        return 0.0
    
    return float((max(valid) - min(valid)) / abs(mean_val))


def detect_anomalies_isolation_forest(
    values: list[float],
    timestamps: list,
    contamination: float = 0.05,
    n_estimators: int = 100,
    classify_types: bool = True,
) -> dict:
    """Детекция аномалий через Isolation Forest + zero dips + significant dips."""
    if len(values) < 10:
        return {
            "anomaly_indices": [],
            "anomaly_timestamps": [],
            "anomaly_values": [],
            "anomaly_scores": [],
            "anomaly_types": [],
            "type_counts": {},
            "total_anomalies": 0,
            "anomaly_rate": 0.0,
        }
    
    log.info("Running Isolation Forest", points=len(values), contamination=contamination)
    
    X = np.array(values).reshape(-1, 1)
    model = IsolationForest(
        contamination=contamination,
        n_estimators=n_estimators,
        random_state=42,
        n_jobs=-1,
    )
    
    predictions = model.fit_predict(X)
    scores = model.decision_function(X)
    
    anomaly_indices = np.where(predictions == -1)[0].tolist()
    anomaly_timestamps = [timestamps[i] for i in anomaly_indices]
    anomaly_values = [values[i] for i in anomaly_indices]
    anomaly_scores = [float(scores[i]) for i in anomaly_indices]
    
    # Zero dips (падения в ноль)
    zero_dips = detect_zero_dips(values, timestamps, zero_threshold_ratio=0.05, min_duration=1)
    zero_indices_set = set(zero_dips['anomaly_indices'])
    
    # Significant dips (значительные падения, не обязательно в ноль)
    sig_dips = detect_significant_dips(values, timestamps, drop_ratio=0.30, min_duration=2)
    sig_dip_indices_set = set(sig_dips['anomaly_indices'])
    
    # Объединяем
    all_dip_indices = zero_indices_set | sig_dip_indices_set
    new_dip_indices = sorted(all_dip_indices - set(anomaly_indices))
    
    if new_dip_indices:
        for idx in new_dip_indices:
            anomaly_indices.append(idx)
            anomaly_timestamps.append(timestamps[idx])
            anomaly_values.append(values[idx])
            anomaly_scores.append(-0.5)
    
    # Сортируем
    combined = sorted(zip(anomaly_indices, anomaly_timestamps, anomaly_values, anomaly_scores), key=lambda x: x[0])
    if combined:
        anomaly_indices, anomaly_timestamps, anomaly_values, anomaly_scores = zip(*combined)
        anomaly_indices, anomaly_timestamps, anomaly_values, anomaly_scores = (
            list(anomaly_indices), list(anomaly_timestamps), list(anomaly_values), list(anomaly_scores)
        )
    else:
        anomaly_indices, anomaly_timestamps, anomaly_values, anomaly_scores = [], [], [], []
    
    if classify_types and len(anomaly_indices) > 0:
        types_result = classify_anomaly_types(
            values=values,
            anomaly_indices=anomaly_indices,
            anomaly_values=anomaly_values,
            zero_dip_indices=all_dip_indices,
        )
        anomaly_types = types_result['types']
        type_counts = types_result['counts']
    else:
        anomaly_types = ["unknown"] * len(anomaly_indices)
    
    result = {
        "anomaly_indices": anomaly_indices,
        "anomaly_timestamps": anomaly_timestamps,
        "anomaly_values": anomaly_values,
        "anomaly_scores": anomaly_scores,
        "anomaly_types": anomaly_types,
        "type_counts": type_counts,
        "zero_dips_events": zero_dips.get('events', []),
        "sig_dips_events": sig_dips.get('events', []),
        "total_anomalies": len(anomaly_indices),
        "anomaly_rate": len(anomaly_indices) / len(values),
    }
    
    log.info(
        "Anomalies detected and classified",
        total=len(anomaly_indices),
        rate=f"{result['anomaly_rate']:.2%}",
        types=type_counts,
        zero_dips=len(zero_dips.get('events', [])),
        sig_dips=len(sig_dips.get('events', [])),
    )
    
    return result


def detect_zero_dips(
    values: list[float],
    timestamps: list,
    zero_threshold_ratio: float = 0.05,
    min_duration: int = 1,
) -> dict:
    """Детектирует падения в ноль или близко к нулю (<5% от среднего)."""
    if len(values) < 5:
        return {"anomaly_indices": [], "anomaly_values": [], "events": []}
    
    mean_value = np.mean([v for v in values if v is not None])
    zero_threshold = abs(mean_value) * zero_threshold_ratio
    
    zero_indices = [i for i, v in enumerate(values) if v is not None and abs(v) <= zero_threshold]
    
    if not zero_indices:
        return {"anomaly_indices": [], "anomaly_values": [], "events": []}
    
    events = []
    current = [zero_indices[0]]
    
    for i in range(1, len(zero_indices)):
        if zero_indices[i] - zero_indices[i-1] == 1:
            current.append(zero_indices[i])
        else:
            if len(current) >= min_duration:
                events.append({
                    "start_idx": current[0],
                    "end_idx": current[-1],
                    "duration": len(current),
                    "min_value": float(min(values[i] for i in current if values[i] is not None)),
                    "indices": list(current),
                })
            current = [zero_indices[i]]
    
    if len(current) >= min_duration:
        events.append({
            "start_idx": current[0],
            "end_idx": current[-1],
            "duration": len(current),
            "min_value": float(min(values[i] for i in current if values[i] is not None)),
            "indices": list(current),
        })
    
    all_indices = []
    for e in events:
        all_indices.extend(e["indices"])
    
    return {
        "anomaly_indices": all_indices,
        "anomaly_values": [values[i] for i in all_indices],
        "events": events,
    }


def detect_significant_dips(
    values: list[float],
    timestamps: list,
    drop_ratio: float = 0.30,
    min_duration: int = 2,
    max_duration_ratio: float = 0.10,
) -> dict:
    """
    Детектирует значительные падения значения (не обязательно в ноль).
    
    Логика:
    - Сканируем ряд в скользящем окне
    - Ищем участки где значение падает >30% от локального среднего ДО участка
    - Длительность провала < 10% от общего периода (кратковременное событие)
    """
    if len(values) < 20:
        return {"anomaly_indices": [], "anomaly_values": [], "events": []}
    
    max_duration = max(min_duration, int(len(values) * max_duration_ratio))
    
    events = []
    i = 0
    
    while i < len(values) - min_duration:
        if values[i] is None:
            i += 1
            continue
        
        # Локальное среднее ДО текущей точки
        window_start = max(0, i - 20)
        window_values = [values[j] for j in range(window_start, i) if values[j] is not None]
        
        if len(window_values) < 3:
            i += 1
            continue
        
        local_mean_before = float(np.mean(window_values))
        if abs(local_mean_before) < 1e-10:
            i += 1
            continue
        
        # Ищем начало провала
        current_val = values[i]
        if current_val is None or current_val >= local_mean_before * (1 - drop_ratio):
            i += 1
            continue
        
        # Нашли начало провала — ищем конец
        start_idx = i
        j = i
        min_val = current_val
        min_idx = i
        
        while j < len(values) and j - start_idx < max_duration:
            if values[j] is None:
                j += 1
                continue
            
            if values[j] < min_val:
                min_val = values[j]
                min_idx = j
            
            # Возврат к норме (значение > 80% от локального среднего)
            if values[j] >= local_mean_before * 0.80:
                break
            j += 1
        
        duration = j - start_idx
        
        # Проверяем условия
        if duration >= min_duration:
            drop_pct = (local_mean_before - min_val) / abs(local_mean_before)
            
            if drop_pct >= drop_ratio:
                indices = list(range(start_idx, min(j, start_idx + max_duration)))
                events.append({
                    "start_idx": start_idx,
                    "end_idx": indices[-1],
                    "duration": len(indices),
                    "min_value": float(min_val),
                    "drop_percent": float(drop_pct),
                    "local_mean_before": float(local_mean_before),
                    "indices": indices,
                })
                i = j
                continue
        
        i += 1
    
    all_indices = []
    for e in events:
        all_indices.extend(e["indices"])
    
    # Убираем дубликаты
    all_indices = sorted(set(all_indices))
    
    return {
        "anomaly_indices": all_indices,
        "anomaly_values": [values[i] for i in all_indices if values[i] is not None],
        "events": events,
    }


def group_anomaly_events(anomaly_indices: list[int], max_gap: int = 2) -> list[dict]:
    """Группирует подряд идущие аномалии в события."""
    if not anomaly_indices:
        return []
    
    events = []
    current = {"indices": [anomaly_indices[0]]}
    
    for i in range(1, len(anomaly_indices)):
        prev = anomaly_indices[i - 1]
        curr = anomaly_indices[i]
        
        if curr - prev <= max_gap + 1:
            current["indices"].append(curr)
        else:
            current["start_idx"] = current["indices"][0]
            current["end_idx"] = current["indices"][-1]
            current["duration"] = len(current["indices"])
            events.append(current)
            current = {"indices": [curr]}
    
    current["start_idx"] = current["indices"][0]
    current["end_idx"] = current["indices"][-1]
    current["duration"] = len(current["indices"])
    events.append(current)
    
    return events


def classify_anomaly_types(
    values: list[float],
    anomaly_indices: list[int],
    anomaly_values: list[float],
    zero_dip_indices: set = None,
) -> dict:
    """
    Классифицирует аномалии (v2 — строгие критерии).
    
    Spike: одиночная точка, локальный z > 1.5, НЕ плато
    Dip: одиночная/короткая точка, локальный z < -1.5 или zero dip
    Drift: 5+ точек, монотонность >75%, R²>0.6, РЕАЛЬНОЕ ИЗМЕНЕНИЕ (не плато)
    Noise: всё остальное
    """
    if not anomaly_indices:
        return {"types": [], "counts": {}}
    
    events = group_anomaly_events(anomaly_indices, max_gap=2)
    zero_dip_indices = zero_dip_indices or set()
    
    types_map = {}
    
    # Приоритет: zero dips всегда "dip"
    for idx in anomaly_indices:
        if idx in zero_dip_indices:
            types_map[idx] = "dip"
    
    for event in events:
        indices = event["indices"]
        duration = event["duration"]
        event_values = [values[i] for i in indices]
        
        # Пропускаем уже помеченные zero dips
        if all(idx in types_map for idx in indices):
            continue
        
        center_idx = indices[len(indices) // 2]
        local_mean, local_std = _compute_local_stats(values, center_idx)
        
        mean_deviation = np.mean([(v - local_mean) / local_std for v in event_values if v is not None])
        abs_deviation = abs(mean_deviation) if not np.isnan(mean_deviation) else 0
        is_above = mean_deviation > 0
        
        # Проверка плато (одинаковые значения)
        is_flat = _is_plateau(event_values, tolerance=0.02)
        
        # Средняя производная
        valid_vals = [v for v in event_values if v is not None]
        if len(valid_vals) > 1:
            derivatives = [abs(valid_vals[i+1] - valid_vals[i]) / local_std for i in range(len(valid_vals)-1)]
            avg_derivative = float(np.mean(derivatives))
        else:
            avg_derivative = 0.0
        
        # КЛАССИФИКАЦИЯ
        
        if duration == 1:
            # Одиночная точка
            if is_flat:
                event_type = "noise"  # странная константа — не spike
            elif abs_deviation > 1.5:
                event_type = "spike" if is_above else "dip"
            else:
                event_type = "noise"
        
        elif duration == 2:
            # Две точки
            if is_flat:
                event_type = "noise"
            elif abs_deviation > 1.5:
                event_type = "spike" if is_above else "dip"
            elif avg_derivative > 2.0:
                event_type = "noise"
            else:
                event_type = "noise"
        
        else:
            # 3+ точек
            monotonic = _is_monotonic(event_values)
            r_squared = _compute_linear_trend(event_values)
            relative_change = _compute_relative_change(event_values)
            
            if is_flat:
                # ПЛАТО (одинаковые значения) — это НЕ дрейф
                event_type = "noise"
            elif avg_derivative > 3.0:
                # Очень быстрые колебания
                event_type = "noise"
            elif duration >= 5 and monotonic and r_squared > 0.6 and relative_change > 0.05:
                # НАСТОЯЩИЙ дрейф: монотонный + линейный + реальное изменение
                event_type = "drift"
            elif abs_deviation > 1.5 and duration < 8:
                # Короткий кластер с сильным отклонением — spike/dip
                event_type = "spike" if is_above else "dip"
            elif r_squared < 0.3 or avg_derivative > 1.5:
                # Нет тренда, хаотично
                event_type = "noise"
            else:
                event_type = "noise"
        
        for idx in indices:
            if idx not in types_map:
                types_map[idx] = event_type
    
    types = [types_map.get(idx, "noise") for idx in anomaly_indices]
    
    counts = {}
    for t in types:
        counts[t] = counts.get(t, 0) + 1
    
    return {"types": types, "counts": counts}


def classify_anomalies_kmeans(
    values: list[float],
    anomaly_indices: list[int],
    anomaly_values: list[float],
    n_clusters: int = 4,
) -> dict:
    """Альтернативный метод: K-Means кластеризация."""
    if len(anomaly_indices) < n_clusters:
        return classify_anomaly_types(values, anomaly_indices, anomaly_values)
    
    mean_value = np.mean(values)
    std_value = np.std(values)
    
    events = group_anomaly_events(anomaly_indices, max_gap=2)
    index_to_event = {}
    for event in events:
        for idx in event["indices"]:
            index_to_event[idx] = event
    
    features = []
    for idx in anomaly_indices:
        event = index_to_event[idx]
        value = values[idx]
        
        z_score = (value - mean_value) / (std_value + 1e-10)
        
        if idx > 0 and idx < len(values) - 1:
            derivative = abs(values[idx+1] - values[idx-1]) / 2 / (std_value + 1e-10)
        else:
            derivative = 0.0
        
        duration_norm = min(event["duration"] / 10.0, 1.0)
        features.append([z_score, derivative, duration_norm])
    
    X = np.array(features)
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(X)
    cluster_centers = kmeans.cluster_centers_.tolist()
    
    cluster_means = []
    for c in range(n_clusters):
        cluster_points = X[cluster_labels == c]
        if len(cluster_points) > 0:
            cluster_means.append(cluster_points.mean(axis=0))
        else:
            cluster_means.append([0, 0, 0])
    
    cluster_type_map = {}
    for c, means in enumerate(cluster_means):
        z_score_mean, derivative_mean, duration_mean = means
        
        if duration_mean > 0.3:
            cluster_type_map[c] = "drift"
        elif derivative_mean > 0.5:
            cluster_type_map[c] = "noise"
        elif z_score_mean > 0:
            cluster_type_map[c] = "spike"
        else:
            cluster_type_map[c] = "dip"
    
    types = [cluster_type_map[cluster_labels[i]] for i in range(len(anomaly_indices))]
    
    counts = {}
    for t in types:
        counts[t] = counts.get(t, 0) + 1
    
    return {"types": types, "counts": counts, "cluster_centers": cluster_centers}
'''

anomalies_path.write_text(new_anomalies, encoding='utf-8', newline='\n')
print('✅ 3. anomalies.py: полностью переписана математика')
print('   • _is_plateau() — проверка на одинаковые значения')
print('   • _is_monotonic() — строгая проверка (>75%, не плато)')
print('   • _compute_relative_change() — проверка реального изменения')
print('   • detect_significant_dips() — падения >30% от локального среднего')
print('   • Drift: 5+ точек + монотонность + R²>0.6 + НЕ плато + изменение >5%')

# ============================================================================
# 4. CHART_SPECS: дрейф как линия (не точки)
# ============================================================================
chart_specs_path = Path('backend/modules/deep_analysis/visualizers/chart_specs.py')
cs_content = chart_specs_path.read_text(encoding='utf-8')

# В create_time_series_spec (single-tag): меняем drift dataset с scatter на line
old_drift_block = '''            datasets.append({
                "label": color_info["label"],
                "data": type_data,
                "borderColor": color_info["color"],
                "backgroundColor": color_info["color"],
                "type": "scatter",
                "pointRadius": 6,
                "pointHoverRadius": 8,
                "showLine": False,
            })'''

# Надо заменить так, чтобы для drift использовать line, для остальных scatter
# Сделаем это через условие по atype

# Ищем и заменяем всю логику создания datasets для аномалий
old_anomaly_loop = '''        for atype, points in anomalies_by_type.items():
            color_info = type_colors.get(atype, type_colors["unknown"])

            type_data = [None] * len(values)
            for idx, val in points:
                if 0 <= idx < len(type_data):
                    type_data[idx] = val

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

new_anomaly_loop = '''        for atype, points in anomalies_by_type.items():
            color_info = type_colors.get(atype, type_colors["unknown"])

            type_data = [None] * len(values)
            for idx, val in points:
                if 0 <= idx < len(type_data):
                    type_data[idx] = val

            # Дрейф рисуем ЛИНИЕЙ (пунктир), остальные — точками
            if atype == "drift":
                datasets.append({
                    "label": color_info["label"],
                    "data": type_data,
                    "borderColor": color_info["color"],
                    "backgroundColor": color_info["color"],
                    "type": "line",
                    "borderWidth": 2,
                    "borderDash": [6, 3],  # пунктир
                    "pointRadius": 3,
                    "pointHoverRadius": 5,
                    "showLine": True,
                    "spanGaps": True,
                })
            else:
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

if old_anomaly_loop in cs_content:
    cs_content = cs_content.replace(old_anomaly_loop, new_anomaly_loop)
    print('✅ 4a. create_time_series_spec: drift рисуется линией (пунктир)')

# То же самое для create_multitag_time_series_spec
old_mt_block = '''            datasets.append({
                "label": label,
                "data": type_data,
                "borderColor": color_info["color"],
                "backgroundColor": color_info["color"],
                "type": "scatter",
                "pointRadius": 5,
                "pointHoverRadius": 7,
                "showLine": False,
            })'''

new_mt_block = '''            # Дрейф рисуем ЛИНИЕЙ (пунктир), остальные — точками
            if atype == "drift":
                datasets.append({
                    "label": label,
                    "data": type_data,
                    "borderColor": color_info["color"],
                    "backgroundColor": color_info["color"],
                    "type": "line",
                    "borderWidth": 2,
                    "borderDash": [6, 3],
                    "pointRadius": 2,
                    "pointHoverRadius": 4,
                    "showLine": True,
                    "spanGaps": True,
                })
            else:
                datasets.append({
                    "label": label,
                    "data": type_data,
                    "borderColor": color_info["color"],
                    "backgroundColor": color_info["color"],
                    "type": "scatter",
                    "pointRadius": 5,
                    "pointHoverRadius": 7,
                    "showLine": False,
                })'''

if old_mt_block in cs_content:
    cs_content = cs_content.replace(old_mt_block, new_mt_block)
    print('✅ 4b. create_multitag_time_series_spec: drift рисуется линией')

chart_specs_path.write_text(cs_content, encoding='utf-8', newline='\n')

print()
print('=' * 70)
print('Теперь исправляем FRONTEND — даты вместо индексов')
print('=' * 70)
print()

# ============================================================================
# 5. FRONTEND: даты вместо индексов в раскрывающихся блоках
# ============================================================================
results_path = Path('frontend/src/components/DeepAnalysisResults.svelte')
results_content = results_path.read_text(encoding='utf-8')

# Helper для форматирования даты (если ещё нет)
if 'function formatAnomalyDate' not in results_content:
    # Добавим в начало <script>
    results_content = results_content.replace(
        '<script lang="ts">',
        '''<script lang="ts">
  function formatAnomalyDate(timestamp: any): string {
    if (!timestamp) return '—'
    try {
      const d = new Date(timestamp)
      if (isNaN(d.getTime())) return String(timestamp)
      return d.toLocaleString('ru-RU', {
        day: '2-digit', month: '2-digit', year: '2-digit',
        hour: '2-digit', minute: '2-digit'
      })
    } catch {
      return String(timestamp)
    }
  }
'''
    )
    print('✅ 5. Добавлена функция formatAnomalyDate()')

# Теперь заменим блоки с #idx на форматирование дат
# Для single-tag: anomaly_timestamps существует
# Для multi-tag: per_tag[tag].anomaly_timestamps существует

# Single-tag spike
old_single_spike = '''                    {@const spikePoints = analysisResult.anomalies.anomaly_indices.filter((idx, i) => analysisResult.anomalies.anomaly_types[i] === 'spike')}
                    <div class="max-h-32 overflow-y-auto space-y-0.5 mt-1">
                      {#each spikePoints.slice(0, 30) as idx, i}
                        {@const val = analysisResult.anomalies.anomaly_values[analysisResult.anomalies.anomaly_indices.indexOf(idx)]}
                        <div class="text-[10px] font-mono text-red-600 dark:text-red-400 flex justify-between">
                          <span>#{idx}</span>
                          <span class="font-semibold">{val !== undefined ? val.toFixed(2) : '—'}</span>
                        </div>
                      {/each}
                    </div>'''

new_single_spike = '''                    {@const spikePoints = analysisResult.anomalies.anomaly_indices
                      .map((idx, i) => ({idx, val: analysisResult.anomalies.anomaly_values[i], ts: analysisResult.anomalies.anomaly_timestamps?.[i]}))
                      .filter(p => analysisResult.anomalies.anomaly_types[p.idx] === 'spike' || analysisResult.anomalies.anomaly_types[analysisResult.anomalies.anomaly_indices.indexOf(p.idx)] === 'spike')}
                    <div class="max-h-32 overflow-y-auto space-y-0.5 mt-1">
                      {#each analysisResult.anomalies.anomaly_indices.map((idx, i) => ({idx, val: analysisResult.anomalies.anomaly_values[i], ts: analysisResult.anomalies.anomaly_timestamps?.[i], type: analysisResult.anomalies.anomaly_types?.[i]})).filter(p => p.type === 'spike').slice(0, 30) as p}
                        <div class="text-[10px] font-mono text-red-600 dark:text-red-400 flex justify-between gap-2">
                          <span class="text-neutral-500">{formatAnomalyDate(p.ts)}</span>
                          <span class="font-semibold">{p.val !== undefined && p.val !== null ? p.val.toFixed(2) : '—'}</span>
                        </div>
                      {/each}
                    </div>'''

if old_single_spike in results_content:
    results_content = results_content.replace(old_single_spike, new_single_spike)
    print('✅ 6a. Single-tag spike: дата-время вместо #idx')

# Multi-tag spike (и другие типы — обобщённая замена)
# Паттерн для всех 4 типов в multi-tag блоке:
import re

# Для каждого типа заменим блок внутри {#if analysisResult?.anomalies?.per_tag}
for atype, color in [('spike', 'red'), ('dip', 'blue'), ('drift', 'amber'), ('noise', 'neutral')]:
    # Старый паттерн
    old_pattern = f'''{@const {atype}Points = (tagData.anomaly_indices || []).filter((idx, i) => (tagData.anomaly_types || [])[i] === '{atype}')}
                      {{#if {atype}Points.length > 0}}
                        <div class="mt-2">
                          <div class="text-[10px] font-semibold text-{color}-700 dark:text-{color}-300 mb-1">{{tagName}} ({{{atype}Points.length}}):</div>
                          <div class="max-h-32 overflow-y-auto space-y-0.5">
                            {{#each {atype}Points.slice(0, 20) as idx}}
                              {{@const val = (tagData.anomaly_values || [])[tagData.anomaly_indices.indexOf(idx)]}}
                              <div class="text-[10px] font-mono text-{color}-600 dark:text-{color}-400 flex justify-between">
                                <span>#{{idx}}</span>
                                <span class="font-semibold">{{val !== undefined ? val.toFixed(2) : '—'}}</span>
                              </div>
                            {{/each}}
                            {{#if {atype}Points.length > 20}}
                              <div class="text-[10px] text-{color}-500 italic">... и ещё {{{atype}Points.length - 20}}</div>
                            {{/if}}
                          </div>
                        </div>
                      {{/if}}'''
    
    new_pattern = f'''{{@const {atype}Data = (tagData.anomaly_indices || []).map((idx, i) => ({{idx, val: (tagData.anomaly_values || [])[i], ts: (tagData.anomaly_timestamps || [])[i], type: (tagData.anomaly_types || [])[i]}})).filter(p => p.type === '{atype}')}}
                      {{#if {atype}Data.length > 0}}
                        <div class="mt-2">
                          <div class="text-[10px] font-semibold text-{color}-700 dark:text-{color}-300 mb-1">{{tagName}} ({{{atype}Data.length}}):</div>
                          <div class="max-h-32 overflow-y-auto space-y-0.5">
                            {{#each {atype}Data.slice(0, 20) as p}}
                              <div class="text-[10px] font-mono text-{color}-600 dark:text-{color}-400 flex justify-between gap-2">
                                <span class="text-neutral-500">{{formatAnomalyDate(p.ts)}}</span>
                                <span class="font-semibold">{{p.val !== undefined && p.val !== null ? p.val.toFixed(2) : '—'}}</span>
                              </div>
                            {{/each}}
                            {{#if {atype}Data.length > 20}}
                              <div class="text-[10px] text-{color}-500 italic">... и ещё {{{atype}Data.length - 20}}</div>
                            {{/if}}
                          </div>
                        </div>
                      {{/if}}'''
    
    if old_pattern in results_content:
        results_content = results_content.replace(old_pattern, new_pattern)
        print(f'✅ 6. Multi-tag {atype}: дата-время вместо #idx')

results_path.write_text(results_content, encoding='utf-8', newline='\n')

print()
print('=' * 70)
print('ИТОГ:')
print('=' * 70)
print()
print('✅ Backend:')
print('   • LIMIT 1000 → LIMIT 10000 (tag_resolver)')
print('   • Убран LIMIT 100000 (data_fetcher) — теперь все данные за период')
print('   • Добавлена _is_plateau() — детекция одинаковых значений')
print('   • Исправлена _is_monotonic() — не считает плато монотонным')
print('   • Добавлена detect_significant_dips() — падения >30%')
print('   • Drift требует: 5+ точек + монотонность + R²>0.6 + не плато + изменение >5%')
print()
print('✅ Chart.js:')
print('   • Drift рисуется ПУНКТИРНОЙ ЛИНИЕЙ (не точками)')
print('   • Остальные типы (spike/dip/noise) — точками')
print()
print('✅ Frontend:')
print('   • В раскрывающихся блоках теперь дата-время: "23.06.26 14:30"')
print('   • Вместо: "#1190"')
print()
print('=' * 70)
print('ПРОВЕРКА:')
print('=' * 70)
print()
print('1. Перезапусти backend')
print('2. Открой фронтенд → выбери R001-CO2 → анализ')
print()
print('Ожидаемые изменения:')
print('  • Значение 409.00 (7 одинаковых точек) БОЛЬШЕ не drift')
print('     (проверка is_plateau → noise)')
print('  • Падение 600→140 теперь отображается как DIP')
print('     (detect_significant_dips поймает падение >30%)')
print('  • Даты после 06.08 ТЕПЕРЬ ЕСТЬ (убран LIMIT 100000)')
print('  • Дрейфы на графике — пунктирные линии, не точки')
print('  • В раскрывающемся блоке: "23.06.26 14:30" вместо "#1190"')
print()
print('В логах:')
print('  [info] Anomalies detected total=N types={{spike, dip, drift, noise}}')
print('  [info] Zero dips detected ...')
print('  [info] Significant dips detected ... (новая функция)')