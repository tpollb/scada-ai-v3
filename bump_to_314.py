from pathlib import Path
import re
import subprocess

print('=== bump_to_314.py ===')
print()

PROJECT_ROOT = Path('.')
OLD_VERSION = '3.1.3'
NEW_VERSION = '3.1.4'

# ============================================================================
# 1. Backend settings.py
# ============================================================================
settings_path = PROJECT_ROOT / 'backend/config/settings.py'
if settings_path.exists():
    content = settings_path.read_text(encoding='utf-8')
    pattern = r'(app_version\s*[:=]\s*["\'])' + re.escape(OLD_VERSION) + r'(["\'])'
    new_content, count = re.subn(pattern, r'\g<1>' + NEW_VERSION + r'\2', content)
    if count > 0:
        settings_path.write_text(new_content, encoding='utf-8', newline='\n')
        print(f'✓ backend/config/settings.py: {OLD_VERSION} → {NEW_VERSION}')
    else:
        print('ℹ backend/config/settings.py: версия не найдена')

# ============================================================================
# 2. Frontend package.json
# ============================================================================
pkg_path = PROJECT_ROOT / 'frontend/package.json'
if pkg_path.exists():
    content = pkg_path.read_text(encoding='utf-8')
    pattern = r'("version"\s*:\s*")' + re.escape(OLD_VERSION) + r'(")'
    new_content, count = re.subn(pattern, r'\g<1>' + NEW_VERSION + r'\2', content)
    if count > 0:
        pkg_path.write_text(new_content, encoding='utf-8', newline='\n')
        print(f'✓ frontend/package.json: {OLD_VERSION} → {NEW_VERSION}')

# ============================================================================
# 3. UI хидеры
# ============================================================================
ui_files = [
    'frontend/src/routes/Home.svelte',
    'frontend/src/routes/Config.svelte',
]

for file_path in ui_files:
    p = PROJECT_ROOT / file_path
    if not p.exists():
        continue
    content = p.read_text(encoding='utf-8')
    new_content = content.replace(f'v{OLD_VERSION}', f'v{NEW_VERSION}')
    if new_content != content:
        p.write_text(new_content, encoding='utf-8', newline='\n')
        print(f'✓ {file_path}: v{OLD_VERSION} → v{NEW_VERSION}')

# ============================================================================
# 4. CHANGELOG.md
# ============================================================================
changelog_path = PROJECT_ROOT / 'CHANGELOG.md'
if changelog_path.exists():
    content = changelog_path.read_text(encoding='utf-8')
    
    section_314 = f'''## [{NEW_VERSION}] - 2026-06-16

### Added
- **LLM-слой для аналитики** (`modules/analytics/llm/analyzer.py`):
  - Класс `AnalyticsLLM` с методом `analyze()` для генерации insights, recommendations, forecast
  - Детальный `ANALYTICS_SYSTEM_PROMPT` с требованиями к JSON-формату
  - Функция `build_analytics_prompt()` для форматирования данных в user prompt
  - Graceful fallback при недоступности LLM (детерминированные рекомендации)
  - Парсинг JSON из ответа LLM (включая markdown code blocks)
- **Параметр `include_llm`** в `GET /analytics/report` (bool, default=true)
- **Поля в ответе** `/analytics/report`:
  - `summary`: краткое резюме ситуации (1-2 предложения)
  - `insights`: список ключевых инсайтов (3-5 пунктов)
  - `recommendations`: список конкретных действий с impact/effort/priority
  - `forecast`: прогноз на 7/30 дней с оценкой риска
  - `llm_error`: сообщение об ошибке если LLM использовал fallback

### Example Output
```
"summary": "Главная проблема — рост влажности...",
"insights": [
  "Влажность растёт на 0.74% в день (R²=0.591)",
  "75% датчиков VOC вышли из строя",
  "Корреляция temperature-humidity: r=-0.623"
],
"recommendations": [
  {
    "action": "Проверьте систему вентиляции в Зоне 2",
    "impact": "+4.7 баллов здоровья",
    "effort": "medium",
    "priority": "high"
  }
],
"forecast": {
  "7_days": "Влажность достигнет 46%",
  "30_days": "Влажность достигнет 63% (CRITICAL)",
  "risk": "medium"
}
```

### Technical
- Ленивая инициализация LLM provider через `core.llm.factory.get_provider()`
- Правильная сигнатура вызова: `provider.generate(system, user) -> str`
- Singleton pattern для `AnalyticsLLM` instance
- Fallback генерирует осмысленные рекомендации на основе топ проблем

'''
    
    if f'## [{NEW_VERSION}]' not in content:
        content = content.replace(
            '# Changelog\n\n',
            '# Changelog\n\n' + section_314
        )
        changelog_path.write_text(content, encoding='utf-8', newline='\n')
        print(f'✓ CHANGELOG.md: добавлена секция {NEW_VERSION}')

# ============================================================================
# 5. Git commit
# ============================================================================
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
for line in changes.split('\n')[:20]:
    print(f'  {line}')

result = subprocess.run(['git', 'add', '-A'], capture_output=True, text=True)
if result.returncode != 0:
    print(f'⚠ git add failed: {result.stderr}')

commit_msg = f'''feat(analytics): add LLM layer for insights and recommendations (v{NEW_VERSION})

Added:
- AnalyticsLLM class with analyze() method for generating insights, recommendations, forecast
- Detailed ANALYTICS_SYSTEM_PROMPT with strict JSON format requirements
- build_analytics_prompt() function for formatting analytics data into user prompt
- Graceful fallback when LLM is unavailable (deterministic recommendations)
- JSON parsing from LLM response (including markdown code blocks)
- API parameter: include_llm (bool, default=true)
- Response fields: summary, insights, recommendations, forecast, llm_error

Example output:
- Summary: "Main issue — humidity growth..."
- Insights: ["Humidity rising +0.74%/day (R²=0.591)", "75% VOC sensors broken"]
- Recommendations: [{"action": "Check ventilation in Zone 2", "impact": "+4.7 health points"}]
- Forecast: {"7_days": "Humidity reaches 46%", "30_days": "Humidity reaches 63% (CRITICAL)"}

Technical:
- Lazy initialization of LLM provider via core.llm.factory.get_provider()
- Correct API signature: provider.generate(system, user) -> str
- Singleton pattern for AnalyticsLLM instance
- Fallback generates meaningful recommendations based on top issues
'''

result = subprocess.run(
    ['git', 'commit', '-m', commit_msg],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    for line in result.stdout.split('\n'):
        if 'main' in line.lower() or line.startswith('[main'):
            print(f'✓ {line}')
            break
    else:
        print('✓ Commit создан')
else:
    print(f'⚠ git commit failed: {result.stderr}')
    exit(1)

print()
print('=' * 60)
print(f'✅ Релиз {NEW_VERSION} готов!')
print('=' * 60)
print()
print('Для пуша в remote:')
print('  git push')
print()
print('После пуша стартуем Фазу 3: Frontend (AnalyticsPanel с табами)')