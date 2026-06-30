"""DDA Interpreter — LLM интерпретация результатов глубокого анализа с SSE streaming"""
from typing import AsyncGenerator
from structlog import get_logger

log = get_logger()


def _get_dda_system_prompt() -> str:
    """
    Получает system prompt из registry (с учётом override) или fallback на дефолт.
    
    Читает prompts_override.yaml через module_registry если он загружен.
    """
    try:
        from core.module_registry import get_registry
        registry = get_registry()
        if "deep_analysis" in registry._modules:
            module = registry._modules["deep_analysis"]
            if module.is_loaded and "DDA_SYSTEM_PROMPT" in module.prompts:
                return module.prompts["DDA_SYSTEM_PROMPT"]
    except Exception as e:
        log.debug("Failed to get prompt from registry, using default", error=str(e))
    
    # Fallback на дефолт
    from modules.deep_analysis.prompts import DDA_SYSTEM_PROMPT
    return DDA_SYSTEM_PROMPT


class DDAInterpreter:
    """
    Интерпретатор результатов DDA через LLM с поддержкой streaming.

    Использует core.llm.factory.get_provider() для получения провайдера.
    Поддерживает SSE streaming для постепенной отдачи результата.
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

    async def interpret_stream(
        self,
        analysis_result: dict,
    ) -> AsyncGenerator[str, None]:
        """
        Генерирует интерпретацию через LLM с streaming.

        Args:
            analysis_result: полный результат анализа из /deep_analysis/run

        Yields:
            Текстовые чанки интерпретации по мере генерации LLM
        """
        from modules.deep_analysis.prompts import build_dda_prompt

        try:
            provider = self._get_provider()
        except Exception as e:
            log.error("LLM unavailable", error=str(e))
            yield f"❌ Ошибка: LLM провайдер недоступен: {e}"
            return

        # Получаем system prompt (с учётом override из registry)
        system_prompt = _get_dda_system_prompt()

        # Строим user prompt с данными
        user_prompt = build_dda_prompt(analysis_result)

        try:
            log.info(
                "Calling LLM for DDA interpretation (streaming)",
                system_chars=len(system_prompt),
                user_chars=len(user_prompt),
            )

            # Используем streaming API провайдера
            async for chunk in provider.generate_stream(
                system=system_prompt,
                user=user_prompt,
            ):
                yield chunk

        except Exception as e:
            log.error("LLM streaming failed", error=str(e))
            yield f"❌ Ошибка генерации: {e}"

    async def interpret(self, analysis_result: dict) -> str:
        """
        Генерирует полную интерпретацию (без streaming).

        Args:
            analysis_result: полный результат анализа из /deep_analysis/run

        Returns:
            Полный текст интерпретации
        """
        from modules.deep_analysis.prompts import build_dda_prompt

        try:
            provider = self._get_provider()
        except Exception as e:
            log.error("LLM unavailable", error=str(e))
            return f"❌ Ошибка: LLM провайдер недоступен: {e}"

        # Получаем system prompt (с учётом override из registry)
        system_prompt = _get_dda_system_prompt()

        # Строим user prompt с данными
        user_prompt = build_dda_prompt(analysis_result)

        try:
            log.info(
                "Calling LLM for DDA interpretation",
                system_chars=len(system_prompt),
                user_chars=len(user_prompt),
            )

            result = await provider.generate(
                system=system_prompt,
                user=user_prompt,
            )

            log.info("LLM interpretation ready", result_chars=len(result))
            return result

        except Exception as e:
            log.error("LLM generation failed", error=str(e))
            return f"❌ Ошибка генерации: {e}"


# Singleton instance
_interpreter = None


def get_dda_interpreter() -> DDAInterpreter:
    """Возвращает singleton интерпретатора DDA."""
    global _interpreter
    if _interpreter is None:
        _interpreter = DDAInterpreter()
    return _interpreter
