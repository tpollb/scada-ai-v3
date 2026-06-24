#!/usr/bin/env python3
"""
fix_add_dda_endpoints.py — добавляем endpoints DDA настроек в config.py
"""
from pathlib import Path
import re

print('=' * 80)
print('ТОЧЕЧНЫЙ ФИКС: Добавляем DDA endpoints в config.py')
print('=' * 80)
print()

config_path = Path('backend/api/routes/config.py')
content = config_path.read_text(encoding='utf-8')

# Проверяем наличие endpoints
if '@router.get("/modules/deep_analysis/settings")' in content:
    print('ℹ️  Endpoints уже есть в config.py')
    print()
    print('Возможные причины 404:')
    print('  1. Backend не перезапущен после изменений')
    print('  2. Backend упал при старте (проверь логи uvicorn)')
    print('  3. Импорт settings.py не работает')
    print()
    print('Проверь:')
    print('  • Логи uvicorn (есть ли ошибка при старте?)')
    print('  • Python import: cd backend && python -c "from modules.deep_analysis.settings import load_dda_settings; print(load_dda_settings())"')
    exit(0)

# Добавляем HTTPException если его нет
if 'HTTPException' not in content:
    content = content.replace(
        'from fastapi import APIRouter',
        'from fastapi import APIRouter, HTTPException'
    )
    print('✅ Добавлен импорт HTTPException')

# Endpoints для DDA настроек
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
        
        # Валидируем через Pydantic
        dda_settings = DDASettings(**settings)
        
        # Сохраняем в config.yaml
        save_dda_settings(dda_settings)
        
        log.info("DDA settings updated")
        
        return {
            "status": "ok",
            "message": "Настройки DDA сохранены. Изменения применятся при следующем анализе.",
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

# Добавляем в конец файла
content += dda_endpoints
config_path.write_text(content, encoding='utf-8', newline='\n')

print('✅ Endpoints добавлены в config.py:')
print('   • GET /config/modules/deep_analysis/settings')
print('   • PUT /config/modules/deep_analysis/settings')
print('   • POST /config/modules/deep_analysis/settings/reset')

# Проверяем что settings.py существует
settings_path = Path('backend/modules/deep_analysis/settings.py')
if settings_path.exists():
    print()
    print('✅ settings.py существует')
    
    # Проверяем импорт
    try:
        import sys
        sys.path.insert(0, 'backend')
        from modules.deep_analysis.settings import load_dda_settings, DDASettings
        settings = load_dda_settings()
        print(f'✅ Импорт работает, загружено {len(settings.anomaly_detection.model_dump())} параметров anomaly_detection')
    except Exception as e:
        print(f'❌ Ошибка импорта: {e}')
else:
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
    contamination: float = Field(0.06, ge=0.01, le=0.20)
    n_estimators: int = Field(100, ge=10, le=500)
    spike_threshold: float = Field(2.0, ge=1.0, le=5.0)
    dip_threshold: float = Field(2.0, ge=1.0, le=5.0)
    drift_min_duration: int = Field(3, ge=2, le=20)
    drift_min_r_squared: float = Field(0.4, ge=0.1, le=0.95)
    drift_min_relative_change: float = Field(0.03, ge=0.01, le=0.20)
    plateau_tolerance: float = Field(0.02, ge=0.001, le=0.10)
    local_window: int = Field(24, ge=5, le=100)
    significant_dip_ratio: float = Field(0.30, ge=0.10, le=0.80)
    zero_threshold_ratio: float = Field(0.05, ge=0.01, le=0.20)


class CorrelationsSettings(BaseModel):
    resample_freq: str = Field("5min")
    pearson_threshold: float = Field(0.3, ge=0.1, le=0.9)
    max_lag: int = Field(50, ge=10, le=200)


class VisualizationSettings(BaseModel):
    max_points: int = Field(1500, ge=200, le=5000)
    anomaly_point_radius: int = Field(6, ge=2, le=15)
    drift_line_width: int = Field(2, ge=1, le=5)


class ColorsSettings(BaseModel):
    spike: str = Field("#ef4444")
    dip: str = Field("#3b82f6")
    drift: str = Field("#f59e0b")
    noise: str = Field("#9ca3af")


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

print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Перезапусти backend (Ctrl+C и снова uvicorn ...)')
print()
print('2. Проверь импорт:')
print('   cd backend && python -c "from modules.deep_analysis.settings import load_dda_settings; s=load_dda_settings(); print(s.anomaly_detection.contamination)"')
print()
print('3. Проверь endpoint:')
print('   curl -s http://localhost:8081/api/v1/config/modules/deep_analysis/settings | python -m json.tool')
print()
print('Ожидаемый результат:')
print('  {')
print('    "anomaly_detection": {')
print('      "contamination": 0.06,')
print('      "spike_threshold": 2.0,')
print('      ...')
print('    },')
print('    ...')
print('  }')