from pathlib import Path
import subprocess

print('=== fix_commit.py ===')
print()

PROJECT_ROOT = Path('.')

# Проверяем что backend/config/settings.py существует и ищем версию
settings_path = PROJECT_ROOT / 'backend/config/settings.py'
if settings_path.exists():
    content = settings_path.read_text(encoding='utf-8')
    if '3.1.3' in content:
        content = content.replace('3.1.3', '3.1.4')
        settings_path.write_text(content, encoding='utf-8', newline='\n')
        print('✓ backend/config/settings.py: 3.1.3 → 3.1.4')
    elif '3.1.4' in content:
        print('ℹ backend/config/settings.py: уже 3.1.4')
    else:
        print('⚠ backend/config/settings.py: версия не найдена')
        # Показываем что там есть
        for i, line in enumerate(content.split('\n'), 1):
            if 'version' in line.lower() and '=' in line:
                print(f'  {i}: {line.strip()}')
else:
    print('⚠ backend/config/settings.py не найден')

# Git commit с обычной строкой (без f-string для commit_msg)
print()
print('=' * 60)
print('Git operations:')
print('=' * 60)

result = subprocess.run(['git', 'status', '--short'], capture_output=True, text=True)
changes = result.stdout.strip()
if not changes:
    print('ℹ Нет изменений для коммита')
    exit(0)

print('Изменения:')
for line in changes.split('\n')[:25]:
    print(f'  {line}')

# git add
result = subprocess.run(['git', 'add', '-A'], capture_output=True, text=True)
if result.returncode != 0:
    print(f'⚠ git add failed: {result.stderr}')

# Commit message БЕЗ f-string (просто обычная строка)
commit_msg = """feat(analytics): add LLM layer for insights and recommendations (v3.1.4)

Added:
- AnalyticsLLM class with analyze() method for generating insights, recommendations, forecast
- Detailed ANALYTICS_SYSTEM_PROMPT with strict JSON format requirements
- build_analytics_prompt() function for formatting analytics data into user prompt
- Graceful fallback when LLM is unavailable (deterministic recommendations)
- JSON parsing from LLM response (including markdown code blocks)
- API parameter: include_llm (bool, default=true)
- Response fields: summary, insights, recommendations, forecast, llm_error

Example output:
- Summary: "Main issue - humidity growth..."
- Insights: ["Humidity rising +0.74%/day (R2=0.591)", "75% VOC sensors broken"]
- Recommendations: action="Check ventilation in Zone 2", impact="+4.7 health points"
- Forecast: 7_days="Humidity reaches 46%", 30_days="Humidity reaches 63% (CRITICAL)"

Technical:
- Lazy initialization of LLM provider via core.llm.factory.get_provider()
- Correct API signature: provider.generate(system, user) -> str
- Singleton pattern for AnalyticsLLM instance
- Fallback generates meaningful recommendations based on top issues
"""

result = subprocess.run(
    ['git', 'commit', '-m', commit_msg],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    print('✓ Commit создан')
    for line in result.stdout.split('\n')[:5]:
        if line.strip():
            print(f'  {line}')
else:
    print(f'⚠ git commit failed: {result.stderr}')
    exit(1)

# Git push
print()
print('Pushing to remote...')
result = subprocess.run(['git', 'push'], capture_output=True, text=True)
if result.returncode == 0:
    print('✓ Pushed successfully')
    # Показываем stderr (там обычно прогресс push)
    for line in result.stderr.split('\n'):
        if '->' in line or 'fast-forward' in line or 'main' in line.lower():
            print(f'  {line}')
else:
    print(f'⚠ git push failed: {result.stderr}')
    print('Попробуй вручную: git push')

print()
print('=' * 60)
print('✅ Релиз 3.1.4 готов!')
print('=' * 60)
print()
print('Теперь стартуем Фазу 3: Frontend (AnalyticsPanel с табами)')