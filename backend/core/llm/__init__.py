"""LLM Provider — агностик интерфейс для разных моделей"""
from .base import LLMProvider, ToolCall, ToolResult
from .factory import get_provider

__all__ = ["LLMProvider", "ToolCall", "ToolResult", "get_provider"]
