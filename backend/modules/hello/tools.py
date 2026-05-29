"""Hello module tools"""
from typing import Dict, Any


async def say_hello(name: str = "оператор") -> Dict[str, Any]:
    """Say hello to the user"""
    return {
        "message": f"Привет, {name}! Я SCADA.AI v3.0.0. Все системы работают.",
        "timestamp": "2026-05-29T12:00:00Z"
    }


TOOLS = [
    {
        "name": "say_hello",
        "description": "Say hello to the user",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "User's name"
                }
            },
            "required": []
        },
        "function": say_hello
    }
]
