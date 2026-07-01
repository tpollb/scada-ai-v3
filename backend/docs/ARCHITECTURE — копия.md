# Архитектура SCADA.AI

## Общая схема

```
┌──────────────────────────────────────────────────────────────┐
│                        Frontend (Svelte 5)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐    │
│  │ Home.svelte  │  │ Config.svelte│  │ SystemLogsPanel  │    │
│  └──────────────┘  └──────────────┘  └──────────────────┘    │
│           │                  │                    │          │
│           └──────────────────┴────────────────────┘          │
│                              │                               │
│                    POST /chat                                │
│                    GET /health/*                             │
│                    GET /system/info                          │
└──────────────────────────────┼───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                       │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │                    API Routers                       │    │
│  │  /chat  /health  /system  /config  /logs             │    │
│  └──────────────────────────────────────────────────────┘    │
│           │                                                  │
│           ▼                                                  │
│  ┌──────────────────────────────────────────────────────┐    │
│  │              Module Registry (auto-discovery)        │    │
│  │  modules/health  modules/hello  modules/logs         │    │
│  └──────────────────────────────────────────────────────┘    │
│           │                                                  │
│           ▼                                                  │
│  ┌──────────────────────────────────────────────────────┐    │
│  │              Tool Executor (dispatch)                │    │
│  │  analyze_logs()  get_health_report()                 │    │
│  └──────────────────────────────────────────────────────┘    │
│           │                                                  │
│           ▼                                                  │
│  ┌──────────────────────────────────────────────────────┐    │
│  │              LLM Provider (YandexGPT)                │    │
│  │  generate()  generate_with_tools()                   │    │
│  └──────────────────────────────────────────────────────┘    │
└──────────────────────────────┼───────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                   PostgreSQL (SCADA DB)                     │
│  tags_value  alarm_events_history  tags_dict  zones_dict    │
└─────────────────────────────────────────────────────────────┘
```

---

## Backend структура

```
backend/
├── main.py                      # FastAPI app + middleware
├── api/
│   └── routes/
│       ├── chat.py              # POST /chat (главный endpoint)
│       ├── health.py            # GET /health/* (metrics, alarms, environmental)
│       ├── system.py            # GET /system/info
│       ├── config.py            # CRUD модулей и промптов
│       └── logs.py              # GET /logs/*
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
│   │   ├── tools.py             # calculate_electricity_cost, get_electricity_consumption
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

---

## Frontend структура

```
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

---

## Flow данных

### Health-запрос

```
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

---

### Logs-запрос (tool calling)

```
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

---

## Module Registry

**Автообнаружение:**
```
# core/module_registry.py
def discover_modules() -> list[str]:
    for path in modules_dir.iterdir():
        if path.is_dir() and (path / "__init__.py").exists():
            modules.append(path.name)
```

**Загрузка модуля:**
```
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

---

## Детерминированный vs LLM

### Health модуль

**Детерминированный слой** (analysis.py):
```
def compute_health_report(data: dict) -> HealthReport:
    # Формулы без LLM
    alarm_idx = _compute_alarm_index(by_priority)
    env_idx = _compute_environmental_index(env)
    equip_idx = _compute_equipment_index(equip)
    # ...
    score = 0.40 * alarm_idx + 0.35 * env_idx + 0.25 * equip_idx
    return HealthReport(score=score, ...)
```

**LLM слой** (prompts.py):
```
HEALTH_SYSTEM_PROMPT = ```
Ты — инженер-аналитик SCADA-системы.
Верни JSON в формате: {score, status, summary, ...}
```
Когда что используется:
Виджеты → детерминированный (быстро, бесплатно)
Narrative в чате → LLM (медленно, но с анализом)
Logs модуль
Только LLM:
```
logs/tools.py
async def analyze_logs(limit: int = 100) -> dict:
logs = system_logger.get_logs(limit=limit)
return {"logs": logs}
```
LLM получает логи через tool и сама анализирует.
Модули энергоучёта
Архитектура
```
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
Интервальные тарифы
```
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
Логика выбора тарифа:
```
def get_active_tariff(resource: str, date: datetime) -> float:
for tariff in tariffs[resource]:
if tariff.start_date <= date and (tariff.end_date is None or date < tariff.end_date):
return tariff.price_per_unit
return DEFAULT_TARIFF
```
Конфигурация
.env файл
```
Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=scada
DB_USER=postgres
DB_PASSWORD=secret
SCADA
SCADA_BASE_URL=http://localhost:9002
YandexGPT
YANDEX_API_KEY=y0_...
YANDEX_FOLDER_ID=b1g...
YANDEX_GPT_MODEL=yandexgpt-5.1/latest
LLM settings
LLM_TEMPERATURE=0.05
LLM_MAX_TOKENS=32000
LLM_TIMEOUT=30
Location
CITY=Москва
TIMEZONE=Europe/Moscow
LATITUDE=55.7558
LONGITUDE=37.6173
Modules
ENABLED_MODULES=hello,health,logs,energy_electricity,energy_water,energy_heat
Logging
LOG_POLL_INTERVAL_MS=2000
```
Безопасность
Текущее состояние
Нет авторизации — все endpoints публичные
Нет CORS — только localhost
API ключи в .env (не коммитятся)
Рекомендации для продакшена
Добавить JWT авторизацию
Настроить CORS (разрешить только frontend домен)
Использовать HTTPS
Rate limiting на /chat
Валидация входных данных (Pydantic models)
Масштабирование
Текущие ограничения
Single instance — один backend процесс
In-memory module registry — не распределённый
PostgreSQL — single master
Для продакшена
Docker Compose — backend + frontend + postgres
Redis — кэширование health-отчётов
Celery — фоновые задачи (scheduled analysis)
Prometheus — метрики
Grafana — дашборды
Отладка
Логи
```
Backend логи
tail -f backend/logs/2026-01-15.log
Frontend консоль
F12 → Console
```
Debug endpoints
```
Список всех endpoints
curl http://localhost:8081/api/v1/health/debug
Проверка БД
curl http://localhost:8081/api/v1/system/info | jq .db_status
```
Common issues
"LLM не настроен":
Проверь YANDEX_API_KEY в .env
Убедись что ключ активен
"Модуль не загружен":
Проверь ENABLED_MODULES в .env
Перезапусти backend
"DB connection failed":
Проверь DB_HOST, DB_PORT, DB_PASSWORD
Убедись что PostgreSQL запущен
