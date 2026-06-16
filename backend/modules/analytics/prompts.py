"""Промпты для analytics-модуля"""

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


def build_analytics_prompt(
    trends: dict,
    correlations: list,
    top_issues: list,
    period_days: int,
) -> str:
    """
    Строит user prompt с данными аналитики.
    """
    import json
    
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
    
    return "\n".join(lines)
