from pathlib import Path

print('=== apply_localization.py ===')
print()

# ============================================================================
# 1. Создаём modules/health/localization.py
# ============================================================================
localization_content = '''"""Локализация статусов и severity для модуля health"""

# Статусы системы и индекса жизнеобеспечения
STATUS_RU = {
    "EXCELLENT": "Отлично",
    "GOOD": "Хорошо",
    "WARNING": "Внимание",
    "CRITICAL": "Критично",
    "NO_DATA": "Нет данных",
    "UNKNOWN": "Неизвестно",
}

# Severity в issues
SEVERITY_RU = {
    "critical": "Критический",
    "major": "Высокий",
    "warning": "Средний",
    "info": "Низкий",
}

# Приоритеты аварий (by_priority ключи)
PRIORITY_RU = {
    "high": "Высокий",
    "medium": "Средний",
    "low": "Низкий",
}

# Подписи параметров жизнеобеспечения
PARAM_LABELS_RU = {
    "co2": "CO2",
    "temperature": "Температура",
    "voc": "VOC",
    "humidity": "Влажность",
    "pressure": "Давление",
}


def translate_status(value: str) -> str:
    """Переводит status в русский. Возвращает оригинал если нет в словаре."""
    if not value:
        return "-"
    return STATUS_RU.get(value.upper(), value)


def translate_severity(value: str) -> str:
    """Переводит severity в русский. Возвращает оригинал если нет в словаре."""
    if not value:
        return "-"
    return SEVERITY_RU.get(value.lower(), value)


def translate_priority(value: str) -> str:
    """Переводит priority в русский. Возвращает оригинал если нет в словаре."""
    if not value:
        return "-"
    return PRIORITY_RU.get(value.lower(), value)
'''

loc_path = Path('modules/health/localization.py')
loc_path.write_text(localization_content, encoding='utf-8', newline='\n')
print(f'✓ Создан: {loc_path}')

# ============================================================================
# 2. Обновляем modules/health/renderers.py
# ============================================================================
renderers_path = Path('modules/health/renderers.py')
content = renderers_path.read_text(encoding='utf-8')

# 2.1. Добавляем импорт локализации
if 'from .localization import' not in content:
    content = content.replace(
        'from .analysis import HealthReport',
        'from .analysis import HealthReport\nfrom .localization import (\n    STATUS_RU, SEVERITY_RU, PRIORITY_RU, PARAM_LABELS_RU,\n    translate_status, translate_severity, translate_priority\n)'
    )
    print('✓ Добавлен импорт локализации в renderers.py')
else:
    print('⚠ Импорт локализации уже есть')

# 2.2. render_voice — заменяем локальный status_ru на общий
old_voice_status = '''    status_ru = {
        "CRITICAL": "критическое", "WARNING": "требует внимания",
        "GOOD": "нормальное", "EXCELLENT": "отличное",
    }.get(report.status, "неизвестное")'''

new_voice_status = '''    # Используем единую локализацию (нижний регистр для естественной речи)
    status_ru_map = {
        "CRITICAL": "критическое", "WARNING": "требует внимания",
        "GOOD": "нормальное", "EXCELLENT": "отличное",
        "NO_DATA": "нет данных", "UNKNOWN": "неизвестное",
    }
    status_ru = status_ru_map.get(report.status, translate_status(report.status).lower())'''

if old_voice_status in content:
    content = content.replace(old_voice_status, new_voice_status)
    print('✓ render_voice: обновлена локализация статуса')
else:
    print('⚠ Не нашёл точный паттерн status_ru в render_voice')

# 2.3. render_narrative — локализуем статусы
content = content.replace(
    'f"**Композитный индекс:** {report.score}/100 ({report.status})"',
    'f"**Композитный индекс:** {report.score}/100 ({translate_status(report.status)})"'
)
content = content.replace(
    "f\"**Индекс жизнеобеспечения:** {life.get('score')}/100 ({life.get('status')})\"",
    "f\"**Индекс жизнеобеспечения:** {life.get('score')}/100 ({translate_status(life.get('status', ''))})\""
)
content = content.replace(
    "f\"**Общая оценка:** {life.get('score')}/100 ({life.get('status')})\"",
    "f\"**Общая оценка:** {life.get('score')}/100 ({translate_status(life.get('status', ''))})\""
)
print('✓ render_narrative: локализованы статусы')

# 2.4. render_narrative — локализуем severity в рекомендациях
old_severity = '''            severity = (issue.get("severity") or "-").upper()
            lines.append(f"{i}. **[{severity}]** {issue.get(\'title\', \'-\')}")'''

new_severity = '''            severity_raw = issue.get("severity") or "-"
            severity_ru = translate_severity(severity_raw).upper()
            lines.append(f"{i}. **[{severity_ru}]** {issue.get(\'title\', \'-\')}")'''

if old_severity in content:
    content = content.replace(old_severity, new_severity)
    print('✓ render_narrative: локализован severity в рекомендациях')
else:
    print('⚠ Не нашёл точный паттерн severity в render_narrative')

# 2.5. render_visual — добавляем status_ru в health_score виджет
old_health_widget = '''        {
            "type": "health_score",
            "data": {
                "score": report.score,
                "status": report.status,
                "sub_scores": report.sub_scores,
            },
            "size": "medium",
        },'''

new_health_widget = '''        {
            "type": "health_score",
            "data": {
                "score": report.score,
                "status": report.status,
                "status_ru": translate_status(report.status),
                "sub_scores": report.sub_scores,
            },
            "size": "medium",
        },'''

if old_health_widget in content:
    content = content.replace(old_health_widget, new_health_widget)
    print('✓ render_visual: добавлен status_ru в health_score виджет')
else:
    print('⚠ Не нашёл точный паттерн health_score виджета')

# 2.6. render_visual — добавляем status_ru в life_support_card
old_life_add = '''    if life_support.get("score") is not None or life_support.get("params"):
        widgets.append({
            "type": "life_support_card",
            "data": life_support,
            "size": "medium",
        })'''

new_life_add = '''    if life_support.get("score") is not None or life_support.get("params"):
        # Добавляем локализованные поля для frontend
        localized_life = dict(life_support)
        localized_life["status_ru"] = translate_status(life_support.get("status", ""))
        # Локализуем статусы параметров
        if "params" in localized_life and isinstance(localized_life["params"], dict):
            for param_key, param_data in localized_life["params"].items():
                if isinstance(param_data, dict) and "status" in param_data:
                    param_data["status_ru"] = translate_status(param_data["status"])
                    param_data["label_ru"] = PARAM_LABELS_RU.get(param_key, param_key)
        widgets.append({
            "type": "life_support_card",
            "data": localized_life,
            "size": "medium",
        })'''

if old_life_add in content:
    content = content.replace(old_life_add, new_life_add)
    print('✓ render_visual: добавлен status_ru в life_support_card виджет')
else:
    print('⚠ Не нашёл точный паттерн life_support_card')

# 2.7. render_visual — локализуем alarms by_priority
old_alarms = '''    alarms = report.alarms or {}
    if alarms:
        widgets.append({"type": "alarms_panel", "data": alarms, "size": "wide"})'''

new_alarms = '''    alarms = report.alarms or {}
    if alarms:
        # Локализуем by_priority для frontend
        localized_alarms = dict(alarms)
        by_priority = alarms.get("by_priority", {}) or {}
        localized_alarms["by_priority_ru"] = {
            translate_priority(k): v for k, v in by_priority.items()
        }
        widgets.append({"type": "alarms_panel", "data": localized_alarms, "size": "wide"})'''

if old_alarms in content:
    content = content.replace(old_alarms, new_alarms)
    print('✓ render_visual: добавлен by_priority_ru в alarms_panel')
else:
    print('⚠ Не нашёл точный паттерн alarms_panel')

renderers_path.write_text(content, encoding='utf-8', newline='\n')
print(f'✓ Обновлён: {renderers_path}')

print()
print('=' * 60)
print('БЭКЕНД ГОТОВ. Что изменилось:')
print('=' * 60)
print('1. modules/health/localization.py — создан')
print('2. modules/health/renderers.py — обновлён:')
print('   • render_voice: единая локализация статуса')
print('   • render_narrative: русские статусы и severity')
print('   • render_visual: status_ru в health_score и life_support_card')
print('   • render_visual: by_priority_ru в alarms_panel')
print()
print('ВАЖНО: analysis.py НЕ изменён — API стабилен.')
print()
print('Проверка импорта:')
print('  python -c "from modules.health.localization import STATUS_RU; print(STATUS_RU)"')
print()
print('СЛЕДУЮЩИЙ ШАГ: фронтенд (HealthScoreCard + LifeSupportCard)')