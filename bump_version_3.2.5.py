#!/usr/bin/env python3
"""
bump_version_3.2.5.py — бамп версии до 3.2.5 с полным сканированием
"""
import re
from pathlib import Path

print('=' * 80)
print('БАМП ВЕРСИИ: 3.2.x → 3.2.5')
print('=' * 80)
print()

# Сканируем проект рекурсивно
root = Path('/c/dev/SCADA.AI/scada-ai-v3')
changes = []

# Файлы для проверки
target_files = [
    'frontend/package.json',
    'frontend/package-lock.json',
    'backend/main.py',
    'backend/config/settings.py',
    'README.md',
    'CHANGELOG.md',
    'pyproject.toml',
]

print('【1】Сканируем файлы на наличие версий 3.2.x')
print('-' * 80)

for rel_path in target_files:
    file_path = root / rel_path
    if not file_path.exists():
        continue
    
    content = file_path.read_text(encoding='utf-8')
    original = content
    
    # Ищем версии 3.2.0-3.2.4 или 3.2.6+
    matches = list(re.finditer(r'3\.2\.[0-46-9]', content))
    
    if matches:
        print(f'  📄 {rel_path}: найдено {len(matches)} упоминаний')
        
        # Заменяем все 3.2.x на 3.2.5
        content = re.sub(r'3\.2\.[0-46-9]', '3.2.5', content)
        
        if content != original:
            file_path.write_text(content, encoding='utf-8', newline='\n')
            changes.append(f'{rel_path}: обновлено {len(matches)} упоминаний')
            print(f'     ✅ Обновлено до 3.2.5')

print()

# 2. Проверяем что везде 3.2.5
print('【2】Проверяем что везде 3.2.5')
print('-' * 80)

for rel_path in target_files:
    file_path = root / rel_path
    if not file_path.exists():
        continue
    
    content = file_path.read_text(encoding='utf-8')
    old_versions = re.findall(r'3\.2\.[0-46-9]', content)
    
    if old_versions:
        print(f'  ⚠️  {rel_path}: всё ещё есть старые версии: {set(old_versions)}')
    else:
        if '3.2.5' in content:
            print(f'  ✅ {rel_path}: 3.2.5')

print()

# 3. Добавляем запись в CHANGELOG
print('【3】Добавляем запись в CHANGELOG.md')
print('-' * 80)

changelog_path = root / 'CHANGELOG.md'
if changelog_path.exists():
    changelog = changelog_path.read_text(encoding='utf-8')
    
    new_entry = '''## [3.2.5] - 2026-06-26

### Fixed
- **Multi-tag анализ**: исправлена проблема с отображением точек аномалий
  - Теперь передаются реальные timestamps вместо индексов в `detect_anomalies_isolation_forest`
  - Точки аномалий корректно отображаются на графике для 2+ тегов
- **ChartModal**: исправлены кнопки zoom/download
  - `bind:chartInstance` → `bind:chart` (правильный синтаксис для svelte-chartjs v4)
  - Все кнопки теперь работают: zoom in/out, reset, download PNG

### Changed
- Улучшена синхронизация данных в multi-tag графиках

'''
    
    # Вставляем после ## [Unreleased] или в начало
    if '## [Unreleased]' in changelog:
        changelog = changelog.replace('## [Unreleased]', f'## [Unreleased]\n\n{new_entry}')
    else:
        # Вставляем в начало после заголовка
        lines = changelog.split('\n')
        insert_idx = 0
        for i, line in enumerate(lines):
            if line.startswith('# ') and i == 0:
                insert_idx = i + 1
                break
            elif line.startswith('## [') and i > 0:
                insert_idx = i
                break
        lines.insert(insert_idx, new_entry)
        changelog = '\n'.join(lines)
    
    changelog_path.write_text(changelog, encoding='utf-8', newline='\n')
    changes.append('CHANGELOG.md: добавлена запись о 3.2.5')
    print('✅ Запись добавлена в CHANGELOG.md')
else:
    print('⚠️  CHANGELOG.md не найден')

print()

# 4. Показываем что изменилось
print('=' * 80)
print('ИЗМЕНЕНИЯ:')
print('=' * 80)
if changes:
    for change in changes:
        print(f'  • {change}')
else:
    print('  (изменений не найдено)')

print()
print('=' * 80)
print('СЛЕДУЮЩИЕ ШАГИ:')
print('=' * 80)
print()
print('Запусти эти команды для коммита и пуша:')
print()
print('  cd /c/dev/SCADA.AI/scada-ai-v3')
print('  git add -A')
print('  git commit -m "fix(dda): multi-tag timestamps + chart modal buttons (v3.2.5)"')
print('  git push')
print()
print('Или одной командой:')
print('  cd /c/dev/SCADA.AI/scada-ai-v3 && git add -A && git commit -m "fix(dda): multi-tag timestamps + chart modal buttons (v3.2.5)" && git push')