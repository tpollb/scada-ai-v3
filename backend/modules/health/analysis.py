"""Детерминированный анализ — композитная формула + индекс жизнеобеспечения"""
from dataclasses import dataclass, field
from structlog import get_logger

log = get_logger()


@dataclass
class HealthReport:
    score: int
    status: str
    summary: str
    issues: list[dict] = field(default_factory=list)
    stats: dict = field(default_factory=dict)
    environmental: dict = field(default_factory=dict)
    equipment: dict = field(default_factory=dict)
    alarms: dict = field(default_factory=dict)
    energy: dict = field(default_factory=dict)
    recommendations: list[dict] = field(default_factory=list)
    sub_scores: dict = field(default_factory=dict)
    life_support: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "score": self.score, "status": self.status, "summary": self.summary,
            "issues": self.issues, "stats": self.stats,
            "environmental": self.environmental, "equipment": self.equipment,
            "alarms": self.alarms, "energy": self.energy,
            "recommendations": self.recommendations,
            "sub_scores": self.sub_scores,
            "life_support": self.life_support,
        }


def _compute_alarm_index(by_priority: dict) -> tuple:
    score = 100
    issues = []
    high = by_priority.get("high", 0) or 0
    medium = by_priority.get("medium", 0) or 0
    low = by_priority.get("low", 0) or 0
    
    if high > 0:
        penalty = min(high * 15, 50)
        score -= penalty
        issues.append(f"High аварии: {high} шт. (-{penalty})")
    if medium > 0:
        penalty = min(medium * 4, 25)
        score -= penalty
        issues.append(f"Medium аварии: {medium} шт. (-{penalty})")
    if low > 0:
        penalty = min(int(low * 0.5), 10)
        score -= penalty
        if low > 10:
            issues.append(f"Low аварии: {low} шт. (-{penalty})")
    
    return max(0, score), issues


def _compute_equipment_index(equipment: dict, broken_sensors: int) -> tuple:
    score = 100
    issues = []
    offline = equipment.get("offline", 0) or 0
    chattering = equipment.get("chattering", 0) or 0
    stuck = equipment.get("stuck", 0) or 0
    total = equipment.get("total_tags", 0) or 1
    
    if broken_sensors > 0:
        broken_pct = broken_sensors / total if total > 0 else 0
        penalty = min(int(broken_pct * 200), 40)
        penalty = max(penalty, min(broken_sensors * 5, 40))
        score -= penalty
        issues.append(f"Битые датчики: {broken_sensors} шт. (-{penalty})")
    if offline > 0:
        offline_pct = offline / total if total > 0 else 0
        penalty = min(int(offline_pct * 150), 30)
        penalty = max(penalty, min(offline * 2, 30))
        score -= penalty
        issues.append(f"Офлайн теги: {offline} шт. (-{penalty})")
    if chattering > 0:
        penalty = min(chattering * 2, 15)
        score -= penalty
        issues.append(f"Дребезжащие: {chattering} шт. (-{penalty})")
    if stuck > 0:
        penalty = min(stuck, 10)
        score -= penalty
        if stuck > 5:
            issues.append(f"Залипшие: {stuck} шт. (-{penalty})")
    
    return max(0, score), issues


def _compute_environmental_index(env: dict) -> tuple:
    weights = {
        "co2": 0.30,
        "temperature": 0.25,
        "humidity": 0.15,
        "voc": 0.20,
        "pressure": 0.10,
    }
    status_scores = {"OK": 100, "WARNING": 55, "CRITICAL": 15}
    total_weight = 0
    weighted_sum = 0
    issues = []
    
    for param_key, weight in weights.items():
        p = env.get(param_key)
        if not isinstance(p, dict):
            continue
        status = p.get("status", "OK")
        s = status_scores.get(status, 70)
        weighted_sum += s * weight
        total_weight += weight
        
        if status == "CRITICAL":
            issues.append(f"{param_key.upper()}: критическое отклонение (-{int((100-s) * weight)})")
        elif status == "WARNING":
            issues.append(f"{param_key}: отклонение от нормы (-{int((100-s) * weight)})")
    
    if total_weight == 0:
        return 70, ["Нет данных о параметрах среды"]
    
    score = int(weighted_sum / total_weight)
    return max(0, min(100, score)), issues


def _compute_energy_index(energy: dict) -> tuple:
    if not energy or energy.get("status") in ("NO_DATA", None):
        return 75, ["Нет данных об энергоэффективности"]
    
    status = energy.get("status", "GOOD")
    status_scores = {"EXCELLENT": 95, "GOOD": 80, "WARNING": 45, "CRITICAL": 15}
    score = status_scores.get(status, 70)
    issues = []
    if status == "WARNING":
        issues.append(f"Неэффективное освещение (-{100-score})")
    elif status == "CRITICAL":
        issues.append(f"Критическая неэффективность (-{100-score})")
    return score, issues


def _compute_life_support_index(env: dict) -> dict:
    """Отдельный индекс жизнеобеспечения — ВСЕГДА возвращает данные"""
    weights = {
        "co2": 0.30,
        "temperature": 0.25,
        "voc": 0.20,
        "humidity": 0.15,
        "pressure": 0.10,
    }
    status_scores = {"OK": 100, "WARNING": 55, "CRITICAL": 15}
    
    total_weight = 0
    weighted_sum = 0
    params_status = {}
    problems = []
    
    for param_key, weight in weights.items():
        p = env.get(param_key)
        if not isinstance(p, dict) or not p:
            params_status[param_key] = {
                "status": "NO_DATA",
                "score": 0,
                "weight": int(weight * 100),
            }
            continue
        
        status = p.get("status", "OK")
        s = status_scores.get(status, 70)
        weighted_sum += s * weight
        total_weight += weight
        
        params_status[param_key] = {
            "status": status,
            "score": s,
            "avg": p.get("avg"),
            "unit": p.get("unit", ""),
            "weight": int(weight * 100),
        }
        
        if status == "CRITICAL":
            problems.append(f"Критическое отклонение: {param_key}")
        elif status == "WARNING":
            problems.append(f"Отклонение: {param_key}")
    
    # ВАЖНО: если нет данных — всё равно возвращаем структуру с score=0
    if total_weight == 0:
        score = 0
        status = "NO_DATA"
    else:
        score = int(weighted_sum / total_weight)
        if score >= 85:
            status = "EXCELLENT"
        elif score >= 60:
            status = "GOOD"
        elif score >= 30:
            status = "WARNING"
        else:
            status = "CRITICAL"
    
    result = {
        "score": score,
        "status": status,
        "params": params_status,
        "problems": problems,
    }
    
    log.info("Life support computed", 
             score=score, 
             status=status,
             params_with_data=sum(1 for v in params_status.values() if v.get("status") != "NO_DATA"))
    
    return result


def compute_health_report(data: dict) -> HealthReport:
    """Главный расчёт"""
    env = data.get("environmental", {}) or {}
    equip = data.get("equipment", {}) or {}
    alarms_data = data.get("alarms_summary", {}) or {}
    lighting = data.get("lighting", {}) or {}

    log.info("Computing health report",
             env_params=list(env.keys()),
             equip_keys=list(equip.keys()),
             lighting_status=lighting.get("status"),
             lighting_keys=list(lighting.keys()))

    issues = []

    # Под-индексы
    by_priority = alarms_data.get("by_priority", {})
    alarm_idx, alarm_issues = _compute_alarm_index(by_priority)
    issues.extend([{
        "severity": "critical" if "High" in i else "major" if "Medium" in i else "info",
        "category": "alarms", "title": i, "details": "", "recommendation": ""
    } for i in alarm_issues])

    broken_sensors = sum(
        (p.get("outliers_count", 0) or 0)
        for p in env.values() if isinstance(p, dict)
    )
    equip_idx, equip_issues = _compute_equipment_index(equip, broken_sensors)
    issues.extend([{
        "severity": "major" if "Битые" in i else "warning",
        "category": "equipment", "title": i, "details": "", "recommendation": ""
    } for i in equip_issues])

    env_idx, env_issues = _compute_environmental_index(env)
    issues.extend([{
        "severity": "critical" if "критическое" in i else "warning",
        "category": "environmental", "title": i, "details": "", "recommendation": ""
    } for i in env_issues])

    # Энергоэффективность — ГАРАНТИРОВАННО передаём координаты
    time_ctx = lighting.get("time_context", {})
    energy_status = lighting.get("status", "NO_DATA")
    energy_recommendation = lighting.get("recommendation", "")
    
    # Берём координаты откуда угодно (lighting → time_ctx → fallback на None)
    latitude = (lighting.get("latitude") 
                or time_ctx.get("latitude"))
    longitude = (lighting.get("longitude") 
                 or time_ctx.get("longitude"))
    
    log.info("Energy block coordinates",
             from_lighting_lat=lighting.get("latitude"),
             from_time_ctx_lat=time_ctx.get("latitude"),
             final_lat=latitude,
             final_lon=longitude)
    
    if energy_status not in ("NO_DATA", None):
        energy_block = {
            "score": int(lighting.get("score") or 75),
            "status": energy_status,
            "summary": energy_recommendation,
            "lighting_on": int(lighting.get("on", 0) or 0),
            "lighting_total": int(lighting.get("total_fixtures", 0) or 0),
            "on_percentage": float(lighting.get("on_percentage", 0) or 0),
            "time_period": time_ctx.get("period", "день" if time_ctx.get("is_day", True) else "ночь"),
            "city": time_ctx.get("city") or lighting.get("city") or "Не указан",
            "hour": time_ctx.get("hour") if time_ctx.get("hour") is not None else 12,
            "is_day": bool(time_ctx.get("is_day", True)),
            "latitude": float(latitude) if latitude is not None else None,
            "longitude": float(longitude) if longitude is not None else None,
            "timezone": time_ctx.get("timezone", "UTC"),
            "recommendation": energy_recommendation,
            "by_zone": lighting.get("by_zone", {}),
        }
    else:
        # Даже если NO_DATA — передаём базовую инфу о локации
        energy_block = {
            "status": "NO_DATA",
            "score": None,
            "summary": "Нет данных об освещении",
            "lighting_on": 0,
            "lighting_total": 0,
            "on_percentage": 0,
            "time_period": time_ctx.get("period", "день"),
            "city": time_ctx.get("city") or "Не указан",
            "hour": time_ctx.get("hour") if time_ctx.get("hour") is not None else 12,
            "is_day": bool(time_ctx.get("is_day", True)),
            "latitude": float(latitude) if latitude is not None else None,
            "longitude": float(longitude) if longitude is not None else None,
            "timezone": time_ctx.get("timezone", "UTC"),
        }
    
    log.info("Energy block built", 
             status=energy_block.get("status"),
             city=energy_block.get("city"),
             lat=energy_block.get("latitude"),
             lon=energy_block.get("longitude"),
             hour=energy_block.get("hour"))

    energy_idx, energy_issues = _compute_energy_index(energy_block)
    issues.extend([{
        "severity": "warning", "category": "energy", 
        "title": i, "details": "", "recommendation": energy_recommendation
    } for i in energy_issues])

    # Битые датчики
    for param_key, p in env.items():
        if not isinstance(p, dict):
            continue
        outliers_count = p.get("outliers_count", 0) or 0
        if outliers_count > 0:
            label = p.get("label", param_key)
            outliers_sample = p.get("outliers", [])[:3]
            sample_desc = ", ".join([f"{o.get('tag_name')}={o.get('value')}" for o in outliers_sample])
            issues.append({
                "severity": "major", "category": "equipment",
                "title": f"{outliers_count} битых датчиков ({label})",
                "details": f"Аномальные значения: {sample_desc}. Исключены из расчёта среднего.",
                "recommendation": f"Заменить или откалибровать датчики {label}",
            })

    # Композитный индекс
    weights = {"alarms": 0.35, "environmental": 0.30, "equipment": 0.25, "energy": 0.10}
    composite = (
        alarm_idx * weights["alarms"] +
        env_idx * weights["environmental"] +
        equip_idx * weights["equipment"] +
        energy_idx * weights["energy"]
    )
    score = int(max(0, min(100, composite)))

    # ИНДЕКС ЖИЗНЕОБЕСПЕЧЕНИЯ — ВСЕГДА вычисляется
    life_support = _compute_life_support_index(env)

    # Статус
    if score < 30:
        status = "CRITICAL"
        summary = f"Критическое состояние системы ({score}/100)."
    elif score < 60:
        status = "WARNING"
        summary = f"Система работает с отклонениями ({score}/100)."
    elif score < 85:
        status = "GOOD"
        summary = f"Система работает нормально ({score}/100)."
    else:
        status = "EXCELLENT"
        summary = f"Система в отличном состоянии ({score}/100)."

    issues = [i for i in issues if i.get("title")]
    severity_order = {"critical": 0, "major": 1, "warning": 2, "info": 3}
    issues.sort(key=lambda x: severity_order.get(x.get("severity", "info"), 9))

    return HealthReport(
        score=score, status=status, summary=summary,
        issues=issues[:10],
        stats={
            "total_alarms_24h": alarms_data.get("total", 0) or 0,
            "high_alarms": by_priority.get("high", 0) or 0,
            "medium_alarms": by_priority.get("medium", 0) or 0,
            "low_alarms": by_priority.get("low", 0) or 0,
            "chattering_tags": equip.get("chattering", 0) or 0,
            "stuck_tags": equip.get("stuck", 0) or 0,
            "broken_sensors": broken_sensors,
            "online_tags": equip.get("online", 0) or 0,
            "offline_tags": equip.get("offline", 0) or 0,
        },
        environmental=env, equipment=equip,
        alarms={
            "total": alarms_data.get("total", 0) or 0,
            "active": alarms_data.get("active", 0) or 0,
            "by_priority": by_priority,
            "top_issues": alarms_data.get("top_alarms", [])[:10],
        },
        energy=energy_block,
        recommendations=[],
        sub_scores={
            "alarms": {"score": alarm_idx, "weight": 40},
            "environmental": {"score": env_idx, "weight": 35},
            "equipment": {"score": equip_idx, "weight": 25},
        },
        life_support=life_support,
    )
