"""Настройки модуля Deep Data Analysis"""
from pathlib import Path
from typing import Any
import yaml
from pydantic import BaseModel, Field
from structlog import get_logger

log = get_logger()

CONFIG_PATH = Path(__file__).parent / "config.yaml"


class AnomalyDetectionSettings(BaseModel):
    """Настройки детекции аномалий"""
    contamination: float = Field(0.06, ge=0.01, le=0.20, description="% аномалий в Isolation Forest")
    n_estimators: int = Field(100, ge=10, le=500, description="Количество деревьев")
    
    spike_threshold: float = Field(2.0, ge=1.0, le=5.0, description="Z-score для пика")
    dip_threshold: float = Field(3.0, ge=1.0, le=5.0, description="Z-score для провала")
    
    drift_min_duration: int = Field(3, ge=2, le=20, description="Мин. точек для дрейфа")
    drift_min_r_squared: float = Field(0.3, ge=0.1, le=0.95, description="Качество тренда")
    drift_min_relative_change: float = Field(0.02, ge=0.01, le=0.20, description="Мин. изменение")
    
    plateau_tolerance: float = Field(0.02, ge=0.001, le=0.10, description="Порог плато")
    local_window: int = Field(24, ge=5, le=100, description="Окно локальной статистики")
    
    significant_dip_ratio: float = Field(0.50, ge=0.10, le=0.80, description="Порог значительного провала")
    zero_threshold_ratio: float = Field(0.05, ge=0.01, le=0.20, description="Порог нуля")


class CorrelationsSettings(BaseModel):
    """Настройки корреляций"""
    resample_freq: str = Field("5min", description="Частота ресемплинга")
    pearson_threshold: float = Field(0.3, ge=0.1, le=0.9, description="Мин. |r| для значимости")
    max_lag: int = Field(50, ge=10, le=200, description="Макс. лаг для cross-correlation")


class VisualizationSettings(BaseModel):
    """Настройки визуализации"""
    max_points: int = Field(3000, ge=500, le=10000, description="Downsampling для графиков")
    anomaly_point_radius: int = Field(6, ge=2, le=15, description="Размер точек аномалий")
    drift_line_width: int = Field(2, ge=1, le=5, description="Толщина линии дрейфа")


class ColorsSettings(BaseModel):
    """Цветовая схема"""
    spike: str = Field("#ef4444", description="Цвет пиков")
    dip: str = Field("#3b82f6", description="Цвет провалов")
    drift: str = Field("#f59e0b", description="Цвет дрейфов")
    noise: str = Field("#9ca3af", description="Цвет шума")


class DDASettings(BaseModel):
    """Полные настройки модуля DDA"""
    anomaly_detection: AnomalyDetectionSettings = Field(default_factory=AnomalyDetectionSettings)
    correlations: CorrelationsSettings = Field(default_factory=CorrelationsSettings)
    visualization: VisualizationSettings = Field(default_factory=VisualizationSettings)
    colors: ColorsSettings = Field(default_factory=ColorsSettings)


# === Singleton для кэширования настроек ===
_cached_settings: DDASettings | None = None


def load_dda_settings() -> DDASettings:
    """Загружает настройки из config.yaml (кэшируется)"""
    global _cached_settings
    
    if _cached_settings is not None:
        return _cached_settings
    
    try:
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            
            # Извлекаем только DDA-специфичные секции
            dda_data = {
                "anomaly_detection": data.get("anomaly_detection", {}),
                "correlations": data.get("correlations", {}),
                "visualization": data.get("visualization", {}),
                "colors": data.get("colors", {}),
            }
            
            _cached_settings = DDASettings(**dda_data)
            log.info("DDA settings loaded", path=str(CONFIG_PATH))
        else:
            log.warning("DDA config not found, using defaults", path=str(CONFIG_PATH))
            _cached_settings = DDASettings()
    
    except Exception as e:
        log.error("Failed to load DDA settings", error=str(e))
        _cached_settings = DDASettings()
    
    return _cached_settings


def reload_dda_settings() -> DDASettings:
    """Перезагружает настройки (сбрасывает кэш)"""
    global _cached_settings
    _cached_settings = None
    return load_dda_settings()


def save_dda_settings(settings: DDASettings) -> None:
    """Сохраняет настройки в config.yaml"""
    global _cached_settings
    
    # Читаем оригинал чтобы сохранить метаданные модуля
    original = {}
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            original = yaml.safe_load(f) or {}
    
    # Обновляем DDA-секции
    original["anomaly_detection"] = settings.anomaly_detection.model_dump()
    original["correlations"] = settings.correlations.model_dump()
    original["visualization"] = settings.visualization.model_dump()
    original["colors"] = settings.colors.model_dump()
    
    # Записываем обратно
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(original, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
    
    # Сбрасываем кэш
    _cached_settings = settings
    
    log.info("DDA settings saved", path=str(CONFIG_PATH))
