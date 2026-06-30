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
            log.debug("Sending tools to YandexGPT", tools_count=len(tools), tools=payload["tools"])

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Api-Key {self.api_key}",
        }

        log.debug("YandexGPT request", payload_keys=list(payload.keys()), messages_count=len(messages))
        resp = await self._client.post(self.API_URL, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        
        # Полное логирование ответа
        result = data.get("result", {})
        alternatives = result.get("alternatives", [])
        log.info("YandexGPT FULL RESPONSE", 
                 usage=result.get("usage"),
                 model_version=result.get("modelVersion"),
                 alternatives_count=len(alternatives))
        
        for i, alt in enumerate(alternatives):
            msg = alt.get("message", {})
            log.info(f"YandexGPT alternative #{i}",
                     status=alt.get("status"),
                     finish_reason=alt.get("finishReason"),  # Ключевое поле!
                     message_keys=list(msg.keys()),
                     text_length=len(msg.get("text", "")),
                     text_preview=msg.get("text", "")[:300],
                     has_function_call=bool(msg.get("functionCall")),
                     function_call=msg.get("functionCall"),
                     has_tool_calls=bool(msg.get("toolCalls")))
        
        # Логируем warning только если это ФИНАЛЬНЫЙ ответ, но он пустой
        # При ALTERNATIVE_STATUS_TOOL_CALLS текст и не нужен — есть toolCallList
        if alternatives:
            status = alternatives[0].get("status", "")
            msg = alternatives[0].get("message", {})
            has_text = bool(msg.get("text"))
            has_tool_call_list = bool(msg.get("toolCallList"))
            is_tool_call = status == "ALTERNATIVE_STATUS_TOOL_CALLS"
            
            # Warning только если финальный ответ пустой
            if not is_tool_call and not has_text and not has_tool_call_list:
                import json
                log.warning("YandexGPT returned empty final response!", 
                           status=status,
                           full_response=json.dumps(data, ensure_ascii=False, indent=2)[:2000])
        
        return data

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

        # Включаем system message в историю — YandexGPT требует его для tool calling
        history = [
            {"role": "system", "text": system},
            {"role": "user", "text": user}
        ]
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
            status = alternatives[0].get("status", "")
            
            # Поддержка ДВУХ форматов tool calling:
            # 1. Старый: message.functionCall (yandexgpt-lite, старые модели)
            # 2. Новый: message.toolCallList.toolCalls[] (yagpt-5.1+, новые модели)
            function_call = msg.get("functionCall")
            
            if not function_call:
                tool_call_list = msg.get("toolCallList", {})
                tool_calls = tool_call_list.get("toolCalls", [])
                if tool_calls:
                    # Берём первый tool call (обычно один)
                    first_tool_call = tool_calls[0]
                    function_call = first_tool_call.get("functionCall")
            
            has_tool_call = function_call is not None or status == "ALTERNATIVE_STATUS_TOOL_CALLS"
            log.debug("LLM response message", 
                      has_text=bool(text), 
                      has_function_call=bool(function_call),
                      status=status,
                      has_tool_call_list=bool(msg.get("toolCallList")))
            
            if not has_tool_call:
                log.info("LLM returned final text", text_length=len(text), text_preview=text[:200] if text else "")
                final_text = text
                break
            
            if not function_call:
                log.warning("ALTERNATIVE_STATUS_TOOL_CALLS but no functionCall found!", 
                           message_keys=list(msg.keys()))
                final_text = text or "Не удалось вызвать инструмент."
                break

            tool_name = function_call.get("name", "")
            tool_args = function_call.get("arguments", {})

            log.info("LLM calls tool", tool=tool_name, args=tool_args)

            tool_call = ToolCall(name=tool_name, arguments=tool_args)
            all_tool_calls.append(tool_call)

            result = await tool_executor.execute(tool_name, tool_args)
            result_content = json.dumps(result, ensure_ascii=False, default=str)

            # Формируем историю согласно документации YandexGPT:
            # https://aistudio.yandex.ru/docs/en/ai-studio/operations/generation/function-call.html
            #
            # Правильная последовательность:
            # 1. assistant с toolCallList (что запросила модель)
            # 2. user с toolResultList (наш ответ от tool) — ОБЯЗАТЕЛЬНО role="user"!
            #
            # Правильная структура toolResult:
            # - functionResult (не functionResponse!)
            # - content = просто строка (не объект с contentType!)
            
            if msg.get("toolCallList"):
                history.append({
                    "role": "assistant",
                    "toolCallList": msg["toolCallList"],
                })
                history.append({
                    "role": "user",  # ВАЖНО: "user", не "assistant"!
                    "toolResultList": {
                        "toolResults": [{
                            "functionResult": {  # ВАЖНО: "functionResult", не "functionResponse"!
                                "name": tool_name,
                                "content": result_content,  # Просто строка, не объект!
                            }
                        }]
                    },
                })
            else:
                # СТАРЫЙ формат: assistant с functionCall, function с functionResponse
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

    async def generate_stream(
        self,
        system: str,
        user: str,
        *,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ):
        """
        Streaming генерация текста через YandexGPT.
        
        Yield-ит текстовые чанки по мере поступления от модели.
        Использует httpx stream() для SSE (Server-Sent Events).
        """
        messages = self._build_messages(system, user)
        input_chars = sum(len(m["text"]) for m in messages)
        actual_max = self._compute_max_tokens(input_chars, max_tokens or self.max_tokens)
        temp = temperature if temperature is not None else self.temperature

        payload = {
            "modelUri": self.model_uri,
            "completionOptions": {
                "stream": True,
                "temperature": temp,
                "maxTokens": actual_max,
            },
            "messages": messages,
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Api-Key {self.api_key}",
        }

        log.debug("YandexGPT streaming request", messages_count=len(messages))

        async with self._client.stream(
            "POST", self.API_URL, headers=headers, json=payload, timeout=self.timeout
        ) as resp:
            resp.raise_for_status()
            
            buffer = ""
            async for raw_line in resp.aiter_lines():
                line = raw_line.strip()
                if not line:
                    continue
                
                # SSE формат: "data: {...}"
                if line.startswith("data:"):
                    line = line[5:].strip()
                
                if not line:
                    continue
                
                # Накопление буфера для неполных JSON
                buffer += line
                try:
                    chunk_data = json.loads(buffer)
                    buffer = ""
                except json.JSONDecodeError:
                    continue
                
                # Извлекаем текст из альтернативы
                alternatives = chunk_data.get("result", {}).get("alternatives", [])
                if alternatives:
                    msg = alternatives[0].get("message", {})
                    text = msg.get("text", "")
                    if text:
                        yield text

    async def health_check(self) -> bool:
        try:
            await self.generate("Ты тест.", "Скажи ок", max_tokens=10)
            return True
        except Exception as e:
            log.warning("YandexGPT health check failed", error=str(e))
            return False

    async def close(self):
        await self._client.aclose()
