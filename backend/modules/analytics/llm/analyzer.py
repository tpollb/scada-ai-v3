"""AnalyticsLLM — генерация insights, recommendations, forecasts через LLM"""
import json
from typing import Any
from structlog import get_logger

log = get_logger()



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

    return "\n".join(lines)


class AnalyticsLLM:
    """
    Обёртка над LLM для генерации аналитических отчётов.
    
    Использует core.llm.factory.get_provider() для получения провайдера.
    Gracefully деградирует если LLM недоступен — возвращает fallback.
    
    API провайдера:
        provider.generate(system: str, user: str) -> str
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
        from modules.analytics.prompts import ANALYTICS_SYSTEM_PROMPT
        
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
            # Вызываем LLM с правильной сигнатурой: generate(system, user)
            log.info(
                "Calling LLM for analytics",
                system_chars=len(ANALYTICS_SYSTEM_PROMPT),
                user_chars=len(user_prompt),
            )
            
            response_text = await provider.generate(
                ANALYTICS_SYSTEM_PROMPT,
                user_prompt,
            )
            
            if not response_text:
                log.warning("LLM returned empty response")
                return self._fallback(trends, correlations, top_issues, llm_error="Empty response")
            
            # Извлекаем JSON из ответа (может быть обёрнут в ```json ... ```)
            json_data = self._extract_json(response_text)
            
            if json_data is None:
                log.warning("LLM returned non-JSON response", response=response_text[:300])
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
                summary_len=len(result["summary"]),
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
