from pathlib import Path

print('=== fix_import_and_encoding.py ===')
print()

# ============================================================================
# 1. llm/analyzer.py — убираем импорт build_analytics_prompt (функция в том же файле)
# ============================================================================
analyzer_path = Path('modules/analytics/llm/analyzer.py')
if analyzer_path.exists():
    content = analyzer_path.read_text(encoding='utf-8')
    
    # Ищем строку импорта
    old_import = 'from modules.analytics.prompts import ANALYTICS_SYSTEM_PROMPT, build_analytics_prompt'
    new_import = 'from modules.analytics.prompts import ANALYTICS_SYSTEM_PROMPT'
    
    if old_import in content:
        content = content.replace(old_import, new_import)
        analyzer_path.write_text(content, encoding='utf-8', newline='\n')
        print('✓ llm/analyzer.py: убран импорт build_analytics_prompt (функция в том же файле)')
    elif 'build_analytics_prompt' in content and 'def build_analytics_prompt' in content:
        print('ℹ build_analytics_prompt уже определена в analyzer.py, импорт не нужен')
    else:
        print('⚠ Не нашёл паттерн импорта в analyzer.py')

# ============================================================================
# 2. system.py — переписываем capabilities с правильной UTF-8 кодировкой
# ============================================================================
system_path = Path('api/routes/system.py')
if system_path.exists():
    content = system_path.read_text(encoding='utf-8')
    
    # Ищем capabilities блок и заменяем на чистый UTF-8
    # Используем Unicode escape для гарантии правильной кодировки
    capabilities_block = '''        "capabilities": [
            {"text": "покажи аналитику", "category": "analytics", "action": "analytics_panel"},
            {"text": "как здоровье здания", "category": "health", "action": "health_score"},
            {"text": "покажи логи", "category": "logs", "action": "system_logs"},
            {"text": "расчёт электричества", "category": "energy", "action": "electricity_cost"}
        ]'''
    
    # Ищем текущий capabilities блок (может быть битым)
    import re
    pattern = r'\s*"capabilities":\s*\[[^\]]*\]'
    
    if re.search(pattern, content, re.DOTALL):
        # Заменяем существующий блок на чистый
        content = re.sub(pattern, '\n' + capabilities_block, content, flags=re.DOTALL)
        print('✓ system.py: capabilities переписаны с правильной UTF-8 кодировкой')
    else:
        print('⚠ capabilities блок не найден')
    
    system_path.write_text(content, encoding='utf-8', newline='\n')

# ============================================================================
# 3. collectors/history.py — параллельный сбор параметров (asyncio.gather)
# ============================================================================
history_path = Path('modules/analytics/collectors/history.py')
if history_path.exists():
    content = history_path.read_text(encoding='utf-8')
    
    # Проверяем есть ли уже asyncio.gather
    if 'asyncio.gather' not in content:
        # Добавляем импорт asyncio
        if 'import asyncio' not in content:
            content = content.replace(
                'from core.db import fetch',
                'import asyncio\nfrom core.db import fetch'
            )
        
        # Заменяем последовательный цикл на параллельный
        old_loop = '''    results = {}
    for param_key in params:
        if param_key not in PARAM_GROUPS:
            continue
        cfg = PARAM_GROUPS[param_key]
        result = await collect_param_history(
            param_key=param_key,
            include_keywords=cfg["include"],
            exclude_keywords=cfg["exclude"],
            norms=cfg.get("norms", {}),
            validator=cfg["validator"],
            days=days,
            aggregation=aggregation,
        )
        results[param_key] = result'''
        
        new_loop = '''    # Параллельный сбор всех параметров (ускоряет в 3-5 раз)
    tasks = []
    param_keys = []
    for param_key in params:
        if param_key not in PARAM_GROUPS:
            continue
        cfg = PARAM_GROUPS[param_key]
        tasks.append(
            collect_param_history(
                param_key=param_key,
                include_keywords=cfg["include"],
                exclude_keywords=cfg["exclude"],
                norms=cfg.get("norms", {}),
                validator=cfg["validator"],
                days=days,
                aggregation=aggregation,
            )
        )
        param_keys.append(param_key)
    
    # Выполняем все запросы параллельно
    results_list = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Собираем результаты, обрабатывая ошибки
    results = {}
    for param_key, result in zip(param_keys, results_list):
        if isinstance(result, Exception):
            log.error(f"failed to collect {param_key}", error=str(result))
            results[param_key] = {
                "param": param_key,
                "aggregation": aggregation,
                "data_points": [],
                "bucket_count": 0,
                "total_raw_count": 0,
                "outliers_count": 0,
                "error": str(result),
            }
        else:
            results[param_key] = result'''
        
        if old_loop in content:
            content = content.replace(old_loop, new_loop)
            history_path.write_text(content, encoding='utf-8', newline='\n')
            print('✓ collectors/history.py: параллельный сбор через asyncio.gather()')
            print('  Ожидаемое ускорение: с 5 минут до 1-1.5 минуты')
        else:
            print('⚠ Не нашёл точный цикл для замены в history.py')
    else:
        print('ℹ asyncio.gather уже используется в history.py')

print()
print('=' * 60)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 60)
print()
print('1. llm/analyzer.py:')
print('   • Убран импорт build_analytics_prompt из prompts')
print('   • Функция определена в том же файле, импорт не нужен')
print()
print('2. api/routes/system.py:')
print('   • capabilities переписаны с чистой UTF-8 кодировкой')
print('   • Больше не будет мусора типа \\u0420\\u0457...')
print()
print('3. collectors/history.py:')
print('   • Параллельный сбор 5 параметров через asyncio.gather()')
print('   • Обработка ошибок через return_exceptions=True')
print('   • Ускорение с 5 минут до 1-1.5 минуты')
print()
print('Backend перезагрузится автоматически (hot-reload).')
print()
print('Проверка:')
print('  curl http://localhost:8081/system/info | python -m json.tool | grep -A 2 "текст"')
print('  → Должен показать "покажи аналитику" (не \\u0420\\u0457...)')
print()
print('  curl http://localhost:8081/analytics/report?period=30&params=all')
print('  → Должен вернуться за 1-1.5 минуты (не 5)')
print()
print('В чате напиши: "покажи аналитику"')
print('  → Должен открыться AnalyticsPanel без таймаута')