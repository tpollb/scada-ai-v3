#!/usr/bin/env python3
"""
fix_anomalies_final.py — полная перезапись математики + contamination в api.py
"""
from pathlib import Path
import re

print('=' * 80)
print('ФИНАЛЬНЫЙ ФИКС: Полная перезапись anomalies.py + contamination')
print('=' * 80)
print()

# ============================================================================
# 1. ПОЛНАЯ ПЕРЕЗАПИСЬ anomalies.py с правильной математикой
# ============================================================================
anomalies_path = Path('backend/modules/deep_analysis/analyzers/anomalies.py')

new_anomalies = '''"""Детекция и классификация аномалий (финальная версия)"""
from typing import Optional, Literal
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.cluster import KMeans
from structlog import get_logger

log = get_logger()


AnomalyType = Literal["spike", "dip", "drift", "noise"]


# =============================================================================
# HELPER ФУНКЦИИ
# =============================================================================

def _compute_local_stats(values: list[float], idx: int, window: int = 24) -> tuple[float, float]:
    """Локальное среднее и std в окне (исключая центральную точку)."""
    half_w = window // 2
    start = max(0, idx - half_w)
    end = min(len(values), idx + half_w + 1)
    
    window_values = [values[i] for i in range(start, end) if i != idx and values[i] is not None]
    
    if len(window_values) < 3:
        valid_all = [v for v in values if v is not None]
        if not valid_all:
            return 0.0, 1.0
        return float(np.mean(valid_all)), max(float(np.std(valid_all)), 1e-10)
    
    local_mean = float(np.mean(window_values))
    local_std = float(np.std(window_values))
    return local_mean, max(local_std, 1e-10)


def _is_monotonic(values: list[float]) -> bool:
    """Проверяет монотонность (>75% изменений в одну сторону, не плато)."""
    if len(values) < 3:
        return False
    
    valid = [v for v in values if v is not None]
    if len(valid) < 3:
        return False
    
    increases = sum(1 for i in range(len(valid)-1) if valid[i+1] > valid[i])
    decreases = sum(1 for i in range(len(valid)-1) if valid[i+1] < valid[i])
    equals = sum(1 for i in range(len(valid)-1) if valid[i+1] == valid[i])
    
    total = len(valid) - 1
    if total == 0:
        return False
    
    # Если большинство значений равны — это ПЛАТО
    if equals / total > 0.5:
        return False
    
    return max(increases, decreases) / total > 0.75


def _is_plateau(values: list[float], tolerance: float = 0.02) -> bool:
    """Проверяет является ли последовательность плато (одинаковые значения).
    
    Args:
        values: значения
        tolerance: допустимое отклонение в долях от среднего (2% по умолчанию)
    """
    valid = [v for v in values if v is not None]
    if len(valid) < 2:
        return False
    
    mean_val = np.mean(valid)
    if abs(mean_val) < 1e-10:
        # Для значений около нуля используем абсолютный размах
        return (max(valid) - min(valid)) < 0.1
    
    range_ratio = (max(valid) - min(valid)) / abs(mean_val)
    return range_ratio < tolerance


def _compute_linear_trend(values: list[float]) -> float:
    """Вычисляет R² линейной регрессии."""
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
    except Exception:
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


# =============================================================================
# ОСНОВНЫЕ ФУНКЦИИ ДЕТЕКЦИИ
# =============================================================================

def detect_anomalies_isolation_forest(
    values: list[float],
    timestamps: list,
    contamination: float = 0.10,
    n_estimators: int = 100,
    classify_types: bool = True,
) -> dict:
    """
    Детекция аномалий через Isolation Forest + эвристики.
    
    Комбинирует 3 метода:
    1. Isolation Forest — основная детекция статистических выбросов
    2. Zero dips — падения значений в ноль (эвристика)
    3. Significant dips — значительные падения >30% (эвристика)
    """
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
            "zero_dips_events": [],
            "sig_dips_events": [],
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
    
    # Объединяем — добавляем пропущенные zero/significant dips
    all_dip_indices = zero_indices_set | sig_dip_indices_set
    new_dip_indices = sorted(all_dip_indices - set(anomaly_indices))
    
    if new_dip_indices:
        for idx in new_dip_indices:
            anomaly_indices.append(idx)
            anomaly_timestamps.append(timestamps[idx])
            anomaly_values.append(values[idx])
            anomaly_scores.append(-0.5)
    
    # Сортируем по индексам
    combined = sorted(
        zip(anomaly_indices, anomaly_timestamps, anomaly_values, anomaly_scores),
        key=lambda x: x[0]
    )
    if combined:
        anomaly_indices, anomaly_timestamps, anomaly_values, anomaly_scores = zip(*combined)
        anomaly_indices = list(anomaly_indices)
        anomaly_timestamps = list(anomaly_timestamps)
        anomaly_values = list(anomaly_values)
        anomaly_scores = list(anomaly_scores)
    else:
        anomaly_indices, anomaly_timestamps, anomaly_values, anomaly_scores = [], [], [], []
    
    # Классификация
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
        type_counts = {}
    
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
    
    valid_all = [v for v in values if v is not None]
    if not valid_all:
        return {"anomaly_indices": [], "anomaly_values": [], "events": []}
    
    mean_value = np.mean(valid_all)
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
                vals = [values[i] for i in current if values[i] is not None]
                events.append({
                    "start_idx": current[0],
                    "end_idx": current[-1],
                    "duration": len(current),
                    "min_value": float(min(vals)) if vals else 0.0,
                    "indices": list(current),
                })
            current = [zero_indices[i]]
    
    if len(current) >= min_duration:
        vals = [values[i] for i in current if values[i] is not None]
        events.append({
            "start_idx": current[0],
            "end_idx": current[-1],
            "duration": len(current),
            "min_value": float(min(vals)) if vals else 0.0,
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
        
        if duration >= min_duration:
            drop_pct = (local_mean_before - min_val) / abs(local_mean_before)
            
            if drop_pct >= drop_ratio:
                indices = list(range(start_idx, min(j, start_idx + max_duration)))
                events.append({
                    "start_idx": start_idx,
                    "end_idx": indices[-1] if indices else start_idx,
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
    Классифицирует аномалии (финальная версия — строгие критерии).
    
    Spike: одиночная точка, локальный z > 1.5, НЕ плато
    Dip: одиночная/короткая точка, локальный z < -1.5 ИЛИ zero dip ИЛИ significant dip
    Drift: 5+ точек, монотонность >75%, R²>0.6, РЕАЛЬНОЕ ИЗМЕНЕНИЕ >5%, НЕ плато
    Noise: всё остальное
    """
    if not anomaly_indices:
        return {"types": [], "counts": {}}
    
    events = group_anomaly_events(anomaly_indices, max_gap=2)
    zero_dip_indices = zero_dip_indices or set()
    
    types_map = {}
    
    # Приоритет 1: zero/significant dips всегда "dip"
    for idx in anomaly_indices:
        if idx in zero_dip_indices:
            types_map[idx] = "dip"
    
    # Приоритет 2: классификация событий
    for event in events:
        indices = event["indices"]
        duration = event["duration"]
        event_values = [values[i] for i in indices if values[i] is not None]
        
        if not event_values:
            continue
        
        # Пропускаем полностью уже помеченные события (zero dips)
        if all(idx in types_map for idx in indices):
            continue
        
        center_idx = indices[len(indices) // 2]
        local_mean, local_std = _compute_local_stats(values, center_idx)
        
        mean_deviation = np.mean([(v - local_mean) / local_std for v in event_values])
        abs_deviation = abs(mean_deviation) if not np.isnan(mean_deviation) else 0
        is_above = mean_deviation > 0
        
        # Проверка плато (одинаковые значения)
        is_flat = _is_plateau(event_values, tolerance=0.02)
        
        # Средняя производная
        if len(event_values) > 1:
            derivatives = [
                abs(event_values[i+1] - event_values[i]) / local_std
                for i in range(len(event_values)-1)
            ]
            avg_derivative = float(np.mean(derivatives))
        else:
            avg_derivative = 0.0
        
        # === КЛАССИФИКАЦИЯ ===
        
        if duration == 1:
            # Одиночная точка
            if is_flat:
                event_type = "noise"
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
                # ПЛАТО — НЕ дрейф (например, 409, 409, 409)
                event_type = "noise"
            elif avg_derivative > 3.0:
                # Очень быстрые колебания
                event_type = "noise"
            elif (duration >= 5 
                  and monotonic 
                  and r_squared > 0.6 
                  and relative_change > 0.05):
                # НАСТОЯЩИЙ дрейф: монотонный + линейный + реальное изменение
                event_type = "drift"
            elif abs_deviation > 1.5 and duration < 8:
                # Короткий кластер с сильным отклонением
                event_type = "spike" if is_above else "dip"
            elif r_squared < 0.3 or avg_derivative > 1.5:
                # Нет тренда, хаотично
                event_type = "noise"
            else:
                # По умолчанию — noise (не drift!)
                event_type = "noise"
        
        # Назначаем тип (не перезаписываем zero dips)
        for idx in indices:
            if idx not in types_map:
                types_map[idx] = event_type
    
    # Формируем результат
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
    """Альтернативный метод: K-Means кластеризация (оставлена для совместимости)."""
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
print('✅ 1. anomalies.py полностью переписан')
print('   • _is_plateau() — проверка на одинаковые значения')
print('   • _is_monotonic() — строгая проверка (>75%, не плато)')
print('   • detect_significant_dips() — падения >30% от локального среднего')
print('   • Drift требует: 5+ точек + монотонность + R²>0.6 + не плато + изменение >5%')
print('   • Защита от перезаписи: if idx not in types_map')
print('   • contamination по умолчанию 0.10 (10%) вместо 0.05')

# ============================================================================
# 2. API.PY — добавляем contamination в вызов
# ============================================================================
api_path = Path('backend/modules/deep_analysis/api.py')
api_content = api_path.read_text(encoding='utf-8')

# Ищем вызов detect_anomalies_isolation_forest без contamination
old_call = '''                    tag_anomalies = detect_anomalies_isolation_forest(
                        valid_values,
                        list(range(len(valid_values))),
                        classify_types=True
                    )'''

new_call = '''                    # Адаптивный contamination: больше аномалий детектируется
                    adaptive_contamination = min(0.15, max(0.08, 200 / max(len(valid_values), 1)))
                    
                    tag_anomalies = detect_anomalies_isolation_forest(
                        valid_values,
                        list(range(len(valid_values))),
                        contamination=adaptive_contamination,
                        classify_types=True
                    )'''

if old_call in api_content:
    api_content = api_content.replace(old_call, new_call)
    api_path.write_text(api_content, encoding='utf-8', newline='\n')
    print('✅ 2. api.py: добавлен adaptive contamination (8-15%)')
    print('   • Для 8000 точек: ~0.08 (800 аномалий)')
    print('   • Для 2000 точек: ~0.10 (200 аномалий)')
    print('   • Для 1000 точек: ~0.15 (150 аномалий)')
elif 'contamination=' in api_content:
    print('ℹ️  contamination уже передаётся в api.py')
else:
    print('⚠️  Не удалось найти блок вызова в api.py')
    # Попробуем альтернативный паттерн
    alt_pattern = re.compile(
        r'tag_anomalies\s*=\s*detect_anomalies_isolation_forest\(\s*'
        r'valid_values,\s*'
        r'list\(range\(len\(valid_values\)\)\)',
        re.MULTILINE
    )
    if alt_pattern.search(api_content):
        # Заменяем через regex
        api_content = alt_pattern.sub(
            'adaptive_contamination = min(0.15, max(0.08, 200 / max(len(valid_values), 1)))\n                    '
            'tag_anomalies = detect_anomalies_isolation_forest(\n'
            '                        valid_values,\n'
            '                        list(range(len(valid_values))),\n'
            '                        contamination=adaptive_contamination',
            api_content
        )
        api_path.write_text(api_content, encoding='utf-8', newline='\n')
        print('✅ 2. api.py: contamination добавлен (через regex)')

# ============================================================================
# 3. DIAG: Проверка tag_resolver.py (LIMIT 1 это нормально)
# ============================================================================
print()
print('【DIAG】tag_resolver.py — проверка LIMIT')
print('-' * 80)
resolver_path = Path('backend/modules/deep_analysis/collectors/tag_resolver.py')
if resolver_path.exists():
    content = resolver_path.read_text(encoding='utf-8')
    limits = re.findall(r'LIMIT\s+(\d+)', content)
    print(f'  Найдено LIMIT: {limits}')
    
    # LIMIT 1 в подзапросах — это нормально (выборка zone_name, last_value)
    # Должно быть LIMIT 10000 для основного запроса тегов
    non_one_limits = [int(x) for x in limits if int(x) > 1]
    if non_one_limits and all(x >= 10000 for x in non_one_limits):
        print('  ✅ Все основные LIMIT >= 10000')
    else:
        print(f'  ⚠️  Основные LIMIT: {non_one_limits}')

# ============================================================================
# 4. ФИНАЛЬНАЯ ДИАГНОСТИКА
# ============================================================================
print()
print('=' * 80)
print('ФИНАЛЬНАЯ ПРОВЕРКА')
print('=' * 80)
print()

checks = []

# 1. _is_plateau
c = anomalies_path.read_text(encoding='utf-8')
checks.append(('_is_plateau', 'def _is_plateau' in c))

# 2. detect_significant_dips (функция)
checks.append(('detect_significant_dips (функция)', 'def detect_significant_dips' in c))

# 3. detect_significant_dips (вызов)
checks.append(('detect_significant_dips (вызов)', 'sig_dips = detect_significant_dips' in c or 'detect_significant_dips(values' in c))

# 4. Защита от перезаписи
checks.append(('Защита от перезаписи (if idx not in types_map)', 'if idx not in types_map' in c))

# 5. Строгая логика drift
checks.append(('Drift: is_flat → noise', 'if is_flat:' in c and 'event_type = "noise"' in c))
checks.append(('Drift: duration >= 5', 'duration >= 5' in c))
checks.append(('Drift: r_squared > 0.6', 'r_squared > 0.6' in c))
checks.append(('Drift: relative_change > 0.05', 'relative_change > 0.05' in c))

# 6. contamination в api.py
c_api = api_path.read_text(encoding='utf-8')
checks.append(('contamination в api.py', 'contamination=' in c_api))

for name, ok in checks:
    status = '✅' if ok else '❌'
    print(f'  {status} {name}')

print()

all_ok = all(ok for _, ok in checks)
if all_ok:
    print('=' * 80)
    print('✅✅✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ! ✅✅✅')
    print('=' * 80)
    print()
    print('Перезапусти backend и проверь:')
    print()
    print('  1. Тегов должно быть 10000 (не 1000):')
    print('     curl -s http://localhost:8081/api/v1/deep_analysis/tags | python -c "import sys,json; print(len(json.load(sys.stdin)))"')
    print()
    print('  2. Падение 600→140 теперь dip (не 0):')
    print('     curl -X POST http://localhost:8081/api/v1/deep_analysis/run \\')
    print('       -H "Content-Type: application/json" \\')
    print('       -d \'{"tags": ["ТЕГ_С_ПРОВАЛОМ"], "period": 30}\' \\')
    print('       | python -c "import sys,json; r=json.load(sys.stdin); print(r[\'anomalies\'][\'type_counts\'])"')
    print()
    print('  3. Плато 409, 409, 409 больше не drift — это noise')
    print()
    print('  4. Дрейфы на графике — пунктирные ЛИНИИ (не точки)')
    print()
    print('  5. Данные после 08.06 теперь есть (убран LIMIT 100000)')
else:
    failed = [name for name, ok in checks if not ok]
    print(f'❌ Осталось проблем: {len(failed)}')
    for name in failed:
        print(f'  • {name}')