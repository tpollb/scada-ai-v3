from pathlib import Path
import re

print('=== register_dda_router.py ===')
print()

main_path = Path('backend/main.py')
content = main_path.read_text(encoding='utf-8')

# Ищем блок с include_router для других роутеров
# Паттерн: ищем последовательность include_router вызовов
router_pattern = r'(from api\.routes import.*?\n)'

# Проверяем, импортирован ли уже deep_analysis
if 'deep_analysis' in content:
    print('ℹ deep_analysis уже зарегистрирован в main.py')
else:
    # Стратегия: найти последний include_router и добавить наш после него
    # Ищем все строки с app.include_router
    include_lines = []
    for i, line in enumerate(content.split('\n')):
        if 'app.include_router' in line and not line.strip().startswith('#'):
            include_lines.append((i, line))
    
    if not include_lines:
        print('⚠ Не найдено app.include_router в main.py')
        print('Возможно роутеры регистрируются через другой паттерн.')
        print()
        print('Покажи полный main.py:')
        print('  cat backend/main.py')
        exit(1)
    
    # Берём последний include_router
    last_idx, last_line = include_lines[-1]
    
    # Определяем отступ
    indent = len(last_line) - len(last_line.lstrip())
    indent_str = ' ' * indent
    
    # Добавляем импорт deep_analysis роутера
    # Ищем блок с импортами роутеров
    import_section_pattern = r'(from api\.routes import [^\n]+(?:\n\s+[^\n]+)*)'
    import_match = re.search(import_section_pattern, content)
    
    if import_match:
        old_imports = import_match.group(1)
        # Добавляем deep_analysis в импорты
        new_imports = old_imports.rstrip() + '\n' + indent_str + '    deep_analysis,'
        content = content.replace(old_imports, new_imports)
        print(f'✓ Добавлен импорт: deep_analysis')
    else:
        # Альтернативный паттерн — импорты построчно
        # Ищем последнюю строку импорта роутера
        route_import_pattern = r'(from api\.routes\.(\w+) import \w+_router\n)'
        all_route_imports = list(re.finditer(route_import_pattern, content))
        
        if all_route_imports:
            # Добавляем после последнего
            last_import = all_route_imports[-1]
            insert_pos = last_import.end()
            new_import = f'from api.routes.deep_analysis import deep_analysis_router\n'
            content = content[:insert_pos] + new_import + content[insert_pos:]
            print(f'✓ Добавлен импорт: from api.routes.deep_analysis import deep_analysis_router')
    
    # Добавляем app.include_router для deep_analysis
    new_line = f'{indent_str}app.include_router(deep_analysis_router)\n'
    
    # Находим позицию после последнего include_router
    insert_pos = content.rfind(last_line) + len(last_line)
    if not last_line.endswith('\n'):
        new_line = '\n' + new_line
    
    content = content[:insert_pos] + '\n' + new_line + content[insert_pos:]
    print(f'✓ Добавлена регистрация: app.include_router(deep_analysis_router)')
    
    main_path.write_text(content, encoding='utf-8', newline='\n')
    print()
    print('✓ main.py обновлён')

# Теперь создаём api/routes/deep_analysis.py
print()
print('Создаём backend/api/routes/deep_analysis.py...')

routes_dir = Path('backend/api/routes')
routes_dir.mkdir(parents=True, exist_ok=True)

route_file = routes_dir / 'deep_analysis.py'

route_content = '''"""Deep Analysis API router — connects module api.py to FastAPI"""
from fastapi import APIRouter

# Импортируем router из модуля
from modules.deep_analysis.api import router as module_router

# Реэкспортируем с правильным именем
deep_analysis_router = APIRouter(prefix="/api/v1")
deep_analysis_router.include_router(module_router)

# Для обратной совместимости — также экспортируем как router
router = deep_analysis_router
'''

route_file.write_text(route_content, encoding='utf-8', newline='\n')
print(f'✓ Создан файл: {route_file}')

print()
print('=' * 70)
print('РЕГИСТРАЦИЯ ЗАВЕРШЕНА')
print('=' * 70)
print()
print('Что сделано:')
print('  1. backend/api/routes/deep_analysis.py — обёртка для FastAPI')
print('  2. backend/main.py — добавлена регистрация роутера')
print()
print('Endpoints будут доступны на:')
print('  POST   http://localhost:8081/api/v1/deep_analysis/run')
print('  GET    http://localhost:8081/api/v1/deep_analysis/tags')
print('  GET    http://localhost:8081/api/v1/deep_analysis/history')
print('  GET    http://localhost:8081/api/v1/deep_analysis/history/{id}')
print('  DELETE http://localhost:8081/api/v1/deep_analysis/history/{id}')
print('  GET    http://localhost:8081/api/v1/deep_analysis/ping')
print()
print('Перезапусти backend:')
print('  Ctrl+C → python -m uvicorn backend.main:app --reload --port 8081')
print()
print('Проверка:')
print('  curl http://localhost:8081/api/v1/deep_analysis/ping')
print()
print('Следующий шаг: frontend — DeepAnalysisPanel.svelte')