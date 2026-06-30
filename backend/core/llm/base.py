"""Абстрактный базовый класс для LLM-провайдеров"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class ToolCall:
    """Вызов инструмента от LLM"""
    name: str
    arguments: dict[str, Any]
    call_id: str = ""


@dataclass
class ToolResult:
    """Результат выполнения инструмента"""
    call_id: str
    name: str
    content: str
    is_error: bool = False


class LLMProvider(ABC):
    """Абстрактный LLM-провайдер. Все реализации наследуются от него."""

    provider_name: str = "base"

    @abstractmethod
    async def generate(
        self,
        system: str,
        user: str,
        *,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:
        """Простая генерация текста без инструментов"""
        ...

    @abstractmethod
    async def generate_with_tools(
        self,
        system: str,
        user: str,
        tools: list[dict],
        *,
        max_tokens: int | None = None,
        temperature: float | None = None,
        max_iterations: int = 10,
        tool_executor=None,
    ) -> dict:
        """
        Генерация с Tool Use.
        Возвращает:
        {
            "text": str,              # финальный текстовый ответ
            "tool_calls": [ToolCall], # все вызванные инструменты
            "iterations": int,
        }
        """
        ...

    @abstractmethod
    async def generate_stream(
        self,
        system: str,
        user: str,
        *,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ):
        """
        Streaming генерация текста.
        Yield-ит текстовые чанки по мере поступления от LLM.
        
        Usage:
            async for chunk in provider.generate_stream(sys, usr):
                print(chunk, end='', flush=True)
        """
        ...
        if False:
            yield ""

    @abstractmethod
    async def health_check(self) -> bool:
        """Проверка доступности провайдера"""
        ...

    def format_tools_for_prompt(self, tools: list[dict]) -> str:
        """Форматирование описания инструментов для системного промпта (fallback)"""
        if not tools:
            return ""
        lines = ["\nДоступные инструменты:"]
        for t in tools:
            name = t.get("name", "")
            desc = t.get("description", "")
            params = t.get("parameters", {}).get("properties", {})
            lines.append(f"- {name}: {desc}")
            if params:
                lines.append(f"  Параметры: {list(params.keys())}")
        return "\n".join(lines)
