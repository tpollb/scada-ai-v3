"""YandexGPT Provider — параметры приходят из factory (из settings/.env)"""
import json
import httpx
from structlog import get_logger

from .base import LLMProvider, ToolCall

log = get_logger()


class YandexLLMProvider(LLMProvider):
    provider_name = "yandex"
    API_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    CONTEXT_WINDOW = 32768

    def __init__(
        self,
        api_key: str,
        folder_id: str,
        model: str = "yandexgpt-5.1/latest",
        max_tokens: int = 32000,
        temperature: float = 0.05,
        timeout: int = 30,
    ):
        if not api_key or not folder_id:
            raise ValueError(
                "YandexGPT credentials не настроены. "
                "Заполни YANDEX_API_KEY и YANDEX_FOLDER_ID в backend/.env"
            )

        self.api_key = api_key
        self.folder_id = folder_id
        self.model = model
        self.model_uri = f"gpt://{folder_id}/{model}"
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)

        log.info(
            "YandexGPT provider initialized",
            model=model,
            folder_id=folder_id[:8] + "...",
            max_tokens=max_tokens,
            temperature=temperature,
        )

    def _compute_max_tokens(self, input_chars: int, requested: int) -> int:
        """Динамический расчёт чтобы не выйти за CONTEXT_WINDOW"""
        est_input = max(1, int(input_chars / 2.3))
        available = self.CONTEXT_WINDOW - est_input - 100
        return min(requested, max(512, available))

    def _build_messages(self, system: str, user: str, history: list | None = None) -> list[dict]:
        messages = [{"role": "system", "text": system}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "text": user})
        return messages

    def _build_tools(self, tools: list[dict]) -> list[dict]:
        return [
            {
                "function": {
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "parameters": t.get("parameters", {"type": "object", "properties": {}}),
                }
            }
            for t in tools
        ]

    async def _request(self, messages: list, max_tokens: int, temperature: float, tools: list | None = None) -> dict:
        payload = {
            "modelUri": self.model_uri,
            "completionOptions": {
                "stream": False,
                "temperature": temperature,
                "maxTokens": max_tokens,
            },
            "messages": messages,
        }
        if tools:
            payload["tools"] = self._build_tools(tools)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Api-Key {self.api_key}",
        }

        resp = await self._client.post(self.API_URL, headers=headers, json=payload)
        resp.raise_for_status()
        return resp.json()

    async def generate(self, system: str, user: str, *, max_tokens=None, temperature=None) -> str:
        messages = self._build_messages(system, user)
        input_chars = sum(len(m["text"]) for m in messages)
        actual_max = self._compute_max_tokens(input_chars, max_tokens or self.max_tokens)
        temp = temperature if temperature is not None else self.temperature

        data = await self._request(messages, actual_max, temp)
        alternatives = data.get("result", {}).get("alternatives", [])
        if alternatives:
            return alternatives[0].get("message", {}).get("text", "")
        return ""

    async def generate_with_tools(
        self,
        system: str,
        user: str,
        tools: list[dict],
        *,
        max_tokens=None,
        temperature=None,
        max_iterations=10,
        tool_executor=None,
    ) -> dict:
        if tool_executor is None:
            raise ValueError("tool_executor обязателен")

        history = [{"role": "user", "text": user}]
        iterations = 0
        all_tool_calls: list[ToolCall] = []
        final_text = ""
        temp = temperature if temperature is not None else self.temperature

        while iterations < max_iterations:
            iterations += 1
            total_chars = len(system) + sum(len(m.get("text", "")) for m in history)
            actual_max = self._compute_max_tokens(total_chars, max_tokens or self.max_tokens)

            log.debug(
                "LLM iteration",
                iteration=iterations,
                history_len=len(history),
                chars=total_chars,
                max_tokens=actual_max,
            )

            try:
                data = await self._request(history, actual_max, temp, tools=tools)
            except httpx.HTTPStatusError as e:
                log.error("YandexGPT HTTP error", status=e.response.status_code, body=e.response.text[:500])
                return {
                    "text": f"⚠️ Ошибка LLM: HTTP {e.response.status_code}",
                    "tool_calls": all_tool_calls,
                    "iterations": iterations,
                    "error": str(e),
                }
            except Exception as e:
                log.error("YandexGPT request failed", error=str(e))
                return {
                    "text": f"⚠️ Ошибка LLM: {e}",
                    "tool_calls": all_tool_calls,
                    "iterations": iterations,
                    "error": str(e),
                }

            alternatives = data.get("result", {}).get("alternatives", [])
            if not alternatives:
                break

            msg = alternatives[0].get("message", {})
            text = msg.get("text", "")
            function_call = msg.get("functionCall")

            if not function_call:
                final_text = text
                break

            tool_name = function_call.get("name", "")
            tool_args = function_call.get("arguments", {})

            log.info("LLM calls tool", tool=tool_name, args=tool_args)

            tool_call = ToolCall(name=tool_name, arguments=tool_args)
            all_tool_calls.append(tool_call)

            result = await tool_executor.execute(tool_name, tool_args)
            result_content = json.dumps(result, ensure_ascii=False, default=str)

            history.append({
                "role": "assistant",
                "text": text,
                "functionCall": function_call,
            })
            history.append({
                "role": "function",
                "functionResponse": {
                    "name": tool_name,
                    "content": result_content,
                },
            })

        return {
            "text": final_text,
            "tool_calls": all_tool_calls,
            "iterations": iterations,
        }

    async def health_check(self) -> bool:
        try:
            await self.generate("Ты тест.", "Скажи ок", max_tokens=10)
            return True
        except Exception as e:
            log.warning("YandexGPT health check failed", error=str(e))
            return False

    async def close(self):
        await self._client.aclose()
