#!/usr/bin/env python3
"""
fix_enable_deep_analysis.py — добавляем deep_analysis в ENABLED_MODULES
"""
from pathlib import Path

print('=' * 80)
print('ФИКС: Добавление deep_analysis в ENABLED_MODULES')
print('=' * 80)
print()

env_path = Path('backend/.env')

if not env_path.exists():
    print('❌ .env не найден!')
    exit(1)

content = env_path.read_text(encoding='utf-8')

# 1. Проверяем текущий ENABLED_MODULES
import re
match = re.search(r'^ENABLED_MODULES=(.+)$', content, re.MULTILINE)

if not match:
    print('⚠️  ENABLED_MODULES не найден в .env, добавляю...')
    content += '\nENABLED_MODULES=hello,health,logs,deep_analysis\n'
    env_path.write_text(content, encoding='utf-8', newline='\n')
    print('✅ Добавлено: ENABLED_MODULES=hello,health,logs,deep_analysis')
else:
    current_modules = match.group(1).strip()
    modules_list = [m.strip() for m in current_modules.split(',') if m.strip()]
    
    print(f'Текущие модули ({len(modules_list)}):')
    for m in modules_list:
        print(f'   • {m}')
    print()
    
    if 'deep_analysis' in modules_list:
        print('✅ deep_analysis уже в списке!')
        print()
        print('Тогда проблема в другом. Проверяю файлы...')
        
        # Проверяем что папка модуля существует
        module_path = Path('backend/modules/deep_analysis')
        if not module_path.exists():
            print(f'❌ Папка {module_path} НЕ существует!')
        else:
            print(f'✅ Папка {module_path} существует')
            
            # Проверяем api.py
            api_path = module_path / 'api.py'
            if api_path.exists():
                print(f'✅ api.py существует')
            else:
                print(f'❌ api.py НЕ существует')
            
            # Проверяем __init__.py
            init_path = module_path / '__init__.py'
            if init_path.exists():
                print(f'✅ __init__.py существует')
            else:
                print(f'⚠️  __init__.py НЕ существует (может быть нормой)')
        
        # Проверяем main.py — импортируется ли роутер
        main_path = Path('backend/main.py')
        if main_path.exists():
            main_content = main_path.read_text(encoding='utf-8')
            if 'deep_analysis' in main_content:
                print(f'✅ deep_analysis упоминается в main.py')
                
                # Показываем строку импорта
                for line in main_content.split('\n'):
                    if 'deep_analysis' in line and 'import' in line:
                        print(f'   {line.strip()}')
            else:
                print(f'❌ deep_analysis НЕ импортируется в main.py')
    else:
        print('❌ deep_analysis НЕ в списке!')
        print()
        
        # Добавляем
        modules_list.append('deep_analysis')
        new_modules_str = ','.join(modules_list)
        
        new_content = re.sub(
            r'^ENABLED_MODULES=.+$',
            f'ENABLED_MODULES={new_modules_str}',
            content,
            flags=re.MULTILINE
        )
        
        env_path.write_text(new_content, encoding='utf-8', newline='\n')
        
        print(f'✅ Добавлено: ENABLED_MODULES={new_modules_str}')

# 2. Проверяем main.py — импортируется ли роутер
print()
print('=' * 80)
print('ПРОВЕРКА main.py:')
print('=' * 80)
print()

main_path = Path('backend/main.py')
if main_path.exists():
    main_content = main_path.read_text(encoding='utf-8')
    
    # Ищем импорт роутеров
    router_imports = []
    for line in main_content.split('\n'):
        if 'import' in line and ('routes' in line or 'router' in line.lower()):
            router_imports.append(line.strip())
    
    if router_imports:
        print('Найденные импорты роутеров:')
        for imp in router_imports[:10]:
            print(f'   {imp}')
    
    # Проверяем подключение deep_analysis
    if 'deep_analysis' in main_content:
        print()
        print('✅ deep_analysis упоминается в main.py')
    else:
        print()
        print('❌ deep_analysis НЕ упоминается в main.py!')
        print('   Нужно добавить импорт роутера')

# 3. Проверяем module_registry.py
print()
print('=' * 80)
print('ПРОВЕРКА module_registry:')
print('=' * 80)
print()

registry_path = Path('backend/core/module_registry.py')
if registry_path.exists():
    registry_content = registry_path.read_text(encoding='utf-8')
    
    # Ищем deep_analysis
    if 'deep_analysis' in registry_content:
        print('✅ deep_analysis упоминается в module_registry.py')
    else:
        print('ℹ️  deep_analysis не упоминается в module_registry.py (может быть нормой)')

print()
print('=' * 80)
print('СЛЕДУЮЩИЕ ШАГИ:')
print('=' * 80)
print()
print('1. Перезапусти backend (Ctrl+C и снова uvicorn ...)')
print()
print('2. В логах должна появиться строка:')
print('   "Module loaded: deep_analysis  tools=..."')
print()
print('3. Проверь endpoint:')
print('   curl -s http://localhost:8081/api/v1/config/modules/deep_analysis/settings \\')
print('     | python -m json.tool | head -20')
print()
print('4. Если всё ещё 404 — проверь логи на наличие ошибок при старте')