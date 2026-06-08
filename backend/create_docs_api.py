from pathlib import Path

print('=== create_docs_api.py (clean version) ===')
print()

# ============================================================================
# 1. Создаём api/routes/docs.py
# ============================================================================
docs_route_content = '''"""Docs API — просмотр документации системы из UI"""
from fastapi import APIRouter, HTTPException
from pathlib import Path
from structlog import get_logger

log = get_logger()
router = APIRouter(prefix="/docs", tags=["docs"])

DOCS_DIR = Path(__file__).parent.parent.parent / "docs"

# Whitelist разрешённых файлов (безопасность)
ALLOWED_FILES = [
    "README.md",
    "MODULES.md",
    "API.md",
    "CHAT_EXAMPLES.md",
    "ARCHITECTURE.md",
    "CHANGELOG.md",
]


@router.get("/list")
async def list_docs():
    """Список доступных файлов документации с заголовками"""
    if not DOCS_DIR.exists():
        log.warning("Docs directory not found", path=str(DOCS_DIR))
        return {"files": [], "error": "Документация не найдена"}

    files = []
    for filename in ALLOWED_FILES:
        file_path = DOCS_DIR / filename
        if file_path.exists():
            try:
                content = file_path.read_text(encoding="utf-8")
                first_line = content.split("\\n")[0].strip()
                title = first_line.lstrip("#").strip()
                size = file_path.stat().st_size
                
                files.append({
                    "filename": filename,
                    "title": title or filename.replace(".md", ""),
                    "size": size,
                })
            except Exception as e:
                log.error("Failed to read doc file", filename=filename, error=str(e))
                files.append({
                    "filename": filename,
                    "title": filename.replace(".md", ""),
                    "size": 0,
                    "error": str(e),
                })

    log.info("Docs list requested", count=len(files))
    return {"files": files}


@router.get("/{filename}")
async def get_doc(filename: str):
    """Читает содержимое файла документации"""
    if filename not in ALLOWED_FILES:
        log.warning("Unauthorized doc access attempt", filename=filename)
        raise HTTPException(status_code=404, detail="Файл не найден")

    file_path = DOCS_DIR / filename
    if not file_path.exists():
        log.warning("Doc file not found", filename=filename)
        raise HTTPException(status_code=404, detail="Файл не найден")

    try:
        content = file_path.read_text(encoding="utf-8")
        log.info("Doc file read", filename=filename, size=len(content))
        return {
            "filename": filename,
            "content": content,
            "size": len(content),
        }
    except Exception as e:
        log.error("Failed to read doc", filename=filename, error=str(e))
        raise HTTPException(status_code=500, detail=f"Ошибка чтения: {str(e)}")
'''

docs_path = Path('api/routes/docs.py')
docs_path.write_text(docs_route_content, encoding='utf-8', newline='\n')
print(f'✓ Создан: {docs_path}')

# ============================================================================
# 2. Патчим main.py — добавляем импорт и регистрацию
# ============================================================================
main_path = Path('main.py')
main = main_path.read_text(encoding='utf-8')

# 2.1. Добавляем docs в импорт
old_import = 'from api.routes import chat, config, health, system  # noqa: E402'
new_import = 'from api.routes import chat, config, health, system, docs  # noqa: E402'

if old_import in main:
    main = main.replace(old_import, new_import)
    print('✓ main.py: добавлен импорт docs роутера')
elif 'from api.routes import chat, config, health, system, docs' in main:
    print('ℹ main.py: импорт docs уже есть')
else:
    print('⚠ main.py: не нашёл точный паттерн импорта')

# 2.2. Добавляем include_router для docs
old_register = 'app.include_router(system.router)'
new_register = 'app.include_router(system.router)\napp.include_router(docs.router)'

if 'app.include_router(docs.router)' not in main:
    if old_register in main:
        main = main.replace(old_register, new_register, 1)  # только первое вхождение
        print('✓ main.py: добавлен include_router(docs.router)')
    else:
        print('⚠ main.py: не нашёл точный паттерн регистрации')
else:
    print('ℹ main.py: docs.router уже зарегистрирован')

main_path.write_text(main, encoding='utf-8', newline='\n')
print(f'✓ Обновлён: {main_path}')

print()
print('=' * 60)
print('ЧТО СДЕЛАНО:')
print('=' * 60)
print('1. Создан api/routes/docs.py с двумя endpoints:')
print('   • GET /docs/list — список файлов с заголовками')
print('   • GET /docs/{filename} — содержимое файла')
print()
print('2. main.py обновлён:')
print('   • Добавлен импорт docs')
print('   • Добавлен app.include_router(docs.router)')
print()
print('Безопасность:')
print('  ✓ Whitelist ALLOWED_FILES — только 6 разрешённых файлов')
print('  ✓ Нет path traversal — filename проверяется по списку')
print('  ✓ Логируются все попытки доступа')
print()
print('СЛЕДУЮЩИЙ ШАГ:')
print('  1. Перезапусти backend: Ctrl+C, затем uvicorn main:app --port 8081')
print('  2. Проверь API:')
print('     curl http://localhost:8081/docs/list')
print('     curl http://localhost:8081/docs/README.md')
print('  3. Когда ок — скажи "docs API ок" и будем делать Frontend viewer')