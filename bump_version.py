import os
import re
import subprocess
from pathlib import Path

print("=== Bumping version to 3.1.0 ===\n")

# Find project root (where this script is located)
script_dir = Path(__file__).parent
project_root = script_dir
os.chdir(project_root)

print(f"Project root: {project_root}\n")

# Files to update
updates = []

# 1. Search for version in backend files
backend_files = [
    'backend/main.py',
    'backend/api/routes/system.py',
    'backend/config/settings.py',
]

for file_path in backend_files:
    full_path = project_root / file_path
    if full_path.exists():
        content = full_path.read_text(encoding='utf-8')
        
        # Pattern 1: APP_VERSION = "3.0.2"
        new_content = re.sub(
            r'(APP_VERSION|VERSION|app_version)\s*[:=]\s*["\'][\d\.]+["\']',
            r'\1 = "3.1.0"' if ':' not in content[:content.find('APP_VERSION') if 'APP_VERSION' in content else 0] else r'\1: "3.1.0"',
            content
        )
        
        if new_content != content:
            full_path.write_text(new_content, encoding='utf-8')
            updates.append(f"✓ {file_path}: version updated to 3.1.0")

# 2. Update frontend/package.json
package_json = project_root / 'frontend/package.json'
if package_json.exists():
    content = package_json.read_text(encoding='utf-8')
    new_content = re.sub(
        r'"version"\s*:\s*"[\d\.]+"',
        '"version": "3.1.0"',
        content
    )
    if new_content != content:
        package_json.write_text(new_content, encoding='utf-8')
        updates.append("✓ frontend/package.json: version updated to 3.1.0")

# 3. Update docs if they have version
docs_files = ['docs/README.md', 'docs/CHANGELOG.md', 'README.md', 'CHANGELOG.md']
for doc_file in docs_files:
    doc_path = project_root / doc_file
    if doc_path.exists():
        content = doc_path.read_text(encoding='utf-8')
        new_content = re.sub(
            r'SCADA\.AI v[\d\.]+',
            'SCADA.AI v3.1.0',
            content
        )
        if new_content != content:
            doc_path.write_text(new_content, encoding='utf-8')
            updates.append(f"✓ {doc_file}: version updated to 3.1.0")

print("Обновлённые файлы:")
if updates:
    for update in updates:
        print(f"  {update}")
else:
    print("  (файлы не найдены или версия уже 3.1.0)")

print("\n=== Git operations ===\n")

# Git add all changes
result = subprocess.run(['git', 'add', '-A'], capture_output=True, text=True)
if result.returncode == 0:
    print("✓ git add -A")
else:
    print(f"✗ git add failed: {result.stderr}")

# Git status to see what changed
result = subprocess.run(['git', 'status', '--short'], capture_output=True, text=True)
if result.returncode == 0:
    changes = result.stdout.strip()
    if changes:
        print("\nИзменения:")
        for line in changes.split('\n')[:10]:  # Show first 10 changes
            print(f"  {line}")
        if len(changes.split('\n')) > 10:
            print(f"  ... и ещё {len(changes.split('\n')) - 10} файлов")
    else:
        print("\nНет изменений для коммита")
        exit(0)

# Git commit
commit_message = """feat: v3.1.0 - модуль энергоучёта (Бабло)

Added:
- Модули energy_electricity, energy_water, energy_heat
- Виджет energy_cost_card с расчётом стоимости
- Конфигуратор тарифов и тегов счётчиков
- Детализация расчёта под статусами индексов

Changed:
- Формула health_score: 40% Аварии + 35% Среда + 25% Оборудование
- Удалён energy_panel (заменён на energy_cost_card)
- Сворачиваемые блоки в health report

Fixed:
- Пустой sub_scores теперь вычисляется детерминированно
- Layout виджетов: 3 в ряд вместо 2×2"""

result = subprocess.run(
    ['git', 'commit', '-m', commit_message],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    print("\n✓ git commit")
    # Extract commit hash
    lines = result.stdout.split('\n')
    for line in lines:
        if line.startswith('main') or line.startswith('[main'):
            print(f"  {line}")
            break
else:
    print(f"\n✗ git commit failed: {result.stderr}")
    exit(1)

# Git push
print("\nPushing to remote...")
result = subprocess.run(['git', 'push'], capture_output=True, text=True)

if result.returncode == 0:
    print("✓ git push")
    print("\n✅ Релиз v3.1.0 успешно запушен!")
else:
    print(f"✗ git push failed: {result.stderr}")
    print("\nВозможно нужно настроить upstream:")
    print("  git push --set-upstream origin main")