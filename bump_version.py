from pathlib import Path
import re

print('=== bump_version.py (3.0.1 → 3.0.2) ===')
print()

changes = []

# 1. Backend: config/settings.py
settings_path = Path('backend/config/settings.py')
if settings_path.exists():
    content = settings_path.read_text(encoding='utf-8')
    pattern = r'app_version:\s*str\s*=\s*["\']3\.0\.1["\']'
    if re.search(pattern, content):
        content = re.sub(pattern, 'app_version: str = "3.0.2"', content)
        settings_path.write_text(content, encoding='utf-8', newline='\n')
        changes.append('✓ backend/config/settings.py: app_version → 3.0.2')
    elif 'app_version: str = "3.0.2"' in content:
        changes.append('ℹ backend/config/settings.py: уже 3.0.2')
    else:
        print('⚠ Не нашёл app_version в settings.py')

# 2. Frontend: Home.svelte
home_path = Path('frontend/src/routes/Home.svelte')
if home_path.exists():
    content = home_path.read_text(encoding='utf-8')
    if 'SCADA.AI v3.0.1' in content:
        content = content.replace('SCADA.AI v3.0.1', 'SCADA.AI v3.0.2')
        home_path.write_text(content, encoding='utf-8', newline='\n')
        changes.append('✓ frontend/src/routes/Home.svelte: v3.0.1 → v3.0.2')
    elif 'SCADA.AI v3.0.2' in content:
        changes.append('ℹ frontend/src/routes/Home.svelte: уже v3.0.2')

# 3. Frontend: Config.svelte
config_path = Path('frontend/src/routes/Config.svelte')
if config_path.exists():
    content = config_path.read_text(encoding='utf-8')
    if 'v3.0.1' in content:
        content = content.replace('v3.0.1', 'v3.0.2')
        config_path.write_text(content, encoding='utf-8', newline='\n')
        changes.append('✓ frontend/src/routes/Config.svelte: v3.0.1 → v3.0.2')
    elif 'v3.0.2' in content:
        changes.append('ℹ frontend/src/routes/Config.svelte: уже v3.0.2')

# 4. Docs CHANGELOG.md
changelog_path = Path('backend/docs/CHANGELOG.md')
if changelog_path.exists():
    content = changelog_path.read_text(encoding='utf-8')
    if '## [3.0.1]' in content and '## [3.0.2]' not in content:
        new_entry = """## [3.0.2] - 2026-06-08

### Added
- **Backend:** Встроенная документация системы (docs/)
  - README.md, MODULES.md, API.md, CHAT_EXAMPLES.md, ARCHITECTURE.md, CHANGELOG.md
  - REST API для доступа к документации (GET /docs/list, GET /docs/{filename})
- **Frontend:** DocsViewer компонент в конфигураторе
  - Sidebar со списком файлов + markdown рендеринг через marked
  - Вкладка "Документация" в Config.svelte

### Changed
- Версия приложения: 3.0.1 → 3.0.2

---

"""
        content = content.replace('# Changelog\n', f'# Changelog\n\n{new_entry}')
        changelog_path.write_text(content, encoding='utf-8', newline='\n')
        changes.append('✓ backend/docs/CHANGELOG.md: добавлена запись 3.0.2')

print()
for change in changes:
    print(f'  {change}')

print()
print('Готово! Перезапусти backend и проверь хидеры.')
