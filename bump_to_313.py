from pathlib import Path
import re
import subprocess

print('=== bump_to_313.py ===')
print()

PROJECT_ROOT = Path('.')
OLD_VERSION = '3.1.2'
NEW_VERSION = '3.1.3'

# ============================================================================
# 1. Backend settings.py
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

# ============================================================================
# 3. UI хидеры
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

# ============================================================================
# 4. CHANGELOG.md
# ============================================================================
changelog_path = PROJECT_ROOT / 'CHANGELOG.md'
if changelog_path.exists():
    content = changelog_path.read_text(encoding='utf-8')
    
    section_313 = f'''## [{NEW_VERSION}] - 2026-06-16

### Added
- **Ранжирование проблем** (`analyzers/aggregators.py`):
  - Расчёт влияния каждого параметра на health score
  - 4 компонента: deviation, trend, anomalies, outliers
  - Веса параметров (CO2: 30%, Temp: 25%, VOC: 20%, Humidity: 15%, Pressure: 10%)
  - Поле `days_to_critical` — дни до достижения критической границы
- **Параметр `top_issues_count`** в `GET /analytics/report` (int, default=5)
- **Поле `top_issues`** в ответе `/analytics/report`

### Fixed
- **Outlier rate formula**: `outliers / (outliers + total_raw)` вместо `outliers / total_raw`
  - Исправлено: VOC outlier_rate был 314.8% (невозможно), теперь 75.9% (корректно)

### Example Output
```
"top_issues": [
  {
    "param": "voc",
    "impact": -5.16,
    "reason": "Avg 0.6 outside optimal range, 75.9% broken sensors",
    "severity": "medium",
    "weight": 0.2,
    "days_to_critical": null,
    "components": {
      "deviation": -1.68,
      "trend": 0,
      "anomalies": -0.44,
      "outliers": -3.04
    }
  },
  {
    "param": "humidity",
    "impact": -4.67,
    "reason": "Rising 0.74/day (R²=0.59), reaches CRITICAL in 52 days",
    "severity": "low",
    "weight": 0.15,
    "days_to_critical": 52,
    "components": {
      "deviation": 0,
      "trend": -4.25,
      "anomalies": 0,
      "outliers": -0.42
    }
  }
]
```

'''
    
    if f'## [{NEW_VERSION}]' not in content:
        content = content.replace(
            '# Changelog\n\n',
            '# Changelog\n\n' + section_313
        )
        changelog_path.write_text(content, encoding='utf-8', newline='\n')
        print(f'✓ CHANGELOG.md: добавлена секция {NEW_VERSION}')

# ============================================================================
# 5. Git commit
# ============================================================================
print()
print('=' * 60)
print('Git operations:')
print('=' * 60)

result = subprocess.run(['git', 'status', '--short'], capture_output=True, text=True)
changes = result.stdout.strip()
if not changes:
    print('ℹ Нет изменений для коммита')
    exit(0)

print('Изменения:')
for line in changes.split('\n')[:20]:
    print(f'  {line}')

result = subprocess.run(['git', 'add', '-A'], capture_output=True, text=True)
if result.returncode != 0:
    print(f'⚠ git add failed: {result.stderr}')

commit_msg = f'''feat(analytics): add top issues ranking to v{NEW_VERSION}

Added:
- rank_issues() — ranks problems by impact on health score
- 4 impact components: deviation, trend, anomalies, outliers
- Parameter weights (CO2: 30%, Temp: 25%, VOC: 20%, Humidity: 15%, Pressure: 10%)
- days_to_critical field — days until reaching critical threshold
- API parameter: top_issues_count (int, default=5)
- Response field: top_issues with severity levels

Fixed:
- Outlier rate formula: outliers / (outliers + total_raw) instead of outliers / total_raw
- Fixed VOC outlier_rate from 314.8% (impossible) to 75.9% (correct)

Example:
- Humidity: rising +0.74/day (R²=0.59), reaches CRITICAL in 52 days
- VOC: 75.9% broken sensors (equipment issue)
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
print('После пуша стартуем Фазу 2, Шаг 3: LLM слой (insights, рекомендации, прогнозы)')