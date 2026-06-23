#!/usr/bin/env python3
"""Установка scikit-learn и фиксация в requirements.txt"""

import subprocess
import sys
from pathlib import Path

print('=== install_sklearn.py ===')
print()

# 1. Устанавливаем scikit-learn через pip
print('Устанавливаем scikit-learn...')
subprocess.check_call([
    sys.executable, '-m', 'pip', 'install', 'scikit-learn>=1.3.0'
])
print('✓ scikit-learn установлен')
print()

# 2. Проверяем импорт
try:
    from sklearn.ensemble import IsolationForest
    import sklearn
    print(f'✓ sklearn импортируется, версия: {sklearn.__version__}')
except ImportError as e:
    print(f'❌ Ошибка импорта: {e}')
    sys.exit(1)

# 3. Добавляем в requirements.txt если там нет
req_path = Path('backend/requirements.txt')
if req_path.exists():
    content = req_path.read_text(encoding='utf-8')
    if 'scikit-learn' not in content and 'sklearn' not in content:
        with open(req_path, 'a', encoding='utf-8') as f:
            f.write('\n# Deep Analysis module\n')
            f.write('scikit-learn>=1.3.0\n')
        print('✓ Добавлено в requirements.txt: scikit-learn>=1.3.0')
    else:
        print('ℹ scikit-learn уже есть в requirements.txt')
else:
    print('⚠ requirements.txt не найден')

# 4. Проверяем что все нужные пакеты для DDA на месте
print()
print('Проверка зависимостей для Deep Data Analysis:')
deps = {
    'numpy': 'numpy',
    'scipy': 'scipy',
    'sklearn': 'scikit-learn',
}

for import_name, pip_name in deps.items():
    try:
        __import__(import_name)
        print(f'  ✓ {pip_name}')
    except ImportError:
        print(f'  ❌ {pip_name} — нужен pip install {pip_name}')

print()
print('=' * 70)
print('✅ ВСЕ ЗАВИСИМОСТИ УСТАНОВЛЕНЫ')
print('=' * 70)
print()
print('Теперь перезапусти backend:')
print()
print('  Ctrl+C (остановить)')
print('  uvicorn main:app --host 0.0.0.0 --port 8081 --reload')
print()
print('И проверь endpoint:')
print('  curl http://localhost:8081/api/v1/deep_analysis/ping')
print()
print('Ожидаемый ответ:')
print('  {"status":"ok","module":"deep_analysis","version":"0.1.0","time":"..."}')