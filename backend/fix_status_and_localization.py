from pathlib import Path

print('=== fix_status_and_localization.py ===')
print()

# ============================================================================
# 1. chat.py — пересчитываем статус детерминированно после LLM
# ============================================================================
chat_path = Path('api/routes/chat.py')
chat = chat_path.read_text(encoding='utf-8')

old_parsed_block = '''    if parsed:
        log.info("JSON parsed from LLM", score=parsed.get("score"), status=parsed.get("status"))

        # ВАЖНО: life_support ВСЕГДА считаем на основе РЕАЛЬНЫХ данных из БД, не LLM
        from modules.health.analysis import _compute_life_support_index
        real_life_support = _compute_life_support_index(env)
        log.info("life_support computed from real env",
                 score=real_life_support.get("score"),
                 status=real_life_support.get("status"))

        report = HealthReport(
            score=parsed.get("score", 50),
            status=parsed.get("status", "UNKNOWN"),
            summary=parsed.get("summary", ""),'''

new_parsed_block = '''    if parsed:
        llm_score = parsed.get("score", 50)
        llm_status = parsed.get("status", "UNKNOWN")
        log.info("JSON parsed from LLM", score=llm_score, llm_status=llm_status)

        # ВАЖНО: статус пересчитываем ДЕТЕРМИНИРОВАННО на основе score
        # LLM часто ошибается со статусом, поэтому не доверяем ему
        if llm_score < 30:
            status = "CRITICAL"
        elif llm_score < 60:
            status = "WARNING"
        elif llm_score < 85:
            status = "GOOD"
        else:
            status = "EXCELLENT"

        if status != llm_status:
            log.warning("LLM status overridden",
                        llm_status=llm_status,
                        deterministic_status=status,
                        score=llm_score)

        # ВАЖНО: life_support ВСЕГДА считаем на основе РЕАЛЬНЫХ данных из БД, не LLM
        from modules.health.analysis import _compute_life_support_index
        real_life_support = _compute_life_support_index(env)
        log.info("life_support computed from real env",
                 score=real_life_support.get("score"),
                 status=real_life_support.get("status"))

        report = HealthReport(
            score=llm_score,
            status=status,
            summary=parsed.get("summary", ""),'''

if old_parsed_block in chat:
    chat = chat.replace(old_parsed_block, new_parsed_block)
    chat_path.write_text(chat, encoding='utf-8', newline='\n')
    print('✓ chat.py: статус теперь пересчитывается детерминированно')
    print('  LLM возвращает score → мы сами определяем status по формуле')
    print('  Если LLM вернула WRONG status → логируем warning и исправляем')
else:
    print('⚠ Не нашёл точный паттерн parsed блока в chat.py')
    # Показываем контекст
    for i, line in enumerate(chat.split('\n'), 1):
        if 'parsed' in line.lower() and ('score' in line.lower() or 'status' in line.lower()):
            print(f'  {i}: {line}')

print()

# ============================================================================
# 2. renderers.py — добавляем status_ru в виджеты (повторное применение)
# ============================================================================
renderers_path = Path('modules/health/renderers.py')
content = renderers_path.read_text(encoding='utf-8')

# Проверяем есть ли уже импорт локализации
has_localization_import = 'from .localization import' in content

if not has_localization_import:
    # Добавляем импорт
    content = content.replace(
        'from .analysis import HealthReport',
        'from .analysis import HealthReport\nfrom .localization import (\n    STATUS_RU, SEVERITY_RU, PRIORITY_RU, PARAM_LABELS_RU,\n    translate_status, translate_severity, translate_priority\n)'
    )
    print('✓ renderers.py: добавлен импорт локализации')
else:
    print('ℹ renderers.py: импорт локализации уже есть')

# Добавляем status_ru в health_score виджет
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
    print('✓ renderers.py: добавлен status_ru в health_score виджет')
elif '"status_ru"' in content:
    print('ℹ renderers.py: status_ru уже есть в health_score')
else:
    print('⚠ Не нашёл точный паттерн health_score виджета')

# Добавляем status_ru в life_support_card
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
    print('✓ renderers.py: добавлен status_ru в life_support_card')
elif 'localized_life' in content:
    print('ℹ renderers.py: life_support локализация уже есть')
else:
    print('⚠ Не нашёл точный паттерн life_support_card')

# Локализуем alarms by_priority
old_alarms = '''    alarms = report.alarms or {}
    if alarms:
        widgets.append({"type": "alarms_panel", "data": alarms, "size": "wide"})'''

new_alarms = '''    alarms = report.alarms or {}
    if alarms:
        localized_alarms = dict(alarms)
        by_priority = alarms.get("by_priority", {}) or {}
        localized_alarms["by_priority_ru"] = {
            translate_priority(k): v for k, v in by_priority.items()
        }
        widgets.append({"type": "alarms_panel", "data": localized_alarms, "size": "wide"})'''

if old_alarms in content:
    content = content.replace(old_alarms, new_alarms)
    print('✓ renderers.py: добавлен by_priority_ru в alarms_panel')
elif 'by_priority_ru' in content:
    print('ℹ renderers.py: alarms локализация уже есть')
else:
    print('⚠ Не нашёл точный паттерн alarms_panel')

renderers_path.write_text(content, encoding='utf-8', newline='\n')
print(f'✓ Обновлён: {renderers_path}')

print()
print('=' * 60)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 60)
print('1. chat.py: статус больше НЕ берётся от LLM')
print('   Score от LLM → детерминированный status по формуле:')
print('   <30=CRITICAL, <60=WARNING, <85=GOOD, >=85=EXCELLENT')
print()
print('2. renderers.py: status_ru добавлен в виджеты')
print('   health_score → data.status_ru')
print('   life_support_card → data.status_ru + params.*.status_ru')
print('   alarms_panel → data.by_priority_ru')
print()
print('Проверка:')
print('  python -c "from modules.health.localization import translate_status; print(translate_status(\'GOOD\'))"')
print('  Должно вывести: Хорошо')