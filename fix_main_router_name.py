from pathlib import Path

print('=== fix_main_router_name.py ===')
print()

main_path = Path('backend/main.py')
content = main_path.read_text(encoding='utf-8')

# Исправляем неправильное имя
if 'app.include_router(deep_analysis_router)' in content:
    content = content.replace(
        'app.include_router(deep_analysis_router)',
        'app.include_router(deep_analysis.router)'
    )
    main_path.write_text(content, encoding='utf-8', newline='\n')
    print('✓ Исправлено: deep_analysis_router → deep_analysis.router')
else:
    print('ℹ Уже правильно: deep_analysis.router')

print()
print('Перезапусти backend:')
print('  Ctrl+C → uvicorn main:app --host 0.0.0.0 --port 8081 --reload')