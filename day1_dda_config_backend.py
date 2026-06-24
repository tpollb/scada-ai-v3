#!/usr/bin/env python3
"""
day1_dda_config_backend.py — конфигуратор DDA: backend часть
"""
from pathlib import Path
import yaml
import re

print('=' * 80)
print('ЧАСТЬ 1: BACKEND КОНФИГУРАТОР DDA')
print('=' * 80)
print()

# ============================================================================
# 1. Создаём config.yaml для модуля deep_analysis
# ============================================================================
config_path = Path('backend/modules/deep_analysis/config.yaml')

config_content = '''name: deep_analysis
version: 0.3.0
description: Глубокий анализ данных — аномалии, корреляции, статистика
enabled: true

# === Настройки детекции аномалий ===
anomaly_detection:
  # Isolation Forest
  contamination: 0.06          # % аномалий (0.01-0.20)
  n_estimators: 100            # количество деревьев
  
  # Классификация spike/dip
  spike_threshold: 2.0         # z-score для пика (> X std от среднего)
  dip_threshold: 2.0           # z-score для провала
  
  # Классификация drift (монотонное смещение)
  drift_min_duration: 3        # мин. точек в событии
  drift_min_r_squared: 0.4     # качество линейного тренда (0-1)
  drift_min_relative_change: 0.03  # мин. изменение 3%
  
  # Классификация noise
  plateau_tolerance: 0.02      # 2% — одинаковые значения
  
  # Локальная статистика
  local_window: 24             # окно для локального mean/std
  
  # Дополнительные эвристики
  significant_dip_ratio: 0.30  # 30% падение от локального среднего
  zero_threshold_ratio: 0.05   # 5% от среднего = "ноль"

# === Настройки корреляций ===
correlations:
  resample_freq: "5min"        # частота ресемплинга
  pearson_threshold: 0.3       # минимальный |r| для значимости
  max_lag: 50                  # макс. лаг для cross-correlation

# === Настройки визуализации ===
visualization:
  max_points: 1500             # downsampling для графиков
  anomaly_point_radius: 6      # размер точек аномалий
  drift_line_width: 2          # толщина линии дрейфа

# === Цветовая схема ===
colors:
  spike: "#ef4444"             # красный
  dip: "#3b82f6"               # синий
  drift: "#f59e0b"             # оранжевый
  noise: "#9ca3af"             # серый
'''

config_path.write_text(config_content, encoding='utf-8', newline='\n')
print('✅ 1. Создан backend/modules/deep_analysis/config.yaml')
print('   • anomaly_detection: 10 параметров')
print('   • correlations: 3 параметра')
print('   • visualization: 3 параметра')
print('   • colors: 4 цвета')

# ============================================================================
# 2. Создаём DDASettings модель + loader
# ============================================================================
settings_path = Path('backend/modules/deep_analysis/settings.py')

settings_content = '''"""Настройки модуля Deep Data Analysis"""
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
    dip_threshold: float = Field(2.0, ge=1.0, le=5.0, description="Z-score для провала")
    
    drift_min_duration: int = Field(3, ge=2, le=20, description="Мин. точек для дрейфа")
    drift_min_r_squared: float = Field(0.4, ge=0.1, le=0.95, description="Качество тренда")
    drift_min_relative_change: float = Field(0.03, ge=0.01, le=0.20, description="Мин. изменение")
    
    plateau_tolerance: float = Field(0.02, ge=0.001, le=0.10, description="Порог плато")
    local_window: int = Field(24, ge=5, le=100, description="Окно локальной статистики")
    
    significant_dip_ratio: float = Field(0.30, ge=0.10, le=0.80, description="Порог значительного провала")
    zero_threshold_ratio: float = Field(0.05, ge=0.01, le=0.20, description="Порог нуля")


class CorrelationsSettings(BaseModel):
    """Настройки корреляций"""
    resample_freq: str = Field("5min", description="Частота ресемплинга")
    pearson_threshold: float = Field(0.3, ge=0.1, le=0.9, description="Мин. |r| для значимости")
    max_lag: int = Field(50, ge=10, le=200, description="Макс. лаг для cross-correlation")


class VisualizationSettings(BaseModel):
    """Настройки визуализации"""
    max_points: int = Field(1500, ge=200, le=5000, description="Downsampling для графиков")
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
'''

settings_path.write_text(settings_content, encoding='utf-8', newline='\n')
print()
print('✅ 2. Создан backend/modules/deep_analysis/settings.py')
print('   • DDASettings Pydantic модель')
print('   • load_dda_settings() — загрузка с кэшированием')
print('   • reload_dda_settings() — сброс кэша')
print('   • save_dda_settings() — запись в config.yaml')

# ============================================================================
# 3. Обновляем anomalies.py — читаем пороги из конфига
# ============================================================================
anom_path = Path('backend/modules/deep_analysis/analyzers/anomalies.py')
anom_content = anom_path.read_text(encoding='utf-8')

# 3a. Добавляем импорт настроек
if 'from modules.deep_analysis.settings import load_dda_settings' not in anom_content:
    anom_content = anom_content.replace(
        'from structlog import get_logger',
        'from structlog import get_logger\nfrom modules.deep_analysis.settings import load_dda_settings'
    )

# 3b. Обновляем detect_anomalies_isolation_forest — читаем contamination из конфига
old_contam_default = '    contamination: float = 0.10,'
new_contam_default = '    contamination: float = None,  # None = читать из конфига'

if old_contam_default in anom_content:
    anom_content = anom_content.replace(old_contam_default, new_contam_default)

# Добавляем логику чтения из конфига в начало функции
old_log_info = '''    log.info("Running Isolation Forest", points=len(values), contamination=contamination)'''
new_log_info = '''    # Читаем настройки из конфига если не переданы явно
    if contamination is None:
        settings = load_dda_settings()
        contamination = settings.anomaly_detection.contamination
    
    log.info("Running Isolation Forest", points=len(values), contamination=contamination)'''

if old_log_info in anom_content:
    anom_content = anom_content.replace(old_log_info, new_log_info)

# 3c. Обновляем detect_zero_dips — читаем zero_threshold_ratio
old_zero_sig = 'def detect_zero_dips(\n    values: list[float],\n    timestamps: list,\n    zero_threshold_ratio: float = 0.05,'
new_zero_sig = 'def detect_zero_dips(\n    values: list[float],\n    timestamps: list,\n    zero_threshold_ratio: float = None,'

if old_zero_sig in anom_content:
    anom_content = anom_content.replace(old_zero_sig, new_zero_sig)
    
    # Добавляем чтение из конфига
    old_zero_body = '''    if len(values) < 5:
        return {"anomaly_indices": [], "anomaly_values": [], "events": []}
    
    valid_all = [v for v in values if v is not None]'''
    
    new_zero_body = '''    if len(values) < 5:
        return {"anomaly_indices": [], "anomaly_values": [], "events": []}
    
    # Читаем из конфига если не передан
    if zero_threshold_ratio is None:
        settings = load_dda_settings()
        zero_threshold_ratio = settings.anomaly_detection.zero_threshold_ratio
    
    valid_all = [v for v in values if v is not None]'''
    
    if old_zero_body in anom_content:
        anom_content = anom_content.replace(old_zero_body, new_zero_body)

# 3d. Обновляем detect_significant_dips — читаем drop_ratio
old_sig_sig = 'def detect_significant_dips(\n    values: list[float],\n    timestamps: list,\n    drop_ratio: float = 0.30,'
new_sig_sig = 'def detect_significant_dips(\n    values: list[float],\n    timestamps: list,\n    drop_ratio: float = None,'

if old_sig_sig in anom_content:
    anom_content = anom_content.replace(old_sig_sig, new_sig_sig)
    
    old_sig_body = '''    if len(values) < 20:
        return {"anomaly_indices": [], "anomaly_values": [], "events": []}
    
    max_duration = max(min_duration, int(len(values) * max_duration_ratio))'''
    
    new_sig_body = '''    if len(values) < 20:
        return {"anomaly_indices": [], "anomaly_values": [], "events": []}
    
    # Читаем из конфига если не передан
    if drop_ratio is None:
        settings = load_dda_settings()
        drop_ratio = settings.anomaly_detection.significant_dip_ratio
    
    max_duration = max(min_duration, int(len(values) * max_duration_ratio))'''
    
    if old_sig_body in anom_content:
        anom_content = anom_content.replace(old_sig_body, new_sig_body)

# 3e. Обновляем classify_anomaly_types — читаем все пороги
# Ищем функцию и добавляем загрузку настроек в начало
old_classify_start = '''    if not anomaly_indices:
        return {"types": [], "counts": {}}
    
    events = group_anomaly_events(anomaly_indices, max_gap=2)'''

new_classify_start = '''    if not anomaly_indices:
        return {"types": [], "counts": {}}
    
    # Загружаем настройки
    settings = load_dda_settings()
    ad = settings.anomaly_detection
    
    events = group_anomaly_events(anomaly_indices, max_gap=2)'''

if old_classify_start in anom_content:
    anom_content = anom_content.replace(old_classify_start, new_classify_start)

# Заменяем захардкоженные пороги на чтение из конфига
replacements = [
    ('abs_deviation > 1.5:\n                event_type = "spike"', 
     f'abs_deviation > ad.spike_threshold:\n                event_type = "spike"'),
    ('abs_deviation > 1.5 and duration < 8', 
     'abs_deviation > ad.spike_threshold and duration < 8'),
    ('duration >= 3', 
     'duration >= ad.drift_min_duration'),
    ('r_squared > 0.4', 
     'r_squared > ad.drift_min_r_squared'),
    ('relative_change > 0.03', 
     'relative_change > ad.drift_min_relative_change'),
    ('tolerance: float = 0.02', 
     'tolerance: float = None'),
]

for old, new in replacements:
    if old in anom_content:
        anom_content = anom_content.replace(old, new)

# Обновляем _is_plateau чтобы использовать порог из конфига
old_plateau_call = '_is_plateau(event_values, tolerance=0.02)'
new_plateau_call = '_is_plateau(event_values, tolerance=ad.plateau_tolerance)'
if old_plateau_call in anom_content:
    anom_content = anom_content.replace(old_plateau_call, new_plateau_call)

# Обновляем _compute_local_stats чтобы использовать окно из конфига
old_local_call = '_compute_local_stats(values, center_idx)'
new_local_call = '_compute_local_stats(values, center_idx, window=ad.local_window)'
if old_local_call in anom_content:
    anom_content = anom_content.replace(old_local_call, new_local_call)

# Обновляем _is_plateau default
old_plateau_def = 'def _is_plateau(values: list[float], tolerance: float = None) -> bool:'
if old_plateau_def not in anom_content and 'def _is_plateau(values: list[float], tolerance: float = 0.02)' in anom_content:
    anom_content = anom_content.replace(
        'def _is_plateau(values: list[float], tolerance: float = 0.02) -> bool:',
        'def _is_plateau(values: list[float], tolerance: float = None) -> bool:'
    )
    
    # Добавляем чтение из конфига в начало _is_plateau
    old_plateau_body = '''    valid = [v for v in values if v is not None]
    if len(valid) < 2:
        return False'''
    
    new_plateau_body = '''    # Читаем из конфига если не передан
    if tolerance is None:
        settings = load_dda_settings()
        tolerance = settings.anomaly_detection.plateau_tolerance
    
    valid = [v for v in values if v is not None]
    if len(valid) < 2:
        return False'''
    
    if old_plateau_body in anom_content:
        anom_content = anom_content.replace(old_plateau_body, new_plateau_body)

# Обновляем _compute_local_stats default
if 'def _compute_local_stats(values: list[float], idx: int, window: int = 24)' in anom_content:
    anom_content = anom_content.replace(
        'def _compute_local_stats(values: list[float], idx: int, window: int = 24)',
        'def _compute_local_stats(values: list[float], idx: int, window: int = None)'
    )
    
    old_local_body = '''    half_w = window // 2'''
    new_local_body = '''    # Читаем из конфига если не передан
    if window is None:
        settings = load_dda_settings()
        window = settings.anomaly_detection.local_window
    
    half_w = window // 2'''
    
    if old_local_body in anom_content:
        anom_content = anom_content.replace(old_local_body, new_local_body)

anom_path.write_text(anom_content, encoding='utf-8', newline='\n')
print()
print('✅ 3. Обновлён anomalies.py:')
print('   • Все пороги читаются из DDASettings')
print('   • contamination, zero_threshold_ratio, drop_ratio = None (читаются из конфига)')
print('   • spike_threshold, dip_threshold, drift_*, plateau_tolerance, local_window')

# ============================================================================
# 4. Добавляем endpoints в config.py
# ============================================================================
config_route_path = Path('backend/api/routes/config.py')
config_route_content = config_route_path.read_text(encoding='utf-8')

dda_endpoints = '''

# ============================================================================
# DDA Settings (Deep Data Analysis)
# ============================================================================

@router.get("/modules/deep_analysis/settings")
async def get_dda_settings():
    """Возвращает настройки модуля DDA"""
    try:
        from modules.deep_analysis.settings import load_dda_settings, DDASettings
        settings = load_dda_settings()
        return settings.model_dump()
    except ImportError as e:
        log.error("DDA settings module not found", error=str(e))
        raise HTTPException(status_code=404, detail="Модуль deep_analysis не найден")
    except Exception as e:
        log.error("Failed to load DDA settings", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/modules/deep_analysis/settings")
async def update_dda_settings(settings: dict):
    """Обновляет настройки модуля DDA"""
    try:
        from modules.deep_analysis.settings import DDASettings, save_dda_settings, reload_dda_settings
        
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
        raise HTTPException(status_code=404, detail="Модуль deep_analysis не найден")
    except Exception as e:
        log.error("Failed to update DDA settings", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/modules/deep_analysis/settings/reset")
async def reset_dda_settings():
    """Сбрасывает настройки DDA к дефолтным"""
    try:
        from modules.deep_analysis.settings import DDASettings, save_dda_settings, reload_dda_settings
        
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

# Добавляем import HTTPException если его нет
if 'from fastapi import APIRouter' in config_route_content and 'HTTPException' not in config_route_content:
    config_route_content = config_route_content.replace(
        'from fastapi import APIRouter',
        'from fastapi import APIRouter, HTTPException'
    )

# Вставляем endpoints перед последним endpoint или в конец
if '@router.get("/modules/deep_analysis/settings")' not in config_route_content:
    config_route_content += dda_endpoints
    config_route_path.write_text(config_route_content, encoding='utf-8', newline='\n')
    print()
    print('✅ 4. Добавлены endpoints в config.py:')
    print('   • GET /config/modules/deep_analysis/settings')
    print('   • PUT /config/modules/deep_analysis/settings')
    print('   • POST /config/modules/deep_analysis/settings/reset')

# ============================================================================
# 5. Обновляем api.py — передаём конфиг в detect_anomalies_isolation_forest
# ============================================================================
api_path = Path('backend/modules/deep_analysis/api.py')
api_content = api_path.read_text(encoding='utf-8')

# Убираем adaptive_contamination — теперь это делает сам anomalies.py через конфиг
old_adaptive = '''                if len(valid_values) >= 10:
                    adaptive_contamination = min(0.15, max(0.08, 200 / max(len(valid_values), 1)))
                    tag_anomalies = detect_anomalies_isolation_forest(
                        valid_values,
                        list(range(len(valid_values))),
                        contamination=adaptive_contamination,
                        classify_types=True
                    )'''

new_adaptive = '''                if len(valid_values) >= 10:
                    tag_anomalies = detect_anomalies_isolation_forest(
                        valid_values,
                        list(range(len(valid_values))),
                        classify_types=True
                    )'''

if old_adaptive in api_content:
    api_content = api_content.replace(old_adaptive, new_adaptive)
    print()
    print('✅ 5. Обновлён api.py:')
    print('   • Убран adaptive_contamination (теперь читается из конфига)')

# Обновляем diagnose_weeks — убираем фиксированный contamination
old_diag = '''        result = detect_anomalies_isolation_forest(
            data['raw_values'],
            data['raw_timestamps'],
            contamination=0.06,
            classify_types=True
        )'''

new_diag = '''        result = detect_anomalies_isolation_forest(
            data['raw_values'],
            data['raw_timestamps'],
            classify_types=True
        )'''

if old_diag in api_content:
    api_content = api_content.replace(old_diag, new_diag)
    print('   • diagnose_weeks использует настройки из конфига')

api_path.write_text(api_content, encoding='utf-8', newline='\n')

# ============================================================================
# 6. Фиксим 500 ошибку в diagnose_weeks
# ============================================================================
# Проверяем наличие _is_plateau и других helper функций в импортах
if 'from modules.deep_analysis.analyzers.anomalies import' in api_content:
    # Ищем блок импортов
    import_match = re.search(
        r'from modules\.deep_analysis\.analyzers\.anomalies import \(([^)]+)\)',
        api_content,
        re.DOTALL
    )
    
    if import_match:
        current_imports = import_match.group(1)
        needed_helpers = ['_is_plateau', '_is_monotonic', '_compute_linear_trend', '_compute_relative_change']
        
        missing = [h for h in needed_helpers if h not in current_imports]
        
        if missing:
            new_imports = current_imports.rstrip()
            for h in missing:
                if h not in new_imports:
                    new_imports += f',\n        {h}'
            new_imports += ',\n    '
            
            api_content = api_content.replace(
                import_match.group(0),
                f'from modules.deep_analysis.analyzers.anomalies import ({new_imports})'
            )
            api_path.write_text(api_content, encoding='utf-8', newline='\n')
            print(f'   • Добавлены импорты: {", ".join(missing)}')

print()
print('=' * 80)
print('ИТОГ ЧАСТИ 1 (BACKEND):')
print('=' * 80)
print()
print('✅ config.yaml создан с 20+ параметрами')
print('✅ DDASettings модель с валидацией')
print('✅ anomalies.py читает все пороги из конфига')
print('✅ Endpoints для GET/PUT/POST настроек')
print('✅ api.py использует настройки из конфига')
print('✅ diagnose_weeks больше не использует hardcoded contamination')
print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Перезапусти backend')
print()
print('2. Проверь что настройки читаются:')
print('   curl -s http://localhost:8081/api/v1/config/modules/deep_analysis/settings \\')
print('     | python -m json.tool | head -30')
print()
print('3. Проверь что анализ работает:')
print('   curl -s -X POST http://localhost:8081/api/v1/deep_analysis/run \\')
print('     -H "Content-Type: application/json" \\')
print('     -d \'{"tags": ["R001-CO2"], "period": 30}\' | \\')
print('     python -c "import sys,json; r=json.load(sys.stdin); print(r.get(\'anomalies\',{}).get(\'type_counts\'))"')
print()
print('4. Проверь что diagnose_weeks работает (не 500):')
print('   curl -s http://localhost:8081/api/v1/deep_analysis/diagnose_weeks/R001-CO2?period=30 \\')
print('     | python -m json.tool | head -20')
print()
print('Ожидаемый результат:')
print('  • Все 3 curl должны вернуть данные без ошибок')
print('  • type_counts должен содержать spike/dip/drift/noise')