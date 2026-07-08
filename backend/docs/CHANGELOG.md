# Changelog

## v3.2.9 (2026-07-01)
## v3.2.9.1 (2026-07-08)

### Fixes
- **DDA**: Исправлен UnicodeEncodeError при логировании результатов анализа с символами ↔ и другими Unicode
- **DDA**: Исправлены кнопки зума (+/-/reset/download) на графике "Типичный паттерн" для multi-tag анализа
  - Заменён единый `patternChartInstance` на `patternChartInstances: Record<string, ChartJS>`
  - Уникальный ID для каждого графика в цикле
  - Функции zoom принимают `tagKey` параметр

### Known Issues
- Health модуль: если SCADA не пишет данные последние 24 часа, отображаются нули (данные есть, но старые)

**Added**

**A/B Анализ** — полноценный статистический модуль сравнения периодов/оборудования

Backend: `POST /api/v1/deep_analysis/ab` endpoint
Backend: модуль `modules/deep_analysis/analyzers/ab.py` с функциями:
`compare_snapshots()` — базовая статистика + Welch's t-test + Cohen's d
`compare_patterns()` — FFT-автодетект периодов + корреляция суточных паттернов
`generate_verdict()` — автоматический вердикт с severity (low/medium/high)
Два режима анализа:
**Before/After**: один тег, разные периоды (оценка эффекта изменений)
**Equipment Comparison**: два тега, один период (сравнение оборудования)
Метрики: mean/median/std/variance/min/max/range delta в %
Статистическая значимость: p-value, t-stat, Cohen's d, интерпретация
Сравнение паттернов: корреляция, совпадение периодов, изменение амплитуды
Автогенерация findings и recommendations на основе результатов
Frontend: `ABComparisonModal.svelte` — модалка с выбором режима/тегов/периодов
Frontend: кнопка "Сравнить периоды (A/B)" в `DeepAnalysisControls`
Frontend: визуализация результатов (verdict, статистика, значимость, паттерны)
Frontend: кнопка "Использовать в анализе" — передача результата в LLM интерпретацию
Frontend: автопереключение на вкладку "Интерпретация" через `forceTab` пропс
Backend: защита от NaN/Inf/None через `_safe_float()` helper
Backend: `_safe_pct_change()` — безопасный расчёт % изменений
Backend: санитизация JSON ответа (рекурсивная замена NaN → null)
Backend: валидация размера выборки (MIN_SAMPLE_SIZE = 10)
Backend: фильтрация невалидных данных перед статистикой
Backend: корректная обработка дат `YYYY-MM-DD` (расширение до 00:00:00 / 23:59:59)
Документация: полная MD-документация по A/B анализу с математикой, API, примерами

**Fixed**

Frontend: **унификация высоты хидеров** SystemLogsPanel / DeepAnalysisControls / DeepAnalysisResults
Убран встроенный margin у `<h2>` через `my-0`
Добавлен `leading-6` (line-height: 24px) для консистентности между тегами
Унифицирован размер шрифта: `text-base` (16px) во всех трёх хидерах
Унифицирован padding: `px-4 py-3` (24px) для всех трёх контейнеров
Восстановлен `border-b border-neutral-200 dark:border-neutral-700` у DeepAnalysisControls
Упрощена структура вкладок: убран лишний `<div>` внутри `<button>`, flex перенесён на кнопку
Убрано подчёркивание у активной вкладки — только цветовое выделение
Сброшены дефолтные стили браузера для `<button>` (border/padding/background)
Кнопки с иконками 16px: `p-1.5` → `p-1` (высота 24px = высоте h2)
Добавлены accessibility атрибуты: `role="button"`, `tabindex="0"`, `onkeydown`
Backend: `KeyError: 'mean'` в `compare_snapshots` при малых выборках
Backend: `ValueError: Out of range float values are not JSON compliant: nan`
Backend: `SmallSampleWarning` от scipy.stats.ttest_ind — добавлена проверка размера
Backend: деление на ноль при `variance = 0` (константные данные) — защита в Cohen's d
Backend: `np.corrcoef` возвращал NaN для константных паттернов — try/except + валидация
Backend: некорректная парсинг дат формата `YYYY-MM-DD` без времени
Backend: 500 ошибка при пустых данных — возврат 400 с понятным сообщением
Frontend: **кнопки zoom (+/-/reset) не работали** на маленьком графике "Типичный паттерн"
Добавлен `$effect` для заполнения `patternChartInstance` после рендеринга
Аналогично time series графику: `ChartJS.getChart(canvas)` с задержкой 200ms
Frontend: `NaN%` в отображении pattern_correlation — корректный путь `comparison.pattern_correlation`
Frontend: миллионы процентов в статистике — `formatDelta()` с каппированием `>+999%` / `<-999%`
Frontend: кнопка "Использовать в анализе" закрывала всю DDA-панель — теперь только модалку
Frontend: раскрывающийся блок "Показать абсолютные значения" для статистики A и B

**Changed**

Frontend: вкладки в DeepAnalysisResults — современный стиль "пилюли" → минималистичный (только цвет)
Frontend: `forceTab` пропс в `DeepAnalysisResults` для программного переключения вкладок
Frontend: `handleABResult` в Home.svelte добавляет `ab_comparison` в `ddaAnalysisResult`
Backend: endpoint `/ab` теперь возвращает структурированный 400 вместо 500 при валидационных ошибках

**Technical**

Helper функции `_safe_float()` и `_safe_pct_change()` в `ab.py` — защита от краевых случаев
Константа `MIN_SAMPLE_SIZE = 10` — минимальный размер выборки для статистики
`is_valid(x)` — фильтрация NaN/Inf/None из данных перед анализом
`sanitize_dict()` — рекурсивная санитизация всех float значений в статистике
try/except вокруг `compute_basic_stats`, `stats.ttest_ind`, `np.corrcoef`
Проверка `variance > 0` перед запуском t-test (константные данные)
Полная типизация: все функции возвращают предсказуемую структуру даже при ошибках

### v3.2.8 (2026-06-30)
- [x] Multi-tag seasonal визуализация
- [x] Chart.js с zoom/pan/tooltips для паттернов
- [x] Интеллектуальный formatPeriod()
- [x] Унифицированный стиль графиков
- [x] Filler plugin для Chart.js
- [x] Исправления всех UI багов

### v3.2.7 (2026-06-29)
- [x] Первая версия с seasonal анализом
- [x] Базовая визуализация в single-tag

### v3.2.5 (2026-06-26)
- [x] Исправлена проблема с отображением точек аномалий в multi-tag анализе
- [x] Добавлены реальные timestamps вместо индексов
- [x] Исправлены кнопки zoom/download в ChartModal

### v3.2.4 (2026-06-25)
- [x] Добавлен конфигуратор настроек DDA
- [x] 4 вкладки: Детекция, Окно анализа, Downsampling, Корреляции

### v3.2.3 (2026-06-24)
- [x] Добавлена визуализация аномалий на графиках
- [x] Цветовая кодировка по типам (spike/dip/drift/noise)

### v3.2.2 (2026-06-23)
- [x] Добавлен multi-tag корреляционный анализ
- [x] Тепловая карта корреляций
- [x] Scatter plot с линией регрессии

### v3.2.1 (2026-06-22)
- [x] Базовая детекция аномалий (Isolation Forest)
- [x] Визуализация временных рядов

## [3.2.0] - 2026-06-17

### Added
- **Модуль analytics** — полноценный движок аналитики SCADA-системы
- **Collectors**: сбор исторических данных (hourly/daily/raw) с адаптивным downsampling
- **Analyzers**: тренды (линейная регрессия), корреляции (Pearson), ранжирование проблем
- **LLM layer**: YandexGPT инсайты + детерминированный fallback
- **Endpoint GET /analytics/report** с параметрами period/params/aggregation
- **Визуализация аналитики** (Chart.js + svelte-chartjs):
- **Интерактивные графики** с 4 линиями (данные, тренд, MA-7, прогноз)
- **Фиксированные пределы оси Y** по физическим границам параметров
- **Zoom/pan** через chartjs-plugin-zoom (колёсико мыши, drag, pinch)
- **Экспорт графиков** в PNG через chart.toBase64Image()
- **Кнопки управления**: Zoom In/Out/Reset/Download

UI аналитики:
- **AnalyticsPanel** виджет с 4 вкладками (Тренды, Проблемы, Рекомендации, Прогноз)
- **Периоды прогноза**: 7/30/90/365 дней
- **Раскрывающиеся карточки проблем** (компоненты impact, нормы параметра)
- **Раскрывающиеся карточки рекомендаций** (детали расчёта)
- **Русификация** всех текстов (severity, effort, reason)

Интеграция с чатом:
- **Ключевые слова**: "аналитик", "тренд", "прогноз", "рекомендац", "корреляц"
- **Команда "покажи аналитику"** в правой инфопанели
- **Автооткрытие AnalyticsPanel** через visual.widgets

### Fixed
- **state_snapshot_uncloneable warning** — убраны callbacks из Chart.js options
- **Математика тренда** — правильная формула на основе дней (не количества точек)
- **Корректное масштабирование оси Y** через suggestedMin/suggestedMax
- **Цветовые конфликты — MA-7** теперь нейтральный серый (#9ca3af)

### Technical

- **Установлены**: chart.js, svelte-chartjs, chartjs-plugin-zoom
- **Backend возвращает raw_data** для графиков (до 500 точек с downsampling)
- **Frontend: ChartJS.getChart(canvas)** для доступа к Chart instance
- **Модуль analytics** добавлен в /system/info capabilities

## [3.1.0] - 2026-06-09

### Added
- **Модуль `energy_electricity`** — расчёт стоимости электроэнергии по тегам ЛЭРС
- **Модуль `energy_water`** — учёт потребления воды (подготовка инфраструктуры)
- **Модуль `energy_heat`** — учёт потребления тепла (подготовка инфраструктуры)
- **Виджет `energy_cost_card`** — суммарная стоимость ресурсов (текущий и прошлый месяц)
- **Конфигуратор: вкладка "Энергоучёт"** — CRUD тарифов и тегов счётчиков
- **Интервальные тарифы** (`data/tariffs.json`) с валидацией дат
- **Конфиг счётчиков** (`data/energy_config.json`)
- **Детализация расчёта** под статусами HealthScoreCard и LifeSupportCard (серым моноширинным текстом)
- **Кнопки (i) с формулами** расчёта во всех health-виджетах
- **Сворачиваемые блоки** в health report (Параметры жизнедеятельности, Аварии, Проблемы)
- **Монохромные иконки** в сайдбаре (Package/Wrench/Zap/Droplet/Flame)

### Changed
- **Формула health_score**: 40% Аварии + 35% Среда + 25% Оборудование (было 35+30+25+10 с Энергией)
- Удалён `energy_panel` виджет (заменён на `energy_cost_card`)
- Удалён `stats_cards` виджет (избыточный)
- **Сайдбар**: раскрывающиеся списки "Модули" и "Инструменты" с шевронами (по умолчанию раскрыты)
- **Виджет энергозатрат**: прошлый месяц как основной (полные данные), текущий — как дополнение

### Fixed
- Async-цепочка в `render_all` (добавлен `await` перед `render_visual`)
- Пустой `sub_scores` от LLM — теперь вычисляется детерминированно из реальных данных
- Корректное отображение "Прошлый месяц" в виджете энергозатрат (114 005 ₽)
- "Виджет не найден" — добавлен `energy_cost_card` в WidgetRouter
- Layout виджетов: 3 в ряд (было 2×2 с пустым углом)

## [3.0.2] - 2026-06-08

### Added
- **Backend:** Встроенная документация системы (docs/)
  - README.md, MODULES.md, API.md, CHAT_EXAMPLES.md, ARCHITECTURE.md, CHANGELOG.md
  - REST API для доступа к документации (GET /docs/list, GET /docs/{filename})
- **Frontend:** DocsViewer компонент в конфигураторе
  - Sidebar со списком файлов + markdown рендеринг через marked
  - Вкладка "Документация" в Config.svelte

### Changed
- Версия приложения: 3.0.1 → 3.0.2

Все значимые изменения в проекте документируются в этом файле.
Формат основан на [Keep a Changelog](https://keepachangelog.com/).

## [3.0.1.2] - 2026-06-08

### Added
- **Backend:** `tools_names` в ответе `/system/info` — список зарегистрированных инструментов
- **Frontend:** Правая панель "Инструменты" с чипсами имён (как у модулей)

### Changed
- **Frontend:** "Tools" → "Инструменты" (локализация)

### Fixed
- **Frontend:** HealthScoreCard — таблица штрафов переведена на русский
  - Авария High → Авария высокого приоритета
  - CRITICAL параметр → Критичный параметр
  - WARNING параметр → Параметр с отклонением

## [3.0.1.1] - 2026-06-08

### Added
- **Backend:** Модуль `localization.py` с маппингами STATUS_RU, SEVERITY_RU, PRIORITY_RU
- **Backend:** `status_ru` поле в виджетах health_score и life_support_card
- **Backend:** `by_priority_ru` в alarms_panel (Высокий/Средний/Низкий)
- **Frontend:** Локализация статусов во всех компонентах health
- **Frontend:** Кнопка (i) в LifeSupportCard теперь работает (исправлен порядок переменных)

### Changed
- **Backend:** Детерминированный пересчёт статуса здоровья (не от LLM)
  - LLM возвращает только score/summary/issues
  - Статус определяется формулой: <30=CRITICAL, <60=WARNING, <85=GOOD, >=85=EXCELLENT
- **Frontend:** EnvironmentalPanel — статусы OK→Норма, WARNING→Внимание, CRITICAL→Критично
- **Frontend:** AlarmsPanel — приоритеты HIGH→Высокий, MEDIUM→Средний, LOW→Низкий

### Fixed
- **Frontend:** LifeSupportCard — удалён блок "Проблемы" (ломал визуал)
- **Frontend:** LifeSupportCard — paramStatusColor теперь понимает русские статусы

## [3.0.1] - 2026-06-03

### Added
- **Backend:** Файловое логирование (один файл на сессию)
- **Backend:** Tool calling через YandexGPT 5.1 (формат `toolCallList`)
- **Backend:** UI настройки модулей (интервал polling логов)
- **Frontend:** SystemLogsPanel — просмотр логов в реальном времени
- **Frontend:** WidgetRouter — динамический боутинг виджетов

### Changed
- **Backend:** Переход на YandexGPT 5.1 (была 4.0)
- **Frontend:** Миграция на Svelte 5 + runes (была 4.x)

### Fixed
- **Backend:** Стабилизация индекса здоровья (few-shot examples в prompt)
- **Frontend:** Responsive layout для mobile устройств

## [3.0.0] - 2026-05-29

### Added
- Первая публичная версия SCADA.AI v3
- **Backend:** FastAPI + asyncpg + YandexGPT
- **Backend:** Модуль health (анализ здоровья системы)
- **Backend:** Модуль hello (базовые ответы)
- **Backend:** Модуль logs (анализ системных логов)
- **Frontend:** Svelte 4 + Tailwind CSS
- **Frontend:** Operator dashboard (Home.svelte)
- **Frontend:** Configurator (Config.svelte)
- **Frontend:** NarrativePanel (текстовые ответы)
- **Frontend:** HealthScoreCard, LifeSupportCard виджеты
- **Frontend:** EnvironmentalPanel, AlarmsPanel, EnergyPanel виджеты
- **Frontend:** Голосовое озвучивание (speechSynthesis)
- **Database:** PostgreSQL интеграция (tags_value, alarm_events_history)

## [2.x.x] - 2025-2026 (Legacy)
Внутренние версии для тестирования. Не публичные.

## [1.x.x] - 2025 (Prototype)
Первоначальный прототип на Python + Flask. Переписан в v3.0.0.

## Roadmap

### v3.1.0 (Реализовано 2026-06-09)
- [x] Модуль `energy_electricity` — расчёт стоимости электроэнергии
- [x] Модуль `energy_water` — инфраструктура для учёта воды
- [x] Модуль `energy_heat` — инфраструктура для учёта тепла
- [x] Интервальные тарифы (tariffs.json) с CRUD в конфигураторе
- [x] Конфигуратор тегов счётчиков (energy_config.json)
- [x] Виджет `energy_cost_card` — суммарная стоимость ресурсов

### v3.2.0 (Планируется)
- [ ] Модуль `historical_data` — тренды и сравнение периодов
- [ ] Модуль `predictive_analytics` — прогнозы экономии
- [ ] Boss dashboard — отдельный экран для руководства

### v4.0.0 (Долгосрочно)
- [ ] Ролевая модель (admin, engineer, operator, boss)
- [ ] Зашифрованное хранилище пользователей (users.enc)
- [ ] Multi-tenancy (несколько зданий в одной системе)
- [ ] Mobile app (React Native)
