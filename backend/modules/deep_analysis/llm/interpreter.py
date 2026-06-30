"""DDA Interpreter — LLM интерпретация результатов глубокого анализа с SSE streaming"""
from typing import AsyncGenerator
from structlog import get_logger

log = get_logger()


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
        from modules.deep_analysis.prompts import DDA_SYSTEM_PROMPT, build_dda_prompt

        try:
            provider = self._get_provider()
        except Exception as e:
            log.error("LLM unavailable", error=str(e))
            yield f"❌ Ошибка: LLM провайдер недоступен: {e}"
            return

        # Строим user prompt с данными
        user_prompt = build_dda_prompt(analysis_result)

        try:
            log.info(
                "Calling LLM for DDA interpretation (streaming)",
                system_chars=len(DDA_SYSTEM_PROMPT),
                user_chars=len(user_prompt),
            )

            # Используем streaming генерацию
            async for chunk in provider.generate_stream(
                DDA_SYSTEM_PROMPT,
                user_prompt,
            ):
                yield chunk

        except Exception as e:
            log.error("LLM streaming failed", error=str(e))
            yield f"\n\n❌ Ошибка генерации: {e}"

    async def interpret(
        self,
        analysis_result: dict,
    ) -> str:
        """
        Генерирует интерпретацию через LLM (без streaming).
        
        Args:
            analysis_result: полный результат анализа из /deep_analysis/run
            
        Returns:
            Полный текст интерпретации в markdown формате
        """
        from modules.deep_analysis.prompts import DDA_SYSTEM_PROMPT, build_dda_prompt

        try:
            provider = self._get_provider()
        except Exception as e:
            log.error("LLM unavailable", error=str(e))
            return f"❌ Ошибка: LLM провайдер недоступен: {e}"

        # Строим user prompt с данными
        user_prompt = build_dda_prompt(analysis_result)

        try:
            log.info(
                "Calling LLM for DDA interpretation",
                system_chars=len(DDA_SYSTEM_PROMPT),
                user_chars=len(user_prompt),
            )

            response_text = await provider.generate(
                DDA_SYSTEM_PROMPT,
                user_prompt,
            )

            if not response_text:
                log.warning("LLM returned empty response")
                return "❌ LLM вернул пустой ответ"

            log.info(
                "LLM interpretation ready",
                response_len=len(response_text),
            )

            return response_text

        except Exception as e:
            log.error("LLM call failed", error=str(e))
            return f"❌ Ошибка генерации: {e}"


# Singleton instance
_dda_interpreter = None


def get_dda_interpreter() -> DDAInterpreter:
    """Получить singleton интерпретатора DDA"""
    global _dda_interpreter
    if _dda_interpreter is None:
        _dda_interpreter = DDAInterpreter()
    return _dda_interpreter
