"""Chat API — JSON mode подход (как в v23)"""
import json
import re
import time
from fastapi import APIRouter
from pydantic import BaseModel
from structlog import get_logger

log = get_logger()
router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    response: str
    status: str
    voice: dict | None = None
    visual: dict | None = None
    tool_calls: list[str] = []


HEALTH_KEYWORDS = ["здоров", "состояни", "проблем", "авари", "диагност", "отчёт", "что с", "как дела"]
ANALYTICS_KEYWORDS = ["аналитик", "тренд", "прогноз", "рекомендац", "корреляц", "analytics"]


def is_analytics_query(text: str) -> bool:
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

        log.info("handle_analytics_query returning",
                 summary_len=len(summary),
                 has_trends="trends" in trends,
                 trends_count=len(trends.get("trends", {})),
                 correlations_count=len(correlations),
                 top_issues_count=len(top_issues),
                 has_llm="summary" in llm_result)
        
        return ChatResponse(
            response=summary,
            status="success",
            visual={
                "widgets": [
                    {
                        "type": "analytics_panel",
                        "data": {
                            "period_days": 30,
                            "trends": trends["trends"],
                            "correlations": correlations,
                            "top_issues": top_issues,
                            "summary": llm_result.get("summary", ""),
                            "insights": llm_result.get("insights", []),
                            "recommendations": llm_result.get("recommendations", []),
                            "forecast": llm_result.get("forecast", {})
                        },
                        "size": "wide"
                    }
                ]
            }
        )
    except Exception as e:
        log.error("Analytics query failed", error=str(e))
        return ChatResponse(
            response=f"Не удалось загрузить аналитику: {e}",
            status="error"
        )



def is_health_query(text: str) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in HEALTH_KEYWORDS)


def _extract_json(text: str) -> dict | None:
    """Извлекает JSON из ответа LLM (как в v23)"""
    if not text:
        return None

    # Убираем markdown code blocks
    text = re.sub(r'''```(?:json)?\s*''', ' ', text)
    text = re.sub(r'''\s*```$''', '', text).strip()

    # Прямой парсинг
    try:
        data = json.loads(text)
        if isinstance(data, dict) and "score" in data:
            return data
    except json.JSONDecodeError:
        pass

    # Ищем JSON внутри текста
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and start < end:
        try:
            data = json.loads(text[start:end + 1])
            if isinstance(data, dict) and "score" in data:
                return data
        except json.JSONDecodeError:
            pass

    return None


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    log.info("Chat request", message=req.message, session=req.session_id)

    try:
        from core.llm import get_provider
        provider = get_provider()
    except Exception as e:
        log.error("LLM provider failed", error=str(e))
        return ChatResponse(
            response=f"⚠️ LLM не настроен: {e}",
            status="error",
        )

    if is_analytics_query(req.message):
        return await handle_analytics_query(req.message, provider)

    if is_health_query(req.message):
        return await handle_health_query(req.message, provider)

    # Проверяем есть ли tools
    from core.tool_executor import get_executor
    executor = get_executor()
    tools_schemas = executor.get_schemas()
    
    system = "Ты — AI-ассистент для оператора SCADA-системы. Отвечай на русском, кратко. Используй доступные инструменты когда это уместно."
    
    try:
        if tools_schemas:
            # Запрос с Tool Use
            log.info("Using tool calling", tools_count=len(tools_schemas))
            result = await provider.generate_with_tools(
                system=system,
                user=req.message,
                tools=tools_schemas,
                tool_executor=executor,
                max_iterations=5,
            )
            
            tool_names = [tc.name for tc in result.get("tool_calls", [])]
            if tool_names:
                log.info("Tools were called", tools=tool_names)
            
            return ChatResponse(
                response=result.get("text") or "Не удалось получить ответ.",
                status="ok",
                tool_calls=tool_names,
            )
        else:
            # Простой запрос — без Tool Use
            log.info("No tools available, using simple generate")
            text = await provider.generate(system, req.message)
            return ChatResponse(response=text or "Не удалось получить ответ.", status="ok")
    except Exception as e:
        log.error("Chat failed", error=str(e))
        return ChatResponse(response=f"⚠️ Ошибка: {e}", status="error")


async def handle_health_query(message: str, provider) -> ChatResponse:
    """Health-запрос: собираем данные → LLM → JSON → рендер"""
    try:
        from modules.health.prompts import HEALTH_SYSTEM_PROMPT
        from modules.health.data_collectors import collect_all_health_data
        from modules.health.analysis import compute_health_report, HealthReport
        from modules.health.renderers import render_all
    except Exception as e:
        log.error("Health module import failed", error=str(e))
        return ChatResponse(response=f"⚠️ Модуль health недоступен: {e}", status="error")

    # 1. Собираем данные из БД
    log.info("Collecting health data from DB")
    t_start = time.time()
    try:
        data = await collect_all_health_data(period_hours=24)
    except Exception as e:
        log.error("Data collection failed", error=str(e))
        return ChatResponse(response=f"⚠️ Не удалось собрать данные из БД: {e}", status="error")

    env = data.get("environmental", {})
    equip = data.get("equipment", {})
    alarms = data.get("alarms_summary", {})

    log.info("Data collected",
             alarms=alarms.get("total", 0),
             online=equip.get("online", 0),
             offline=equip.get("offline", 0),
             chattering=equip.get("chattering", 0))

    # 2. Формируем контекст для LLM
    context_json = json.dumps(data, ensure_ascii=False, indent=2, default=str)
    user_message = f"Данные для анализа за последние {data['period_hours']} часа:\n\n```json\n{context_json}\n```\n\nПроанализируй и верни JSON согласно формату."

    # 3. ОДИН запрос к LLM
    t_llm = time.time()
    try:
        response_text = await provider.generate(
            system=HEALTH_SYSTEM_PROMPT,
            user=user_message,
        )
        log.info("LLM response received", length=len(response_text), preview=response_text[:200])
    except Exception as e:
        log.error("LLM call failed", error=str(e))
        # Fallback на детерминированный расчёт
        report = compute_health_report(data)
        rendered = await render_all(report)
        return ChatResponse(
            response=rendered["narrative"]["text"],
            status="ok",
            voice=rendered["voice"],
            visual=rendered["visual"],
            tool_calls=["fallback_to_deterministic"],
        )

    # 4. Парсим JSON
    parsed = _extract_json(response_text)

    if parsed:
        log.info("JSON parsed from LLM", score=parsed.get("score"), status=parsed.get("status"))
        
        # ВАЖНО: life_support ВСЕГДА считаем на основе РЕАЛЬНЫХ данных из БД, не LLM
        from modules.health.analysis import _compute_life_support_index
        real_life_support = _compute_life_support_index(env)
        log.info("life_support computed from real env", 
                 score=real_life_support.get("score"),
                 status=real_life_support.get("status"))
        
        # sub_scores вычисляем ДЕТЕРМИНИРОВАННО из реальных данных (не из LLM)
        from modules.health.analysis import compute_health_report
        deterministic_report = compute_health_report(data)
        log.info("Using deterministic sub_scores", sub_scores=deterministic_report.sub_scores)

        report = HealthReport(
            score=parsed.get("score", 50),
            status=parsed.get("status", "UNKNOWN"),
            summary=parsed.get("summary", ""),
            issues=parsed.get("issues", []),
            stats=parsed.get("stats", {}),
            environmental=parsed.get("environmental", env),
            equipment=parsed.get("equipment", equip),
            alarms=parsed.get("alarms", alarms),
            energy=parsed.get("energy", {}),
            recommendations=parsed.get("recommendations", []),
            sub_scores=deterministic_report.sub_scores,
            life_support=real_life_support,  # Всегда из реальных данных!
        )
    else:
        log.warning("Failed to parse JSON from LLM, using fallback")
        report = compute_health_report(data)

    # 5. Рендерим отчёт
    rendered = await render_all(report)

    # 6. Обновляем системную инфу для сайдбара
    try:
        from api.routes.system import update_last_health_check
        update_last_health_check(
            duration_sec=round(time.time() - t_start, 2),
            score=report.score,
        )
    except Exception as e:
        log.warning("Failed to update last health check", error=str(e))

    # 7. Возвращаем ответ
    return ChatResponse(
        response=rendered["narrative"]["text"],
        status="ok",
        voice=rendered["voice"],
        visual=rendered["visual"],
        tool_calls=["collect_all_health_data", "llm_analyze"],
    )
