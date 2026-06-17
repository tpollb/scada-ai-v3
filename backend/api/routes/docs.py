"""Docs API — просмотр документации системы из UI"""
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
    "ANALYTICS.md",
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
                first_line = content.split("\n")[0].strip()
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
