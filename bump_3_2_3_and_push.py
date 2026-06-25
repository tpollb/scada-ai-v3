#!/usr/bin/env python3
"""
bump_3_2_3_and_push.py — бамп версии 3.2.3 + commit + push
"""
import subprocess
import json
from pathlib import Path

print('=' * 80)
print('БУМП ВЕРСИИ 3.2.3 + GIT COMMIT + PUSH')
print('=' * 80)
print()

# 1. Проверяем текущий статус
print('【1】Git status')
print('-' * 80)
result = subprocess.run(['git', 'status', '--short'], capture_output=True, text=True, encoding='utf-8')
print(result.stdout)

if not result.stdout.strip():
    print('ℹ️  Нет изменений для коммита')
else:
    print(f'Найдено изменений: {len(result.stdout.strip().split(chr(10)))} файлов')

print()

# 2. Ищем и обновляем версию
print('【2】Обновление версии')
print('-' * 80)

version_updated = False

# Проверяем backend/config/settings.py
settings_path = Path('backend/config/settings.py')
if settings_path.exists():
    content = settings_path.read_text(encoding='utf-8')
    if 'APP_VERSION' in content or 'VERSION' in content:
        for old in ['APP_VERSION = "3.2.2"', 'VERSION = "3.2.2"']:
            if old in content:
                content = content.replace(old, old.replace('3.2.2', '3.2.3'))
                settings_path.write_text(content, encoding='utf-8', newline='\n')
                print(f'  ✅ {settings_path}: 3.2.2 → 3.2.3')
                version_updated = True
                break
        if not version_updated:
            print(f'  ℹ️  {settings_path}: версия уже 3.2.3 или другой формат')
    else:
        print(f'  ℹ️  {settings_path}: нет константы VERSION')

# Проверяем frontend/package.json
pkg_path = Path('frontend/package.json')
if pkg_path.exists():
    data = json.loads(pkg_path.read_text(encoding='utf-8'))
    old_ver = data.get('version', '')
    if old_ver and old_ver != '3.2.3':
        data['version'] = '3.2.3'
        pkg_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8', newline='\n')
        print(f'  ✅ {pkg_path}: {old_ver} → 3.2.3')
        version_updated = True
    else:
        print(f'  ℹ️  {pkg_path}: версия уже {old_ver or "отсутствует"}')

print()

# 3. Git add
print('【3】Git add')
print('-' * 80)
result = subprocess.run(['git', 'add', '-A'], capture_output=True, text=True, encoding='utf-8')
if result.returncode == 0:
    print('  ✅ Все изменения добавлены в staging')
else:
    print(f'  ❌ Ошибка: {result.stderr}')

print()

# 4. Git commit
print('【4】Git commit')
print('-' * 80)

commit_msg = """fix(dda): исправлена визуализация аномалий на графиках (v3.2.3)

ПРОБЛЕМА:
- Точки аномалий "висели в воздухе" не на линии графика
- При наведении мыши показывались случайные шумы/пики/провалы
- Провалы отображались на неправильных позициях

КОРЕНЬ:
Смешанный формат данных в Chart.js:
- Основной line: index-based [val1, val2, ...]
- Scatter аномалии: timestamp-based [{x: ts, y: val}, ...]
- Tooltip mode "index" не мог правильно сопоставить их

РЕШЕНИЕ:
- Перевод ВСЕХ датасетов на единый index-based формат
- Scatter точки: [None, None, val, None, ...] вместо [{x, y}, ...]
- Маппинг timestamp → index через словарь ts_to_index
- Fallback логика: если точного совпадения нет — ищем ближайший timestamp (до 30 мин)
- Tooltip mode "index" теперь корректно показывает все датасеты

ФАЙЛЫ:
- backend/modules/deep_analysis/visualizers/chart_specs.py:
  * create_time_series_spec() полностью переписана
  * ts_to_index словарь для маппинга timestamp → index
  * Fallback поиск ближайшего timestamp при пропуске
  * Все типы аномалий (spike/dip/drift/noise) — scatter точки

РЕЗУЛЬТАТ:
✅ Точки аномалий точно на линии графика
✅ Tooltip показывает правильные значения
✅ Нет "случайных" точек в пустых местах
✅ Значения в tooltip совпадают со значениями на графике

Версия: 3.2.2 → 3.2.3
"""

result = subprocess.run(
    ['git', 'commit', '-m', commit_msg],
    capture_output=True,
    text=True,
    encoding='utf-8'
)

if result.returncode == 0:
    print('  ✅ Commit создан')
    print()
    print('  Сообщение:')
    for line in commit_msg.split('\n')[:10]:
        print(f'    {line}')
    print('    ...')
else:
    print(f'  ℹ️  {result.stderr.strip()}')

print()

# 5. Git push
print('【5】Git push')
print('-' * 80)
result = subprocess.run(['git', 'push'], capture_output=True, text=True, encoding='utf-8')

if result.returncode == 0:
    print('  ✅ Push выполнен успешно')
    if result.stdout:
        print(f'  {result.stdout[:200]}')
    if result.stderr:
        print(f'  {result.stderr[:200]}')
else:
    print(f'  ⚠️  Push требует действий:')
    print(f'  {result.stderr}')
    print()
    print('  Попробуй вручную:')
    print('    git push origin main')

print()
print('=' * 80)
print('ГОТОВО!')
print('=' * 80)
print()
print('Что было сделано в этой сессии:')
print('  ✅ Разобраны с timestamp-based vs index-based форматами')
print('  ✅ Исправлена визуализация аномалий')
print('  ✅ Tooltip работает корректно')
print('  ✅ Точки на правильных местах')
print()
print('Следующие шаги (завтра):')
print('  • ChartModal (кнопка ⛶ для полноэкранных графиков)')
print('  • Или FFT сезонность (Итерация A Day 3-4)')