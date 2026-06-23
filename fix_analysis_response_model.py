#!/usr/bin/env python3
"""
fix_analysis_response_model.py — делаем поля AnalysisResponse Optional
"""

from pathlib import Path
import re

print('=' * 70)
print('ФИКС: Делаем поля AnalysisResponse Optional')
print('=' * 70)
print()

api_path = Path('backend/modules/deep_analysis/api.py')
content = api_path.read_text(encoding='utf-8')

# Ищем модель AnalysisResponse
model_pattern = r'class AnalysisResponse\(BaseModel\):.*?(?=\n\nclass|\n\n\n#|$)'
match = re.search(model_pattern, content, re.DOTALL)

if not match:
    print('⚠ Не удалось найти модель AnalysisResponse')
    exit(1)

old_model = match.group(0)
print('Текущая модель:')
print('-' * 60)
print(old_model)
print('-' * 60)
print()

# Создаём новую модель с Optional полями
new_model = '''class AnalysisResponse(BaseModel):
    """Ответ с результатами анализа"""
    analysis_id: str
    status: Literal["completed", "failed"]
    created_at: str
    tags: list[str]
    period: str
    summary: str
    statistics: Optional[dict] = None  # None для мульти-тег анализа
    anomalies: Optional[dict] = None   # None для мульти-тег анализа
    correlations: Optional[dict] = None
    seasonality: Optional[dict] = None
    visualizations: dict
    history_path: str'''

# Заменяем
content = content.replace(old_model, new_model)

# Сохраняем
api_path.write_text(content, encoding='utf-8', newline='\n')

print()
print('=' * 70)
print('✅ ИСПРАВЛЕНО!')
print('=' * 70)
print()
print('Что изменилось:')
print('  statistics: dict              → statistics: Optional[dict] = None')
print('  anomalies: Optional[dict]     → anomalies: Optional[dict] = None')
print('  correlations: Optional[dict]  → correlations: Optional[dict] = None')
print('  seasonality: Optional[dict]   → seasonality: Optional[dict] = None')
print()
print('Теперь мульти-тег анализ может передавать None для полей')
print('которые не применимы (statistics, anomalies для группового анализа).')
print()
print('=' * 70)
print('ПЕРЕРЕЗАПУСТИ BACKEND И ПРОВЕРЬ:')
print('=' * 70)
print()
print('  curl -X POST http://localhost:8081/api/v1/deep_analysis/run \\')
print('    -H "Content-Type: application/json" \\')
print('    -d \'{"tags": ["R203-Temperature", "R203-CO2", "R203-Humidity"], "period": 30}\'')
print()
print('Должно вернуться:')
print('  • "status": "completed"')
print('  • "statistics": null')
print('  • "anomalies": null')
print('  • "correlations": {матрица 3x3}')
print('  • "visualizations": {"heatmap": {...}, "scatter": {...}}')