from pathlib import Path

print('=== fix_main_deep_analysis.py ===')
print()

main_path = Path('backend/main.py')
lines = main_path.read_text(encoding='utf-8').split('\n')

# Находим и исправляем строки
new_lines = []
for i, line in enumerate(lines):
    # Удаляем ошибочную строку "    deep_analysis,"
    if line.strip() == 'deep_analysis,':
        print(f'✓ Удалена ошибочная строка {i+1}: "    deep_analysis,"')
        continue
    
    # Добавляем deep_analysis в import statement (строка 141)
    if 'from api.routes import' in line and 'chat, config, health' in line:
        if 'deep_analysis' not in line:
            line = line.replace('analytics', 'analytics, deep_analysis')
            print(f'✓ Добавлен импорт: deep_analysis в строку {i+1}')
    
    new_lines.append(line)
    
    # Добавляем app.include_router(deep_analysis.router) после последней include_router
    if 'app.include_router(analytics.router)' in line:
        indent = ' ' * (len(line) - len(line.lstrip()))
        new_lines.append(f'{indent}app.include_router(deep_analysis.router)')
        print(f'✓ Добавлена регистрация: app.include_router(deep_analysis.router)')

# Сохраняем
main_path.write_text('\n'.join(new_lines), encoding='utf-8', newline='\n')

print()
print('=' * 70)
print('✅ main.py исправлен')
print('=' * 70)
print()
print('Теперь должно быть:')
print('  141: from api.routes import chat, config, health, system, docs, energy, analytics, deep_analysis')
print('  143: app.include_router(chat.router, tags=["chat"])')
print('  144: app.include_router(config.router, tags=["config"])')
print('  ...')
print('  150: app.include_router(analytics.router)')
print('  151: app.include_router(deep_analysis.router)')
print()
print('Перезапусти backend:')
print('  Ctrl+C → uvicorn main:app --host 0.0.0.0 --port 8081 --reload')