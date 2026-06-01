"""Health API — с подробным логированием для дебага"""
from fastapi import APIRouter, Query
from datetime import datetime, timedelta
from structlog import get_logger

from core.db import fetch
from modules.health.data_collectors import _priority_label, PARAM_GROUPS, collect_environmental_params

log = get_logger()
router = APIRouter(prefix="/health", tags=["health"])


@router.get("/ping")
async def ping():
    """Простой health-check эндпоинт"""
    return {"status": "ok", "time": datetime.now().isoformat()}


@router.get("/metrics-summary")
async def get_metrics_summary():
    """Сводка по параметрам среды с агрегацией по зонам"""
    log.info("metrics-summary requested")
    try:
        env = await collect_environmental_params(period_hours=24)
        log.info("metrics-summary collected", params=list(env.keys()))
    except Exception as e:
        log.error("metrics-summary failed", error=str(e))
        return {"error": str(e)}

    for param_key, param_data in env.items():
        tag_ids = [t["tag_id"] for t in param_data.get("tags_last_values", [])]
        if not tag_ids:
            continue
        try:
            zone_rows = await fetch(
                """
                SELECT tz.tag_id, z.zone_name, t.tag_name
                FROM tags_zones tz
                JOIN zones_dict z ON z.zone_id = tz.zone_id
                JOIN tags_dict t ON t.tag_id = tz.tag_id
                WHERE tz.tag_id = ANY($1::bigint[])
                """,
                tag_ids,
            )
            tag_zone_map = {r["tag_id"]: r["zone_name"] for r in zone_rows}
            by_zone = {}
            for tag in param_data.get("tags_last_values", []):
                zone = tag_zone_map.get(tag["tag_id"], "Неизвестная зона")
                if zone not in by_zone:
                    by_zone[zone] = {"tags": [], "values": []}
                by_zone[zone]["tags"].append(tag)
                if tag.get("last_value") is not None:
                    by_zone[zone]["values"].append(tag["last_value"])
            zone_stat = {}
            for zone, data in by_zone.items():
                values = data["values"]
                if values:
                    zone_stat[zone] = {
                        "count": len(values),
                        "avg": round(sum(values) / len(values), 2),
                        "min": round(min(values), 2),
                        "max": round(max(values), 2),
                        "tags": data["tags"][:10],
                    }
            param_data["by_zone"] = zone_stat
        except Exception as e:
            log.warning(f"Failed to aggregate {param_key} by zones", error=str(e))

    text_parts = ["## Сводка по параметрам среды", ""]
    for param_key, p in env.items():
        label = p.get("label", param_key)
        unit = p.get("unit", "")
        status = p.get("status", "—")
        status_marker = {"OK": "[OK]", "WARNING": "[!]", "CRITICAL": "[!!!]"}.get(status, "[?]")
        text_parts.append(f"### {label} {status_marker}")
        text_parts.append(f"- Среднее: **{p.get('avg', '—')} {unit}**")
        text_parts.append(f"- Диапазон: {p.get('min', '—')} — {p.get('max', '—')} {unit}")
        text_parts.append(f"- Тегов: {p.get('tags_count', 0)}")
        by_zone = p.get("by_zone", {})
        if by_zone:
            text_parts.append(f"- Зон: {len(by_zone)}")
            for zone_name, zone_data in list(by_zone.items())[:5]:
                text_parts.append(f"  - {zone_name}: avg {zone_data['avg']} {unit} ({zone_data['count']} тегов)")
        text_parts.append("")

    return {"params": env, "text": "\n".join(text_parts)}


@router.get("/alarms")
async def get_alarms(
    period_hours: int = Query(24, ge=1, le=168),
    priority: str = Query("all", pattern="^(all|high|medium|low)$"),
    limit: int = Query(200, ge=1, le=1000),
):
    """Список аварий с деталями"""
    log.info("alarms requested", period=period_hours, priority=priority, limit=limit)
    since = datetime.now() - timedelta(hours=period_hours)
    
    if priority == "high":
        priority_filter = "AND a.alarm_priority >= 150"
    elif priority == "medium":
        priority_filter = "AND a.alarm_priority >= 100 AND a.alarm_priority < 150"
    elif priority == "low":
        priority_filter = "AND a.alarm_priority < 100"
    else:
        priority_filter = ""

    try:
        rows = await fetch(
            f"""
            SELECT a.id, a.alarm_priority, a.alarm_state, a.bound_name, a.is_completed,
                   e.date_created, e.message, t.tag_name, z.zone_name
            FROM alarm_events_history a
            JOIN events_history e ON e.id = a.event_id
            LEFT JOIN tags_dict t ON t.tag_id = a.tag_id
            LEFT JOIN tags_zones tz ON tz.tag_id = a.tag_id
            LEFT JOIN zones_dict z ON z.zone_id = tz.zone_id
            WHERE e.date_created >= $1 {priority_filter}
            ORDER BY e.date_created DESC LIMIT $2
            """,
            since, limit,
        )
        log.info("alarms fetched", count=len(rows))
    except Exception as e:
        log.error("alarms fetch failed", error=str(e))
        return {"error": str(e), "alarms": []}

    return {
        "period_hours": period_hours,
        "filter": priority,
        "count": len(rows),
        "alarms": [
            {
                "id": r["id"],
                "name": r["tag_name"] or r["bound_name"] or f"alarm_{r['id']}",
                "bound": r["bound_name"],
                "priority": r["alarm_priority"],
                "priority_label": _priority_label(r["alarm_priority"]),
                "state": r["alarm_state"],
                "is_active": not r["is_completed"],
                "timestamp": r["date_created"].isoformat() if r["date_created"] else None,
                "message": r["message"],
                "zone": r["zone_name"],
            }
            for r in rows
        ],
    }


@router.get("/environmental/{param}")
async def get_environmental_history(
    param: str,
    period_hours: int = Query(24, ge=1, le=168),
    limit: int = Query(5000, ge=100, le=20000),
):
    """История параметра с drilldown"""
    log.info("environmental requested", param=param, period=period_hours, limit=limit)
    
    if param not in PARAM_GROUPS:
        log.warning("unknown param", param=param, valid=list(PARAM_GROUPS.keys()))
        return {"error": f"Unknown param: {param}. Valid: {list(PARAM_GROUPS.keys())}"}

    cfg = PARAM_GROUPS[param]
    since = datetime.now() - timedelta(hours=period_hours)

    include_patterns = cfg.get("include", [])
    exclude_patterns = cfg.get("exclude", [])
    if not include_patterns:
        return {"error": f"No include patterns for param: {param}"}

    include_conds = [f"LOWER(tag_name) LIKE '%{p.lower()}%'" for p in include_patterns]
    include_sql = " OR ".join(include_conds)

    if exclude_patterns:
        exclude_conds = [f"LOWER(tag_name) NOT LIKE '%{p.lower()}%'" for p in exclude_patterns]
        exclude_sql = " AND ".join(exclude_conds)
        tag_query = f"SELECT tag_id, tag_name FROM tags_dict WHERE ({include_sql}) AND {exclude_sql} LIMIT 100"
    else:
        tag_query = f"SELECT tag_id, tag_name FROM tags_dict WHERE {include_sql} LIMIT 100"

    try:
        tag_rows = await fetch(tag_query)
        log.info(f"tags found for {param}", count=len(tag_rows))
    except Exception as e:
        log.error("tag search failed", error=str(e))
        return {"error": f"DB error: {str(e)}"}

    if not tag_rows:
        return {
            "param": param, "label": cfg.get("label", param), "unit": cfg.get("unit", ""),
            "count": 0, "outliers_count": 0, "history": [], "hourly": [],
            "tags_last_values": [], "outliers": [],
        }

    tag_ids = [r["tag_id"] for r in tag_rows]
    tag_map = {r["tag_id"]: r["tag_name"] for r in tag_rows}

    try:
        history_rows = await fetch(
            """
            SELECT tag_id, value, date_created
            FROM tags_value
            WHERE tag_id = ANY($1::bigint[]) AND date_created >= $2
            ORDER BY date_created ASC
            LIMIT $3
            """,
            tag_ids, since, limit,
        )
        log.info(f"history fetched for {param}", rows=len(history_rows))
    except Exception as e:
        log.error("history fetch failed", error=str(e))
        return {"error": f"History DB error: {str(e)}"}

    validator = cfg.get("validator", {"min": -999999, "max": 999999})
    valid_history = []
    outliers = []

    for r in history_rows:
        if r["value"] is None:
            continue
        try:
            v = float(r["value"])
        except (ValueError, TypeError):
            continue

        tag_name = tag_map.get(r["tag_id"], f"tag_{r['tag_id']}")
        ts = r["date_created"].isoformat() if r["date_created"] else None

        if v < validator.get("min", -999999) or v > validator.get("max", 999999):
            outliers.append({
                "tag_id": r["tag_id"],
                "tag_name": tag_name,
                "value": v,
                "threshold": f"{validator.get('min', '?')}..{validator.get('max', '?')} {cfg.get('unit', '')}",
                "timestamp": ts,
            })
        else:
            valid_history.append({
                "tag_id": r["tag_id"],
                "tag_name": tag_name,
                "value": v,
                "timestamp": ts,
            })

    tags_last_values = {}
    for h in reversed(valid_history):
        tid = h["tag_id"]
        if tid not in tags_last_values:
            tags_last_values[tid] = {
                "tag_id": tid,
                "tag_name": h["tag_name"],
                "last_value": h["value"],
                "is_valid": True,
                "timestamp": h["timestamp"],
            }
    
    # Добавляем теги из outliers как битые
    for o in outliers:
        tid = o["tag_id"]
        if tid not in tags_last_values:
            tags_last_values[tid] = {
                "tag_id": tid,
                "tag_name": o["tag_name"],
                "last_value": o["value"],
                "is_valid": False,
                "timestamp": o["timestamp"],
            }

    hourly = {}
    for h in valid_history:
        if not h["timestamp"]:
            continue
        hour = h["timestamp"][:13]
        if hour not in hourly:
            hourly[hour] = {"sum": 0, "count": 0, "min": h["value"], "max": h["value"]}
        hourly[hour]["sum"] += h["value"]
        hourly[hour]["count"] += 1
        hourly[hour]["min"] = min(hourly[hour]["min"], h["value"])
        hourly[hour]["max"] = max(hourly[hour]["max"], h["value"])

    hourly_data = [
        {"hour": hour, "avg": round(d["sum"] / d["count"], 2), "min": round(d["min"], 2), "max": round(d["max"], 2)}
        for hour, d in sorted(hourly.items())
    ]

    log.info(f"environmental result for {param}", 
             valid=len(valid_history), outliers=len(outliers), 
             tags_last=len(tags_last_values), hourly=len(hourly_data))

    return {
        "param": param,
        "label": cfg.get("label", param),
        "unit": cfg.get("unit", ""),
        "norms": cfg.get("norms", {}),
        "validator": validator,
        "period_hours": period_hours,
        "count": len(valid_history),
        "outliers_count": len(outliers),
        "history": valid_history[-500:],
        "hourly": hourly_data,
        "tags_last_values": list(tags_last_values.values()),
        "outliers": outliers,
    }


@router.get("/debug")
async def debug_routes():
    """Список всех доступных эндпоинтов health API"""
    return {
        "endpoints": [
            "GET /health/ping",
            "GET /health/debug",
            "GET /health/metrics-summary",
            "GET /health/alarms?period_hours=24&priority=all&limit=200",
            "GET /health/environmental/temperature",
            "GET /health/environmental/humidity",
            "GET /health/environmental/co2",
            "GET /health/environmental/pressure",
            "GET /health/environmental/voc",
        ],
        "param_groups": list(PARAM_GROUPS.keys()),
        "time": datetime.now().isoformat(),
    }
