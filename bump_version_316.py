from pathlib import Path
import json
import re

print('=== Bump to v3.1.6 ===')
print()

PROJECT_ROOT = Path('.')

# ============================================================================
# 1. Backend: config/settings.py
# ============================================================================
settings_path = PROJECT_ROOT / 'backend/config/settings.py'
if settings_path.exists():
    content = settings_path.read_text(encoding='utf-8')
    old_content = content
    
    # Ищем app_version = "..."
    pattern = r'(app_version\s*=\s*["\'])([^"\']+)(["\'])'
    match = re.search(pattern, content)
    if match:
        old_version = match.group(2)
        content = re.sub(pattern, rf'\g<1>3.1.6\g<3>', content)
        settings_path.write_text(content, encoding='utf-8', newline='\n')
        print(f'✓ Backend: {old_version} → 3.1.6')
    else:
        print('⚠ Backend: app_version не найден')

# ============================================================================
# 2. Frontend: package.json
# ============================================================================
package_path = PROJECT_ROOT / 'frontend/package.json'
if package_path.exists():
    with open(package_path, 'r', encoding='utf-8') as f:
        package = json.load(f)
    
    old_version = package.get('version', 'unknown')
    package['version'] = '3.1.6'
    
    with open(package_path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(package, f, indent=2, ensure_ascii=False)
        f.write('\n')
    
    print(f'✓ Frontend: {old_version} → 3.1.6')

# ============================================================================
# 3. CHANGELOG.md
# ============================================================================
changelog_path = PROJECT_ROOT / 'CHANGELOG.md'
if changelog_path.exists():
    content = changelog_path.read_text(encoding='utf-8')
    
    new_entry = f'''## [3.1.6] - 2026-06-17

### Added
- Analytics dashboard with interactive charts (Chart.js)
- Trend line and forecast visualization
- Moving average (MA-7) for smoothing data
- Expandable cards for issues and recommendations
- Forecast tab with 7/30/90/365 day periods

### Fixed
- Chart.js `state_snapshot_uncloneable` warning (removed callbacks)
- Y-axis limits now use `suggestedMin`/`suggestedMax` for proper scaling
- MA-7 color changed to purple to avoid conflict with VOC orange
- Trend line math corrected (proper day-based calculation)
- Forecast values clipped to physical limits

### Improved
- Russian UI translation for all analytics components
- Adaptive downsampling for large datasets (up to 500 points)
- Period selector correctly triggers new data fetch
- Raw data now uses last 200 points instead of first

'''
    
    # Вставляем после заголовка
    content = content.replace('# Changelog\n\n', f'# Changelog\n\n{new_entry}')
    changelog_path.write_text(content, encoding='utf-8', newline='\n')
    print('✓ CHANGELOG.md: добавлена запись 3.1.6')

print()
print('=' * 60)
print('Версия обновлена до 3.1.6')
print('=' * 60)
print()
print('Теперь выполни коммит:')
print()
print('```bash')
print('cd /c/dev/SCADA.AI/scada-ai-v3')
print('git add -A')
print('git commit -m "chore(release): bump to v3.1.6"')
print('git push origin main')
print('```')
print()
print('После push скажи **"3.1.6 в remote"** и расскажи какие идеи есть — продолжим улучшать аналитику! 🔵')