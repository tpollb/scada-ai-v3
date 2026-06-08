from pathlib import Path

print('=== check_and_fix_version.py ===')
print()

files = {
    'frontend/src/routes/Home.svelte': 'SCADA.AI v3.0.2',
    'frontend/src/routes/Config.svelte': 'v3.0.2',
}

for file_path, expected_version in files.items():
    path = Path(file_path)
    if not path.exists():
        print(f'❌ Файл не найден: {file_path}')
        continue
    
    content = path.read_text(encoding='utf-8')
    
    # Проверяем наличие старой и новой версии
    has_old = '3.0.1' in content
    has_new = '3.0.2' in content
    
    print(f'📄 {file_path}')
    print(f'   Содержит "3.0.1": {has_old}')
    print(f'   Содержит "3.0.2": {has_new}')
    
    if has_old and not has_new:
        # Заменяем 3.0.1 на 3.0.2
        content = content.replace('3.0.1', '3.0.2')
        path.write_text(content, encoding='utf-8', newline='\n')
        print(f'   ✅ Обновлено: 3.0.1 → 3.0.2')
    elif has_new:
        print(f'   ✅ Уже содержит {expected_version}')
    else:
        print(f'   ⚠️ Не найдена версия в файле')
    
    print()

print('=' * 60)
print('СЛЕДУЮЩИЙ ШАГ:')
print('  1. Vite должен подхватить через HMR')
print('  2. Если не подхватил — перезапусти dev server:')
print('     cd frontend')
print('     npm run dev')
print('  3. Обнови страницу (Ctrl+Shift+R для hard reload)')
print()
print('Проверь хидеры:')
print('  • Home: SCADA.AI v3.0.2')
print('  • Config: Конфигуратор v3.0.2')