from pathlib import Path
import re

print('=== bump_to_311.py ===')
print()

PROJECT_ROOT = Path('.')
OLD_VERSION = '3.1.0'
NEW_VERSION = '3.1.1'

# ============================================================================
# 1. Backend settings.py — app_version
# ============================================================================
settings_path = PROJECT_ROOT / 'backend/config/settings.py'
if settings_path.exists():
    content = settings_path.read_text(encoding='utf-8')
    # Ищем app_version: str = "3.1.0" или app_version = "3.1.0"
    pattern = r'(app_version\s*[:=]\s*["\'])' + re.escape(OLD_VERSION) + r'(["\'])'
    new_content, count = re.subn(pattern, r'\g<1>' + NEW_VERSION + r'\2', content)
    if count > 0:
        settings_path.write_text(new_content, encoding='utf-8', newline='\n')
        print(f'✓ backend/config/settings.py: {OLD_VERSION} → {NEW_VERSION} ({count} вхождений)')
    else:
        print('ℹ backend/config/settings.py: версия не найдена (может уже обновлена)')
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
# 4. CHANGELOG.md — добавляем секцию 3.1.1
# ============================================================================
changelog_path = PROJECT_ROOT / 'CHANGELOG.md'
if changelog_path.exists():
    content = changelog_path.read_text(encoding='utf-8')
    
    section_311 = f'''## [{NEW_VERSION}] - 2026-06-16

### Added
- **Модуль `analytics`** (скелет) — основа для трендов, корреляций и рекомендаций
  - `collectors/history.py` — сбор исторических данных за 7/30/90/365 дней
  - `analyzers/trends.py` — линейная регрессия, Z-score аномалии, slope_per_day
  - `api/routes/analytics.py` — endpoint `GET /analytics/report`

### Changed
- **Умная валидация** данных: используются строгие границы из `norms.crit_min/crit_max` вместо физических `validator.min/max`
  - Temperature: 10..35°C (отсекает битые датчики типа 0°C в помещении)
  - CO2: 350..2000 ppm (атмосферный ~415 ppm, 0 = битый)
- **SQL-агрегация** `GROUP BY DATE_TRUNC('hour'/'day')` вместо загрузки всех сырых точек
- **Автовыбор агрегации** по периоду: 7-90 дней → hourly, >90 дней → daily
- **Правильный slope** по реальным timestamps (единиц в день), а не по индексам

### Technical
- Backend: отдельный роутер `/analytics`, подключён в `main.py`
- Backend: структура `modules/analytics/` с `collectors/` и `analyzers/` подпапками
- Backend: все 5 параметров среды (temperature, humidity, co2, pressure, voc)

'''
    
    if f'## [{NEW_VERSION}]' not in content:
        # Вставляем после заголовка "# Changelog"
        content = content.replace(
            '# Changelog\n\n',
            '# Changelog\n\n' + section_311
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
import subprocess

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
commit_msg = f'''chore: bump version to {NEW_VERSION}

Release notes:
- Added analytics module skeleton (collectors + analyzers + router)
- Smart validation using norms.crit_min/crit_max instead of validator bounds
- SQL aggregation (GROUP BY hour/day) with auto-selection by period
- Proper slope calculation using real timestamps (units per day)
- All 5 environmental parameters supported (temperature, humidity, co2, pressure, voc)
'''

result = subprocess.run(
    ['git', 'commit', '-m', commit_msg],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    # Показываем hash коммита
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