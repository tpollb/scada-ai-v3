"""Рендеринг отчёта — гарантированное добавление life_support + компактные виджеты"""
from modules.health.data_collectors import PARAM_GROUPS
from .analysis import HealthReport
from structlog import get_logger

log = get_logger()


def _safe_int(value, default=0) -> int:
    if value is None: return default
    try: return int(value)
    except (ValueError, TypeError): return default


def render_voice(report: HealthReport) -> dict:
    status_ru = {
        "CRITICAL": "критическое", "WARNING": "требует внимания",
        "GOOD": "нормальное", "EXCELLENT": "отличное",
    }.get(report.status, "неизвестное")

    parts = [f"Здоровье системы {report.score} из 100, состояние {status_ru}."]

    life = report.life_support or {}
    life_score = life.get("score")
    if life_score is not None:
        parts.append(f"Жизнеобеспечение {life_score} из 100.")

    alarms = report.alarms or {}
    high = (alarms.get("by_priority") or {}).get("high", 0)
    if _safe_int(high) > 0:
        parts.append(f"Аварий высокого приоритета: {high}.")

    return {
        "text": " ".join(parts),
        "priority": "alert" if report.status in ("CRITICAL", "WARNING") else "normal",
        "interrupt": report.status == "CRITICAL",
    }


def render_narrative(report: HealthReport) -> dict:
    lines = []
    lines.append("# Отчёт о здоровье системы")
    lines.append("")
    lines.append(f"**Композитный индекс:** {report.score}/100 ({report.status})")

    life = report.life_support or {}
    if life.get("score") is not None:
        lines.append(f"**Индекс жизнеобеспечения:** {life.get('score')}/100 ({life.get('status')})")

    lines.append(f"**Резюме:** {report.summary}")
    lines.append("")

    lines.append("## Формула расчёта композитного индекса")
    lines.append("")
    lines.append("Индекс = взвешенная сумма четырёх под-индексов:")
    lines.append("")
    lines.append("| Под-индекс | Вес | Значение | Вклад |")
    lines.append("|---|---|---|---|")

    sub = report.sub_scores or {}
    total_contribution = 0
    for key, label in [("alarms", "Аварии"), ("environmental", "Среда"),
                       ("equipment", "Оборудование"), ("energy", "Энергия")]:
        data = sub.get(key, {})
        s = _safe_int(data.get("score"), 75)
        w = _safe_int(data.get("weight"), 25)
        contrib = int(s * w / 100)
        total_contribution += contrib
        lines.append(f"| {label} | {w}% | {s}/100 | +{contrib} |")

    lines.append(f"| **Итого** | **100%** | — | **{total_contribution}/100** |")
    lines.append("")

    # Жизнеобеспечение
    if life.get("score") is not None:
        lines.append("## Индекс жизнеобеспечения")
        lines.append("")
        lines.append(f"**Общая оценка:** {life.get('score')}/100 ({life.get('status')})")
        lines.append("")
        lines.append("| Параметр | Вес | Статус | Оценка |")
        lines.append("|---|---|---|---|")
        params = life.get("params", {})
        param_labels = {
            "co2": "CO2", "temperature": "Температура", "voc": "VOC",
            "humidity": "Влажность", "pressure": "Давление",
        }
        for param_key in ["co2", "temperature", "voc", "humidity", "pressure"]:
            p = params.get(param_key, {})
            label = param_labels.get(param_key, param_key)
            w = p.get("weight", "—")
            status = p.get("status", "—")
            s = p.get("score", "—")
            lines.append(f"| {label} | {w}% | {status} | {s}/100 |")
        lines.append("")

    # Параметры среды
    env = report.environmental or {}
    if env:
        lines.append("## Параметры жизнедеятельности (детально)")
        lines.append("")
        for param_key, p in env.items():
            if not isinstance(p, dict): continue
            cfg = PARAM_GROUPS.get(param_key, {})
            label = cfg.get("label", param_key)
            unit = cfg.get("unit", "")
            norms = cfg.get("norms", {})
            status = p.get("status", "-")
            status_marker = {"OK": "[OK]", "WARNING": "[!]", "CRITICAL": "[!!!]"}.get(status, "[?]")
            lines.append(f"**{label}** {status_marker}")
            lines.append(f"- Среднее: {p.get('avg', '-')} {unit}")
            lines.append(f"- Мин/Макс: {p.get('min', '-')} / {p.get('max', '-')} {unit}")
            lines.append(f"- Норма: {norms.get('opt_min', '?')}-{norms.get('opt_max', '?')} {unit}")
            lines.append("")

    # Рекомендации
    issues = report.issues or []
    if issues:
        lines.append("## Рекомендации")
        lines.append("")
        for i, issue in enumerate(issues[:10], 1):
            severity = (issue.get("severity") or "-").upper()
            lines.append(f"{i}. **[{severity}]** {issue.get('title', '-')}")
            if issue.get("recommendation"):
                lines.append(f"   {issue.get('recommendation')}")
        lines.append("")

    return {"text": "\n".join(lines), "format": "markdown"}


def render_visual(report: HealthReport) -> dict:
    """Виджеты для Workspace — ГАРАНТИРОВАННО life_support + компактный health_score"""
    
    # 1. Индекс здоровья (компактный)
    widgets = [
        {
            "type": "health_score",
            "data": {
                "score": report.score,
                "status": report.status,
                "sub_scores": report.sub_scores,
            },
            "size": "medium",
        },
    ]

    # 2. Индекс жизнеобеспечения — ВСЕГДА добавляем если есть данные в life_support
    life_support = report.life_support or {}
    log.info("render_visual life_support", 
             has_data=bool(life_support),
             score=life_support.get("score"),
             status=life_support.get("status"))
    
    # Добавляем если есть score ИЛИ есть params (даже с NO_DATA)
    if life_support.get("score") is not None or life_support.get("params"):
        widgets.append({
            "type": "life_support_card",
            "data": life_support,
            "size": "medium",
        })
        log.info("life_support_card added to widgets")
    else:
        log.warning("life_support_card NOT added — life_support is empty")

    # 3. Остальные виджеты
    env = report.environmental or {}
    if env:
        widgets.append({"type": "environmental_panel", "data": env, "size": "wide"})

    alarms = report.alarms or {}
    if alarms:
        widgets.append({"type": "alarms_panel", "data": alarms, "size": "wide"})

    energy = report.energy or {}
    if energy:
        widgets.append({"type": "energy_panel", "data": energy, "size": "wide"})

    if report.stats:
        widgets.append({"type": "stats_cards", "data": report.stats, "size": "wide"})

    if report.issues:
        widgets.append({"type": "issues_list", "data": {"issues": report.issues}, "size": "wide"})

    log.info("render_visual widgets", 
             count=len(widgets),
             types=[w.get("type") for w in widgets])

    return {"widgets": widgets}


def render_all(report: HealthReport) -> dict:
    return {
        "voice": render_voice(report),
        "narrative": render_narrative(report),
        "visual": render_visual(report),
    }
