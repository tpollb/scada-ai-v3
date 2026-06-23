#!/usr/bin/env python3
"""Создание структуры модуля deep_analysis (Итерация 1)"""

from pathlib import Path
import os

# Базовый путь
BASE = Path("backend/modules/deep_analysis")

# Создаём структуру папок
dirs = [
    BASE,
    BASE / "collectors",
    BASE / "analyzers",
    BASE / "visualizers",
    BASE / "reporter",
    BASE / "history",
]

for d in dirs:
    d.mkdir(parents=True, exist_ok=True)
    print(f"✓ Создана папка: {d}")

# ============================================================================
# __init__.py
# ============================================================================
init_content = '''"""Deep Data Analysis — хирургический анализ тегов SCADA"""
from structlog import get_logger

__version__ = "0.1.0"
log = get_logger()


def on_load():
    """Вызывается при загрузке модуля"""
    log.info("Deep Analysis module loaded", version=__version__)
'''

(BASE / "__init__.py").write_text(init_content, encoding="utf-8")
print(f"✓ Создан файл: {BASE / '__init__.py'}")

# ============================================================================
# config.yaml
# ============================================================================
config_content = '''name: deep_analysis
version: 0.1.0
description: Глубокий анализ тегов — статистика, аномалии, корреляции, сезонность
enabled: true

# Доступные периоды для анализа
available_periods: [7, 30, 120, 365]

# Опции анализа (можно включать/выключать)
analysis_options:
  anomalies: true        # Isolation Forest + K-Means
  correlations: true     # Pearson + Mutual Information + Granger
  seasonality: true      # FFT для циклов
  compare_periods: true  # A/B сравнение

# Форматы экспорта
export_formats:
  - pdf
  - excel
  - csv

# Папка для хранения истории анализов
history_dir: "data/analysis_history"

# Максимальное количество точек для анализа (downsampling)
max_points: 50000

# Параметры для Isolation Forest
isolation_forest:
  contamination: 0.05    # предполагаемый % аномалий
  n_estimators: 100      # количество деревьев

# Параметры для FFT
fft:
  min_period_hours: 1    # минимальный период для детекции
  max_period_hours: 168  # максимальный период (неделя)
  significance_threshold: 0.1  # порог значимости пика
'''

(BASE / "config.yaml").write_text(config_content, encoding="utf-8")
print(f"✓ Создан файл: {BASE / 'config.yaml'}")

# ============================================================================
# prompts.py (пустой для начала)
# ============================================================================
prompts_content = '''"""Промпты для LLM-интерпретации результатов анализа"""

# TODO: добавить в Итерации 4 (отчёты и интеграция)
# DEEP_ANALYSIS_SYSTEM_PROMPT = """..."""
# DEEP_ANALYSIS_SUMMARY_PROMPT = """..."""
'''

(BASE / "prompts.py").write_text(prompts_content, encoding="utf-8")
print(f"✓ Создан файл: {BASE / 'prompts.py'}")

# ============================================================================
# tools.py (пустой для начала)
# ============================================================================
tools_content = '''"""Tools для LLM tool calling (опционально)"""

# TODO: добавить в Итерации 4 (интеграция с чатом)
# TOOLS = [
#     {
#         "name": "run_deep_analysis",
#         "description": "Запустить глубокий анализ тега или группы тегов",
#         "parameters": {...}
#     }
# ]

TOOLS = []
'''

(BASE / "tools.py").write_text(tools_content, encoding="utf-8")
print(f"✓ Создан файл: {BASE / 'tools.py'}")

# ============================================================================
# collectors/__init__.py
# ============================================================================
collectors_init = '''"""Collectors — сбор данных из БД"""
'''

(BASE / "collectors" / "__init__.py").write_text(collectors_init, encoding="utf-8")

# ============================================================================
# collectors/data_fetcher.py
# ============================================================================
data_fetcher_content = '''"""Сбор данных из tags_value с обработкой пропусков"""
from datetime import datetime, timedelta
from typing import Optional
from structlog import get_logger
import numpy as np

from core.db import fetch

log = get_logger()


async def fetch_tag_data(
    tag_name: str,
    start_date: datetime,
    end_date: datetime,
    exclude_nulls: bool = True,
) -> dict:
    """
    Собирает данные по конкретному тегу за период.
    
    Args:
        tag_name: имя тега (например, "Temperature_Zone1")
        start_date: начало периода
        end_date: конец периода
        exclude_nulls: исключать NULL значения из расчётов
    
    Returns:
        {
            "tag_name": str,
            "timestamps": list[datetime],
            "values": list[float],
            "total_count": int,
            "valid_count": int,
            "null_count": int,
            "metadata": {...}
        }
    """
    log.info(
        "Fetching tag data",
        tag=tag_name,
        start=start_date.isoformat(),
        end=end_date.isoformat()
    )
    
    # SQL запрос к tags_value
    null_clause = "AND tv.value IS NOT NULL" if exclude_nulls else ""
    
    query = f"""
        SELECT 
            tv.date_created as timestamp,
            tv.value,
            td.tag_name,
            td.tag_id,
            z.zone_name
        FROM tags_value tv
        JOIN tags_dict td ON td.tag_id = tv.tag_id
        LEFT JOIN zones_dict z ON z.zone_id = td.zone_id
        WHERE td.tag_name = $1
          AND tv.date_created >= $2
          AND tv.date_created <= $3
          {null_clause}
        ORDER BY tv.date_created ASC
    """
    
    rows = await fetch(query, tag_name, start_date, end_date)
    
    timestamps = []
    values = []
    null_count = 0
    
    for row in rows:
        timestamps.append(row['timestamp'])
        if row['value'] is not None:
            values.append(float(row['value']))
        else:
            null_count += 1
    
    # Metadata (берём из первой строки)
    metadata = {}
    if rows:
        metadata = {
            "tag_id": rows[0].get('tag_id'),
            "zone_name": rows[0].get('zone_name'),
        }
    
    result = {
        "tag_name": tag_name,
        "timestamps": timestamps,
        "values": values,
        "total_count": len(rows),
        "valid_count": len(values),
        "null_count": null_count,
        "metadata": metadata,
    }
    
    log.info(
        "Tag data fetched",
        tag=tag_name,
        total=len(rows),
        valid=len(values),
        nulls=null_count
    )
    
    return result


async def fetch_multiple_tags(
    tag_names: list[str],
    start_date: datetime,
    end_date: datetime,
    exclude_nulls: bool = True,
) -> dict:
    """
    Собирает данные по группе тегов для кросс-анализа.
    
    Returns:
        {
            "tags": {tag_name: {...data...}, ...},
            "common_timestamps": list[datetime],  # общие точки для корреляций
        }
    """
    log.info("Fetching multiple tags", count=len(tag_names))
    
    tags_data = {}
    for tag_name in tag_names:
        tags_data[tag_name] = await fetch_tag_data(
            tag_name, start_date, end_date, exclude_nulls
        )
    
    # Находим общие timestamps для корреляций
    # (пока пропускаем — реализуем в Итерации 2)
    common_timestamps = []
    
    return {
        "tags": tags_data,
        "common_timestamps": common_timestamps,
    }
'''

(BASE / "collectors" / "data_fetcher.py").write_text(data_fetcher_content, encoding="utf-8")
print(f"✓ Создан файл: {BASE / 'collectors' / 'data_fetcher.py'}")

# ============================================================================
# collectors/tag_resolver.py
# ============================================================================
tag_resolver_content = '''"""Получение списка доступных тегов для UI"""
from structlog import get_logger
from core.db import fetch

log = get_logger()


async def get_available_tags() -> list[dict]:
    """
    Возвращает список всех тегов из tags_dict.
    
    Returns:
        [
            {
                "tag_id": int,
                "tag_name": str,
                "zone_name": str | None,
                "unit": str | None,
                "last_value": float | None,
                "last_update": datetime | None,
            },
            ...
        ]
    """
    log.info("Fetching available tags")
    
    query = """
        SELECT 
            td.tag_id,
            td.tag_name,
            z.zone_name,
            td.unit,
            (
                SELECT tv.value 
                FROM tags_value tv 
                WHERE tv.tag_id = td.tag_id 
                ORDER BY tv.date_created DESC 
                LIMIT 1
            ) as last_value,
            (
                SELECT tv.date_created 
                FROM tags_value tv 
                WHERE tv.tag_id = td.tag_id 
                ORDER BY tv.date_created DESC 
                LIMIT 1
            ) as last_update
        FROM tags_dict td
        LEFT JOIN zones_dict z ON z.zone_id = td.zone_id
        ORDER BY td.tag_name ASC
    """
    
    rows = await fetch(query)
    
    tags = []
    for row in rows:
        tags.append({
            "tag_id": row['tag_id'],
            "tag_name": row['tag_name'],
            "zone_name": row.get('zone_name'),
            "unit": row.get('unit'),
            "last_value": row.get('last_value'),
            "last_update": row.get('last_update'),
        })
    
    log.info("Available tags fetched", count=len(tags))
    return tags


async def get_tags_by_zone() -> dict:
    """
    Группирует теги по зонам (для UI с фильтрами).
    
    Returns:
        {
            "zone_name_1": [tag1, tag2, ...],
            "zone_name_2": [...],
        }
    """
    tags = await get_available_tags()
    
    by_zone = {}
    for tag in tags:
        zone = tag.get('zone_name') or 'Без зоны'
        if zone not in by_zone:
            by_zone[zone] = []
        by_zone[zone].append(tag)
    
    return by_zone
'''

(BASE / "collectors" / "tag_resolver.py").write_text(tag_resolver_content, encoding="utf-8")
print(f"✓ Создан файл: {BASE / 'collectors' / 'tag_resolver.py'}")

# ============================================================================
# analyzers/__init__.py
# ============================================================================
analyzers_init = '''"""Analyzers — статистика, аномалии, корреляции"""
'''

(BASE / "analyzers" / "__init__.py").write_text(analyzers_init, encoding="utf-8")

# ============================================================================
# analyzers/stats.py
# ============================================================================
stats_content = '''"""Базовая статистика: mean, median, std, quartiles, IQR, KDE"""
from typing import Optional
import numpy as np
from structlog import get_logger

log = get_logger()


def compute_basic_stats(values: list[float]) -> dict:
    """
    Вычисляет базовую статистику по массиву значений.
    
    Args:
        values: список числовых значений (без NaN)
    
    Returns:
        {
            "count": int,
            "mean": float,
            "median": float,
            "std": float,
            "variance": float,
            "min": float,
            "max": float,
            "range": float,
            "q1": float,  # 25-й перцентиль
            "q3": float,  # 75-й перцентиль
            "iqr": float, # межквартильный размах
            "skewness": float,  # асимметрия
            "kurtosis": float,  # эксцесс
        }
    """
    if not values:
        return {"count": 0}
    
    arr = np.array(values, dtype=np.float64)
    
    q1 = np.percentile(arr, 25)
    q3 = np.percentile(arr, 75)
    
    stats = {
        "count": len(arr),
        "mean": float(np.mean(arr)),
        "median": float(np.median(arr)),
        "std": float(np.std(arr, ddof=1)),  # sample std
        "variance": float(np.var(arr, ddof=1)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "range": float(np.max(arr) - np.min(arr)),
        "q1": float(q1),
        "q3": float(q3),
        "iqr": float(q3 - q1),
        "skewness": float(_skewness(arr)),
        "kurtosis": float(_kurtosis(arr)),
    }
    
    log.debug("Basic stats computed", count=len(arr), mean=stats['mean'], std=stats['std'])
    return stats


def _skewness(arr: np.ndarray) -> float:
    """Вычисляет коэффициент асимметрии"""
    n = len(arr)
    if n < 3:
        return 0.0
    
    mean = np.mean(arr)
    std = np.std(arr, ddof=1)
    if std == 0:
        return 0.0
    
    return float(np.sum(((arr - mean) / std) ** 3) * n / ((n - 1) * (n - 2)))


def _kurtosis(arr: np.ndarray) -> float:
    """Вычисляет коэффициент эксцесса (избыточный)"""
    n = len(arr)
    if n < 4:
        return 0.0
    
    mean = np.mean(arr)
    std = np.std(arr, ddof=1)
    if std == 0:
        return 0.0
    
    m4 = np.mean((arr - mean) ** 4)
    m2 = np.var(arr, ddof=1)
    
    # Избыточный эксцесс (нормальное распределение = 0)
    return float(m4 / (m2 ** 2) - 3)


def compute_histogram(
    values: list[float],
    bins: int = 50
) -> dict:
    """
    Вычисляет гистограмму распределения.
    
    Returns:
        {
            "bin_edges": list[float],
            "bin_counts": list[int],
            "bin_centers": list[float],
        }
    """
    if not values:
        return {"bin_edges": [], "bin_counts": [], "bin_centers": []}
    
    arr = np.array(values, dtype=np.float64)
    counts, bin_edges = np.histogram(arr, bins=bins)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    
    return {
        "bin_edges": bin_edges.tolist(),
        "bin_counts": counts.tolist(),
        "bin_centers": bin_centers.tolist(),
    }
'''

(BASE / "analyzers" / "stats.py").write_text(stats_content, encoding="utf-8")
print(f"✓ Создан файл: {BASE / 'analyzers' / 'stats.py'}")

# ============================================================================
# analyzers/anomalies.py
# ============================================================================
anomalies_content = '''"""Детекция аномалий через Isolation Forest"""
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
'''

(BASE / "analyzers" / "anomalies.py").write_text(anomalies_content, encoding="utf-8")
print(f"✓ Создан файл: {BASE / 'analyzers' / 'anomalies.py'}")

# ============================================================================
# visualizers/__init__.py
# ============================================================================
visualizers_init = '''"""Visualizers — генерация JSON для Chart.js"""
'''

(BASE / "visualizers" / "__init__.py").write_text(visualizers_init, encoding="utf-8")

# ============================================================================
# visualizers/chart_specs.py
# ============================================================================
chart_specs_content = '''"""Генерация JSON-спецификаций для Chart.js"""
from typing import Optional
from datetime import datetime
from structlog import get_logger

log = get_logger()


def create_time_series_spec(
    timestamps: list[datetime],
    values: list[float],
    tag_name: str,
    anomalies: Optional[dict] = None,
) -> dict:
    """
    Создаёт JSON-спецификацию для time series графика.
    
    Args:
        timestamps: массив timestamps
        values: массив значений
        tag_name: имя тега (для заголовка)
        anomalies: результат от detect_anomalies_isolation_forest
    
    Returns:
        Chart.js конфигурация (dict) для передачи в Line компонент
    """
    # Форматируем timestamps для Chart.js
    labels = [ts.strftime("%Y-%m-%d %H:%M") for ts in timestamps]
    
    # Основной dataset (данные)
    datasets = [
        {
            "label": tag_name,
            "data": values,
            "borderColor": "#3b82f6",  # синий
            "backgroundColor": "#3b82f620",
            "tension": 0.3,
            "fill": False,
            "pointRadius": 0,
            "pointHoverRadius": 4,
        }
    ]
    
    # Если есть аномалии — добавляем scatter dataset
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
        })
    
    spec = {
        "type": "line",
        "data": {
            "labels": labels,
            "datasets": datasets,
        },
        "options": {
            "responsive": True,
            "maintainAspectRatio": False,
            "plugins": {
                "legend": {
                    "display": True,
                    "position": "top",
                },
                "tooltip": {
                    "mode": "index",
                    "intersect": False,
                },
            },
            "scales": {
                "x": {
                    "display": True,
                    "grid": {"display": False},
                    "ticks": {"maxTicksLimit": 10},
                },
                "y": {
                    "display": True,
                    "grid": {"color": "rgba(0, 0, 0, 0.05)"},
                },
            },
            "interaction": {
                "mode": "nearest",
                "axis": "x",
                "intersect": False,
            },
        },
    }
    
    return spec


def create_histogram_spec(
    histogram_data: dict,
    tag_name: str,
) -> dict:
    """
    Создаёт спецификацию для гистограммы распределения.
    
    Args:
        histogram_data: результат от compute_histogram()
        tag_name: имя тега
    
    Returns:
        Chart.js конфигурация для Bar chart
    """
    spec = {
        "type": "bar",
        "data": {
            "labels": [f"{x:.2f}" for x in histogram_data['bin_centers']],
            "datasets": [
                {
                    "label": f"Распределение {tag_name}",
                    "data": histogram_data['bin_counts'],
                    "backgroundColor": "#3b82f680",
                    "borderColor": "#3b82f6",
                    "borderWidth": 1,
                }
            ],
        },
        "options": {
            "responsive": True,
            "maintainAspectRatio": False,
            "plugins": {
                "legend": {"display": False},
            },
            "scales": {
                "x": {
                    "display": True,
                    "title": {"display": True, "text": "Значение"},
                },
                "y": {
                    "display": True,
                    "title": {"display": True, "text": "Частота"},
                },
            },
        },
    }
    
    return spec
'''

(BASE / "visualizers" / "chart_specs.py").write_text(chart_specs_content, encoding="utf-8")
print(f"✓ Создан файл: {BASE / 'visualizers' / 'chart_specs.py'}")

# ============================================================================
# history/__init__.py
# ============================================================================
history_init = '''"""History — сохранение и загрузка анализов"""
'''

(BASE / "history" / "__init__.py").write_text(history_init, encoding="utf-8")

# ============================================================================
# history/storage.py
# ============================================================================
storage_content = '''"""Сохранение результатов анализа в JSON файлы"""
from pathlib import Path
from datetime import datetime
from typing import Optional
import json
import hashlib
from structlog import get_logger

log = get_logger()

# Папка для хранения истории (создаётся автоматически)
HISTORY_DIR = Path("backend/data/analysis_history")


def ensure_history_dir():
    """Создаёт папку для истории если её нет"""
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def save_analysis(
    analysis_id: str,
    params: dict,
    results: dict,
) -> str:
    """
    Сохраняет результат анализа в JSON файл.
    
    Args:
        analysis_id: уникальный ID анализа (timestamp + hash тегов)
        params: параметры запроса (теги, период, опции)
        results: результаты анализа (статистика, аномалии, etc)
    
    Returns:
        Путь к сохранённому файлу
    """
    ensure_history_dir()
    
    filepath = HISTORY_DIR / f"{analysis_id}.json"
    
    data = {
        "analysis_id": analysis_id,
        "created_at": datetime.now().isoformat(),
        "params": params,
        "results": results,
    }
    
    # Сериализуем datetime объекты
    def json_serializer(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=json_serializer)
    
    log.info("Analysis saved", id=analysis_id, path=str(filepath))
    return str(filepath)


def load_analysis(analysis_id: str) -> Optional[dict]:
    """
    Загружает сохранённый анализ по ID.
    
    Returns:
        Данные анализа или None если не найден
    """
    ensure_history_dir()
    
    filepath = HISTORY_DIR / f"{analysis_id}.json"
    
    if not filepath.exists():
        log.warning("Analysis not found", id=analysis_id)
        return None
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    log.info("Analysis loaded", id=analysis_id)
    return data


def list_analyses(limit: int = 50) -> list[dict]:
    """
    Возвращает список сохранённых анализов.
    
    Returns:
        [
            {
                "analysis_id": str,
                "created_at": str,
                "tags": list[str],
                "period": str,
            },
            ...
        ]
    """
    ensure_history_dir()
    
    analyses = []
    for filepath in sorted(HISTORY_DIR.glob("*.json"), reverse=True)[:limit]:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            analyses.append({
                "analysis_id": data['analysis_id'],
                "created_at": data['created_at'],
                "tags": data['params'].get('tags', []),
                "period": data['params'].get('period', 'unknown'),
            })
        except Exception as e:
            log.warning("Failed to load analysis", file=filepath.name, error=str(e))
    
    return analyses


def delete_analysis(analysis_id: str) -> bool:
    """Удаляет анализ по ID"""
    ensure_history_dir()
    
    filepath = HISTORY_DIR / f"{analysis_id}.json"
    
    if filepath.exists():
        filepath.unlink()
        log.info("Analysis deleted", id=analysis_id)
        return True
    
    return False


def generate_analysis_id(tags: list[str], period: str) -> str:
    """
    Генерирует уникальный ID для анализа.
    
    Формат: {timestamp}_{hash_тегов}
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Hash от тегов и периода
    tags_str = "|".join(sorted(tags)) + f"|{period}"
    hash_obj = hashlib.md5(tags_str.encode('utf-8'))
    hash_short = hash_obj.hexdigest()[:8]
    
    return f"{timestamp}_{hash_short}"
'''

(BASE / "history" / "storage.py").write_text(storage_content, encoding="utf-8")
print(f"✓ Создан файл: {BASE / 'history' / 'storage.py'}")

# ============================================================================
# reporter/__init__.py (пустой для Итерации 4)
# ============================================================================
reporter_init = '''"""Reporter — экспорт в PDF/Excel (Итерация 4)"""
'''

(BASE / "reporter" / "__init__.py").write_text(reporter_init, encoding="utf-8")

print()
print("=" * 70)
print("✅ СТРУКТУРА МОДУЛЯ СОЗДАНА")
print("=" * 70)
print()
print("Созданные файлы:")
print("  backend/modules/deep_analysis/")
print("  ├── __init__.py")
print("  ├── config.yaml")
print("  ├── prompts.py (пустой)")
print("  ├── tools.py (пустой)")
print("  ├── collectors/")
print("  │   ├── __init__.py")
print("  │   ├── data_fetcher.py")
print("  │   └── tag_resolver.py")
print("  ├── analyzers/")
print("  │   ├── __init__.py")
print("  │   ├── stats.py")
print("  │   └── anomalies.py")
print("  ├── visualizers/")
print("  │   ├── __init__.py")
print("  │   └── chart_specs.py")
print("  ├── history/")
print("  │   ├── __init__.py")
print("  │   └── storage.py")
print("  └── reporter/")
print("      └── __init__.py (пустой)")
print()
print("Следующий шаг:")
print("  Создадим api.py с endpoints:")
print("    - POST /deep_analysis/run")
print("    - GET /deep_analysis/history")
print("    - GET /deep_analysis/history/{id}")
print("    - GET /deep_analysis/tags")