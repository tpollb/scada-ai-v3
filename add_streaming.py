#!/usr/bin/env python3
"""
add_streaming.py — добавляем streaming в YandexLLMProvider
"""
from pathlib import Path

print('=' * 80)
print('ШАГ 1: Добавляем streaming в YandexLLMProvider')
print('=' * 80)
print()

yandex_path = Path('backend/core/llm/yandex.py')
content = yandex_path.read_text(encoding='utf-8')

# Ищем место перед health_check и добавляем generate_stream
marker = '    async def health_check(self) -> bool:'

if 'async def generate_stream' in content:
    print('ℹ️  generate_stream уже есть, пропускаем')
else:
    streaming_method = '''    async def generate_stream(
        self,
        system: str,
        user: str,
        *,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ):
        """
        Streaming генерация текста.
        Yield-ит текстовые чанки по мере их поступления от YandexGPT.
        
        Usage:
            async for chunk in provider.generate_stream(sys, usr):
                print(chunk, end='', flush=True)
        """
        messages = self._build_messages(system, user)
        input_chars = sum(len(m["text"]) for m in messages)
        actual_max = self._compute_max_tokens(input_chars, max_tokens or self.max_tokens)
        temp = temperature if temperature is not None else self.temperature

        payload = {
            "modelUri": self.model_uri,
            "completionOptions": {
                "stream": True,  # ← Включаем streaming
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

        # Используем stream=True в httpx для SSE
        async with self._client.stream(
            "POST", self.API_URL, headers=headers, json=payload, timeout=self.timeout
        ) as resp:
            resp.raise_for_status()
            
            # YandexGPT SSE: каждая строка — это JSON chunk
            # Формат: "data: {...}" или просто JSON объекты в потоке
            buffer = ""
            async for raw_line in resp.aiter_lines():
                line = raw_line.strip()
                if not line:
                    continue
                
                # Убираем "data: " prefix если есть (SSE формат)
                if line.startswith("data:"):
                    line = line[5:].strip()
                
                if not line:
                    continue
                
                try:
                    chunk_data = json.loads(line)
                except json.JSONDecodeError:
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

    '''
    
    content = content.replace(marker, streaming_method + marker)
    print('✅ Добавлен метод generate_stream')

# Обновляем base.py — добавляем абстрактный метод
base_path = Path('backend/core/llm/base.py')
base_content = base_path.read_text(encoding='utf-8')

if 'async def generate_stream' in base_content:
    print('ℹ️  generate_stream в base.py уже есть')
else:
    # Ищем последний @abstractmethod (health_check)
    base_marker = '    @abstractmethod\n    async def health_check(self) -> bool:'
    
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
        Yield-ит текстовые чанки по мере поступления.
        """
        ...
        yield ""  # type hint для async generator

    '''
    
    base_content = base_content.replace(base_marker, stream_abstract + base_marker)
    base_path.write_text(base_content, encoding='utf-8', newline='\n')
    print('✅ Добавлен абстрактный метод generate_stream в base.py')

# Сохраняем yandex.py
yandex_path.write_text(content, encoding='utf-8', newline='\n')
print('✅ Файлы сохранены')

print()
print('=' * 80)
print('ЧТО ДОБАВЛЕНО:')
print('=' * 80)
print()
print('1. YandexLLMProvider.generate_stream(system, user, ...)')
print('   • Включает "stream": True в completionOptions')
print('   • Использует httpx.client.stream() для SSE')
print('   • Парсит JSON чанки (с обработкой data: prefix)')
print('   • Yield-ит текстовые фрагменты')
print()
print('2. LLMProvider.generate_stream (абстрактный метод)')
print('   • В базовом классе для совместимости')
print()
print('ПРИМЕР ИСПОЛЬЗОВАНИЯ:')
print('  async for chunk in provider.generate_stream(sys, usr):')
print('      yield chunk  # SSE event')
print()
print('=' * 80)
print('СЛЕДУЮЩИЙ ШАГ:')
print('=' * 80)
print()
print('Создаём модуль ab_analysis.py:')
print('• compare_snapshots(data_a, data_b)')
print('• compare_patterns(pattern_a, pattern_b)')
print('• API endpoint: POST /api/v1/ab_analysis/run')