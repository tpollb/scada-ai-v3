from pathlib import Path
import json
import re

print('=== Bump to v3.2.0 (Analytics Engine Complete) ===')
print()

PROJECT_ROOT = Path('.')

# ============================================================================
# 1. Backend: config/settings.py
# ============================================================================
settings_path = PROJECT_ROOT / 'backend/config/settings.py'
if settings_path.exists():
    content = settings_path.read_text(encoding='utf-8')
    pattern = r'(app_version\s*=\s*["\'])([^"\']+)(["\'])'
    match = re.search(pattern, content)
    if match:
        old_version = match.group(2)
        content = re.sub(pattern, rf'\g<1>3.2.0\g<3>', content)
        settings_path.write_text(content, encoding='utf-8', newline='\n')
        print(f'✓ Backend: {old_version} → 3.2.0')

# ============================================================================
# 2. Frontend: package.json
# ============================================================================
package_path = PROJECT_ROOT / 'frontend/package.json'
if package_path.exists():
    with open(package_path, 'r', encoding='utf-8') as f:
        package = json.load(f)
    
    old_version = package.get('version', 'unknown')
    package['version'] = '3.2.0'
    
    with open(package_path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(package, f, indent=2, ensure_ascii=False)
        f.write('\n')
    
    print(f'✓ Frontend: {old_version} → 3.2.0')

# ============================================================================
# 3. CHANGELOG.md — добавляем запись 3.2.0
# ============================================================================
changelog_path = PROJECT_ROOT / 'CHANGELOG.md'
if changelog_path.exists():
    content = changelog_path.read_text(encoding='utf-8')
    
    # Если запись 3.2.0 уже есть — заменяем её на полную версию
    if '## [3.2.0]' in content:
        # Удаляем старую запись
        content = re.sub(
            r'## \[3\.2\.0\].*?(?=## \[3\.1\.0\]|\Z)',
            '',
            content,
            flags=re.DOTALL
        )
    
    new_entry = '''## [3.2.0] - 2026-06-17

### Added
- **Модуль `analytics`** — полноценный движок аналитики SCADA-системы:
  - `collectors/history.py` — сбор исторических данных (hourly/daily/raw)
  - `analyzers/trends.py` — линейная регрессия (slope, R², direction)
  - `analyzers/correlations.py` — Pearson + временной лаг
  - `analyzers/aggregators.py` — ранжирование проблем (impact score)
  - `llm/analyzer.py` — YandexGPT insights + deterministic fallback
  - `norms.py` — нормативные диапазоны параметров
- **Endpoint `GET /analytics/report`** с параметрами:
  - `period` (1-365 дней)
  - `params` (all или список)
  - `aggregation` (auto/hourly/daily/raw)
  - `include_llm` (true/false)
- **Визуализация аналитики** (Chart.js + svelte-chartjs):
  - Интерактивные графики с 4 линиями: данные, тренд, MA-7, прогноз
  - Фиксированные пределы оси Y по физическим границам параметров
  - Zoom/pan через `chartjs-plugin-zoom` (колёсико мыши, drag, pinch)
  - Экспорт графиков в PNG через `chart.toBase64Image()`
  - Кнопки управления: Zoom In / Zoom Out / Reset / Download PNG
- **UI аналитики** (`AnalyticsPanel.svelte`):
  - 4 вкладки: Тренды, Проблемы, Рекомендации, Прогноз
  - Периоды прогноза: 7/30/90/365 дней
  - Раскрывающиеся карточки проблем (компоненты impact, нормы параметра)
  - Раскрывающиеся карточки рекомендаций (детали расчёта)
  - Русификация всех текстов (severity, effort, reason)
- **Интеграция с чатом**:
  - Ключевые слова: "аналитик", "тренд", "прогноз", "рекомендац", "корреляц"
  - Команда "покажи аналитику" в правой инфопанели
  - Автооткрытие AnalyticsPanel через `visual.widgets`
- **Документация модуля**: `backend/docs/ANALYTICS.md` (исчерпывающее описание формул, API, примеров)

### Fixed
- `state_snapshot_uncloneable` warning — убраны все callbacks из Chart.js options
- Математика тренда — правильная формула на основе дней (не количества точек)
- Корректное масштабирование оси Y через `suggestedMin`/`suggestedMax`
- Цветовые конфликты — MA-7 теперь нейтральный серый (#9ca3af)
- Адаптивный downsampling raw_data (до 500 точек)
- `raw_data` теперь берёт последние точки (не первые)

### Technical
- Установлены: `chart.js`, `svelte-chartjs`, `chartjs-plugin-zoom`
- Backend возвращает `raw_data` для графиков с адаптивным downsampling
- Frontend: `ChartJS.getChart(canvas)` для доступа к Chart instance
- Модуль `analytics` добавлен в `/system/info` capabilities
- `ALLOWED_FILES` в docs.py автоматически включает все .md файлы из `backend/docs/`

'''
    
    # Вставляем перед 3.1.0
    if '## [3.1.0]' in content:
        content = content.replace('## [3.1.0]', new_entry + '## [3.1.0]')
    else:
        # Вставляем после заголовка
        content = content.replace('# Changelog\n\n', f'# Changelog\n\n{new_entry}')
    
    # Обновляем Roadmap
    content = content.replace(
        '### v3.2.0 (Планируется)\n- [ ] Модуль `historical_data`',
        '### v3.2.0 (Реализовано 2026-06-17) ✅\n- [x] Модуль `analytics`'
    )
    content = re.sub(
        r'- \[ \] Модуль `historical_data`.*?\n',
        '- [x] Тренд-анализ и корреляции\n- [x] Интерактивная визуализация (Chart.js + zoom/pan)\n- [x] Прогнозы на 7/30/90/365 дней\n',
        content
    )
    content = content.replace(
        '- [ ] Модуль `predictive_analytics` — прогнозы экономии\n',
        '- [x] Раскрывающиеся карточки проблем и рекомендаций\n'
    )
    
    changelog_path.write_text(content, encoding='utf-8', newline='\n')
    print('✓ CHANGELOG.md: добавлена полная запись 3.2.0')

print()
print('=' * 70)
print('🎉 ВЕРСИЯ 3.2.0 — ANALYTICS ENGINE COMPLETE')
print('=' * 70)
print()
print('Что реализовано в Фазе 2, Шаг 4:')
print('  ✓ Модуль analytics (collectors + analyzers + LLM)')
print('  ✓ Endpoint GET /analytics/report')
print('  ✓ Chart.js визуализация с 4 линиями')
print('  ✓ Zoom/pan/download для графиков')
print('  ✓ Раскрывающиеся карточки')
print('  ✓ Русификация UI')
print('  ✓ Исчерпывающая документация')
print()
print('Выполни коммит и push:')
print()
print('```bash')
print('cd /c/dev/SCADA.AI/scada-ai-v3')
print('git add -A')
print('git commit -m "chore(release): bump to v3.2.0 — Analytics Engine complete"')
print('git push origin main')
print('```')
print()
print('После push скажи "3.2.0 в remote" — подведу итоги всей Фазы 2! 🚀')