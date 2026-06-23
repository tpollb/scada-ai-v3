"""Deep Analysis API router — connects module api.py to FastAPI"""
from fastapi import APIRouter

# Импортируем router из модуля
from modules.deep_analysis.api import router as module_router

# Реэкспортируем с правильным именем
deep_analysis_router = APIRouter(prefix="/api/v1")
deep_analysis_router.include_router(module_router)

# Для обратной совместимости — также экспортируем как router
router = deep_analysis_router
