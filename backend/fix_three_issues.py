from pathlib import Path

print('=== fix_three_issues.py ===')
print()

# ============================================================================
# 1. Переносим build_analytics_prompt() из prompts.py в llm/analyzer.py
# ============================================================================
prompts_path = Path('modules/analytics/prompts.py')
prompts_content = '''"""Промпты для analytics-модуля"""

ANALYTICS_SYSTEM_PROMPT = """Ты — старший инженер-аналитик SCADA-системы промышленного здания.

Твоя задача — на основе предоставленных данных аналитики (тренды, корреляции, топ проблем) дать:
1. Краткое резюме ситуации (1-2 предложения)
2. Ключевые инсайты (3-5 пунктов)
3. Конкретные рекомендации с ожидаемым эффектом (2-4 пункта)
4. Прогноз развития ситуации на 7 и 30 дней

ПРИНЦИПЫ:
- Говори конкретно и по делу. Без воды.
- Каждое утверждение должно быть основано на цифрах из входных данных.
- Рекомендации должны быть выполнимыми инженером/техником.
- Указывай ожидаемый эффект в баллах здоровья или физических единицах.
- Прогнозы должны учитывать линейный тренд (slope_per_day) и R².
- Если есть корреляция между параметрами — упомяни это как возможную причину.

ФОРМАТ ОТВЕТА (СТРОГО JSON, без markdown):
{
  "summary": "1-2 предложения о текущем состоянии",
  "insights": [
    "Инсайт 1 с конкретными цифрами",
    "Инсайт 2 с конкретными цифрами",
    "Инсайт 3 с конкретными цифрами"
  ],
  "recommendations": [
    {
      "action": "Конкретное действие (например: проверьте вентиляцию в Зоне 2)",
      "impact": "+N баллов здоровья или экономия N кВт·ч",
      "effort": "low|medium|high",
      "priority": "low|medium|high|critical"
    }
  ],
  "forecast": {
    "7_days": "Что произойдёт через 7 дней если ничего не менять",
    "30_days": "Что произойдёт через 30 дней если ничего не менять",
    "risk": "low|medium|high"
  }
}

ВАЖНО:
- НЕ выдумывай данные, которых нет в input
- Используй ТОЛЬКО предоставленные числа
- НЕ используй markdown в ответе (только чистый JSON)
- Отвечай на русском языке
"""
'''

prompts_path.write_text(prompts_content, encoding='utf-8', newline='\n')
print('✓ modules/analytics/prompts.py: удалена функция build_analytics_prompt()')

# ============================================================================
# 2. Добавляем build_analytics_prompt() в llm/analyzer.py
# ============================================================================
analyzer_path = Path('modules/analytics/llm/analyzer.py')
if analyzer_path.exists():
    content = analyzer_path.read_text(encoding='utf-8')
    
    # Добавляем функцию после импортов (перед class AnalyticsLLM)
    if 'def build_analytics_prompt' not in content:
        func_code = '''
def build_analytics_prompt(
    trends: dict,
    correlations: list,
    top_issues: list,
    period_days: int,
) -> str:
    """
    Строит user prompt с данными аналитики.
    """
    lines = [
        f"Анализирую данные за последние {period_days} дней. Дай аналитический отчёт.",
        "",
        "=== ТРЕНДЫ ПАРАМЕТРОВ ===",
    ]

    for param, trend in trends.items():
        lines.append(f"• {param}:")
        lines.append(f"    Среднее: {trend.get('avg', 'N/A')}")
        lines.append(f"    Диапазон: {trend.get('min', 'N/A')} - {trend.get('max', 'N/A')}")
        lines.append(f"    Тренд: {trend.get('direction', 'N/A')} ({trend.get('slope_per_day', 0):+.3f}/день, R²={trend.get('r_squared', 0):.3f})")
        lines.append(f"    Аномалий: {trend.get('anomalies', 0)} ({trend.get('anomaly_rate', 0):.1%})")
        lines.append(f"    Битых датчиков: {trend.get('outliers_count', 0)}")
        lines.append("")

    lines.append("=== КОРРЕЛЯЦИИ ===")
    if correlations:
        for corr in correlations[:5]:
            lines.append(f"• {corr['params'][0]} ↔ {corr['params'][1]}: r={corr['coefficient']:+.3f} ({corr['interpretation']}, {corr['strength']})")
    else:
        lines.append("• Сильных корреляций не обнаружено")
    lines.append("")

    lines.append("=== ТОП ПРОБЛЕМ (по влиянию на health score) ===")
    if top_issues:
        for i, issue in enumerate(top_issues[:5], 1):
            lines.append(f"{i}. {issue['param']}: impact={issue['impact']:+.1f} баллов, severity={issue['severity']}")
            lines.append(f"   Причина: {issue['reason']}")
            if issue.get('days_to_critical'):
                lines.append(f"   Дней до критического уровня: {issue['days_to_critical']}")
    else:
        lines.append("• Серьёзных проблем не обнаружено")
    lines.append("")

    lines.append("=== ТВОЯ ЗАДАЧА ===")
    lines.append("Сгенерируй отчёт в СТРОГОМ JSON-формате согласно системному промпту.")
    lines.append("Используй реальные цифры из данных выше. Не выдумывай.")

    return "\\n".join(lines)


'''
        # Вставляем перед class AnalyticsLLM
        content = content.replace(
            'class AnalyticsLLM:',
            func_code + 'class AnalyticsLLM:'
        )
        analyzer_path.write_text(content, encoding='utf-8', newline='\n')
        print('✓ modules/analytics/llm/analyzer.py: добавлена build_analytics_prompt()')
    else:
        print('ℹ modules/analytics/llm/analyzer.py: build_analytics_prompt уже есть')

# ============================================================================
# 3. Добавляем фильтр в module_registry.py (только строки в prompts)
# ============================================================================
registry_path = Path('core/module_registry.py')
if registry_path.exists():
    content = registry_path.read_text(encoding='utf-8')
    
    # Ищем блок загрузки prompts
    old_block = '''        # Load prompts
        prompts_module = importlib.import_module(f"modules.{self.name}.prompts")
        self.prompts = {
            name: getattr(prompts_module, name)
            for name in dir(prompts_module)
            if not name.startswith("_")
        }'''
    
    new_block = '''        # Load prompts (только строки, функции игнорируем)
        prompts_module = importlib.import_module(f"modules.{self.name}.prompts")
        self.prompts = {
            name: getattr(prompts_module, name)
            for name in dir(prompts_module)
            if not name.startswith("_") and isinstance(getattr(prompts_module, name), str)
        }'''
    
    if old_block in content:
        content = content.replace(old_block, new_block)
        registry_path.write_text(content, encoding='utf-8', newline='\n')
        print('✓ core/module_registry.py: добавлен фильтр isinstance(..., str) для prompts')
    else:
        print('⚠ core/module_registry.py: не найден точный блок для замены')

# ============================================================================
# 4. Добавляем хендлер analytics в chat endpoint
# ============================================================================
chat_path = Path('api/routes/chat.py')
if chat_path.exists():
    content = chat_path.read_text(encoding='utf-8')
    
    # Добавляем ANALYTICS_KEYWORDS после HEALTH_KEYWORDS
    if 'ANALYTICS_KEYWORDS' not in content:
        content = content.replace(
            'HEALTH_KEYWORDS = ["здоров", "состояни", "аналитик", "проблем", "авари", "диагност", "отчёт", "что с", "как дела"]',
            'HEALTH_KEYWORDS = ["здоров", "состояни", "проблем", "авари", "диагност", "отчёт", "что с", "как дела"]\nANALYTICS_KEYWORDS = ["аналитик", "тренд", "прогноз", "рекомендац", "корреляц", "analytics"]'
        )
        print('✓ api/routes/chat.py: добавлен ANALYTICS_KEYWORDS (убрал "аналитик" из HEALTH)')
    
    # Добавляем функцию is_analytics_query и handle_analytics_query
    if 'def is_analytics_query' not in content:
        analytics_func = '''

def is_analytics_query(message: str) -> bool:
    """Проверяет запрос на аналитику"""
    lower = message.lower()
    return any(kw in lower for kw in ANALYTICS_KEYWORDS)


async def handle_analytics_query(message: str, provider) -> ChatResponse:
    """Обрабатывает запрос на аналитику"""
    try:
        from modules.analytics.collectors.history import collect_history
        from modules.analytics.analyzers.trends import analyze_trends
        from modules.analytics.analyzers.correlations import find_correlations
        from modules.analytics.analyzers.aggregators import rank_issues
        from modules.analytics.llm.analyzer import get_analytics_llm
        
        # Собираем данные за 30 дней
        history = await collect_history(days=30, params=None, aggregation="auto")
        trends = analyze_trends(history)
        correlations = find_correlations(history, min_correlation=0.5)
        top_issues = rank_issues(history_data=history, trends_data=trends, top_n=5)
        
        # LLM insights
        llm = get_analytics_llm()
        llm_result = await llm.analyze(
            trends=trends["trends"],
            correlations=correlations,
            top_issues=top_issues,
            period_days=30,
        )
        
        summary = llm_result.get("summary", "Аналитический отчёт готов")
        
        return ChatResponse(
            response=summary,
            status="success",
            visual={
                "widgets": [
                    {"type": "analytics_panel", "data": {}, "size": "wide"}
                ]
            }
        )
    except Exception as e:
        log.error("Analytics query failed", error=str(e))
        return ChatResponse(
            response=f"Не удалось загрузить аналитику: {e}",
            status="error"
        )

'''
        # Вставляем перед def is_health_query
        content = content.replace(
            'def is_health_query(message: str) -> bool:',
            analytics_func + 'def is_health_query(message: str) -> bool:'
        )
        print('✓ api/routes/chat.py: добавлены is_analytics_query() и handle_analytics_query()')
    
    # Добавляем проверку analytics в функцию chat()
    if 'if is_analytics_query(req.message):' not in content:
        content = content.replace(
            '    if is_health_query(req.message):',
            '    if is_analytics_query(req.message):\n        return await handle_analytics_query(req.message, provider)\n\n    if is_health_query(req.message):'
        )
        print('✓ api/routes/chat.py: добавлен вызов handle_analytics_query()')

    chat_path.write_text(content, encoding='utf-8', newline='\n')

# ============================================================================
# 5. Добавляем capability для аналитики в /system/info
# ============================================================================
system_path = Path('api/routes/system.py')
if system_path.exists():
    content = system_path.read_text(encoding='utf-8')
    
    # Ищем где возвращается capabilities
    if '"capabilities":' in content:
        # Добавляем analytics capability
        if '"text": "покажи аналитику"' not in content:
            content = content.replace(
                '"capabilities": [',
                '"capabilities": [\n            {"text": "покажи аналитику", "category": "analytics", "action": "analytics_panel"},'
            )
            system_path.write_text(content, encoding='utf-8', newline='\n')
            print('✓ api/routes/system.py: добавлена capability "покажи аналитику"')
    else:
        print('ℹ api/routes/system.py: capabilities не найдены (добавим вручную)')

print()
print('=' * 60)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 60)
print()
print('1. Сериализация /config/modules:')
print('   • build_analytics_prompt() перенесена из prompts.py в llm/analyzer.py')
print('   • Добавлен фильтр isinstance(..., str) в module_registry.py')
print('   • Теперь prompts содержит только строки (не функции)')
print()
print('2. Чат "аналитика" → analytics_panel (не health):')
print('   • Убран "аналитик" из HEALTH_KEYWORDS')
print('   • Добавлен ANALYTICS_KEYWORDS = ["аналитик", "тренд", "прогноз", ...]')
print('   • Добавлен хендлер handle_analytics_query()')
print('   • Возвращает widget type: "analytics_panel"')
print()
print('3. Подсказки в инфопанели:')
print('   • Добавлена capability "покажи аналитику" в /system/info')
print('   • Появится в списке быстрых команд в UI')
print()
print('Backend перезагрузится автоматически (hot-reload).')
print()
print('Проверка:')
print('  curl http://localhost:8081/config/modules')
print('  curl http://localhost:8081/system/info')
print()
print('В чате:')
print('  • "покажи аналитику" → откроет AnalyticsPanel')
print('  • "как здоровье здания" → откроет HealthScore')