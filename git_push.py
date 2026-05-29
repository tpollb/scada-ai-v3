"""git_push.py — полный git workflow: add → commit → push → tag"""
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).parent

def run(cmd, check=True, capture=True):
    """Запуск shell-команды с красивым выводом"""
    print(f"  > {cmd}")
    result = subprocess.run(
        cmd, shell=True, cwd=BASE,
        capture_output=capture, text=True
    )
    if capture and result.stdout.strip():
        for line in result.stdout.strip().split("\n"):
            print(f"    {line}")
    if capture and result.stderr.strip() and result.returncode != 0:
        for line in result.stderr.strip().split("\n"):
            print(f"    [err] {line}")
    if check and result.returncode != 0:
        print(f"❌ Команда завершилась с кодом {result.returncode}")
        sys.exit(1)
    return result

print(f"📂 Рабочая папка: {BASE}")
print("=" * 60)

# 1. Проверка что это git-репозиторий
if not (BASE / ".git").exists():
    print("❌ Папка не является git-репозиторием. Запусти 'git init' сначала.")
    sys.exit(1)
print("✅ Git-репозиторий найден")

# 2. Настройка пользователя (если не настроен)
result = run("git config user.name", check=False)
if not result.stdout.strip():
    print("\n⚙️  Git user не настроен. Настройте:")
    name = input("  Your name (например 'Ivan Uskov'): ").strip() or "SCADA Developer"
    email = input("  Your email: ").strip() or "dev@scada-ai.local"
    run(f'git config user.name "{name}"')
    run(f'git config user.email "{email}"')
    print(f"✅ Настроено: {name} <{email}>")

# 3. Ветка main
run("git branch -M main", check=False)
print("✅ Ветка: main")

# 4. Статус
print("\n📋 Статус репозитория:")
run("git status --short")

# 5. git add
print("\n➕ Добавляем все файлы...")
run("git add .")

# 6. Проверяем есть ли что коммитить
result = run("git diff --cached --name-only", check=False)
changed_files = [f for f in result.stdout.strip().split("\n") if f.strip()]

if not changed_files:
    print("ℹ️  Нечего коммитить (всё уже закоммичено)")
    # Проверим есть ли коммиты вообще
    commits = run("git log --oneline", check=False)
    if not commits.stdout.strip():
        print("⚠️  Репозиторий пустой — делаем initial commit")
        run('git commit -m "feat: v3.0.0 initial release"')
    else:
        print("✅ Продолжаем с существующими коммитами")
else:
    print(f"\n📦 Изменено файлов: {len(changed_files)}")
    # Показываем первые 10
    for f in changed_files[:10]:
        print(f"    {f}")
    if len(changed_files) > 10:
        print(f"    ... и ещё {len(changed_files) - 10}")

    # 7. Commit
    print("\n💾 Коммитим...")
    commit_msg = """feat: v3.0.0 initial release

Backend:
- FastAPI + модульная архитектура (ModuleRegistry + ToolExecutor)
- Тестовый модуль hello с Tool Use
- API: /health, /chat
- Конфигурация через .env

Frontend:
- Svelte 5 + Tailwind v4
- 4 канала вывода: Voice / Narrative / Visual / Command Log
- 2 режима: Operator Mode + Config Mode
- UI компоненты: Input, NarrativePanel

Архитектурные принципы:
- Модульность (каждый модуль изолирован)
- Read-Only AI (чтение из БД, команды через SCADA API)
- Tool Use (модель вызывает инструменты)
- DB-Agnostic History Layer (PostgreSQL → TimescaleDB)
"""
    # Записываем сообщение во временный файл (избегаем проблем с кавычками)
    msg_file = BASE / ".git_commit_msg.txt"
    msg_file.write_text(commit_msg, encoding="utf-8")
    run(f'git commit -F ".git_commit_msg.txt"')
    msg_file.unlink()
    print("✅ Коммит создан")

# 8. Логи
print("\n📜 Последние коммиты:")
run("git log --oneline -5")

# 9. Remote
print("\n🌍 Проверяем remote...")
result = run("git remote -v", check=False)
remotes = result.stdout.strip()

if not remotes:
    print("⚠️  Remote не настроен.")
    print("\n📝 Введите URL репозитория (GitHub/GitLab/Bitbucket):")
    print("   Примеры:")
    print("   - https://github.com/username/scada-ai-v3.git")
    print("   - git@github.com:username/scada-ai-v3.git")
    print("   - https://gitlab.com/username/scada-ai-v3.git")
    print()
    url = input("  URL: ").strip()
    if not url:
        print("❌ URL не указан. Пропускаем push.")
        print("\n💡 Позже можно добавить:")
        print("   git remote add origin <URL>")
        print("   git push -u origin main")
        sys.exit(0)
    run(f'git remote add origin "{url}"')
    print(f"✅ Remote 'origin' добавлен: {url}")
else:
    print("✅ Remote настроен:")
    for line in remotes.split("\n")[:2]:
        print(f"    {line}")

# 10. Push
print("\n🚀 Пушим в origin/main...")
result = run("git push -u origin main", check=False)
if result.returncode != 0:
    print("\n⚠️  Push не удался. Возможные причины:")
    print("   1. Неверный URL репозитория")
    print("   2. Нет прав (нужен токен или SSH-ключ)")
    print("   3. Ветка 'main' не существует на remote")
    print("\n💡 Решения:")
    print("   - Для GitHub: используй Personal Access Token")
    print("     git remote set-url origin https://TOKEN@github.com/user/repo.git")
    print("   - Для SSH: проверь что ключ добавлен в GitHub")
    print("   - Попробуй форсировать (ОСТОРОЖНО, перезапишет remote!):")
    print("     git push -u origin main --force")

    force = input("\n🔥 Попробовать force push? (yes/no): ").strip().lower()
    if force == "yes":
        run("git push -u origin main --force")
    else:
        print("ℹ️  Force push отменён. Исправь remote вручную.")
        sys.exit(1)
else:
    print("✅ Push успешен!")

# 11. Тег
print("\n🏷️  Создаём тег v3.0.0...")
result = run("git tag -l v3.0.0", check=False)
if result.stdout.strip():
    print("ℹ️  Тег v3.0.0 уже существует — пропускаем")
else:
    run('git tag -a v3.0.0 -m "v3.0.0: Initial release - modular architecture + 4 output channels"')
    run("git push origin v3.0.0", check=False)
    print("✅ Тег v3.0.0 создан и запушен")

# 12. Финал
print("\n" + "=" * 60)
print("🎉 ГОТОВО!")
print("=" * 60)
print("\n📊 Итог:")
run("git log --oneline -3", check=False)
print()
run("git tag -l", check=False)
print()
run("git remote -v", check=False)
print("\n✅ Репозиторий v3.0.0 закоммичен, запушен и помечен тегом.")
print("🚀 Можно продолжать разработку v3.0.1!")
