#!/usr/bin/env python3
"""
add_streaming_clean.py — добавляем generate_stream правильно (один раз, без ошибок отступов)
"""
from pathlib import Path
import ast

print('=' * 80)
print('ЧИСТЫЙ ФИКС: Добавление generate_stream в base.py и yandex.py')
print('=' * 80)
print()

# ============================================================================
# 1. BASE.PY — добавляем абстрактный метод
# ============================================================================
print('【1】Обновляем base.py')
print('-' * 80)

base_path = Path('backend/core/llm/base.py')
base_content = base_path.read_text(encoding='utf-8')

# Точный маркер из файла — вставляем ПЕРЕД ним
base_marker = '''    @abstractmethod
    async def health_check(self) -> bool:
        """Проверка доступности провайдера"""
        ...'''

stream_abstract = '''    @abstractmethod
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
        ...'''

if base_marker not in base_content:
    print('❌ Маркер не найден в base.py')
    exit(1)

if 'async def generate_stream' in base_content:
    print('ℹ️  generate_stream уже есть в base.py, пропускаем')
else:
    base_content = base_content.replace(base_marker, stream_abstract)
    base_path.write_text(base_content, encoding='utf-8', newline='\n')
    print('✅ Добавлен абстрактный метод generate_stream в base.py')

# Проверка синтаксиса base.py
try:
    ast.parse(base_content)
    print('✅ base.py синтаксически корректен')
except SyntaxError as e:
    print(f'❌ Ошибка в base.py: {e}')
    exit(1)

# ============================================================================
# 2. YANDEX.PY — добавляем реализацию метода
# ============================================================================
print()
print('【2】Обновляем yandex.py')
print('-' * 80)

yandex_path = Path('backend/core/llm/yandex.py')
yandex_content = yandex_path.read_text(encoding='utf-8')

# Точный маркер — вставляем ПЕРЕД health_check
yandex_marker = '''    async def health_check(self) -> bool:
        try:
            await self.generate("Ты тест.", "Скажи ок", max_tokens=10)
            return True
        except Exception as e:
            log.warning("YandexGPT health check failed", error=str(e))
            return False'''

stream_impl = '''    async def generate_stream(
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
            return False'''

if yandex_marker not in yandex_content:
    print('❌ Маркер не найден в yandex.py')
    exit(1)

if 'async def generate_stream' in yandex_content:
    print('ℹ️  generate_stream уже есть в yandex.py, пропускаем')
else:
    yandex_content = yandex_content.replace(yandex_marker, stream_impl)
    yandex_path.write_text(yandex_content, encoding='utf-8', newline='\n')
    print('✅ Добавлен метод generate_stream в yandex.py')

# Проверка синтаксиса yandex.py
try:
    ast.parse(yandex_content)
    print('✅ yandex.py синтаксически корректен')
except SyntaxError as e:
    print(f'❌ Ошибка в yandex.py: {e}')
    exit(1)

print()
print('=' * 80)
print('ГОТОВО! Что добавлено:')
print('=' * 80)
print()
print('1. LLMProvider.generate_stream (абстрактный метод)')
print('2. YandexLLMProvider.generate_stream (реализация):')
print('   • stream: True в completionOptions')
print('   • httpx.AsyncClient.stream() для SSE')
print('   • Парсинг JSON чанков с буфером')
print('   • Yield текстовых фрагментов')
print()
print('=' * 80)
print('СЛЕДУЮЩИЕ ШАГИ:')
print('=' * 80)
print()
print('1. Запусти backend:')
print('   cd backend')
print('   python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8081')
print()
print('2. Убедись что нет ошибки "LLM provider failed to initialize"')
print()
print('3. Дальше: модуль ab_analysis.py (A/B анализ)')