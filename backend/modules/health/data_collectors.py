"""Сбор данных — с блоком освещения и данными по зонам"""
from datetime import datetime, timedelta
from typing import Any
from structlog import get_logger
import traceback

from core.db import fetch, fetchval

log = get_logger()


def _priority_label(priority: int | None) -> str:
    """Возвращает машинный ключ приоритета. Локализация — на фронте."""
    if priority is None:
        return "unknown"
    if priority >= 150: return "high"
    if priority >= 100: return "medium"
    return "low"


# === 5 групп параметров + освещение ===
PARAM_GROUPS = {
    "co2": {
        "label": "CO2",
        "include": ["co2", "углекисл", "carbon_dioxide", "carbon dioxide"],
        "exclude": ["online", "_online", "is_online", "status_online", "_status", "availability", "avail", "_state", "connection", "connected", "_ping", "heartbeat", "alive"],
        "unit": "ppm",
        # Атмосферный CO2 ~415 ppm. В помещении 400-1000 норма.
        # < 100 ppm = битый датчик (не может быть ниже атмосферного)
        # > 5000 ppm = явная аномалия (опасно для жизни)
        "norms": {"opt_min": 400, "opt_max": 800, "crit_min": 350, "crit_max": 2000},
        "validator": {"min": 100, "max": 5000},
    },
    "voc": {
        "label": "VOC (качество воздуха)",
        "include": ["voc", "tvoc", "летуч", "air_quality", "air quality", "качество воздуха"],
        "exclude": ["vocal", "vocabulary", "avocado", "online", "_online", "is_online", "status_online", "_status", "availability", "avail", "_state", "connection", "connected", "_ping", "heartbeat", "alive"],
        "unit": "мг/м³",
        # Нормативы ВОЗ для летучих органических соединений:
        # < 0.3 мг/м³: отличное качество воздуха
        # 0.3-0.5: хороший, допустимый уровень
        # 0.6-1.0: загрязнённый воздух (запахи, дискомфорт)
        # > 1.0: плохое качество (головная боль, раздражение)
        # Validator: < 0.01 = битый датчик (всегда есть фон), > 50 = явная аномалия
        "norms": {"opt_min": 0, "opt_max": 0.3, "crit_min": 0, "crit_max": 1.0},
        "validator": {"min": 0.01, "max": 50},
    },
    "temperature": {
        "label": "Температура",
        "include": [
            "temp", "температур", "t_sensor", "t_air", "t_room",
            "t_outside", "t_supply", "t_return", "t_воды", "t_vody",
            "t_pr", "t_obr", "t_pod",
        ],
        "exclude": ["template", "tempo", "timestamp", "temporarily", "temptation", "online", "_online", "is_online", "status_online", "_status", "availability", "avail", "_state", "connection", "connected", "_ping", "heartbeat", "alive"],
        "unit": "°C",
        "norms": {"opt_min": 18, "opt_max": 24, "crit_min": 10, "crit_max": 35},
        "validator": {"min": -50, "max": 80},
    },
    "humidity": {
        "label": "Влажность",
        "include": [
            "hum", "влажн", "rh_", "rh-", "relative_hum", "relative hum",
            "h_sensor", "h_air", "h_room",
        ],
        "exclude": ["human", "humidity_setpoint", "online", "_online", "is_online", "status_online", "_status", "availability", "avail", "_state", "connection", "connected", "_ping", "heartbeat", "alive"],
        "unit": "%",
        "norms": {"opt_min": 30, "opt_max": 60, "crit_min": 20, "crit_max": 80},
        "validator": {"min": 0, "max": 100},
    },
    "pressure": {
        "label": "Давление",
        "include": [
            "press", "давлен", "barometr", "атмосф", "atmospheric",
            "p_sensor", "p_air", "p_room", "p_diff", "diff_press",
            "перепад давл", "perepad",
        ],
        "exclude": ["depress", "compress", "suppress", "express", "impression", "repress", "oppress", "decompress", "pressing", "presser", "online", "_online", "is_online", "status_online", "_status", "availability", "avail", "_state", "connection", "connected", "_ping", "heartbeat", "alive"],
        "unit": "мм рт. ст.",
        "norms": {"opt_min": 720, "opt_max": 780, "crit_min": 680, "crit_max": 820},
        "validator": {"min": 500, "max": 900},
    },
}

# === Паттерны для освещения ===
LIGHTING_PATTERNS = {
    "include": ["light", "свет", "лампа", "lamp", "l_", "освещ", "lux", "lux_"],
    "exclude": ["highlight", "lightweight", "moonlight", "flashlight"],
}


def _match_tag_to_category(tag_name: str) -> str | None:
    name_lower = tag_name.lower()
    for param_key, cfg in PARAM_GROUPS.items():
        if any(excl in name_lower for excl in cfg["exclude"]):
            continue
        if any(incl in name_lower for incl in cfg["include"]):
            return param_key
    return None


def _is_lighting_tag(tag_name: str) -> bool:
    name_lower = tag_name.lower()
    if any(excl in name_lower for excl in LIGHTING_PATTERNS["exclude"]):
        return False
    return any(incl in name_lower for incl in LIGHTING_PATTERNS["include"])


def _check_status(value: float, norms: dict) -> str:
    if value < norms["crit_min"] or value > norms["crit_max"]:
        return "CRITICAL"
    if value < norms["opt_min"] or value > norms["opt_max"]:
        return "WARNING"
    return "OK"


def _is_daytime() -> dict:
    """Определяет день/ночь + возвращает координаты для UI"""
    from config.settings import settings
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo(settings.timezone)
        now = datetime.now(tz)
    except Exception:
        now = datetime.now()
    
    hour = now.hour
    is_day = 6 <= hour < 22
    
    # Гарантируем что координаты всегда присутствуют
    lat = getattr(settings, 'latitude', None)
    lon = getattr(settings, 'longitude', None)
    
    log.info("Location resolved",
             city=settings.city,
             timezone=settings.timezone,
             latitude=lat,
             longitude=lon,
             hour=hour,
             is_day=is_day)
    
    return {
        "hour": hour,
        "is_day": is_day,
        "city": settings.city or "Не указан",
        "timezone": settings.timezone or "UTC",
        "latitude": float(lat) if lat is not None else None,
        "longitude": float(lon) if lon is not None else None,
        "period": "день" if is_day else "ночь",
        "recommendation": "естественное освещение" if is_day else "требуется искусственное",
    }


async def collect_environmental_params(period_hours: int = 24) -> dict[str, Any]:
    """Параметры среды — 5 групп с валидацией"""
    since = datetime.now() - timedelta(hours=period_hours)
    
    all_tags = await fetch("SELECT tag_id, tag_name FROM tags_dict")
    log.info("Total tags in dict", count=len(all_tags))
    
    categorized = {key: [] for key in PARAM_GROUPS}
    for row in all_tags:
        tag_id = row["tag_id"]
        tag_name = row["tag_name"]
        category = _match_tag_to_category(tag_name)
        if category:
            categorized[category].append((tag_id, tag_name))
    
    log.info("Tags categorized",
             temperature=len(categorized["temperature"]),
             humidity=len(categorized["humidity"]),
             co2=len(categorized["co2"]),
             pressure=len(categorized["pressure"]),
             voc=len(categorized["voc"]))
    
    result = {}
    for param_key, cfg in PARAM_GROUPS.items():
        tag_list = categorized[param_key]
        if not tag_list:
            continue
        
        tag_ids = [t[0] for t in tag_list]
        tag_map = {t[0]: t[1] for t in tag_list}
        
        try:
            rows = await fetch(
                """
                SELECT tag_id, value, date_created FROM tags_value
                WHERE tag_id = ANY($1::bigint[]) AND date_created >= $2
                ORDER BY date_created DESC LIMIT 10000
                """,
                tag_ids, since,
            )
            
            if not rows:
                continue
            
            validator = cfg["validator"]
            valid_values = []
            outliers = []
            
            for r in rows:
                if r["value"] is None: continue
                try:
                    v = float(r["value"])
                except (ValueError, TypeError): continue
                
                if v < validator["min"] or v > validator["max"]:
                    outliers.append({
                        "tag_id": r["tag_id"],
                        "tag_name": tag_map.get(r["tag_id"], f"tag_{r['tag_id']}"),
                        "value": v,
                        "threshold": f"{validator['min']}..{validator['max']} {cfg['unit']}",
                        "timestamp": r["date_created"].isoformat() if r["date_created"] else None,
                    })
                else:
                    valid_values.append(v)
            
            if not valid_values:
                continue
            
            avg = round(sum(valid_values) / len(valid_values), 2)
            min_v = round(min(valid_values), 2)
            max_v = round(max(valid_values), 2)
            status = _check_status(avg, cfg["norms"])
            norms = cfg["norms"]
            deviations_count = sum(1 for v in valid_values if v < norms["opt_min"] or v > norms["opt_max"])
            
            last_by_tag = {}
            for r in rows:
                tid = r["tag_id"]
                if tid not in last_by_tag and r["value"] is not None:
                    try:
                        v = float(r["value"])
                        is_valid = validator["min"] <= v <= validator["max"]
                        last_by_tag[tid] = {
                            "tag_id": tid,
                            "tag_name": tag_map.get(tid, f"tag_{tid}"),
                            "last_value": round(v, 2),
                            "is_valid": is_valid,
                            "timestamp": r["date_created"].isoformat() if r["date_created"] else None,
                        }
                    except (ValueError, TypeError): pass
            
            result[param_key] = {
                "label": cfg["label"],
                "unit": cfg["unit"],
                "count": len(valid_values),
                "outliers_count": len(outliers),
                "avg": avg,
                "min": min_v,
                "max": max_v,
                "last_value": round(valid_values[0], 2),
                "status": status,
                "deviations_count": deviations_count,
                "norms": cfg["norms"],
                "tags_count": len(tag_ids),
                "tag_names": [tag_map[tid] for tid in tag_ids[:10]],
                "tags_last_values": list(last_by_tag.values())[:50],
                "outliers": outliers[:20],
            }
        except Exception as e:
            log.warning(f"Failed to collect {param_key}", error_type=type(e).__name__, error=str(e))
    
    return result


async def collect_lighting() -> dict[str, Any]:
    """Сбор данных по освещению для блока энергоэффективности"""
    # Все теги освещения
    all_tags = await fetch("SELECT tag_id, tag_name FROM tags_dict")
    lighting_tags = [
        (r["tag_id"], r["tag_name"]) for r in all_tags
        if _is_lighting_tag(r["tag_name"])
    ]
    
    if not lighting_tags:
        return {
            "total_fixtures": 0,
            "on": 0,
            "off": 0,
            "status": "NO_DATA",
            "time_context": _is_daytime(),
        }
    
    tag_ids = [t[0] for t in lighting_tags]
    tag_map = {t[0]: t[1] for t in lighting_tags}
    
    # Последние значения по каждому тегу
    rows = await fetch(
        """
        SELECT DISTINCT ON (tag_id) tag_id, value, date_created
        FROM tags_value
        WHERE tag_id = ANY($1::bigint[])
        ORDER BY tag_id, date_created DESC
        """,
        tag_ids,
    )
    
    # Группируем по зонам (если есть связь tags_zones)
    zones_map = {}
    try:
        zone_rows = await fetch(
            """
            SELECT tz.tag_id, z.zone_name
            FROM tags_zones tz
            JOIN zones_dict z ON z.zone_id = tz.zone_id
            WHERE tz.tag_id = ANY($1::bigint[])
            """,
            tag_ids,
        )
        zones_map = {r["tag_id"]: r["zone_name"] for r in zone_rows}
    except Exception as e:
        log.warning("Failed to fetch zones for lighting", error=str(e))
    
    # Анализ состояния
    on_fixtures = []
    off_fixtures = []
    by_zone = {}
    
    for r in rows:
        if r["value"] is None:
            continue
        try:
            v = float(r["value"])
        except (ValueError, TypeError):
            continue
        
        is_on = v > 0.5
        tag_name = tag_map.get(r["tag_id"], f"tag_{r['tag_id']}")
        zone = zones_map.get(r["tag_id"], "Неизвестная зона")
        
        fixture = {
            "tag_id": r["tag_id"],
            "tag_name": tag_name,
            "value": v,
            "is_on": is_on,
            "zone": zone,
            "timestamp": r["date_created"].isoformat() if r["date_created"] else None,
        }
        
        if is_on:
            on_fixtures.append(fixture)
        else:
            off_fixtures.append(fixture)
        
        if zone not in by_zone:
            by_zone[zone] = {"total": 0, "on": 0, "off": 0}
        by_zone[zone]["total"] += 1
        if is_on:
            by_zone[zone]["on"] += 1
        else:
            by_zone[zone]["off"] += 1
    
    total = len(on_fixtures) + len(off_fixtures)
    time_ctx = _is_daytime()
    
    # Рекомендация на основе времени суток
    on_pct = (len(on_fixtures) / total * 100) if total > 0 else 0
    
    if time_ctx["is_day"]:
        if on_pct > 50:
            status = "WARNING"
            recommendation = f"Дневное время ({time_ctx['hour']:02d}:00). Выключено {len(on_fixtures)} из {total} светильников. Рекомендуется использовать естественное освещение."
        else:
            status = "EXCELLENT"
            recommendation = f"Дневное время. Экономное использование освещения ({len(on_fixtures)} из {total} включено)."
    else:
        if on_pct < 30 and total > 10:
            status = "WARNING"
            recommendation = f"Ночное время ({time_ctx['hour']:02d}:00). Включено только {len(on_fixtures)} из {total} светильников. Проверьте достаточность освещения."
        else:
            status = "GOOD"
            recommendation = f"Ночное время. Адекватное использование освещения ({len(on_fixtures)} из {total} включено)."
    
    score = 100
    if time_ctx["is_day"] and on_pct > 70:
        score = 40
    elif time_ctx["is_day"] and on_pct > 50:
        score = 70
    elif not time_ctx["is_day"] and on_pct < 10:
        score = 60
    
    return {
        "total_fixtures": total,
        "on": len(on_fixtures),
        "off": len(off_fixtures),
        "on_percentage": round(on_pct, 1),
        "status": status,
        "score": score,
        "recommendation": recommendation,
        "time_context": time_ctx,
        "latitude": time_ctx.get("latitude"),
        "longitude": time_ctx.get("longitude"),
        "by_zone": by_zone,
        "on_fixtures": on_fixtures[:20],
        "off_fixtures": off_fixtures[:20],
    }


async def collect_equipment_status(period_hours: int = 24) -> dict[str, Any]:
    since = datetime.now() - timedelta(hours=period_hours)
    recent_threshold = datetime.now() - timedelta(hours=2)
    
    all_tags_result = await fetch("SELECT tag_id, tag_name FROM tags_dict LIMIT 5000")
    total_tags = len(all_tags_result)
    
    online_tags = await fetch("SELECT DISTINCT tag_id FROM tags_value WHERE date_created >= $1 LIMIT 5000", recent_threshold)
    online_ids = {r["tag_id"] for r in online_tags}
    
    snapshot_age_hours = None
    if not online_ids:
        older_threshold = datetime.now() - timedelta(hours=24)
        online_tags = await fetch("SELECT DISTINCT tag_id FROM tags_value WHERE date_created >= $1 LIMIT 5000", older_threshold)
        online_ids = {r["tag_id"] for r in online_tags}
        snapshot_age_hours = 24.0
        log.info("Using 24h data as snapshot", tags=len(online_ids))
    
    active_tags = await fetch(
        "SELECT DISTINCT c.tag_id FROM tag_change_events_history c JOIN events_history e ON e.id = c.event_id WHERE e.date_created >= $1 LIMIT 5000",
        since,
    )
    active_ids = {r["tag_id"] for r in active_tags}
    
    chattering = await fetch(
        """
        SELECT c.tag_id, t.tag_name, COUNT(*) as changes
        FROM tag_change_events_history c
        JOIN events_history e ON e.id = c.event_id
        JOIN tags_dict t ON t.tag_id = c.tag_id
        WHERE e.date_created >= $1
        GROUP BY c.tag_id, t.tag_name HAVING COUNT(*) >= 20
        ORDER BY changes DESC LIMIT 20
        """,
        since,
    )
    
    offline_tags = [
        {"tag_id": t["tag_id"], "name": t["tag_name"]}
        for t in all_tags_result if t["tag_id"] not in online_ids
    ][:20]
    
    return {
        "total_tags": total_tags,
        "online": len(online_ids),
        "offline": len(offline_tags),
        "active": len(active_ids),
        "stuck": max(0, min(total_tags - len(active_ids) - len(offline_tags), total_tags)),
        "chattering": len(chattering),
        "offline_list": offline_tags[:10],
        "chattering_list": [{"tag_id": r["tag_id"], "name": r["tag_name"], "changes": r["changes"]} for r in chattering],
        "last_snapshot_count": len(online_ids) if snapshot_age_hours else 0,
        "snapshot_age_hours": snapshot_age_hours,
        "data_freshness": "recent" if snapshot_age_hours is None else f"snapshot_{int(snapshot_age_hours)}h_old",
    }


async def collect_alarms_summary(period_hours: int = 24) -> dict[str, Any]:
    since = datetime.now() - timedelta(hours=period_hours)
    rows = await fetch(
        """
        SELECT COALESCE(a.alarm_priority, 0) as priority, COUNT(*) as count,
               SUM(CASE WHEN a.is_completed = FALSE THEN 1 ELSE 0 END) as active_count
        FROM alarm_events_history a
        JOIN events_history e ON e.id = a.event_id
        WHERE e.date_created >= $1
        GROUP BY a.alarm_priority ORDER BY priority DESC
        """,
        since,
    )
    
    total = await fetchval("SELECT COUNT(*) FROM alarm_events_history a JOIN events_history e ON e.id = a.event_id WHERE e.date_created >= $1", since)
    active_total = await fetchval("SELECT COUNT(*) FROM alarm_events_history a JOIN events_history e ON e.id = a.event_id WHERE e.date_created >= $1 AND a.is_completed = FALSE", since)
    
    top_alarms = await fetch(
        """
        SELECT COALESCE(t.tag_name, a.bound_name, 'unknown') as name, COUNT(*) as count,
               MAX(e.date_created) as last_occurrence, MAX(a.alarm_priority) as priority
        FROM alarm_events_history a
        JOIN events_history e ON e.id = a.event_id
        LEFT JOIN tags_dict t ON t.tag_id = a.tag_id
        WHERE e.date_created >= $1
        GROUP BY t.tag_name, a.bound_name ORDER BY count DESC LIMIT 10
        """,
        since,
    )
    
    by_priority_agg = {"high": 0, "medium": 0, "low": 0}
    for r in rows:
        label = _priority_label(r["priority"])
        by_priority_agg[label] = by_priority_agg.get(label, 0) + r["count"]
    
    return {
        "period_hours": period_hours,
        "total": total or 0,
        "active": active_total or 0,
        "by_priority": by_priority_agg,
        "top_alarms": [
            {"name": r["name"], "count": r["count"], "priority": _priority_label(r["priority"]),
             "last_occurrence": r["last_occurrence"].isoformat() if r["last_occurrence"] else None}
            for r in top_alarms
        ],
    }


async def collect_all_health_data(period_hours: int = 24) -> dict[str, Any]:
    """Собирает все данные параллельно, включая lighting"""
    import asyncio, time
    
    start = time.time()
    log.info("Starting data collection", period_hours=period_hours)
    
    collectors = [
        ("environmental", collect_environmental_params(period_hours)),
        ("equipment", collect_equipment_status(period_hours)),
        ("alarms", collect_alarms_summary(period_hours)),
        ("lighting", collect_lighting()),
    ]
    
    results = {}
    for name, coro in collectors:
        t0 = time.time()
        try:
            data = await coro
            elapsed = round(time.time() - t0, 2)
            log.info(f"Collector {name} done", elapsed_sec=elapsed,
                    keys=list(data.keys()) if isinstance(data, dict) else None)
            results[name] = data
        except Exception as e:
            elapsed = round(time.time() - t0, 2)
            log.error(f"Collector {name} failed", elapsed_sec=elapsed,
                     error_type=type(e).__name__, error=str(e))
            results[name] = None
    
    total_elapsed = round(time.time() - start, 2)
    log.info("All collectors finished", total_sec=total_elapsed)
    
    return {
        "period_hours": period_hours,
        "collected_at": datetime.now().isoformat(),
        "collection_time_sec": total_elapsed,
        "environmental": results["environmental"] or {},
        "equipment": results["equipment"] or {"total_tags": 0, "online": 0, "offline": 0, "stuck": 0, "chattering": 0},
        "alarms_summary": results["alarms"] or {"total": 0, "active": 0, "by_priority": {}, "top_alarms": []},
        "lighting": results["lighting"] or {"total_fixtures": 0, "on": 0, "off": 0, "status": "NO_DATA"},
    }
