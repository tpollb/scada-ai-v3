#!/usr/bin/env python3
"""Добавляет endpoints для LLM интерпретации DDA"""
from pathlib import Path

api_path = Path('backend/modules/deep_analysis/api.py')
content = api_path.read_text(encoding='utf-8')

# 1. Добавляем импорты если их нет
imports_to_add = []

if 'from fastapi.responses import StreamingResponse' not in content:
    imports_to_add.append('from fastapi.responses import StreamingResponse')

if imports_to_add:
    # Ищем последнюю строку импортов
    lines = content.split('\n')
    import_insert_pos = 0
    
    for i, line in enumerate(lines):
        if line.startswith('from ') or line.startswith('import '):
            import_insert_pos = i + 1
    
    # Вставляем импорты
    for imp in reversed(imports_to_add):
        lines.insert(import_insert_pos, imp)
    
    content = '\n'.join(lines)
    print(f'✅ Добавлены импорты: {", ".join(imports_to_add)}')

# 2. Добавляем endpoints в конец файла
endpoints_code = '''

# ============================================================================
# LLM INTERPRETATION ENDPOINTS
# ============================================================================

@router.post("/interpret", response_model=dict)
async def interpret_analysis(request: Request):
    """
    Генерирует LLM-интерпретацию результатов глубокого анализа.
    
    Принимает результат анализа (полный или частичный) и возвращает
    экспертную интерпретацию в markdown формате.
    """
    from modules.deep_analysis.llm.interpreter import get_dda_interpreter
    
    try:
        body = await request.json()
        analysis_result = body.get('analysis_result', {})
        
        if not analysis_result:
            return {
                "error": "No analysis_result provided",
                "interpretation": "❌ Не предоставлены данные для интерпретации"
            }
        
        interpreter = get_dda_interpreter()
        interpretation = await interpreter.interpret(analysis_result)
        
        return {
            "interpretation": interpretation,
            "success": True
        }
        
    except Exception as e:
        log.error("Interpret endpoint failed", error=str(e))
        return {
            "error": str(e),
            "interpretation": f"❌ Ошибка интерпретации: {e}"
        }


@router.post("/interpret/stream")
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
        analysis_result = body.get('analysis_result', {})
        
        if not analysis_result:
            async def error_stream():
                yield f"data: {json.dumps({'error': 'No analysis_result provided'})}\n\n"
            return StreamingResponse(error_stream(), media_type="text/event-stream")
        
        interpreter = get_dda_interpreter()
        
        async def generate_stream():
            try:
                async for chunk in interpreter.interpret_stream(analysis_result):
                    # Отправляем каждый чанк как SSE event
                    yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                
                # Сигнал завершения
                yield f"data: {json.dumps({'done': True})}\n\n"
                
            except Exception as e:
                log.error("Stream generation failed", error=str(e))
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Для nginx
            }
        )
        
    except Exception as e:
        log.error("Interpret stream endpoint failed", error=str(e))
        
        async def error_stream():
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return StreamingResponse(error_stream(), media_type="text/event-stream")


@router.get("/interpret/ping")
async def interpret_ping():
    """Проверка доступности LLM интерпретации"""
    from modules.deep_analysis.llm.interpreter import get_dda_interpreter
    
    try:
        interpreter = get_dda_interpreter()
        provider = interpreter._get_provider()
        
        # Пробуем health check
        health_ok = await provider.health_check()
        
        return {
            "status": "ok" if health_ok else "degraded",
            "llm_available": health_ok,
            "provider": provider.provider_name if hasattr(provider, 'provider_name') else "unknown"
        }
    except Exception as e:
        return {
            "status": "error",
            "llm_available": False,
            "error": str(e)
        }
'''

# Проверяем что endpoints ещё не добавлены
if '@router.post("/interpret"' not in content:
    content += endpoints_code
    print('✅ Добавлены endpoints: /interpret, /interpret/stream, /interpret/ping')
else:
    print('ℹ️  Endpoints уже существуют')

# Сохраняем
api_path.write_text(content, encoding='utf-8')

print()
print('=' * 80)
print('ENDPOINTS ДОБАВЛЕНЫ:')
print('=' * 80)
print()
print('1. POST /api/v1/deep_analysis/interpret')
print('   - Обычная интерпретация (возвращает JSON)')
print('   - Request: {"analysis_result": {...}}')
print('   - Response: {"interpretation": "...", "success": true}')
print()
print('2. POST /api/v1/deep_analysis/interpret/stream')
print('   - Streaming интерпретация (SSE)')
print('   - Request: {"analysis_result": {...}}')
print('   - Response: SSE events с chunks')
print()
print('3. GET /api/v1/deep_analysis/interpret/ping')
print('   - Проверка доступности LLM')
print('   - Response: {"status": "ok", "llm_available": true}')
print()
