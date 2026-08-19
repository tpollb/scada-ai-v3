"""Logs module tools — анализ системного лога через LLM"""
from typing import Dict, Any
from structlog import get_logger

log = get_logger()


async def analyze_system_logs(limit: int = 500) -> Dict[str, Any]:
    """Анализирует системный лог через LLM и возвращает структурированный отчёт"""
    try:
        from core.logger import system_logger
        from modules.logs.prompts import LOGS_ANALYSIS_PROMPT, LOGS_SYSTEM_PROMPT
        from core.llm import get_provider
        
        # Читаем последние N записей из текущего файла
        current_file = system_logger.current_file.name
        recent_logs = system_logger.read_file(current_file, limit=limit)
        
        if not recent_logs:
            return "Системный лог пуст. Нет данных для анализа."
        
        # Формируем читаемый текст лога
        logs_text_lines = []
        for entry in recent_logs:
            ts = entry.get('timestamp', '')
            if 'T' in ts:
                ts = ts[11:19]
            level = entry.get('level', 'info').upper()
            msg = entry.get('message', '')
            data = entry.get('data')
            data_str = f" | {data}" if data else ""
            logs_text_lines.append(f"[{ts}] [{level}] {msg}{data_str}")
        
        logs_text = "\n".join(logs_text_lines)
        
        # Формируем промпт
        prompt = LOGS_ANALYSIS_PROMPT.format(
            count=len(recent_logs),
            logs_text=logs_text
        )
        
        # Вызываем LLM с ПРАВИЛЬНОЙ сигнатурой generate()
        provider = get_provider()
        analysis_text = await provider.generate(
            system=LOGS_SYSTEM_PROMPT,
            user=prompt,
            temperature=0.3,
            max_tokens=1500,
        )
        
        if not analysis_text:
            analysis_text = "Не удалось получить анализ от LLM."
        
        log.info("Logs analysis completed", file=current_file, count=len(recent_logs))
        
        # Возвращаем ТОЛЬКО Markdown-анализ (строку) — LLM с ней проще работать
        return analysis_text
    except Exception as e:
        log.error("Logs analysis failed", error=str(e))
        return f"Ошибка анализа лога: {e}"


TOOLS = [
    {
        "name": "analyze_system_logs",
        "description": "Проанализировать системный лог SCADA.AI. Возвращает детальный отчёт с критическими событиями, аномалиями и рекомендациями. Вызывается когда пользователь просит 'проанализируй системный лог', 'анализ логов', 'что происходит в системе'.",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Количество последних записей для анализа (по умолчанию 500)",
                    "default": 500
                }
            },
            "required": []
        },
        "function": analyze_system_logs
    }
]
