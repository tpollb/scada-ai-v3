# Архитектура SCADA.AI

## Общая схема

```text
┌──────────────────────────────────────────────────────────────┐
│                        Frontend (Svelte 5)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐     │
│  │ Home.svelte  │  │ Config.svelte│  │ SystemLogsPanel  │     │
│  └──────────────┘  └──────────────┘  └──────────────────┘     │
│           │                  │                     │           │
│  ┌────────────────────────────────────────────────────────┐   │
│  │              Deep Analysis Components                  │   │
│  │  DeepAnalysisControls  │  ABComparisonModal  │         │   │
│  │  DeepAnalysisResults   │  ChartModal        │         │   │
│  │  DDAInterpretation                              │         │   │
│  └────────────────────────────────────────────────────────┘   │
│           │                                                    │
│           └──────────────────┴────────────────────┘            │
│                              │                                 │
│                     POST /chat                                  │
│                    GET /health/*                                │
│                    GET /system/info                             │
│              POST /api/v1/deep_analysis/analyze                 │
│              POST /api/v1/deep_analysis/ab                      │
│              GET  /api/v1/deep_analysis/tags                    │
└──── ──────────────────────────┼─────────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                         │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    API Routers                           │  │
│  │  /chat  /health  /system  /config  /logs                 │  │
│  │  /api/v1/deep_analysis  /analytics  /energy  /docs       │  │
│  └──────────────────────────────────────────────────────────┘  │
│           │                                                    │
│           ▼                                                    │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              Module Registry (auto-discovery)          │    │
│  │  modules/health      modules/hello    modules/logs     │    │
│  │  modules/analytics   modules/energy_* modules/deep_*   │    │
│  └────────────────────────────────────────────────────────┘    │
│           │                                                    │
│           ▼                                                    │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              Tool Executor (dispatch)                  │    │
│  │  analyze_logs()  get_health_report()                   │    │
│  │  calculate_electricity_cost()                          │    │
│  └────────────────────────────────────────────────────────┘    │
│           │                                                    │
│           ▼                                                    │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              LLM Provider (YandexGPT 5.1)              │    │
│  │  generate()  generate_with_tools()                     │    │
│  └────────────────────────────────────────────────────────┘    │
└──────────────────────────────┼─────────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────────┐
│                   PostgreSQL (SCADA DB)                        │
│  tags_value  alarm_events_history  tags_dict  zones_dict       │
│  anomaly_events (deep_analysis)                                │
└────────────────────────────────────────────────────────────────┘
```

## Backend структура

```text
backend/
├── main.py                      # FastAPI app + middleware
├── api/
│   └── routes/
│       ├── chat.py              # POST /chat (главный endpoint)
│       ├── health.py            # GET /health/* (metrics, alarms, environmental)
│       ├── system.py            # GET /system/info
│       ├── config.py            # CRUD модулей и промптов
│       ├── docs.py              # GET /docs/* (whitelist MD файлов)
│       ├── analytics.py         # GET /analytics/report
│       ├── energy.py            # GET /energy/*
│       ├── logs.py              # GET /logs/*
│       └── deep_analysis.py     # POST /api/v1/deep_analysis/*
├── core/
│   ├── module_registry.py       # Автообнаружение модулей
│   ├── tool_executor.py         # Dispatch tool calls
│   ├── db.py                    # asyncpg pool
│   ├── logger.py                # Файловое логирование
│   └── llm/
│       ├── base.py              # Abstract LLM provider
│       ├── yandex.py            # YandexGPT implementation
│       └── factory.py           # get_provider()
├── modules/
│   ├── energy_electricity/
│   │   ├── __init__.py
│   │   ├── config.yaml
│   │   ├── tools.py             # calculate_electricity_cost, get_consumption
│   │   └── prompts.py
│   ├── energy_water/
│   │   └── ...                  # аналогично electricity
│   ├── energy_heat/
│   │   └── ...                  # аналогично electricity
│   ├── health/
│   │   ├── __init__.py
│   │   ├── config.yaml
│   │   ├── prompts.py           # HEALTH_SYSTEM_PROMPT
│   │   ├── data_collectors.py   # SQL queries
│   │   ├── analysis.py          # Детерминированные формулы
│   │   ├── renderers.py         # narrative/voice/visual
│   │   ├── localization.py      # Перевод статусов на русский
│   │   └── tools.py             # TOOLS = []
│   ├── analytics/
│   │   ├── __init__.py
│   │   ├── collectors/history.py   # Сбор из TimescaleDB
│   │   ├── analyzers/
│   │   │   ├── trends.py           # Линейная регрессия, R², slope
│   │   │   ├── correlations.py     # Pearson + временной лаг
│   │   │   └── aggregators.py      # Ранжирование проблем
│   │   ├── llm/analyzer.py         # YandexGPT + fallback
│   │   └── norms.py                # Нормативные диапазоны
│   ├── deep_analysis/
│   │   ├── __init__.py
│   │   ├── api.py                  # FastAPI endpoints
│   │   ├── core.py                 # Оркестрация анализа
│   │   └── analyzers/
│   │       ├── anomaly_detection.py  # Isolation Forest, Z-score, IQR
│   │       ├── correlation.py        # Pearson correlation matrix
│   │       ├── seasonal.py           # FFT, seasonal pattern extraction
│   │       ├── stats.py              # compute_basic_stats, downsampling
│   │       └── ab.py                 # A/B анализ (Welch's t-test, Cohen's d)
│   ├── hello/
│   │   └── ...
│   └── logs/
│       ├── tools.py             # analyze_logs()
│       └── prompts.py
├── data/
│   ├── tariffs.json             # Интервальные тарифы (electricity/water/heat)
│   └── energy_config.json       # Конфигурация счётчиков
└── config/
    └── settings.py              # Pydantic settings
```

## Frontend структура

```text
frontend/
├── src/
│   ├── App.svelte               # Главный компонент (роутинг)
│   ├── routes/
│   │   ├── Home.svelte          # Операторский интерфейс
│   │   └── Config.svelte        # Конфигуратор
│   ├── components/
│   │   ├── Input.svelte         # Поле ввода
│   │   ├── NarrativePanel.svelte # Текстовые ответы
│   │   ├── WidgetRouter.svelte  # Роутинг виджетов
│   │   ├── SystemLogsPanel.svelte
│   │   ├── ChartModal.svelte    # Полноэкранные графики с zoom
│   │   ├── ABComparisonModal.svelte  # A/B анализ модалка
│   │   ├── DeepAnalysisControls.svelte  # Выбор тегов/периодов DDA
│   │   ├── DeepAnalysisResults.svelte   # 4 вкладки результатов DDA
│   │   ├── DDAInterpretation.svelte     # LLM интерпретация DDA
│   │   ├── analytics/
│   │   │   ├── AnalyticsPanel.svelte
│   │   │   └── TrendChart.svelte
│   │   └── health/
│   │       ├── HealthScoreCard.svelte
│   │       ├── LifeSupportCard.svelte
│   │       ├── EnvironmentalPanel.svelte
│   │       ├── AlarmsPanel.svelte
│   │       ├── EnergyCostCard.svelte
│   │       └── IssuesList.svelte
│   ├── stores/
│   │   ├── chat.ts              # messages, isLoading
│   │   ├── theme.ts             # dark/light mode
│   │   └── ui.ts                # currentPage
│   └── lib/
│       └── api.ts               # ky HTTP client
├── index.html
├── package.json
└── vite.config.ts
```

## Flow данных

### Health-запрос

```text
1. User: "покажи здоровье здания"
   ↓
2. Frontend: POST /chat {message: "..."}
   ↓
3. chat.py: is_health_query() → True
   ↓
4. handle_health_query():
   a. data_collectors.collect_all_health_data()
      → SQL queries к tags_value, alarm_events_history
   b. LLM.generate(HEALTH_SYSTEM_PROMPT, data)
      → JSON response
   c. analysis.compute_health_report()
      → Детерминированный расчёт (fallback если LLM failed)
   d. renderers.render_all(report)
      → narrative + voice + visual
   ↓
5. Response: {response, voice, visual: {widgets: [...]}}
   ↓
6. Frontend:
   a. NarrativePanel показывает response
   b. WidgetRouter рендерит виджеты
   c. speechSynthesis.speak(voice.text)
```

### Logs-запрос (tool calling)

```text
1. User: "проанализируй логи"
   ↓
2. Frontend: POST /chat
   ↓
3. chat.py:
   a. LLM.generate_with_tools(system, user, tools_schemas)
   ↓
4. LLM: "Я вызову analyze_logs"
   ↓
5. tool_executor.execute("analyze_logs", {limit: 100})
   ↓
6. logs/tools.py: analyze_logs()
   → Читает логи из core.logger
   → Возвращает {"logs": [...]}
   ↓
7. LLM: получает результат, генерирует анализ
   ↓
8. Response: {response: "В логах обнаружено 3 ошибки..."}
   ↓
9. Frontend: NarrativePanel показывает анализ
```

### Deep Data Analysis (DDA)

```text
1. Пользователь в DeepAnalysisControls:
   a. Выбирает теги (1 или несколько)
   b. Указывает период (7/30/90/365 дней)
   c. Настраивает параметры (downsampling, anomaly detection)
   d. Нажимает "Запустить анализ"
   ↓
2. Frontend: POST /api/v1/deep_analysis/analyze
   {
     "tags": ["R001-Temperature", "R002-Pressure"],
     "period": "30 days",
     "params": {
       "anomaly_detection": true,
       "seasonal_analysis": true,
       "correlation_matrix": true
     }
   }
   ↓
3. deep_analysis/api.py → core.py:
   a. Загрузка данных из PostgreSQL (asyncpg)
   b. Downsampling до 500 точек для визуализации
   c. Параллельный запуск анализаторов:
      - anomaly_detection.detect_anomalies()
        → Isolation Forest + Z-score + IQR
        → Типизация: spike/dip/drift/noise
      - seasonal.detect_dominant_periods()
        → FFT (Fast Fourier Transform)
        → get_seasonal_pattern() → усреднённый профиль
      - correlation.compute_correlation_matrix()
        → Pearson для всех пар тегов
   d. Сохранение результатов в БД (anomaly_events)
   ↓
4. Response:
   {
     "analysis_id": "20260701_142756_cc6dd1f4",
     "status": "completed",
     "statistics": {...},
     "anomalies": [...],
     "seasonality": {...},
     "correlations": {...},
     "visualizations": {
       "time_series": {...},
       "scatter_plots": [...],
       "heatmap": {...}
     }
   }
   ↓
5. Frontend: DeepAnalysisResults показывает в 4 вкладках:
   a. Обзор: статистика, аномалии на графике, типичный паттерн
   b. Корреляции: тепловая карта (multi-tag)
   c. Таблица пар: scatter plots с линиями регрессии
   d. Интерпретация: DDAInterpretation → LLM анализ результатов
   ↓
6. Опционально: пользователь нажимает "Использовать в анализе"
   → Результат передаётся в chat для LLM интерпретации
```

### A/B Анализ

```text
1. Пользователь в DeepAnalysisControls:
   a. Нажимает "Сравнить периоды (A/B)"
   b. Открывается ABComparisonModal
   ↓
2. ABComparisonModal:
   a. Выбирает режим:
      - Before/After: один тег, разные периоды
      - Equipment Comparison: два тега, один период
   b. Указывает snapshot_a и snapshot_b
   c. Нажимает "Сравнить"
   ↓
3. Frontend: POST /api/v1/deep_analysis/ab
   {
     "snapshot_a": {
       "tag": "R001-Temperature",
       "start": "2026-01-01",
       "end": "2026-03-31"
     },
     "snapshot_b": {
       "tag": "R001-Temperature",
       "start": "2026-04-01",
       "end": "2026-06-30"
     }
   }
   ↓
4. deep_analysis/analyzers/ab.py:
   a. Загрузка данных для обоих snapshots
   b. Валидация размера выборки (MIN_SAMPLE_SIZE = 10)
   c. Фильтрация NaN/Inf через is_valid()
   d. compute_basic_stats() для каждого snapshot:
      - mean, median, std, variance, min, max, range
   e. compare_snapshots():
      - Дельта статистик в процентах через _safe_pct_change()
      - Welch's t-test: stats.ttest_ind(equal_var=False)
      - Cohen's d: (μ_B - μ_A) / σ_pooled
      - Интерпретация значимости
   f. compare_patterns():
      - FFT автодетект доминирующих периодов
      - Извлечение усреднённых суточных паттернов
      - np.corrcoef(pattern_a, pattern_b) → корреляция
      - Сравнение амплитуд
   g. generate_verdict():
      - Автоматическая оценка severity (low/medium/high)
      - Key findings из статистики
      - Recommendations на основе результатов
   h. Санитизация: _safe_float() убирает NaN/Inf
   ↓
5. Response:
   {
     "mode": "before_after",
     "comparison": {
       "statistics": {"a": {...}, "b": {...}, "delta": {...}},
       "significance": {
         "t_stat": 12.34,
         "p_value": 0.000000001,
         "cohens_d": 0.89,
         "interpretation": "highly_significant"
       }
     },
     "pattern_comparison": {
       "a": {"period": 288, "pattern": [...], "amplitude": 8.5},
       "b": {"period": 288, "pattern": [...], "amplitude": 10.2},
       "comparison": {
         "period_match": true,
         "delta_amplitude_pct": 20.0,
         "pattern_correlation": 0.87
       }
     },
     "verdict": {
       "summary": "Обнаружены критические различия",
       "key_findings": [...],
       "recommendations": [...],
       "severity": "high"
     }
   }
   ↓
6. Frontend: ABComparisonModal показывает результаты:
   - Вердикт с цветовой индикацией severity
   - Статистика с процентными изменениями (каппирование >999%)
   - Значимость (p-value, Cohen's d)
   - Сравнение паттернов (корреляция, амплитуда)
   ↓
7. Пользователь нажимает "Использовать в анализе":
   a. handleABResult() добавляет результат в ddaAnalysisResult.ab_comparison
   b. Закрывается модалка (не вся панель DDA)
   c. Автопереключение на вкладку "Интерпретация" через forceTab
   d. DDAInterpretation использует ab_comparison для LLM анализа
```

## Module Registry

### Автообнаружение

```python
# core/module_registry.py
def discover_modules() -> list[str]:
    for path in modules_dir.iterdir():
        if path.is_dir() and (path / "__init__.py").exists():
            modules.append(path.name)
```

### Загрузка модуля

```python
def load_module(name: str):
    # 1. Читаем config.yaml
    config = yaml.safe_load(path / "config.yaml")
    
    # 2. Импортируем prompts
    prompts_module = import_module(f"modules.{name}.prompts")
    
    # 3. Импортируем tools
    tools_module = import_module(f"modules.{name}.tools")
    tools = tools_module.TOOLS
    
    # 4. Регистрируем tools в executor
    for tool in tools:
        executor.register_tool(tool["name"], tool["func"], tool["schema"])
```

### Список модулей

| Модуль | Тип | Описание |
|--------|-----|----------|
| **health** | Детерминированный + LLM | Анализ здоровья системы (alarms, environmental, equipment) |
| **deep_analysis** | Детерминированный | DDA: аномалии, сезонность, корреляции, A/B |
| **analytics** | Детерминированный + LLM | Тренды, прогнозы, impact scoring |
| **energy_electricity** | Детерминированный | Расчёт стоимости электроэнергии |
| **energy_water** | Детерминированный | Учёт потребления воды (инфраструктура) |
| **energy_heat** | Детерминированный | Учёт потребления тепла (инфраструктура) |
| **logs** | LLM (tool calling) | Анализ системных логов |
| **hello** | Текстовый | Базовые ответы на приветствия |

## Детерминированный vs LLM

### Health модуль

**Детерминированный слой** (`analysis.py`):

```python
def compute_health_report(data: dict) -> HealthReport:
    # Формулы без LLM
    alarm_idx = _compute_alarm_index(by_priority)
    env_idx = _compute_environmental_index(env)
    equip_idx = _compute_equipment_index(equip)
    # ...
    score = 0.40 * alarm_idx + 0.35 * env_idx + 0.25 * equip_idx
    return HealthReport(score=score, ...)
```

**LLM слой** (`prompts.py`):

```python
HEALTH_SYSTEM_PROMPT = """
Ты — инженер-аналитик SCADA-системы.
Верни JSON в формате: {score, status, summary, ...}
"""
```

**Когда что используется**:
- Виджеты → детерминированный (быстро, бесплатно)
- Narrative в чате → LLM (медленно, но с анализом)

### Deep Analysis модуль

**Полностью детерминированный**:
- Аномалии: Isolation Forest + статистические пороги
- Сезонность: FFT + математическая декомпозиция
- A/B: Welch's t-test + Cohen's d (scipy.stats)
- Корреляции: numpy.corrcoef (Pearson)

**LLM используется только для интерпретации**:
- DDAInterpretation отправляет структурированные результаты в YandexGPT
- LLM генерирует человекочитаемый отчёт на русском языке

### Logs модуль

**Только LLM**:

```python
# logs/tools.py
async def analyze_logs(limit: int = 100) -> dict:
    logs = system_logger.get_logs(limit=limit)
    return {"logs": logs}
```

LLM получает логи через tool и сама анализирует.

## Модули энергоучёта

### Архитектура

```text
User: "сколько денег потратили на электричество?"
↓
chat.py → LLM.generate_with_tools()
↓
LLM: "Вызову calculate_electricity_cost"
↓
tool_executor → energy_electricity/tools.py
↓
Читаем energy_config.json (теги счётчиков)
SQL-запросы к ЛЭРС (current/last month)
Читаем tariffs.json
Выбираем действующий тариф по дате
Считаем стоимость: потребление × тариф
↓
Response: { current_month: {cost: 26350}, last_month: {cost: 114005} }
```

### Интервальные тарифы

```json
{
  "electricity": [
    {
      "id": "t1",
      "start_date": "2025-01-01",
      "end_date": "2026-02-01",
      "price_per_unit": 5.50,
      "currency": "RUB"
    },
    {
      "id": "t2",
      "start_date": "2026-02-01",
      "end_date": null,
      "price_per_unit": 6.20,
      "currency": "RUB"
    }
  ]
}
```

**Логика выбора тарифа**:

```python
def get_active_tariff(resource: str, date: datetime) -> float:
    for tariff in tariffs[resource]:
        if tariff.start_date <= date and (tariff.end_date is None or date < tariff.end_date):
            return tariff.price_per_unit
    return DEFAULT_TARIFF
```

## Конфигурация

### .env файл

```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=scada
DB_USER=postgres
DB_PASSWORD=secret

# SCADA
SCADA_BASE_URL=http://localhost:9002

# YandexGPT
YANDEX_API_KEY=y0_...
YANDEX_FOLDER_ID=b1g...
YANDEX_GPT_MODEL=yandexgpt-5.1/latest

# LLM settings
LLM_TEMPERATURE=0.05
LLM_MAX_TOKENS=32000
LLM_TIMEOUT=30

# Location
CITY=Москва
TIMEZONE=Europe/Moscow
LATITUDE=55.7558
LONGITUDE=37.6173

# Modules
ENABLED_MODULES=hello,health,logs,energy_electricity,energy_water,energy_heat,analytics,deep_analysis

# Logging
LOG_POLL_INTERVAL_MS=2000
```

## Безопасность

### Текущее состояние
- Нет авторизации — все endpoints публичные
- Нет CORS — только localhost
- API ключи в `.env` (не коммитятся)

### Рекомендации для продакшена
- Добавить JWT авторизацию
- Настроить CORS (разрешить только frontend домен)
- Использовать HTTPS
- Rate limiting на `/chat`
- Валидация входных данных (Pydantic models)

### Защита от edge cases в Deep Analysis

**A/B анализ**:
- Минимальный размер выборки: 10 точек
- Фильтрация NaN/Inf через `is_valid()`
- Обработка константных данных (σ² = 0)
- Санитизация JSON ответа (NaN → null через `_safe_float()`)
- Защита от деления на ноль в Cohen's d
- try/except вокруг `stats.ttest_ind` и `np.corrcoef`

**Сезонный анализ**:
- Fallback на 288 точек если FFT не нашёл период
- Защита от NaN в `np.corrcoef` для константных паттернов

**Детекция аномалий**:
- Isolation Forest с `contamination=0.05`
- Z-score с `threshold=3σ`
- IQR с `Q1-1.5×IQR, Q3+1.5×IQR`

## Масштабирование

### Текущие ограничения
- Single instance — один backend процесс
- In-memory module registry — не распределённый
- PostgreSQL — single master

### Для продакшена
- Docker Compose — backend + frontend + postgres
- Redis — кэширование health-отчётов и DDA результатов
- Celery — фоновые задачи (scheduled analysis)
- Prometheus — метрики
- Grafana — дашборды

### Производительность

**Типичное время выполнения**:

| Операция | Время |
|----------|-------|
| Health report | 50-100ms |
| DDA анализ (30 дней, 1 тег) | 200-500ms |
| A/B анализ (3 месяца) | 100-300ms |
| FFT автодетект периода | 10-50ms (O(n log n)) |
| Welch's t-test | 5-20ms (O(n)) |
| LLM интерпретация | 5-10s |

**Оптимизации**:
- Downsampling до 500 точек для графиков
- Параллельный запуск анализаторов
- Кэширование результатов в Redis (planned)

## Отладка

### Логи

**Backend логи**:
```bash
tail -f backend/logs/2026-01-15.log
```

**Frontend консоль**:
F12 → Console

### Debug endpoints

**Список всех endpoints**:
```bash
curl http://localhost:8081/api/v1/health/debug
```

**Проверка БД**:
```bash
curl http://localhost:8081/api/v1/system/info | jq .db_status
```

**Проверка DDA**:
```bash
curl -X POST http://localhost:8081/api/v1/deep_analysis/tags
```

### Common issues

**"LLM не настроен"**:
- Проверь `YANDEX_API_KEY` в `.env`
- Убедись что ключ активен

**"Модуль не загружен"**:
- Проверь `ENABLED_MODULES` в `.env`
- Перезапусти backend

**"DB connection failed"**:
- Проверь `DB_HOST`, `DB_PORT`, `DB_PASSWORD`
- Убедись что PostgreSQL запущен

**"A/B KeyError: 'mean'"**:
- Проверь что данные не пустые
- Убедись что `MIN_SAMPLE_SIZE = 10` соблюдён
- Проверь логи на `SmallSampleWarning`

**"NaN в JSON response"**:
- Проверь что `_safe_float()` применяется ко всем float значениям
- Убедись что `sanitize_dict()` вызывается перед возвратом

**"Кнопки зума не работают"**:
- Проверь что `$effect` заполняет `chartInstance` после рендеринга
- Убедись что `ChartJS.getChart(canvas)` вызывается с задержкой 200ms

## Документация

Полная документация системы:

| Файл | Описание |
|------|----------|
| **README.md** | Обзор системы и быстрый старт |
| **MODULES.md** | Подробное описание всех модулей |
| **DDA.md** | Deep Data Analysis — глубокое исследование данных |
| **SEASON_ANALYSIS.md** | Сезонный анализ и FFT автодетект периодов |
| **AB_ANALYSIS.md** | A/B анализ с полной математикой |
| **ANALYTICS.md** | Тренд-анализ, прогнозы и корреляции |
| **API.md** | HTTP endpoints с примерами запросов |
| **ARCHITECTURE.md** | Этот файл — архитектура системы |
| **CHAT_EXAMPLES.md** | Примеры запросов к AI-ассистенту |
| **CHANGELOG.md** | История изменений по версиям |

Доступ через UI (Конфигуратор → Документация) и REST API:
```bash
GET /docs/list              # Список файлов
GET /docs/{filename}        # Содержимое MD-файла
```

---

**Версия**: 3.2.9  
**Дата обновления**: 2026-07-01  
**Автор**: Усков Сергей Евгеньевич