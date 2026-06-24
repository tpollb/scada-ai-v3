#!/usr/bin/env python3
"""
day1_kmeans_anomalies.py — классификация аномалий по типам (Spike/Dip/Drift/Noise)
"""

from pathlib import Path

print('=' * 70)
print('K-MEANS КЛАСТЕРИЗАЦИЯ АНОМАЛИЙ (Day 1-2)')
print('=' * 70)
print()

# ============================================================================
# 1. Обновляем anomalies.py — добавляем кластеризацию
# ============================================================================
anomalies_path = Path('backend/modules/deep_analysis/analyzers/anomalies.py')

new_anomalies = '''"""Детекция и классификация аномалий"""
from typing import Optional, Literal
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.cluster import KMeans
from structlog import get_logger

log = get_logger()


AnomalyType = Literal["spike", "dip", "drift", "noise"]


def detect_anomalies_isolation_forest(
    values: list[float],
    timestamps: list,
    contamination: float = 0.05,
    n_estimators: int = 100,
    classify_types: bool = True,
) -> dict:
    """
    Детектирует аномалии через Isolation Forest + классифицирует по типам.
    
    Args:
        values: массив значений
        timestamps: массив timestamps
        contamination: предполагаемый % аномалий (0.05 = 5%)
        n_estimators: количество деревьев
        classify_types: классифицировать ли аномалии по типам
    
    Returns:
        {
            "anomaly_indices": list[int],
            "anomaly_timestamps": list[datetime],
            "anomaly_values": list[float],
            "anomaly_scores": list[float],
            "anomaly_types": list[str],  # NEW: тип каждой аномалии
            "type_counts": dict,         # NEW: количество по типам
            "total_anomalies": int,
            "anomaly_rate": float,
        }
    """
    if len(values) < 10:
        log.warning("Not enough data for anomaly detection", count=len(values))
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

    log.info(
        "Running Isolation Forest",
        points=len(values),
        contamination=contamination
    )

    # Подготовка данных
    X = np.array(values).reshape(-1, 1)

    # Isolation Forest
    model = IsolationForest(
        contamination=contamination,
        n_estimators=n_estimators,
        random_state=42,
        n_jobs=-1,
    )

    # Обучаем и предсказываем
    predictions = model.fit_predict(X)  # 1 = normal, -1 = anomaly
    scores = model.decision_function(X)  # чем меньше, тем аномальнее

    # Находим индексы аномалий
    anomaly_indices = np.where(predictions == -1)[0].tolist()

    # Извлекаем данные аномалий
    anomaly_timestamps = [timestamps[i] for i in anomaly_indices]
    anomaly_values = [values[i] for i in anomaly_indices]
    anomaly_scores = [float(scores[i]) for i in anomaly_indices]
    
    # Классификация по типам
    anomaly_types = []
    type_counts = {}
    
    if classify_types and len(anomaly_indices) > 0:
        types_result = classify_anomaly_types(
            values=values,
            anomaly_indices=anomaly_indices,
            anomaly_values=anomaly_values
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
        "total_anomalies": len(anomaly_indices),
        "anomaly_rate": len(anomaly_indices) / len(values),
    }

    log.info(
        "Anomalies detected and classified",
        total=len(anomaly_indices),
        rate=f"{result['anomaly_rate']:.2%}",
        types=type_counts
    )

    return result


def group_anomaly_events(
    anomaly_indices: list[int],
    max_gap: int = 2
) -> list[dict]:
    """
    Группирует подряд идущие аномалии в "события".
    
    Args:
        anomaly_indices: индексы аномальных точек
        max_gap: максимальный разрыв для объединения в одно событие
    
    Returns:
        [
            {
                "start_idx": int,
                "end_idx": int,
                "indices": list[int],
                "duration": int,  # количество точек
            },
            ...
        ]
    """
    if not anomaly_indices:
        return []
    
    events = []
    current_event = {"indices": [anomaly_indices[0]]}
    
    for i in range(1, len(anomaly_indices)):
        prev_idx = anomaly_indices[i - 1]
        curr_idx = anomaly_indices[i]
        
        # Если разрыв <= max_gap — добавляем в текущее событие
        if curr_idx - prev_idx <= max_gap + 1:
            current_event["indices"].append(curr_idx)
        else:
            # Завершаем текущее событие и начинаем новое
            current_event["start_idx"] = current_event["indices"][0]
            current_event["end_idx"] = current_event["indices"][-1]
            current_event["duration"] = len(current_event["indices"])
            events.append(current_event)
            current_event = {"indices": [curr_idx]}
    
    # Добавляем последнее событие
    current_event["start_idx"] = current_event["indices"][0]
    current_event["end_idx"] = current_event["indices"][-1]
    current_event["duration"] = len(current_event["indices"])
    events.append(current_event)
    
    return events


def classify_anomaly_types(
    values: list[float],
    anomaly_indices: list[int],
    anomaly_values: list[float],
) -> dict:
    """
    Классифицирует аномалии по типам: spike, dip, drift, noise.
    
    Логика:
    1. Группируем подряд идущие аномалии в события
    2. Для каждого события вычисляем признаки:
       - Средняя высота отклонения от среднего
       - Длительность (количество точек)
       - Средняя скорость изменения (derivative)
       - Знак отклонения (выше/ниже среднего)
    3. Классифицируем по правилам:
       - Spike: короткое (1-2 точки) + высокое отклонение + выше среднего
       - Dip: короткое + высокое отклонение + ниже среднего
       - Drift: длинное (>=3 точек) + одно направление
       - Noise: быстрые колебания (высокая производная, смена знаков)
    
    Returns:
        {
            "types": list[str],  # тип для каждой аномалии
            "counts": dict,      # количество по типам
        }
    """
    if not anomaly_indices:
        return {"types": [], "counts": {}}
    
    # Среднее значение ряда
    mean_value = np.mean(values)
    std_value = np.std(values)
    
    # Группируем в события
    events = group_anomaly_events(anomaly_indices, max_gap=2)
    
    # Для каждой аномалии определяем тип
    types_map = {}  # index -> type
    
    for event in events:
        indices = event["indices"]
        duration = event["duration"]
        event_values = [values[i] for i in indices]
        
        # Среднее отклонение от mean (в единицах std)
        mean_deviation = np.mean([(v - mean_value) / (std_value + 1e-10) for v in event_values])
        
        # Средняя скорость изменения (derivative)
        if len(event_values) > 1:
            derivatives = [abs(event_values[i+1] - event_values[i]) for i in range(len(event_values)-1)]
            avg_derivative = np.mean(derivatives) / (std_value + 1e-10)
        else:
            avg_derivative = 0.0
        
        # Знак отклонения
        is_above = mean_deviation > 0
        
        # Классификация
        if duration == 1:
            # Одиночная точка
            if is_above:
                event_type = "spike"
            else:
                event_type = "dip"
        elif duration == 2:
            # Две точки подряд
            if avg_derivative > 2.0:
                # Быстрое изменение — noise
                event_type = "noise"
            elif is_above:
                event_type = "spike"
            else:
                event_type = "dip"
        else:
            # 3+ точек подряд
            if avg_derivative > 3.0:
                # Быстрые колебания — noise
                event_type = "noise"
            else:
                # Постепенное отклонение — drift
                event_type = "drift"
        
        # Назначаем тип всем точкам в событии
        for idx in indices:
            types_map[idx] = event_type
    
    # Формируем список типов в порядке anomaly_indices
    types = [types_map[idx] for idx in anomaly_indices]
    
    # Считаем количество по типам
    counts = {}
    for t in types:
        counts[t] = counts.get(t, 0) + 1
    
    return {
        "types": types,
        "counts": counts,
    }


def classify_anomalies_kmeans(
    values: list[float],
    anomaly_indices: list[int],
    anomaly_values: list[float],
    n_clusters: int = 4,
) -> dict:
    """
    Альтернативный метод: K-Means кластеризация признаков аномалий.
    
    Признаки для каждой аномалии:
    1. Z-score (отклонение от среднего в единицах std)
    2. Локальная производная (скорость изменения)
    3. Длительность события (сколько точек подряд)
    
    После кластеризации автоматически присваиваем метки:
    - Кластер с высоким z-score + короткой длительностью → spike/dip
    - Кластер с длинной длительностью → drift
    - Кластер с высокой производной → noise
    
    Returns:
        {
            "types": list[str],
            "counts": dict,
            "cluster_centers": list[list[float]],  # для отладки
        }
    """
    if len(anomaly_indices) < n_clusters:
        # Слишком мало аномалий для K-Means
        return classify_anomaly_types(values, anomaly_indices, anomaly_values)
    
    # Среднее и std
    mean_value = np.mean(values)
    std_value = np.std(values)
    
    # Группируем в события
    events = group_anomaly_events(anomaly_indices, max_gap=2)
    
    # Создаём map: index -> event
    index_to_event = {}
    for event in events:
        for idx in event["indices"]:
            index_to_event[idx] = event
    
    # Извлекаем признаки для каждой аномалии
    features = []
    for idx in anomaly_indices:
        event = index_to_event[idx]
        value = values[idx]
        
        # 1. Z-score
        z_score = (value - mean_value) / (std_value + 1e-10)
        
        # 2. Локальная производная
        if idx > 0 and idx < len(values) - 1:
            derivative = abs(values[idx+1] - values[idx-1]) / 2 / (std_value + 1e-10)
        else:
            derivative = 0.0
        
        # 3. Длительность события (нормализованная)
        duration_norm = min(event["duration"] / 10.0, 1.0)
        
        features.append([z_score, derivative, duration_norm])
    
    # K-Means кластеризация
    X = np.array(features)
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(X)
    cluster_centers = kmeans.cluster_centers_.tolist()
    
    # Автоматическая интерпретация кластеров
    # Для каждого кластера вычисляем средние признаки
    cluster_means = []
    for c in range(n_clusters):
        cluster_points = X[cluster_labels == c]
        if len(cluster_points) > 0:
            means = cluster_points.mean(axis=0)
            cluster_means.append(means)
        else:
            cluster_means.append([0, 0, 0])
    
    # Присваиваем метки кластерам
    cluster_type_map = {}
    for c, means in enumerate(cluster_means):
        z_score_mean, derivative_mean, duration_mean = means
        
        # Логика присвоения меток
        if duration_mean > 0.3:
            # Длительные события
            cluster_type_map[c] = "drift"
        elif derivative_mean > 0.5:
            # Быстрые изменения
            cluster_type_map[c] = "noise"
        elif z_score_mean > 0:
            # Высокие положительные отклонения
            cluster_type_map[c] = "spike"
        else:
            # Низкие отрицательные отклонения
            cluster_type_map[c] = "dip"
    
    # Формируем список типов
    types = [cluster_type_map[cluster_labels[i]] for i in range(len(anomaly_indices))]
    
    # Считаем количество
    counts = {}
    for t in types:
        counts[t] = counts.get(t, 0) + 1
    
    return {
        "types": types,
        "counts": counts,
        "cluster_centers": cluster_centers,
    }
'''

anomalies_path.write_text(new_anomalies, encoding='utf-8', newline='\n')
print('✓ anomalies.py обновлён')
print()
print('Что добавлено:')
print('  • group_anomaly_events() — группирует подряд идущие аномалии')
print('  • classify_anomaly_types() — rule-based классификация')
print('  • classify_anomalies_kmeans() — K-Means кластеризация признаков')
print('  • Обновлена detect_anomalies_isolation_forest() — добавлены поля:')
print('    - anomaly_types: list[str]')
print('    - type_counts: dict')
print()

# ============================================================================
# 2. Обновляем chart_specs.py — цветовая кодировка типов аномалий
# ============================================================================
chart_specs_path = Path('backend/modules/deep_analysis/visualizers/chart_specs.py')
content = chart_specs_path.read_text(encoding='utf-8')

# Обновляем create_time_series_spec чтобы принимать anomaly_types
old_spec = '''def create_time_series_spec(
    timestamps: list[datetime],
    values: list[float],
    tag_name: str,
    anomalies: Optional[dict] = None,
) -> dict:'''

new_spec = '''def create_time_series_spec(
    timestamps: list[datetime],
    values: list[float],
    tag_name: str,
    anomalies: Optional[dict] = None,
) -> dict:
    """
    Создаёт JSON-спецификацию для time series графика с цветовой кодировкой аномалий.
    
    Цвета аномалий:
    - 🔴 Spike (пик) — красный
    - 🔵 Dip (провал) — синий
    - 🟠 Drift (дрейф) — оранжевый
    - ⚪ Noise (шум) — серый
    """'''

if old_spec in content:
    content = content.replace(old_spec, new_spec)

# Обновляем блок с аномалиями
old_anomalies_block = '''    # Если есть аномалии — добавляем scatter dataset
    if anomalies and anomalies['anomaly_indices']:
        # Создаём массив с null для нормальных точек
        anomaly_data = [None] * len(values)
        for idx, val in zip(anomalies['anomaly_indices'], anomalies['anomaly_values']):
            anomaly_data[idx] = val
        
        datasets.append({
            "label": "Аномалии",
            "data": anomaly_data,
            "borderColor": "#ef4444",  # красный
            "backgroundColor": "#ef4444",
            "type": "scatter",
            "pointRadius": 6,
            "pointHoverRadius": 8,
            "showLine": False,
        })'''

new_anomalies_block = '''    # Если есть аномалии — добавляем scatter datasets по типам
    if anomalies and anomalies.get('anomaly_indices'):
        anomaly_types = anomalies.get('anomaly_types', [])
        
        # Цвета для разных типов
        type_colors = {
            "spike": {"color": "#ef4444", "label": "Пики (Spike)"},      # красный
            "dip": {"color": "#3b82f6", "label": "Провалы (Dip)"},       # синий
            "drift": {"color": "#f59e0b", "label": "Дрейфы (Drift)"},    # оранжевый
            "noise": {"color": "#6b7280", "label": "Шум (Noise)"},       # серый
            "unknown": {"color": "#ef4444", "label": "Аномалии"},        # fallback
        }
        
        # Группируем аномалии по типам
        anomalies_by_type = {}
        for i, (idx, val, atype) in enumerate(
            zip(anomalies['anomaly_indices'], anomalies['anomaly_values'], anomaly_types)
        ):
            if atype not in anomalies_by_type:
                anomalies_by_type[atype] = []
            anomalies_by_type[atype].append((idx, val))
        
        # Создаём dataset для каждого типа
        for atype, points in anomalies_by_type.items():
            color_info = type_colors.get(atype, type_colors["unknown"])
            
            # Создаём массив с null для всех точек кроме этого типа
            type_data = [None] * len(values)
            for idx, val in points:
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

if old_anomalies_block in content:
    content = content.replace(old_anomalies_block, new_anomalies_block)
    chart_specs_path.write_text(content, encoding='utf-8', newline='\n')
    print('✓ chart_specs.py обновлён')
    print('  • Цветовая кодировка аномалий по типам')
    print('  • 🔴 Spike, 🔵 Dip, 🟠 Drift, ⚪ Noise')
else:
    print('⚠ Не удалось найти блок аномалий в chart_specs.py')

print()
print('=' * 70)
print('СЛЕДУЮЩИЙ ШАГ: Обновление UI')
print('=' * 70)
print()
print('Перезапусти backend и проверь:')
print()
print('  curl -X POST http://localhost:8081/api/v1/deep_analysis/run \\')
print('    -H "Content-Type: application/json" \\')
print('    -d \'{"tags": ["R203-CO2"], "period": 30}\'')
print()
print('В ответе должно быть:')
print('  • "anomaly_types": ["spike", "drift", "spike", ...]')
print('  • "type_counts": {"spike": 12, "dip": 3, "drift": 5, "noise": 8}')
print()
print('На графике аномалии будут разных цветов:')
print('  • 🔴 Красные точки — пики')
print('  • 🔵 Синие точки — провалы')
print('  • 🟠 Оранжевые точки — дрейфы')
print('  • ⚪ Серые точки — шум')