from pathlib import Path

print('=== add_llm_layer.py ===')
print()

# ============================================================================
# 1. Создаём папку llm
# ============================================================================
llm_dir = Path('modules/analytics/llm')
llm_dir.mkdir(exist_ok=True)

# ============================================================================
# 2. llm/__init__.py
# ============================================================================
(llm_dir / '__init__.py').write_text(
    '"""LLM layer for analytics module — insights, recommendations, forecasts"""\n',
    encoding='utf-8'
)
print('✓ modules/analytics/llm/__init__.py')

# ============================================================================
# 3. llm/analyzer.py — единый класс для вызова LLM
# ============================================================================
analyzer_content = '''"""AnalyticsLLM — генерация insights, recommendations, forecasts через LLM"""
import json
from typing import Any
from structlog import get_logger

log = get_logger()


class AnalyticsLLM:
    """
    Обёртка над LLM для генерации аналитических отчётов.
    
    Использует core.llm.factory.get_provider() для получения провайдера.
    Gracefully деградирует если LLM недоступен — возвращает fallback.
    """
    
    def __init__(self):
        self._provider = None
    
    def _get_provider(self):
        """Ленивая инициализация провайдера"""
        if self._provider is None:
            try:
                from core.llm.factory import get_provider
                self._provider = get_provider()
            except Exception as e:
                log.error("Failed to get LLM provider", error=str(e))
                raise
        return self._provider
    
    async def analyze(
        self,
        trends: dict,
        correlations: list,
        top_issues: list,
        period_days: int,
    ) -> dict:
        """
        Генерирует insights, recommendations и forecast через LLM.
        
        Returns:
            {
                "summary": "Главная проблема — рост влажности...",
                "insights": [
                    "Влажность растёт на 0.74% в день...",
                    "75% датчиков VOC вышли из строя..."
                ],
                "recommendations": [
                    {
                        "action": "Проверьте систему вентиляции в Зоне 2",
                        "impact": "+8 баллов здоровья",
                        "effort": "medium",
                        "priority": "high"
                    }
                ],
                "forecast": {
                    "7_days": "Влажность достигнет 50%",
                    "30_days": "Влажность достигнет 60% (верхняя граница нормы)",
                    "risk": "medium"
                }
            }
        
        При ошибке LLM возвращает fallback с полем "llm_error".
        """
        from modules.analytics.prompts import ANALYTICS_SYSTEM_PROMPT, build_analytics_prompt
        
        try:
            provider = self._get_provider()
        except Exception as e:
            log.warning("LLM unavailable, using fallback", error=str(e))
            return self._fallback(trends, correlations, top_issues, llm_error=f"Provider unavailable: {e}")
        
        # Строим user prompt с данными
        user_prompt = build_analytics_prompt(
            trends=trends,
            correlations=correlations,
            top_issues=top_issues,
            period_days=period_days,
        )
        
        try:
            # Вызываем LLM
            log.info("Calling LLM for analytics", prompt_chars=len(user_prompt))
            
            # API может быть разным у разных провайдеров — пробуем разные варианты
            response = None
            if hasattr(provider, 'generate'):
                # Вариант 1: provider.generate(prompt, system_prompt=...)
                try:
                    response = await provider.generate(
                        user_prompt,
                        system_prompt=ANALYTICS_SYSTEM_PROMPT,
                    )
                except TypeError:
                    # Вариант 2: provider.generate(messages=[...])
                    response = await provider.generate([
                        {"role": "system", "content": ANALYTICS_SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ])
            elif hasattr(provider, 'complete'):
                # Вариант 3: provider.complete(messages=[...])
                response = await provider.complete([
                    {"role": "system", "content": ANALYTICS_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ])
            else:
                raise AttributeError(f"Unknown provider API: {dir(provider)}")
            
            # Парсим ответ
            if isinstance(response, str):
                response_text = response
            elif isinstance(response, dict):
                response_text = response.get("text") or response.get("content") or str(response)
            else:
                response_text = str(response)
            
            # Извлекаем JSON из ответа (может быть обёрнут в ```json ... ```)
            json_data = self._extract_json(response_text)
            
            if json_data is None:
                log.warning("LLM returned non-JSON response", response=response_text[:200])
                return self._fallback(trends, correlations, top_issues, llm_error="Non-JSON response")
            
            # Валидация структуры
            result = {
                "summary": json_data.get("summary", ""),
                "insights": json_data.get("insights", []),
                "recommendations": json_data.get("recommendations", []),
                "forecast": json_data.get("forecast", {}),
            }
            
            log.info(
                "LLM analytics ready",
                insights=len(result["insights"]),
                recommendations=len(result["recommendations"]),
            )
            
            return result
            
        except Exception as e:
            log.error("LLM call failed, using fallback", error=str(e))
            return self._fallback(trends, correlations, top_issues, llm_error=str(e))
    
    def _extract_json(self, text: str) -> dict | None:
        """Извлекает JSON из текста (может быть обёрнут в markdown код-блок)"""
        # Убираем markdown код-блоки
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        # Пробуем парсить
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Ищем JSON внутри текста
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(text[start:end+1])
                except json.JSONDecodeError:
                    return None
            return None
    
    def _fallback(
        self,
        trends: dict,
        correlations: list,
        top_issues: list,
        llm_error: str = None,
    ) -> dict:
        """Детерминированный fallback когда LLM недоступен"""
        # Строим summary из топ проблем
        if top_issues:
            worst = top_issues[0]
            summary = f"Главная проблема: {worst['param']} ({worst['reason']})."
            if worst.get("days_to_critical"):
                summary += f" Достигнет критического уровня через {worst['days_to_critical']} дней."
        else:
            summary = "Серьёзных проблем не обнаружено. Все параметры в норме."
        
        # Insights из трендов
        insights = []
        for param_key, trend in trends.items():
            if trend.get("direction") == "rising" and trend.get("r_squared", 0) > 0.3:
                insights.append(f"{param_key} растёт ({trend['slope_per_day']:.2f}/день, R²={trend['r_squared']:.2f})")
            elif trend.get("direction") == "falling" and trend.get("r_squared", 0) > 0.3:
                insights.append(f"{param_key} падает ({trend['slope_per_day']:.2f}/день, R²={trend['r_squared']:.2f})")
        
        # Рекомендации из топ проблем (простые шаблоны)
        recommendations = []
        for issue in top_issues[:3]:
            param = issue["param"]
            if "broken sensors" in issue.get("reason", ""):
                recommendations.append({
                    "action": f"Замените или откалибруйте датчики {param}",
                    "impact": f"+{abs(issue['impact']):.1f} баллов здоровья",
                    "effort": "medium",
                    "priority": "high" if issue["severity"] in ("high", "critical") else "medium",
                })
            elif "Rising" in issue.get("reason", "") or "Falling" in issue.get("reason", ""):
                recommendations.append({
                    "action": f"Проверьте систему управления параметром {param}",
                    "impact": f"+{abs(issue['impact']):.1f} баллов здоровья",
                    "effort": "medium",
                    "priority": "high" if issue.get("days_to_critical", 999) < 30 else "medium",
                })
        
        # Forecast из трендов
        forecast = {}
        for param_key, trend in trends.items():
            slope = trend.get("slope_per_day", 0)
            if abs(slope) > 0.1 and trend.get("r_squared", 0) > 0.3:
                avg = trend.get("avg", 0)
                forecast[f"{param_key}_7_days"] = f"Прогноз через 7 дней: {avg + slope * 7:.2f}"
        
        result = {
            "summary": summary,
            "insights": insights,
            "recommendations": recommendations,
            "forecast": forecast,
        }
        
        if llm_error:
            result["llm_error"] = llm_error
        
        return result


# Singleton instance
_analytics_llm = None


def get_analytics_llm() -> AnalyticsLLM:
    global _analytics_llm
    if _analytics_llm is None:
        _analytics_llm = AnalyticsLLM()
    return _analytics_llm
'''

(llm_dir / 'analyzer.py').write_text(analyzer_content, encoding='utf-8', newline='\n')
print('✓ modules/analytics/llm/analyzer.py: класс AnalyticsLLM с fallback')

# ============================================================================
# 4. Обновляем prompts.py — детальный промпт
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
    
    return "\\n".join(lines)
'''

prompts_path.write_text(prompts_content, encoding='utf-8', newline='\n')
print('✓ modules/analytics/prompts.py: ANALYTICS_SYSTEM_PROMPT + build_analytics_prompt')

# ============================================================================
# 5. Обновляем api/routes/analytics.py — вызов LLM
# ============================================================================
router_path = Path('api/routes/analytics.py')
router_content = '''"""Analytics API — тренды, корреляции, топ проблемы + LLM insights"""
from fastapi import APIRouter, Query
from datetime import datetime
from structlog import get_logger

from modules.analytics.collectors.history import collect_history
from modules.analytics.analyzers.trends import analyze_trends
from modules.analytics.analyzers.correlations import find_correlations
from modules.analytics.analyzers.aggregators import rank_issues
from modules.analytics.llm.analyzer import get_analytics_llm

log = get_logger()
router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/ping")
async def ping():
    """Простой health-check"""
    return {"status": "ok", "time": datetime.now().isoformat()}


@router.get("/report")
async def get_report(
    period: int = Query(30, description="Период в днях (7, 30, 90, 365)"),
    params: str = Query("all", description="Параметры через запятую или 'all'"),
    aggregation: str = Query("auto", description="Агрегация: raw/hourly/daily/auto"),
    min_correlation: float = Query(0.5, description="Минимальный |r| для корреляций"),
    top_issues_count: int = Query(5, description="Количество топ проблем"),
    include_llm: bool = Query(True, description="Включить LLM-анализ (insights, рекомендации, прогнозы)"),
):
    """
    Полный отчёт аналитики: тренды, корреляции, топ проблемы + LLM insights.
    
    Параметры:
      - period: период в днях (7, 30, 90, 365)
      - aggregation: raw/hourly/daily/auto
      - min_correlation: порог для корреляций (default 0.5)
      - top_issues_count: количество топ проблем (default 5)
      - include_llm: вызывать ли LLM (default true)
    
    При include_llm=true возвращает поля:
      - summary: краткое резюме
      - insights: список инсайтов
      - recommendations: список рекомендаций
      - forecast: прогноз на 7/30 дней
    
    При ошибке LLM возвращается fallback с полем llm_error.
    """
    log.info(
        "analytics/report requested",
        period=period,
        params=params,
        aggregation=aggregation,
        min_correlation=min_correlation,
        top_issues_count=top_issues_count,
        include_llm=include_llm,
    )

    # Парсим params
    if params == "all":
        params_list = None
    else:
        params_list = [p.strip() for p in params.split(",")]

    # 1. Собираем историю (с валидацией + агрегацией)
    history = await collect_history(
        days=period,
        params=params_list,
        aggregation=aggregation,
    )

    # 2. Анализируем тренды
    trends = analyze_trends(history)

    # 3. Находим корреляции
    correlations = find_correlations(
        history,
        min_correlation=min_correlation,
    )

    # 4. Ранжируем проблемы
    top_issues = rank_issues(
        history_data=history,
        trends_data=trends,
        top_n=top_issues_count,
    )

    # Базовый ответ
    response = {
        "period_days": period,
        "aggregation": history["aggregation"],
        "collected_at": history["collected_at"],
        "trends": trends["trends"],
        "correlations": correlations,
        "top_issues": top_issues,
    }

    # 5. LLM insights (если включено)
    if include_llm:
        try:
            llm = get_analytics_llm()
            llm_result = await llm.analyze(
                trends=trends["trends"],
                correlations=correlations,
                top_issues=top_issues,
                period_days=period,
            )
            response["summary"] = llm_result.get("summary", "")
            response["insights"] = llm_result.get("insights", [])
            response["recommendations"] = llm_result.get("recommendations", [])
            response["forecast"] = llm_result.get("forecast", {})
            if "llm_error" in llm_result:
                response["llm_error"] = llm_result["llm_error"]
                log.warning("LLM used fallback", error=llm_result["llm_error"])
        except Exception as e:
            log.error("LLM analysis failed", error=str(e))
            response["llm_error"] = str(e)

    log.info(
        "analytics/report ready",
        period=period,
        aggregation=history["aggregation"],
        params=list(trends["trends"].keys()),
        correlations=len(correlations),
        top_issues=len(top_issues),
        has_llm="summary" in response,
    )

    return response
'''

router_path.write_text(router_content, encoding='utf-8', newline='\n')
print('✓ api/routes/analytics.py: добавлен параметр include_llm и вызов AnalyticsLLM')

print()
print('=' * 60)
print('ЧТО ДОБАВЛЕНО:')
print('=' * 60)
print()
print('1. modules/analytics/llm/analyzer.py:')
print('   • Класс AnalyticsLLM с методом analyze()')
print('   • Ленивая инициализация через core.llm.factory.get_provider()')
print('   • Поддержка разных API провайдеров (generate/complete)')
print('   • Парсинг JSON из ответа LLM (включая markdown code blocks)')
print('   • Детерминированный fallback при ошибке LLM')
print('   • get_analytics_llm() — singleton instance')
print()
print('2. modules/analytics/prompts.py:')
print('   • ANALYTICS_SYSTEM_PROMPT — детальный системный промпт')
print('   • build_analytics_prompt() — строит user prompt с данными')
print('   • Требует строгого JSON ответа без markdown')
print()
print('3. api/routes/analytics.py:')
print('   • Новый параметр: include_llm (bool, default=true)')
print('   • При include_llm=true: вызывает LLM и добавляет поля')
print('     summary, insights, recommendations, forecast')
print('   • При ошибке LLM: graceful degradation с полем llm_error')
print()
print('Backend перезагрузится автоматически (hot-reload).')
print()
print('Проверка (с LLM):')
print('  curl "http://localhost:8081/analytics/report?period=30&params=all"')
print()
print('Проверка (без LLM, только детерминированные данные):')
print('  curl "http://localhost:8081/analytics/report?period=30&params=all&include_llm=false"')
print()
print('Ожидаемый результат:')
print('  • summary: "Главная проблема: humidity (Rising 0.74/day...)"')
print('  • insights: ["Влажность растёт на 0.74% в день...", ...]')
print('  • recommendations: [{"action": "Проверьте вентиляцию...", ...}]')
print('  • forecast: {"7_days": "...", "30_days": "...", "risk": "medium"}')