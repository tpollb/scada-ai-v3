#!/usr/bin/env python3
"""
fix_test_seasonal_env.py — добавляем загрузку .env в тестовый скрипт
"""
from pathlib import Path

print('=' * 80)
print('ФИКС: Добавляем загрузку .env в test_seasonal.py')
print('=' * 80)
print()

test_path = Path('test_seasonal.py')
content = test_path.read_text(encoding='utf-8')

# Добавляем загрузку .env в начало файла
old_imports = '''import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Добавляем backend в путь
sys.path.insert(0, str(Path('backend').absolute()))'''

new_imports = '''import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Загружаем переменные окружения из .env
env_path = Path('backend/.env')
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Загружены переменные окружения из {env_path}")
else:
    print(f"⚠️  Файл {env_path} не найден")

# Добавляем backend в путь
sys.path.insert(0, str(Path('backend').absolute()))'''

if old_imports in content:
    content = content.replace(old_imports, new_imports)
    test_path.write_text(content, encoding='utf-8', newline='\n')
    print('✅ Добавлена загрузка .env в test_seasonal.py')
else:
    print('⚠️  Блок импортов не найден')

print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('Запусти тест снова:')
print('  python test_seasonal.py')
print()
print('Теперь скрипт загрузит credentials из backend/.env')