"""Tool Executor — dispatches LLM function calls to actual implementations"""
from typing import Dict, Any, Callable, Optional
from structlog import get_logger
import json

log = get_logger()


class ToolExecutor:
    """Executes tools called by the LLM"""

    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._schemas: Dict[str, Dict] = {}

    def register_tool(self, name: str, func: Callable, schema: Dict):
        """Register a tool with its schema"""
        self._tools[name] = func
        self._schemas[name] = schema
        log.debug(f"Tool registered: {name}")

    def get_schemas(self) -> list[Dict]:
        """Get all tool schemas for LLM"""
        return [
            {
                "name": name,
                "description": schema.get("description", ""),
                "parameters": schema.get("parameters", {})
            }
            for name, schema in self._schemas.items()
        ]

    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool by name"""
        if tool_name not in self._tools:
            log.error(f"Unknown tool: {tool_name}")
            return {"error": f"Unknown tool: {tool_name}", "status": "error"}

        func = self._tools[tool_name]
        try:
            result = await func(**arguments)
            log.info(f"Tool executed: {tool_name}", status="ok")
            return {"result": result, "status": "ok"}
        except Exception as e:
            log.error(f"Tool execution failed: {tool_name}", error=str(e))
            return {"error": str(e), "status": "error"}


# Singleton instance
_executor: Optional[ToolExecutor] = None


def get_executor() -> ToolExecutor:
    """Get or create the global executor"""
    global _executor
    if _executor is None:
        _executor = ToolExecutor()
    return _executor
