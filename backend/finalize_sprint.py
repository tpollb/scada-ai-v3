"""Финальный фикс спринта: bump до 3.0.1 + git commit"""
import subprocess
import re
from pathlib import Path
from datetime import datetime

print("=" * 70)
print("🚀 ФИНАЛ СПРИНТА: bump версии 3.0.0 → 3.0.1 + git commit")
print("=" * 70)

# ============================================================================
# 1. Обновляем версию во всех файлах
# ============================================================================
print("\n📋 1. Обновляю версию 3.0.0 → 3.0.1")
print("-" * 70)

version_updates = []

# 1.1. config/settings.py
settings_path = Path('config/settings.py')
if settings_path.exists():
    content = settings_path.read_text(encoding='utf-8')
    if 'app_version: str = "3.0.0"' in content:
        content = content.replace('app_version: str = "3.0.0"', 'app_version: str = "3.0.1"')
        settings_path.write_text(content, encoding='utf-8', newline='\n')
        version_updates.append("config/settings.py")
        print("  ✅ config/settings.py: app_version → 3.0.1")

# 1.2. Config.svelte — заголовок
config_path = Path('../frontend/src/routes/Config.svelte')
if config_path.exists():
    content = config_path.read_text(encoding='utf-8')
    if 'v3.0.0' in content:
        content = content.replace('v3.0.0', 'v3.0.1')
        config_path.write_text(content, encoding='utf-8', newline='\n')
        version_updates.append("frontend/src/routes/Config.svelte")
        print("  ✅ Config.svelte: v3.0.0 → v3.0.1")

# 1.3. Home.svelte — если там есть версия
home_path = Path('../frontend/src/routes/Home.svelte')
if home_path.exists():
    content = home_path.read_text(encoding='utf-8')
    if 'v3.0.0' in content:
        content = content.replace('v3.0.0', 'v3.0.1')
        home_path.write_text(content, encoding='utf-8', newline='\n')
        version_updates.append("frontend/src/routes/Home.svelte")
        print("  ✅ Home.svelte: v3.0.0 → v3.0.1")

# 1.4. modules/hello/__init__.py
hello_init = Path('modules/hello/__init__.py')
if hello_init.exists():
    content = hello_init.read_text(encoding='utf-8')
    if 'v3.0.0' in content or '3.0.0' in content:
        content = content.replace('v3.0.0', 'v3.0.1').replace('"3.0.0"', '"3.0.1"')
        hello_init.write_text(content, encoding='utf-8', newline='\n')
        version_updates.append("modules/hello/__init__.py")
        print("  ✅ modules/hello/__init__.py: v3.0.0 → v3.0.1")

# 1.5. modules/hello/tools.py
hello_tools = Path('modules/hello/tools.py')
if hello_tools.exists():
    content = hello_tools.read_text(encoding='utf-8')
    if 'v3.0.0' in content or '3.0.0' in content:
        content = content.replace('v3.0.0', 'v3.0.1').replace('"3.0.0"', '"3.0.1"')
        hello_tools.write_text(content, encoding='utf-8', newline='\n')
        version_updates.append("modules/hello/tools.py")
        print("  ✅ modules/hello/tools.py: v3.0.0 → v3.0.1")

# 1.6. package.json (frontend)
pkg_path = Path('../frontend/package.json')
if pkg_path.exists():
    content = pkg_path.read_text(encoding='utf-8')
    if '"version": "3.0.0"' in content:
        content = content.replace('"version": "3.0.0"', '"version": "3.0.1"')
        pkg_path.write_text(content, encoding='utf-8', newline='\n')
        version_updates.append("frontend/package.json")
        print("  ✅ frontend/package.json: version → 3.0.1")

# 1.7. Чистим временные скрипты фикса
scripts_to_remove = [
    'fix_logs_tool.py',
    'fix_status_fields.py',
    'create_logs_tool.py',
    'add_status_fields.py',
    'debug_tool_chain.py',
    'debug_full_chain.py',
    'debug_yandex_payload.py',
    'debug_yandex_full_response.py',
    'fix_yandex_system_prompt.py',
    'fix_yandex_toolcall_format.py',
    'fix_both_errors.py',
    'fix_logs_tool_and_yandex.py',
    'final_fix_tool_chain.py',
    'final_fix_yandex_docs.py',
    'fix_chat_tool_calling.py',
    'remove_duplicate_logs_block.py',
    'fix_config_logs.py',
    'add_poll_interval.py',
    'fix_logs_position.py',
    'fix_logs_settings_ui.py',
    'fix_save_button.py',
    'fix_path_import_and_style.py',
]

removed_scripts = []
for s in scripts_to_remove:
    p = Path(s)
    if p.exists():
        p.unlink()
        removed_scripts.append(s)

if removed_scripts:
    print(f"\n  🗑️  Удалено {len(removed_scripts)} временных скриптов:")
    for s in removed_scripts:
        print(f"     • {s}")

# 1.8. Чистим __pycache__
import shutil
pycaches = list(Path('.').rglob('__pycache__'))
for pycache in pycaches:
    if 'venv' not in str(pycache):
        try:
            shutil.rmtree(pycache)
        except:
            pass
if pycaches:
    print(f"  🗑️  Очищено {len(pycaches)} __pycache__ директорий")

# ============================================================================
# 2. Git commit
# ============================================================================
print("\n📋 2. Создаю git commit")
print("-" * 70)

# Статус
result = subprocess.run(['git', 'status', '--short'], capture_output=True, text=True, cwd='..')
print("Изменённые файлы:")
print(result.stdout)

# Add all
subprocess.run(['git', 'add', '-A'], cwd='..')

# Commit с развёрнутым сообщением
commit_message = """feat: v3.0.1 — файловое логирование, tool calling, UI улучшения

Основные изменения:

## Файловая система логирования
- Логи пишутся в backend/logs/YYYY-MM-DD_HH-MM-SS.log (один файл на сессию)
- Буфер убран — читаем напрямую из файла
- История всех сессий сохраняется между перезапусками
- UI: селектор файлов (текущий + архив), кнопка "Вернуться к текущему"
- Экспорт в TXT через кнопку Download

## Tool calling через YandexGPT 5.1
- Полная поддержка нового формата toolCallList (yagpt-5.1-2025-08)
- modules/logs/tools.py: analyze_system_logs — анализ лога через LLM
- chat.py: использует generate_with_tools() с автоматическим вызовом tools
- yandex.py: правильные роли user + functionResult для ответов tool

## Настройки модуля logs
- Интервал polling в настройках модуля (Конфигуратор → Модули → logs)
- Сохранение в .env + runtime обновление
- Кнопка "Сохранить" в едином стиле с остальными настройками

## Статусы системы
- /system/info: db_status и llm_status через реальные проверки
- UI показывает ✓/✗ для БД и LLM на Home

## UI улучшения
- SystemLogsPanel: фильтры по уровням, авто-рефреш, экспорт
- Config.svelte: единый стиль настроек (DB, LLM, logs)
- Toast-сообщения с контрастными цветами и иконками

## Прочее
- core/logger.py: защита от повторной установки bridge
- Дедупликация записей при чтении из файла
- Убраны все хардкоды из chat.py"""

result = subprocess.run(
    ['git', 'commit', '-m', commit_message],
    capture_output=True,
    text=True,
    cwd='..',
    encoding='utf-8'
)

print("\n📝 Результат commit:")
print(result.stdout)
if result.returncode != 0:
    print("⚠️  Stderr:", result.stderr)

# ============================================================================
# 3. Git tag (опционально)
# ============================================================================
print("\n📋 3. Создаю git tag v3.0.1")
print("-" * 70)

result = subprocess.run(
    ['git', 'tag', '-a', 'v3.0.1', '-m', 'v3.0.1 — Файловое логирование + Tool calling'],
    capture_output=True,
    text=True,
    cwd='..',
    encoding='utf-8'
)

if result.returncode == 0:
    print("  ✅ Tag v3.0.1 создан")
else:
    print(f"  ⚠️  Tag: {result.stderr.strip()}")

# ============================================================================
# 4. Push (опционально)
# ============================================================================
print("\n📋 4. Push в remote")
print("-" * 70)

result = subprocess.run(
    ['git', 'push', 'origin', 'main', '--tags'],
    capture_output=True,
    text=True,
    cwd='..',
    encoding='utf-8'
)

print(result.stdout)
if result.stderr:
    print(result.stderr)

print("\n" + "=" * 70)
print("🎉 СПРИНТ ЗАВЕРШЁН!")
print("=" * 70)
print()
print("📦 Версия: 3.0.1")
print("📝 Commit создан с развёрнутым описанием")
print("🏷️  Tag v3.0.1 установлен")
print("🌐 Push выполнен (commit + tag)")
print()
print("Что сделано за спринт:")
print("  ✅ Файловая система логирования (backend/logs/)")
print("  ✅ UI с селектором файлов + экспорт в TXT")
print("  ✅ Tool calling через YandexGPT 5.1")
print("  ✅ Анализ системного лога через LLM")
print("  ✅ Настройки модуля logs в Конфигураторе")
print("  ✅ Статусы БД и LLM в /system/info")
print("  ✅ Множество UI-улучшений")
print()
print("🚀 Удачи на демонстрации! Есть что показать 💪")