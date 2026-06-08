from pathlib import Path
import re

print('=== bump_version.py (3.0.1 → 3.0.2) ===')
print()

# Файлы для проверки
files_to_check = [
    ('backend/config/settings.py', 'app_version'),
    ('frontend/src/routes/Home.svelte', 'SCADA.AI v'),
    ('frontend/src/routes/Config.svelte', 'v3.0.1'),
]

changes = []

# 1. Backend: config/settings.py
settings_path = Path('/c/dev/SCADA.AI/scada-ai-v3/backend/config/settings.py')
if settings_path.exists():
    content = settings_path.read_text(encoding='utf-8')
    
    # Ищем app_version: str = "3.0.1"
    pattern = r'app_version:\s*str\s*=\s*["\']3\.0\.1["\']'
    if re.search(pattern, content):
        content = re.sub(pattern, 'app_version: str = "3.0.2"', content)
        settings_path.write_text(content, encoding='utf-8', newline='\n')
        changes.append('✓ backend/config/settings.py: app_version → 3.0.2')
    else:
        print('⚠ Не нашёл app_version: str = "3.0.1" в settings.py')
else:
    print('⚠ Файл не найден: settings.py')

# 2. Frontend: Home.svelte (хидер)
home_path = Path('/c/dev/SCADA.AI/scada-ai-v3/frontend/src/routes/Home.svelte')
if home_path.exists():
    content = home_path.read_text(encoding='utf-8')
    
    # Ищем SCADA.AI v3.0.1
    if 'SCADA.AI v3.0.1' in content:
        content = content.replace('SCADA.AI v3.0.1', 'SCADA.AI v3.0.2')
        home_path.write_text(content, encoding='utf-8', newline='\n')
        changes.append('✓ frontend/src/routes/Home.svelte: SCADA.AI v3.0.1 → v3.0.2')
    else:
        print('⚠ Не нашёл "SCADA.AI v3.0.1" в Home.svelte')
else:
    print('⚠ Файл не найден: Home.svelte')

# 3. Frontend: Config.svelte (хидер)
config_path = Path('/c/dev/SCADA.AI/scada-ai-v3/frontend/src/routes/Config.svelte')
if config_path.exists():
    content = config_path.read_text(encoding='utf-8')
    
    # Ищем v3.0.1
    if 'v3.0.1' in content:
        content = content.replace('v3.0.1', 'v3.0.2')
        config_path.write_text(content, encoding='utf-8', newline='\n')
        changes.append('✓ frontend/src/routes/Config.svelte: v3.0.1 → v3.0.2')
    else:
        print('⚠ Не нашёл "v3.0.1" в Config.svelte')
else:
    print('⚠ Файл не найден: Config.svelte')

# 4. Проверяем другие возможные места
other_files = [
    '/c/dev/SCADA.AI/scada-ai-v3/backend/pyproject.toml',
    '/c/dev/SCADA.AI/scada-ai-v3/frontend/package.json',
]

for file_path in other_files:
    path = Path(file_path)
    if path.exists():
        content = path.read_text(encoding='utf-8')
        if '3.0.1' in content:
            print(f'ℹ {path.name}: содержит "3.0.1" (проверь вручную)')

print()
print('=' * 60)
print('ВНЕСЁННЫЕ ИЗМЕНЕНИЯ:')
print('=' * 60)
for change in changes:
    print(f'  {change}')

print()
print('=' * 60)
print('СЛЕДУЮЩИЙ ШАГ:')
print('=' * 60)
print('  Backend: перезапустить для применения новой версии')
print('  Frontend: Vite подхватит через HMR')
print()
print('Проверь:')
print('  • Home.svelte хидер: SCADA.AI v3.0.2')
print('  • Config.svelte хидер: v3.0.2')
print('  • API ответ /: version: 3.0.2')
print()
print('Когда ок — скажи "версия обновлена" и коммитим')