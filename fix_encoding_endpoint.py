#!/usr/bin/env python3
"""
fix_encoding_endpoint.py - делает endpoint устойчивым к Windows-1251
"""
from pathlib import Path

api_path = Path('backend/modules/deep_analysis/api.py')
content = api_path.read_text(encoding='utf-8')

print('Исправляю endpoint /interpret для работы с Windows-1251...')
print()

# Находим функцию interpret_analysis
old_interpret = '''@router.post("/interpret", response_model=dict)
async def interpret_analysis(request: Request):
    """
    Генерирует LLM-интерпретацию результатов глубокого анализа.
    
    Принимает результат анализа (полный или частичный) и возвращает
    экспертную интерпретацию в markdown формате.
    """
    from modules.deep_analysis.llm.interpreter import get_dda_interpreter
    
    try:
        body = await request.json()
        analysis_result = body.get('analysis_result', {})'''

new_interpret = '''@router.post("/interpret", response_model=dict)
async def interpret_analysis(request: Request):
    """
    Генерирует LLM-интерпретацию результатов глубокого анализа.
    
    Принимает результат анализа (полный или частичный) и возвращает
    экспертную интерпретацию в markdown формате.
    """
    from modules.deep_analysis.llm.interpreter import get_dda_interpreter
    import json
    
    try:
        # Читаем сырое тело запроса
        raw_body = await request.body()
        
        # Пробуем декодировать как UTF-8
        try:
            body_text = raw_body.decode('utf-8')
        except UnicodeDecodeError:
            # Fallback: пробуем Windows-1251 (частая проблема в Windows Git Bash)
            try:
                body_text = raw_body.decode('cp1251')
                log.warning("Request body decoded as cp1251 (Windows encoding)")
            except UnicodeDecodeError:
                # Последний fallback: latin-1 (всегда работает)
                body_text = raw_body.decode('latin-1')
                log.warning("Request body decoded as latin-1")
        
        # Парсим JSON
        try:
            body = json.loads(body_text)
        except json.JSONDecodeError as e:
            log.error("Invalid JSON in request", error=str(e))
            return {
                "error": f"Invalid JSON: {e}",
                "interpretation": "❌ Некорректный JSON в запросе"
            }
        
        analysis_result = body.get('analysis_result', {})'''

if old_interpret in content:
    content = content.replace(old_interpret, new_interpret)
    print('✅ Endpoint /interpret исправлен')
else:
    print('⚠️  Endpoint /interpret не найден в ожидаемом виде')

# То же самое для streaming endpoint
old_stream = '''@router.post("/interpret/stream")
async def interpret_analysis_stream(request: Request):
    """
    Генерирует LLM-интерпретацию с SSE streaming.
    
    Возвращает интерпретацию по частям через Server-Sent Events.
    Клиент получает текст постепенно по мере генерации LLM.
    
    SSE формат:
    - data: {"chunk": "текст"} - для текстовых чанков
    - data: {"done": true} - сигнал завершения
    """
    from modules.deep_analysis.llm.interpreter import get_dda_interpreter
    import json
    
    try:
        body = await request.json()
        analysis_result = body.get('analysis_result', {})'''

new_stream = '''@router.post("/interpret/stream")
async def interpret_analysis_stream(request: Request):
    """
    Генерирует LLM-интерпретацию с SSE streaming.
    
    Возвращает интерпретацию по частям через Server-Sent Events.
    Клиент получает текст постепенно по мере генерации LLM.
    
    SSE формат:
    - data: {"chunk": "текст"} - для текстовых чанков
    - data: {"done": true} - сигнал завершения
    """
    from modules.deep_analysis.llm.interpreter import get_dda_interpreter
    import json
    
    try:
        # Читаем сырое тело запроса
        raw_body = await request.body()
        
        # Пробуем декодировать как UTF-8
        try:
            body_text = raw_body.decode('utf-8')
        except UnicodeDecodeError:
            try:
                body_text = raw_body.decode('cp1251')
                log.warning("Stream request body decoded as cp1251")
            except UnicodeDecodeError:
                body_text = raw_body.decode('latin-1')
                log.warning("Stream request body decoded as latin-1")
        
        # Парсим JSON
        try:
            body = json.loads(body_text)
        except json.JSONDecodeError as e:
            async def error_stream():
                error_data = json.dumps({"error": f"Invalid JSON: {e}"})
                yield f"data: {error_data}\\n\\n"
            return StreamingResponse(error_stream(), media_type="text/event-stream")
        
        analysis_result = body.get('analysis_result', {})'''

if old_stream in content:
    content = content.replace(old_stream, new_stream)
    print('✅ Endpoint /interpret/stream исправлен')
else:
    print('⚠️  Endpoint /interpret/stream не найден в ожидаемом виде')

# Сохраняем
api_path.write_text(content, encoding='utf-8', newline='\n')

# Проверяем синтаксис
import ast
try:
    ast.parse(content)
    print()
    print('✅ Файл синтаксически корректен')
except SyntaxError as e:
    print(f'❌ Синтаксическая ошибка: {e}')

print()
print('=' * 80)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 80)
print()
print('Endpoint теперь:')
print('1. Читает сырое тело через request.body()')
print('2. Пробует декодировать как UTF-8')
print('3. Если не получается — fallback на cp1251 (Windows)')
print('4. Если и это не работает — fallback на latin-1 (всегда ок)')
print('5. Парсит JSON уже из текстовой строки')
print()
print('Теперь curl с кириллицей должен работать корректно!')