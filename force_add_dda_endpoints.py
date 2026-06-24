#!/usr/bin/env python3
"""
force_add_dda_endpoints.py — принудительное добавление endpoints DDA настроек
"""
from pathlib import Path

print('=' * 80)
print('ПРИНУДИТЕЛЬНОЕ ДОБАВЛЕНИЕ DDA ENDPOINTS')
print('=' * 80)
print()

config_path = Path('backend/api/routes/config.py')
content = config_path.read_text(encoding='utf-8')

# 1. Проверяем есть ли endpoints
if '@router.get("/modules/deep_analysis/settings")' in content:
    print('ℹ️  Endpoints уже есть в файле')
    print('   Возможно backend не был перезапущен или endpoint сломан.')
    print()
else:
    print('❌ Endpoints НЕ найдены в файле!')
    print('   Добавляю принудительно...')
    print()

# 2. Добавляем HTTPException если его нет
if 'HTTPException' not in content:
    content = content.replace(
        'from fastapi import APIRouter',
        'from fastapi import APIRouter, HTTPException'
    )
    print('✅ Добавлен импорт HTTPException')

# 3. Endpoints для DDA
dda_endpoints = '''

# ============================================================================
# DDA Settings (Deep Data Analysis module)
# ============================================================================

@router.get("/modules/deep_analysis/settings")
async def get_dda_settings():
    """Возвращает настройки модуля DDA"""
    try:
        from modules.deep_analysis.settings import load_dda_settings
        settings = load_dda_settings()
        return settings.model_dump()
    except ImportError as e:
        log.error("DDA settings module not found", error=str(e))
        raise HTTPException(status_code=404, detail=f"Модуль deep_analysis не найден: {e}")
    except Exception as e:
        log.error("Failed to load DDA settings", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/modules/deep_analysis/settings")
async def update_dda_settings(settings: dict):
    """Обновляет настройки модуля DDA"""
    try:
        from modules.deep_analysis.settings import DDASettings, save_dda_settings
        
        dda_settings = DDASettings(**settings)
        save_dda_settings(dda_settings)
        
        log.info("DDA settings updated")
        
        return {
            "status": "ok",
            "message": "Настройки DDA сохранены",
            "settings": dda_settings.model_dump()
        }
    except ImportError as e:
        log.error("DDA settings module not found", error=str(e))
        raise HTTPException(status_code=404, detail=f"Модуль deep_analysis не найден: {e}")
    except Exception as e:
        log.error("Failed to update DDA settings", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/modules/deep_analysis/settings/reset")
async def reset_dda_settings():
    """Сбрасывает настройки DDA к дефолтным"""
    try:
        from modules.deep_analysis.settings import DDASettings, save_dda_settings
        
        default_settings = DDASettings()
        save_dda_settings(default_settings)
        
        log.info("DDA settings reset to defaults")
        
        return {
            "status": "ok",
            "message": "Настройки DDA сброшены к значениям по умолчанию",
            "settings": default_settings.model_dump()
        }
    except Exception as e:
        log.error("Failed to reset DDA settings", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

'''

# 4. Добавляем endpoints в конец файла (если их ещё нет)
if '@router.get("/modules/deep_analysis/settings")' not in content:
    content += dda_endpoints
    config_path.write_text(content, encoding='utf-8', newline='\n')
    print('✅ Endpoints добавлены в конец config.py')
else:
    print('ℹ️  Endpoints уже есть')

# 5. Проверяем что settings.py существует
settings_path = Path('backend/modules/deep_analysis/settings.py')
if not settings_path.exists():
    print()
    print('❌ settings.py НЕ существует! Создаю...')
    
    settings_content = '''"""Настройки модуля Deep Data Analysis"""
from pathlib import Path
from typing import Any
import yaml
from pydantic import BaseModel, Field
from structlog import get_logger

log = get_logger()

CONFIG_PATH = Path(__file__).parent / "config.yaml"


class AnomalyDetectionSettings(BaseModel):
    contamination: float = Field(0.06, ge=0.01, le=0.20, description="% аномалий в Isolation Forest")
    n_estimators: int = Field(100, ge=10, le=500, description="Количество деревьев")
    spike_threshold: float = Field(2.0, ge=1.0, le=5.0, description="Z-score для пика")
    dip_threshold: float = Field(2.0, ge=1.0, le=5.0, description="Z-score для провала")
    drift_min_duration: int = Field(3, ge=2, le=20, description="Мин. точек для дрейфа")
    drift_min_r_squared: float = Field(0.4, ge=0.1, le=0.95, description="Качество тренда")
    drift_min_relative_change: float = Field(0.03, ge=0.01, le=0.20, description="Мин. изменение")
    plateau_tolerance: float = Field(0.02, ge=0.001, le=0.10, description="Порог плато")
    local_window: int = Field(24, ge=5, le=100, description="Окно локальной статистики")
    significant_dip_ratio: float = Field(0.30, ge=0.10, le=0.80, description="Порог значительного провала")
    zero_threshold_ratio: float = Field(0.05, ge=0.01, le=0.20, description="Порог нуля")


class CorrelationsSettings(BaseModel):
    resample_freq: str = Field("5min", description="Частота ресемплинга")
    pearson_threshold: float = Field(0.3, ge=0.1, le=0.9, description="Мин. |r| для значимости")
    max_lag: int = Field(50, ge=10, le=200, description="Макс. лаг для cross-correlation")


class VisualizationSettings(BaseModel):
    max_points: int = Field(1500, ge=200, le=5000, description="Downsampling для графиков")
    anomaly_point_radius: int = Field(6, ge=2, le=15, description="Размер точек аномалий")
    drift_line_width: int = Field(2, ge=1, le=5, description="Толщина линии дрейфа")


class ColorsSettings(BaseModel):
    spike: str = Field("#ef4444", description="Цвет пиков")
    dip: str = Field("#3b82f6", description="Цвет провалов")
    drift: str = Field("#f59e0b", description="Цвет дрейфов")
    noise: str = Field("#9ca3af", description="Цвет шума")


class DDASettings(BaseModel):
    anomaly_detection: AnomalyDetectionSettings = Field(default_factory=AnomalyDetectionSettings)
    correlations: CorrelationsSettings = Field(default_factory=CorrelationsSettings)
    visualization: VisualizationSettings = Field(default_factory=VisualizationSettings)
    colors: ColorsSettings = Field(default_factory=ColorsSettings)


_cached_settings: DDASettings | None = None


def load_dda_settings() -> DDASettings:
    global _cached_settings
    if _cached_settings is not None:
        return _cached_settings
    
    try:
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            
            dda_data = {
                "anomaly_detection": data.get("anomaly_detection", {}),
                "correlations": data.get("correlations", {}),
                "visualization": data.get("visualization", {}),
                "colors": data.get("colors", {}),
            }
            
            _cached_settings = DDASettings(**dda_data)
            log.info("DDA settings loaded")
        else:
            log.warning("DDA config not found, using defaults")
            _cached_settings = DDASettings()
    except Exception as e:
        log.error("Failed to load DDA settings", error=str(e))
        _cached_settings = DDASettings()
    
    return _cached_settings


def save_dda_settings(settings: DDASettings) -> None:
    global _cached_settings
    
    original = {}
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            original = yaml.safe_load(f) or {}
    
    original["anomaly_detection"] = settings.anomaly_detection.model_dump()
    original["correlations"] = settings.correlations.model_dump()
    original["visualization"] = settings.visualization.model_dump()
    original["colors"] = settings.colors.model_dump()
    
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(original, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
    
    _cached_settings = settings
    log.info("DDA settings saved")
'''
    
    settings_path.write_text(settings_content, encoding='utf-8', newline='\n')
    print('✅ settings.py создан')

# 6. Проверяем импорт
print()
print('=' * 80)
print('ПРОВЕРКА ИМПОРТА:')
print('=' * 80)
print()

import sys
sys.path.insert(0, 'backend')

try:
    from modules.deep_analysis.settings import load_dda_settings, DDASettings
    settings = load_dda_settings()
    print(f'✅ Импорт работает')
    print(f'   contamination: {settings.anomaly_detection.contamination}')
    print(f'   spike_threshold: {settings.anomaly_detection.spike_threshold}')
    print(f'   drift_min_r_squared: {settings.anomaly_detection.drift_min_r_squared}')
except Exception as e:
    print(f'❌ Ошибка импорта: {e}')

print()
print('=' * 80)
print('ПРОВЕРКА ENDPOINTS В ФАЙЛЕ:')
print('=' * 80)
print()

# Проверяем наличие endpoints в файле
final_content = config_path.read_text(encoding='utf-8')
checks = [
    ('GET endpoint', '@router.get("/modules/deep_analysis/settings")'),
    ('PUT endpoint', '@router.put("/modules/deep_analysis/settings")'),
    ('POST reset endpoint', '@router.post("/modules/deep_analysis/settings/reset")'),
    ('HTTPException import', 'HTTPException'),
]

for name, pattern in checks:
    status = '✅' if pattern in final_content else '❌'
    print(f'  {status} {name}')

print()
print('=' * 80)
print('СЛЕДУЮЩИЕ ШАГИ:')
print('=' * 80)
print()
print('1. Перезапусти backend (Ctrl+C и снова uvicorn ...)')
print()
print('2. Проверь что endpoints зарегистрированы:')
print('   curl -s http://localhost:8081/api/v1/config/modules/deep_analysis/settings \\')
print('     | python -m json.tool')
print()
print('3. Если всё ещё 404 — проверь логи uvicorn:')
print('   • Есть ли ошибка при старте?')
print('   • Не падает ли импорт settings.py?')