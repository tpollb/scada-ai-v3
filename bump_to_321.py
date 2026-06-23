#!/usr/bin/env python3
"""
bump_to_321.py — bump версии 3.2.0 → 3.2.1 везде
"""

from pathlib import Path
import re
import subprocess
from datetime import datetime

print('=' * 70)
print('BUMP VERSION: 3.2.0 → 3.2.1')
print('=' * 70)
print()

OLD_VERSION = '3.2.0'
NEW_VERSION = '3.2.1'

# Файлы для обновления
files_to_check = [
    'backend/config/settings.py',
    'backend/main.py',
    'frontend/package.json',
    'frontend/src/routes/Home.svelte',
    'frontend/src/routes/Config.svelte',
]

changes = []

# ============================================================================
# 1. Ищем все файлы с 3.2.0
# ============================================================================
print('🔍 Ищем файлы с версией 3.2.0...')
print()

for file_path in files_to_check:
    path = Path(file_path)
    if not path.exists():
        print(f'  ⚠ {file_path}: не найден')
        continue
    
    content = path.read_text(encoding='utf-8')
    
    # Ищем упоминания версии
    if OLD_VERSION in content:
        count = content.count(OLD_VERSION)
        
        # Обновляем
        new_content = content.replace(OLD_VERSION, NEW_VERSION)
        path.write_text(new_content, encoding='utf-8', newline='\n')
        
        changes.append(f'{file_path}: {count} упоминаний')
        print(f'  ✓ {file_path}: {count} упоминаний')
    else:
        print(f'  ℹ {file_path}: версия не найдена')

# ============================================================================
# 2. Обновляем backend/config/settings.py (app_version)
# ============================================================================
print()
print('📝 Обновляем backend/config/settings.py...')

settings_path = Path('backend/config/settings.py')
if settings_path.exists():
    content = settings_path.read_text(encoding='utf-8')
    
    # Паттерн: app_version = "X.Y.Z"
    pattern = r'(app_version\s*=\s*["\'])([^"\']+)(["\'])'
    match = re.search(pattern, content)
    
    if match:
        current_ver = match.group(2)
        if current_ver != NEW_VERSION:
            new_content = re.sub(pattern, rf'\g<1>{NEW_VERSION}\g<3>', content)
            settings_path.write_text(new_content, encoding='utf-8', newline='\n')
            changes.append(f'settings.py: app_version {current_ver} → {NEW_VERSION}')
            print(f'  ✓ app_version: {current_ver} → {NEW_VERSION}')
        else:
            print(f'  ℹ app_version уже {NEW_VERSION}')
    else:
        print('  ⚠ app_version не найден в settings.py')

# ============================================================================
# 3. Обновляем backend/main.py (docstring)
# ============================================================================
print()
print('📝 Обновляем backend/main.py...')

main_path = Path('backend/main.py')
if main_path.exists():
    content = main_path.read_text(encoding='utf-8')
    
    # Паттерн: """SCADA.AI vX.Y.Z — Main application"""
    pattern = r'("""SCADA\.AI v)[\d.]+( — Main application""")'
    match = re.search(pattern, content)
    
    if match:
        new_content = re.sub(pattern, rf'\g<1>{NEW_VERSION}\g<2>', content)
        if new_content != content:
            main_path.write_text(new_content, encoding='utf-8', newline='\n')
            changes.append(f'main.py: docstring v{OLD_VERSION} → v{NEW_VERSION}')
            print(f'  ✓ Docstring: v{OLD_VERSION} → v{NEW_VERSION}')
        else:
            print(f'  ℹ Docstring уже v{NEW_VERSION}')
    else:
        print('  ⚠ Docstring не найден в main.py')

# ============================================================================
# 4. Обновляем frontend/package.json
# ============================================================================
print()
print('📝 Обновляем frontend/package.json...')

package_path = Path('frontend/package.json')
if package_path.exists():
    import json
    with open(package_path, 'r', encoding='utf-8') as f:
        package = json.load(f)
    
    current_ver = package.get('version', 'unknown')
    if current_ver != NEW_VERSION:
        package['version'] = NEW_VERSION
        with open(package_path, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(package, f, indent=2, ensure_ascii=False)
            f.write('\n')
        changes.append(f'package.json: version {current_ver} → {NEW_VERSION}')
        print(f'  ✓ version: {current_ver} → {NEW_VERSION}')
    else:
        print(f'  ℹ version уже {NEW_VERSION}')

# ============================================================================
# 5. Проверяем CHANGELOG.md (если есть)
# ============================================================================
changelog_path = Path('CHANGELOG.md')
if changelog_path.exists():
    print()
    print('📝 Проверяем CHANGELOG.md...')
    content = changelog_path.read_text(encoding='utf-8')
    
    if f'## [{NEW_VERSION}]' not in content and f'## {NEW_VERSION}' not in content:
        print(f'  ⚠ CHANGELOG.md не содержит запись для {NEW_VERSION}')
        print(f'  💡 Добавь вручную:')
        print(f'     ## [{NEW_VERSION}] - {datetime.now().strftime("%Y-%m-%d")}')
        print(f'     ### Added')
        print(f'     - Deep Data Analysis module (Итерация 1)')
        print(f'     - Isolation Forest для детекции аномалий')
        print(f'     - Chart.js с zoom/pan/download')
        print(f'     - Layout 50/50 для одновременной работы с DDA и чатом')
    else:
        print(f'  ℹ CHANGELOG.md уже содержит запись для {NEW_VERSION}')

# ============================================================================
# 6. Создаём коммит
# ============================================================================
print()
print('=' * 70)
print('ИТОГ:')
print('=' * 70)
for i, c in enumerate(changes, 1):
    print(f'  {i}. ✓ {c}')

if not changes:
    print()
    print('ℹ Ничего не изменилось — версия уже 3.2.1')
else:
    print()
    print('📦 Создаём коммит...')
    
    # Git add
    result = subprocess.run(['git', 'add', '-A'], capture_output=True, text=True)
    if result.returncode != 0:
        print(f'  ⚠ git add failed: {result.stderr}')
    else:
        print('  ✓ git add -A')
    
    # Git commit
    commit_msg = f"""chore: bump version to {NEW_VERSION}

Deep Data Analysis module (Итерация 1):
- Модуль deep_analysis с Isolation Forest для детекции аномалий
- Chart.js с zoom/pan/download PNG
- Layout 50/50 для одновременной работы с DDA и чатом
- API endpoints: /deep_analysis/run, /tags, /history
- Frontend: DeepAnalysisControls + DeepAnalysisResults
- Исправлены дубликаты SystemLogsPanel
- Добавлена кнопка закрытия (Х) в DeepAnalysisControls

Backend:
- backend/modules/deep_analysis/ (полная структура)
- backend/api/routes/deep_analysis.py
- backend/main.py: регистрация роутера

Frontend:
- frontend/src/components/DeepAnalysisControls.svelte
- frontend/src/components/DeepAnalysisResults.svelte
- frontend/src/routes/Home.svelte: интеграция

Dependencies:
- chartjs-plugin-zoom
- hammerjs
- scikit-learn>=1.3.0"""
    
    result = subprocess.run(
        ['git', 'commit', '-m', commit_msg],
        capture_output=True,
        text=True,
        encoding='utf-8'
    )
    
    if result.returncode == 0:
        print('  ✓ git commit')
        print()
        print('📤 Коммит создан!')
        print()
        print('Для пуша в remote:')
        print('  git push origin main')
    else:
        print(f'  ⚠ git commit failed: {result.stderr}')
        print()
        print('Создай коммит вручную:')
        print('  git add -A')
        print('  git commit -m "chore: bump version to 3.2.1"')

print()
print('=' * 70)
print(f'✅ ВЕРСИЯ {NEW_VERSION} ГОТОВА!')
print('=' * 70)
print()
print('Проверка:')
print('  1. Открой фронтенд')
print('  2. В хедере должно быть: SCADA.AI v3.2.1')
print('  3. В конфигураторе внизу: v3.2.1')
print('  4. Backend API: curl http://localhost:8081/api/v1/system/info')
print()
print('Что дальше:')
print('  • Продолжить Итерацию 2 (корреляции, сезонность, A/B сравнение)')
print('  • Или Итерация 3 (UX улучшения, кастомные периоды)')
print('  • Или Итерация 4 (PDF/Excel экспорт, LLM integration)')