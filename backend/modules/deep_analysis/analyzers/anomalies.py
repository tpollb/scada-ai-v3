"""Детекция аномалий через Isolation Forest"""
from typing import Optional
import numpy as np
from sklearn.ensemble import IsolationForest
from structlog import get_logger

log = get_logger()


def detect_anomalies_isolation_forest(
    values: list[float],
    timestamps: list,
    contamination: float = 0.05,
    n_estimators: int = 100,
) -> dict:
    """
    Детектирует аномалии через Isolation Forest.
    
    Args:
        values: массив значений
        timestamps: массив timestamps (для привязки к времени)
        contamination: предполагаемый % аномалий (0.05 = 5%)
        n_estimators: количество деревьев в лесе
    
    Returns:
        {
            "anomaly_indices": list[int],  # индексы аномальных точек
            "anomaly_timestamps": list[datetime],
            "anomaly_values": list[float],
            "anomaly_scores": list[float],  # scores от IsolationForest
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
    
    result = {
        "anomaly_indices": anomaly_indices,
        "anomaly_timestamps": anomaly_timestamps,
        "anomaly_values": anomaly_values,
        "anomaly_scores": anomaly_scores,
        "total_anomalies": len(anomaly_indices),
        "anomaly_rate": len(anomaly_indices) / len(values),
    }
    
    log.info(
        "Anomalies detected",
        total=len(anomaly_indices),
        rate=f"{result['anomaly_rate']:.2%}"
    )
    
    return result
