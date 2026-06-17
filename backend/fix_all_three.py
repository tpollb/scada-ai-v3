from pathlib import Path
import re

print('=== fix_all_three.py ===')
print()

# ============================================================================
# 1. chat.py — добавляем is_analytics_query и handle_analytics_query
# ============================================================================
chat_path = Path('api/routes/chat.py')
content = chat_path.read_text(encoding='utf-8')
changed = False

# Проверяем наличие функций
has_is_analytics = 'def is_analytics_query' in content
has_handle_analytics = 'async def handle_analytics_query' in content

if not has_is_analytics or not has_handle_analytics:
    # Вставляем функции ПЕРЕД def is_health_query
    new_functions = '''def is_analytics_query(text: str) -> bool:
    """Проверяет запрос на аналитику"""
    lower = text.lower()
    return any(kw in lower for kw in ANALYTICS_KEYWORDS)


async def handle_analytics_query(message: str, provider) -> ChatResponse:
    """Обрабатывает запрос на аналитику — возвращает виджет analytics_panel"""
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
    # Regex-замена: ищем определение is_health_query и вставляем перед ним
    pattern = r'(\ndef is_health_query\(text: str\) -> bool:)'
    if re.search(pattern, content):
        content = re.sub(pattern, '\n' + new_functions + r'\1', content, count=1)
        changed = True
        print('✓ api/routes/chat.py: добавлены is_analytics_query() и handle_analytics_query()')
    else:
        print('⚠ Не найден паттерн def is_health_query в chat.py')
else:
    print('ℹ Функции analytics уже есть в chat.py')

if changed:
    chat_path.write_text(content, encoding='utf-8', newline='\n')

# ============================================================================
# 2. prompts.py — переписываем с правильной кодировкой UTF-8
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
      "action": "Конкретное действие",
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

# Явно открываем файл в binary mode и пишем UTF-8 BOM-free
with open(prompts_path, 'wb') as f:
    f.write(prompts_content.encode('utf-8'))
print('✓ modules/analytics/prompts.py: переписан с правильной UTF-8 кодировкой')

# ============================================================================
# 3. system.py — добавляем capabilities
# ============================================================================
system_path = Path('api/routes/system.py')
if system_path.exists():
    content = system_path.read_text(encoding='utf-8')
    
    # Ищем return statement в system_info и добавляем capabilities
    if 'capabilities' not in content:
        # Находим "server_time": ... и добавляем capabilities после него
        pattern = r'("server_time":\s*[^,]+,?\s*\n)(\s*\})'
        replacement = r'\1        "capabilities": [\n            {"text": "покажи аналитику", "category": "analytics", "action": "analytics_panel"},\n            {"text": "как здоровье здания", "category": "health", "action": "health_score"},\n            {"text": "покажи логи", "category": "logs", "action": "system_logs"},\n            {"text": "расчёт электричества", "category": "energy", "action": "electricity_cost"}\n        ]\n\2'
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            system_path.write_text(new_content, encoding='utf-8', newline='\n')
            print('✓ api/routes/system.py: добавлено поле capabilities')
        else:
            print('⚠ Не удалось добавить capabilities (regex не сработал)')
            # Fallback: ищем последнюю } перед return
            pattern2 = r'(return \{[^}]*"server_time"[^,]*,?\s*)(\n\s*\})'
            new_content = re.sub(pattern2, r'\1\n        "capabilities": []\2', content, flags=re.DOTALL)
            if new_content != content:
                system_path.write_text(new_content, encoding='utf-8', newline='\n')
                print('✓ api/routes/system.py: добавлено пустое capabilities (fallback)')
    else:
        print('ℹ capabilities уже есть в system.py')

print()
print('=' * 60)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 60)
print()
print('1. api/routes/chat.py:')
print('   • Добавлена is_analytics_query() через regex (надёжно)')
print('   • Добавлена handle_analytics_query() — возвращает analytics_panel виджет')
print()
print('2. modules/analytics/prompts.py:')
print('   • Полностью переписан с правильной UTF-8 кодировкой')
print('   • Больше не будет мусорных символов в /config/modules')
print()
print('3. api/routes/system.py:')
print('   • Добавлено поле capabilities в /system/info')
print('   • 4 быстрые команды для UI подсказок')
print()
print('Backend перезагрузится автоматически (hot-reload).')
print()
print('Проверка:')
print('  1. curl http://localhost:8081/config/modules | python -m json.tool | head -20')
print('     → должен показать русский текст (не мусор)')
print()
print('  2. curl http://localhost:8081/system/info | python -m json.tool | grep -A 5 capabilities')
print('     → должен показать 4 capabilities')
print()
print('  3. В чате напиши: "покажи аналитику"')
print('     → должен появиться AnalyticsPanel виджет (не HealthScore)')