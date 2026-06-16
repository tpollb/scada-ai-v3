from pathlib import Path
import re
import subprocess

print('=== bump_to_312.py ===')
print()

PROJECT_ROOT = Path('.')
OLD_VERSION = '3.1.1'
NEW_VERSION = '3.1.2'

# ============================================================================
# 1. Backend settings.py — app_version
# ============================================================================
settings_path = PROJECT_ROOT / 'backend/config/settings.py'
if settings_path.exists():
    content = settings_path.read_text(encoding='utf-8')
    pattern = r'(app_version\s*[:=]\s*["\'])' + re.escape(OLD_VERSION) + r'(["\'])'
    new_content, count = re.subn(pattern, r'\g<1>' + NEW_VERSION + r'\2', content)
    if count > 0:
        settings_path.write_text(new_content, encoding='utf-8', newline='\n')
        print(f'✓ backend/config/settings.py: {OLD_VERSION} → {NEW_VERSION}')
    else:
        print('ℹ backend/config/settings.py: версия не найдена')
else:
    print('⚠ backend/config/settings.py не найден')

# ============================================================================
# 2. Frontend package.json
# ============================================================================
pkg_path = PROJECT_ROOT / 'frontend/package.json'
if pkg_path.exists():
    content = pkg_path.read_text(encoding='utf-8')
    pattern = r'("version"\s*:\s*")' + re.escape(OLD_VERSION) + r'(")'
    new_content, count = re.subn(pattern, r'\g<1>' + NEW_VERSION + r'\2', content)
    if count > 0:
        pkg_path.write_text(new_content, encoding='utf-8', newline='\n')
        print(f'✓ frontend/package.json: {OLD_VERSION} → {NEW_VERSION}')
    else:
        print('ℹ frontend/package.json: версия не найдена')

# ============================================================================
# 3. UI хидеры — Home.svelte, Config.svelte
# ============================================================================
ui_files = [
    'frontend/src/routes/Home.svelte',
    'frontend/src/routes/Config.svelte',
]

for file_path in ui_files:
    p = PROJECT_ROOT / file_path
    if not p.exists():
        continue
    content = p.read_text(encoding='utf-8')
    new_content = content.replace(f'v{OLD_VERSION}', f'v{NEW_VERSION}')
    if new_content != content:
        p.write_text(new_content, encoding='utf-8', newline='\n')
        print(f'✓ {file_path}: v{OLD_VERSION} → v{NEW_VERSION}')
    else:
        print(f'ℹ {file_path}: v{OLD_VERSION} не найден')

# ============================================================================
# 4. CHANGELOG.md — добавляем секцию 3.1.2
# ============================================================================
changelog_path = PROJECT_ROOT / 'CHANGELOG.md'
if changelog_path.exists():
    content = changelog_path.read_text(encoding='utf-8')
    
    section_312 = f'''## [{NEW_VERSION}] - 2026-06-16

### Added
- **Корреляционный анализ** (`analyzers/correlations.py`):
  - Pearson correlation между всеми парами параметров (10 пар для 5 параметров)
  - Выравнивание временных рядов по timestamp (только совпадающие часы)
  - Фильтрация по `min_correlation` (по умолчанию 0.5)
  - Интерпретация: positive/negative, strong/moderate/weak
  - Сортировка по убыванию |coefficient|
- **Параметр `min_correlation`** в `GET /analytics/report` (float, default=0.5)
- **Поле `correlations`** в ответе `/analytics/report`

### Technical
- Pearson correlation без внешних зависимостей (чистый Python)
- Выравнивание временных рядов по bucket_start (hourly/daily агрегация)
- Фильтрация корреляций с малой выборкой (<10 точек)

### Example Output
```
"correlations": [
  {
    "params": ["temperature", "humidity"],
    "coefficient": -0.622,
    "interpretation": "negative",
    "strength": "moderate",
    "sample_size": 462
  }
]
```

'''
    
    if f'## [{NEW_VERSION}]' not in content:
        content = content.replace(
            '# Changelog\n\n',
            '# Changelog\n\n' + section_312
        )
        changelog_path.write_text(content, encoding='utf-8', newline='\n')
        print(f'✓ CHANGELOG.md: добавлена секция {NEW_VERSION}')
    else:
        print(f'ℹ CHANGELOG.md: секция {NEW_VERSION} уже есть')
else:
    print('⚠ CHANGELOG.md не найден')

# ============================================================================
# 5. Git commit
# ============================================================================
print()
print('=' * 60)
print('Git operations:')
print('=' * 60)

# git status
result = subprocess.run(['git', 'status', '--short'], capture_output=True, text=True)
changes = result.stdout.strip()
if not changes:
    print('ℹ Нет изменений для коммита')
    exit(0)

print('Изменения:')
for line in changes.split('\n')[:20]:
    print(f'  {line}')

# git add
result = subprocess.run(['git', 'add', '-A'], capture_output=True, text=True)
if result.returncode != 0:
    print(f'⚠ git add failed: {result.stderr}')

# git commit
commit_msg = f'''feat(analytics): add correlation analysis to v{NEW_VERSION}

Added:
- Pearson correlation between all parameter pairs (10 pairs for 5 params)
- Time series alignment by bucket_start (hourly/daily aggregation)
- Filtering by min_correlation threshold (default 0.5)
- Interpretation: positive/negative, strong/moderate/weak
- Sorted by |coefficient| descending

Example correlation found:
- temperature ↔ humidity: -0.622 (negative, moderate)
  Physical interpretation: higher temperature → lower relative humidity

API changes:
- GET /analytics/report?min_correlation=0.5
- Response includes "correlations" field with list of correlations

Technical:
- Pure Python Pearson implementation (no external dependencies)
- Filters correlations with small sample size (<10 points)
- Aligns time series before correlation calculation
'''

result = subprocess.run(
    ['git', 'commit', '-m', commit_msg],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    for line in result.stdout.split('\n'):
        if 'main' in line.lower() or line.startswith('[main'):
            print(f'✓ {line}')
            break
    else:
        print('✓ Commit создан')
else:
    print(f'⚠ git commit failed: {result.stderr}')
    exit(1)

print()
print('=' * 60)
print(f'✅ Релиз {NEW_VERSION} готов!')
print('=' * 60)
print()
print('Для пуша в remote:')
print('  git push')
print()
print('После пуша стартуем Фазу 2, Шаг 2: Топ проблем (ранжирование по влиянию на health score)')