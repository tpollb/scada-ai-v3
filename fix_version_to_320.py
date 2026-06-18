from pathlib import Path
import re

print('=== fix_version_to_320.py ===')
print()

PROJECT_ROOT = Path('.')

files_to_update = [
    ('frontend/src/routes/Home.svelte', 'v3.1.4', 'v3.2.0'),
    ('frontend/src/routes/Config.svelte', 'v3.1.4', 'v3.2.0'),
]

# ============================================================================
# 1. Обновляем фронтенд (хардкоды)
# ============================================================================
for file_path, old_ver, new_ver in files_to_update:
    path = PROJECT_ROOT / file_path
    if not path.exists():
        print(f'⚠ Файл не найден: {file_path}')
        continue
    
    content = path.read_text(encoding='utf-8')
    if old_ver in content:
        new_content = content.replace(old_ver, new_ver)
        path.write_text(new_content, encoding='utf-8', newline='\n')
        count = content.count(old_ver)
        print(f'✓ {file_path}: {old_ver} → {new_ver} ({count} упоминаний)')
    elif new_ver in content:
        print(f'ℹ {file_path}: уже {new_ver}')
    else:
        print(f'⚠ {file_path}: не найдена версия {old_ver}')

# ============================================================================
# 2. Проверяем backend/config/settings.py
# ============================================================================
settings_path = PROJECT_ROOT / 'backend/config/settings.py'
if settings_path.exists():
    content = settings_path.read_text(encoding='utf-8')
    # Ищем app_version = "..."
    pattern = r'(app_version\s*=\s*["\'])([^"\']+)(["\'])'
    match = re.search(pattern, content)
    if match:
        current_ver = match.group(2)
        if current_ver != '3.2.0':
            new_content = re.sub(pattern, rf'\g<1>3.2.0\g<3>', content)
            settings_path.write_text(new_content, encoding='utf-8', newline='\n')
            print(f'✓ backend/config/settings.py: {current_ver} → 3.2.0')
        else:
            print(f'ℹ backend/config/settings.py: уже 3.2.0')
    else:
        print('⚠ backend/config/settings.py: app_version не найден')

# ============================================================================
# 3. Проверяем frontend/package.json
# ============================================================================
import json
package_path = PROJECT_ROOT / 'frontend/package.json'
if package_path.exists():
    with open(package_path, 'r', encoding='utf-8') as f:
        package = json.load(f)
    
    current_ver = package.get('version', 'unknown')
    if current_ver != '3.2.0':
        package['version'] = '3.2.0'
        with open(package_path, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(package, f, indent=2, ensure_ascii=False)
            f.write('\n')
        print(f'✓ frontend/package.json: {current_ver} → 3.2.0')
    else:
        print(f'ℹ frontend/package.json: уже 3.2.0')

print()
print('=' * 60)
print('ВЕРСИЯ ОБНОВЛЕНА ДО 3.2.0')
print('=' * 60)
print()
print('Обновлено:')
print('  • frontend/src/routes/Home.svelte (хедер)')
print('  • frontend/src/routes/Config.svelte (футер)')
print('  • backend/config/settings.py (API /system/info)')
print('  • frontend/package.json')
print()
print('Frontend перезагрузится автоматически (Vite HMR).')
print('Backend перезапусти: Ctrl+C → python -m uvicorn backend.main:app')
print()
print('Коммит и пуш:')
print()
print('```bash')
print('cd /c/dev/SCADA.AI/scada-ai-v3')
print('git add -A')
print('git commit -m "chore: bump version to 3.2.0 in UI headers"')
print('git push origin main')
print('```')