from pathlib import Path

print('=== generate_docs.py ===')
print()

docs_dir = Path('docs')
docs_dir.mkdir(exist_ok=True)

# ============================================================================
# 1. README.md — главная страница
# ============================================================================
readme_content = """# SCADA.AI v3.0.1

**AI-ассистент для оператора SCADA-системы промышленного здания**

Система анализирует исторические данные из базы PostgreSQL, предоставляет детерминированные отчёты о здоровье системы и позволяет задавать вопросы на естественном языке.

## Быстрый старт

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8081

# Frontend
cd frontend
npm install
npm run dev
```

## Возможности

- **Индекс здоровья системы** — композитная оценка состояния (0-100)
- **Индекс жизнеобеспечения** — параметры среды (CO2, температура, влажность, давление, VOC)
- **Журнал аварий** — приоритеты HIGH/MEDIUM/LOW с детализацией
- **Энергоэффективность** — анализ освещения относительно времени суток
- **Системные логи** — AI-анализ через tool calling
- **Конфигуратор** — управление модулями и промптами

## Документация

- [MODULES.md](MODULES.md) — описание модулей (health, hello, logs)
- [API.md](API.md) — HTTP endpoints с примерами
- [CHAT_EXAMPLES.md](CHAT_EXAMPLES.md) — примеры запросов к чату
- [ARCHITECTURE.md](ARCHITECTURE.md) — архитектура системы
- [CHANGELOG.md](CHANGELOG.md) — история изменений

## Технологический стек

**Backend:**
- FastAPI + asyncpg (PostgreSQL)
- YandexGPT 5.1 (tool calling)
- structlog (логирование)

**Frontend:**
- Svelte 5 + runes
- Tailwind CSS
- ky (HTTP client)

## Лицензия

Proprietary. Все права защищены.
"""

(docs_dir / 'README.md').write_text(readme_content, encoding='utf-8')
print('✓ Создан: docs/README.md')

# ============================================================================
# 2. MODULES.md — описание модулей
# ============================================================================
modules_content = """# Модули SCADA.AI

Система состоит из независимых модулей, каждый из которых предоставляет свои tools для LLM и endpoints для API.

## Обзор модулей

| Модуль | Назначение | Tools | Виджеты |
|--------|-----------|-------|---------|
| **health** | Анализ здоровья системы | `get_health_report` | health_score, life_support_card, environmental_panel, alarms_panel, energy_panel |
| **hello** | Базовые ответы | — | — |
| **logs** | Анализ системных логов | `analyze_logs` | — |

---

## Модуль health

**Назначение:** Детерминированный анализ состояния системы на основе исторических данных из PostgreSQL.

### Архитектура

```
modules/health/
├── __init__.py              # Регистрация модуля
├── prompts.py               # HEALTH_SYSTEM_PROMPT для LLM
├── data_collectors.py       # SQL-запросы к БД
├── analysis.py              # Детерминированные формулы
├── renderers.py             # Генерация narrative/voice/visual
└── tools.py                 # Tools для tool calling
```

### Индекс здоровья системы (health_score)

**Композитная формула:**
```
score = 0.35 × Аварии + 0.30 × Среда + 0.25 × Оборудование + 0.10 × Энергия
```

**Под-индексы:**

#### 1. Индекс аварий (alarms)
```
score = 100 - min(high × 15, 50) - min(medium × 4, 25) - min(low × 0.5, 10)
```

**Штрафы:**
- High авария: -15 (макс -50)
- Medium авария: -4 (макс -25)
- Low авария: -0.5 (макс -10)

#### 2. Индекс среды (environmental)
```
score = взвешенная сумма статусов 5 параметров
```

**Веса:**
- CO2: 30%
- Температура: 25%
- VOC: 20%
- Влажность: 15%
- Давление: 10%

**Статусы параметров:**
- OK: 100 баллов
- WARNING: 55 баллов
- CRITICAL: 15 баллов

**Нормативы:**
- Температура: оптимум 18-24°C, критично <10 или >35
- Влажность: оптимум 30-60%, критично <20 или >80
- CO2: оптимум 400-800 ppm, критично >2000
- Давление: оптимум 720-780 мм рт.ст.
- VOC: оптимум <220 ppb, критично >660 ppb

#### 3. Индекс оборудования (equipment)
```
score = 100 - штрафы за битые/офлайн/дребезжащие/залипшие теги
```

**Штрафы:**
- Битый датчик: до -40
- Офлайн тег: до -30
- Дребезжащий тег: до -15
- Залипший тег: до -10

#### 4. Индекс энергоэффективности (energy)
```
score = оценка освещения относительно времени суток
```

**Статусы:**
- EXCELLENT: 95 баллов (днём выключено >50%, ночью включено >30%)
- GOOD: 80 баллов
- WARNING: 45 баллов (днём включено >70%, ночью <10%)
- CRITICAL: 15 баллов

### Индекс жизнеобеспечения (life_support)

**Отдельный индекс** для параметров среды, ВСЕГДА вычисляется даже если нет данных.

**Формула:**
```
score = взвешенная сумма статусов 5 параметров (те же веса что в environmental)
```

**Статусы:**
- ≥85: EXCELLENT
- 60-84: GOOD
- 30-59: WARNING
- <30: CRITICAL

### Виджеты

#### health_score
Круговая диаграмма с композитным индексом (0-100) и статусом (CRITICAL/WARNING/GOOD/EXCELLENT).

#### life_support_card
Круговая диаграмма с индексом жизнеобеспечения + таблица параметров с весами и статусами.

#### environmental_panel
Карточки 5 параметров среды с drilldown (история по часам, теги, битые датчики).

#### alarms_panel
Сводка аварий по приоритетам (High/Medium/Low) + топ повторяющихся + журнал с фильтрами.

#### energy_panel
Оценка энергоэффективности освещения с рекомендациями.

### Детерминированный vs LLM

**Детерминированный слой** (`analysis.py`):
- Быстрый (50мс)
- Бесплатный
- Надёжный
- Используется для виджетов

**LLM слой** (`prompts.py` + `chat.py`):
- Медленный (5-10 сек)
- Платный
- Генерирует narrative на основе детерминированных данных
- Используется для ответов в чате

---

## Модуль hello

**Назначение:** Базовые ответы на приветствия и общие вопросы.

**Tools:** нет (простые текстовые ответы)

**Примеры:**
- "Привет" → "Здравствуйте! Чем могу помочь?"
- "Как дела?" → "Система работает нормально. Хотите посмотреть отчёт?"

---

## Модуль logs

**Назначение:** Анализ системных логов через AI tool calling.

### Tools

#### analyze_logs
```python
async def analyze_logs(level: str = None, limit: int = 100) -> dict:
    ```
    Читает логи из core.logger и передаёт LLM для анализа.
    
    Args:
        level: фильтр по уровню (INFO/WARNING/ERROR)
        limit: максимальное количество строк
    
    Returns:
        {"analysis": "текст анализа от LLM", "log_count": N}
    ```
```

**Flow:**
1. Frontend вызывает `POST /chat` с сообщением "проанализируй логи"
2. `chat.py` определяет что это logs-запрос
3. LLM вызывает tool `analyze_logs`
4. Tool читает логи из `core.logger`
5. LLM анализирует логи и возвращает текст
6. Frontend показывает анализ в NarrativePanel

**Пример диалога:**
```
User: "проанализируй системный лог"
→ LLM вызывает analyze_logs(limit=100)
→ Tool возвращает 100 строк логов
→ LLM: "В логах за последний час обнаружено 3 ошибки подключения к БД..."
```

---

## Управление модулями

### Включение/выключение

Модули включаются через переменную окружения `ENABLED_MODULES`:

```bash
# .env
ENABLED_MODULES=hello,health,logs
```

Изменение через UI: Конфигуратор → Модули → переключатель.

**Важно:** После изменения требуется перезапуск backend.

### Добавление нового модуля

1. Создать папку `modules/my_module/`
2. Создать `__init__.py` (можно пустой)
3. Создать `config.yaml` с metadata
4. Создать `tools.py` с `TOOLS = [...]`
5. Создать `prompts.py` с системными промптами
6. Добавить `my_module` в `ENABLED_MODULES`
7. Перезапустить backend

**Пример config.yaml:**
```yaml
name: my_module
version: 1.0.0
description: Описание модуля
enabled: true
```

**Пример tools.py:**
```python
TOOLS = [
    {
        "name": "my_tool",
        "description": "Описание для LLM",
        "parameters": {
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": "Описание"}
            },
            "required": ["param1"]
        }
    }
]

async def my_tool(param1: str) -> dict:
    return {"result": f"Processed {param1}"}
```
"""

(docs_dir / 'MODULES.md').write_text(modules_content, encoding='utf-8')
print('✓ Создан: docs/MODULES.md')

# ============================================================================
# 3. API.md — HTTP endpoints
# ============================================================================
api_content = """# API Reference

Все endpoints доступны на `http://localhost:8081/api/v1/`.

## Health API

### GET /health/ping

Простой health-check.

**Response:**
```json
{
  "status": "ok",
  "time": "2026-01-15T10:30:00"
}
```

---

### GET /health/metrics-summary

Сводка по параметрам среды с агрегацией по зонам.

**Query Parameters:**
- `period_hours` (int, default=24) — период анализа

**Response:**
```json
{
  "params": {
    "temperature": {
      "label": "Температура",
      "unit": "°C",
      "avg": 22.5,
      "min": 18.0,
      "max": 26.0,
      "status": "OK",
      "tags_count": 150,
      "outliers_count": 2,
      "by_zone": {
        "Зона 1": {"avg": 22.0, "count": 50},
        "Зона 2": {"avg": 23.0, "count": 100}
      }
    }
  },
  "text": "## Сводка по параметрам среды..."
}
```

**Использование:** Frontend для environmental_panel виджета.

---

### GET /health/alarms

Журнал аварий с фильтрами.

**Query Parameters:**
- `period_hours` (int, default=24, min=1, max=168)
- `priority` (string: "all" | "high" | "medium" | "low", default="all")
- `limit` (int, default=200, min=1, max=1000)

**Response:**
```json
{
  "period_hours": 24,
  "filter": "all",
  "count": 15,
  "alarms": [
    {
      "id": 12345,
      "name": "Temperature_sensor_1",
      "bound": "High",
      "priority": 150,
      "priority_label": "high",
      "state": 1,
      "is_active": true,
      "timestamp": "2026-01-15T10:00:00",
      "message": "Превышение температуры",
      "zone": "Зона 1"
    }
  ]
}
```

**Приоритеты:**
- `high` (≥150): критические аварии
- `medium` (100-149): средние аварии
- `low` (<100): информационные события

**Использование:** Frontend для alarms_panel виджета.

---

### GET /health/environmental/{param}

Детальный drilldown по параметру среды.

**Path Parameters:**
- `param` (string: "temperature" | "humidity" | "co2" | "pressure" | "voc")

**Query Parameters:**
- `period_hours` (int, default=24)
- `limit` (int, default=5000, min=100, max=20000)

**Response:**
```json
{
  "param": "temperature",
  "label": "Температура",
  "unit": "°C",
  "norms": {"opt_min": 18, "opt_max": 24},
  "validator": {"min": -50, "max": 80},
  "count": 5000,
  "outliers_count": 3,
  "history": [
    {"tag_id": 1, "tag_name": "temp_1", "value": 22.5, "timestamp": "..."}
  ],
  "hourly": [
    {"hour": "2026-01-15T10", "avg": 22.0, "min": 20.0, "max": 24.0}
  ],
  "tags_last_values": [
    {"tag_id": 1, "tag_name": "temp_1", "last_value": 22.5, "is_valid": true}
  ],
  "outliers": [
    {"tag_id": 2, "tag_name": "temp_2", "value": -999, "threshold": "-50..80 °C"}
  ]
}
```

**Использование:** Frontend модалка drilldown в environmental_panel.

---

### GET /health/debug

Список всех доступных endpoints health API.

**Response:**
```json
{
  "endpoints": [
    "GET /health/ping",
    "GET /health/debug",
    "GET /health/metrics-summary",
    "GET /health/alarms"
  ],
  "param_groups": ["temperature", "humidity", "co2", "pressure", "voc"],
  "time": "2026-01-15T10:30:00"
}
```

---

## Chat API

### POST /chat

Основной endpoint для диалога с AI.

**Request:**
```json
{
  "message": "покажи здоровье здания",
  "session_id": "default"
}
```

**Response:**
```json
{
  "response": "# Отчёт о здоровье системы\\n\\n**Композитный индекс:** 65/100...",
  "status": "ok",
  "voice": {
    "text": "Здоровье системы 65 из 100, состояние нормальное.",
    "priority": "normal",
    "interrupt": false
  },
  "visual": {
    "widgets": [
      {
        "type": "health_score",
        "data": {"score": 65, "status": "GOOD", "status_ru": "Хорошо"},
        "size": "medium"
      }
    ]
  },
  "tool_calls": ["get_health_report"]
}
```

**Flow:**
1. Frontend отправляет `POST /chat`
2. Backend определяет тип запроса (health/logs/general)
3. Для health: собирает данные → LLM → рендерит виджеты
4. Frontend показывает narrative + виджеты + озвучивает voice

---

## System API

### GET /system/info

Информация о системе (для сайдбара).

**Response:**
```json
{
  "app_name": "SCADA.AI",
  "app_version": "3.0.1",
  "modules": ["hello", "health", "logs"],
  "tools_count": 2,
  "tools_names": ["analyze_logs", "get_health_report"],
  "db_host": "localhost",
  "db_status": "ok",
  "llm_model": "yandexgpt-5.1/latest",
  "llm_status": "ok",
  "scada_url": "http://localhost:9002",
  "last_health_check": {
    "timestamp": "2026-01-15T10:00:00",
    "duration_sec": 2.5,
    "score": 65
  },
  "server_time": "2026-01-15T10:30:00"
}
```

---

## Config API

### GET /config/modules

Список модулей с их статусом.

**Response:**
```json
[
  {
    "name": "health",
    "version": "1.0.0",
    "description": "Анализ здоровья системы",
    "enabled": true,
    "status": "loaded",
    "prompts": {"HEALTH_SYSTEM_PROMPT": "..."}
  }
]
```

---

### PUT /config/modules/{module_name}/enabled

Включить/выключить модуль.

**Request:**
```json
{
  "enabled": true
}
```

**Response:**
```json
{
  "status": "ok",
  "message": "Модуль 'health' включён. Перезапустите backend.",
  "restart_required": true
}
```

---

### GET /config/env

Читает системную конфигурацию из `.env`.

**Response:**
```json
{
  "db_host": "localhost",
  "db_port": 5432,
  "scada_base_url": "http://localhost:9002",
  "yandex_api_key": "***",
  "yandex_gpt_model": "yandexgpt-5.1/latest",
  "city": "Москва",
  "latitude": 55.7558,
  "longitude": 37.6173
}
```

---

### GET /config/resolve-city?city=Нижний Тагил

Определяет координаты и timezone по названию города (через Nominatim/OpenStreetMap).

**Response:**
```json
{
  "city": "Нижний Тагил",
  "latitude": 57.9167,
  "longitude": 59.9750,
  "timezone": "Asia/Yekaterinburg"
}
```

---

## Logs API

### GET /logs/files

Список файлов логов.

**Response:**
```json
{
  "count": 5,
  "files": [
    {"name": "2026-01-15.log", "size": 1024},
    {"name": "2026-01-14.log", "size": 2048}
  ]
}
```

---

### GET /logs/current?limit=100&level=ERROR

Текущие логи из буфера.

**Response:**
```json
{
  "count": 100,
  "logs": [
    {"timestamp": "...", "level": "ERROR", "message": "DB connection failed"}
  ],
  "source": "current",
  "file": "2026-01-15.log"
}
```
"""

(docs_dir / 'API.md').write_text(api_content, encoding='utf-8')
print('✓ Создан: docs/API.md')

# ============================================================================
# 4. CHAT_EXAMPLES.md — примеры запросов
# ============================================================================
chat_examples_content = """# Примеры запросов к чату

SCADA.AI понимает запросы на естественном русском языке и автоматически определяет какой модуль использовать.

## Модуль health

### Базовые запросы

**"покажи здоровье здания"**
- Триггерит health-анализ
- Возвращает narrative + виджеты (health_score, life_support_card, environmental_panel, alarms_panel, energy_panel)
- Озвучивает краткое резюме

**"проанализируй состояние системы"**
- Аналогично "покажи здоровье здания"

**"что с системой?"**
- Аналогично "покажи здоровье здания"

---

### Параметры среды

**"температура и влажность"**
- Показывает environmental_panel виджет
- Сводка по 5 параметрам с зонами

**"покажи CO2"**
- Открывает drilldown по CO2
- История по часам, теги, битые датчики

**"давление за последние 48 часов"**
- Drilldown по давлению с period_hours=48

---

### Аварии

**"какие аварии были сегодня?"**
- Показывает alarms_panel
- Журнал аварий за 24 часа

**"покажи критические аварии"**
- Фильтр priority=high
- Только High-аварии

---

## Модуль logs

**"проанализируй системный лог"**
- LLM вызывает tool `analyze_logs`
- Читает последние 100 строк логов
- Возвращает текстовый анализ

**"покажи логи"**
- Открывает SystemLogsPanel (не через чат)
- Прямой доступ к логам без AI

**"есть ли ошибки в логах?"**
- LLM фильтрует level=ERROR
- Анализ только ошибок

---

## Модуль hello

**"привет"**
- Базовое приветствие

**"как дела?"**
- Общий ответ о состоянии системы

**"что ты умеешь?"**
- Список возможностей

---

## Навигация

**"открой конфигуратор"**
- Переключает на страницу Config
- Эквивалент клика на иконку Settings

**"настройки"**
- Аналогично "открой конфигуратор"

---

## Комбинированные запросы

**"покажи здоровье и проанализируй логи"**
- Выполняет health-анализ
- Затем вызывает `analyze_logs`
- Возвращает два блока: narrative + logs analysis

---

## Голосовое управление

Все ответы озвучиваются через `speechSynthesis` API.

**Кнопка "Повторить голосом"** (Volume2 иконка в хедере):
- Повторяет последний voice-ответ
- Используется если не расслышал

**Прерывание:**
- Если status="CRITICAL" → interrupt=true (прерывает текущую речь)
- Если status="WARNING" → priority="alert" (повышенный приоритет)

---

## Обработка ошибок

**Если БД недоступна:**
```
User: "покажи здоровье"
→ Backend: DB connection failed
→ Response: "⚠️ Не удалось собрать данные из БД: connection refused"
```

**Если LLM не настроен:**
```
User: "любой запрос"
→ Backend: YANDEX_API_KEY пустой
→ Response: "⚠️ LLM не настроен: YANDEX_API_KEY is empty"
```

**Если модуль выключен:**
```
User: "проанализируй логи" (но logs module disabled)
→ LLM не видит tool `analyze_logs`
→ Response: "Извините, я не могу проанализировать логи. Модуль logs отключен."
```

---

## Технические детали

### Определение типа запроса

Backend использует keyword matching:

```python
HEALTH_KEYWORDS = ["здоров", "состояни", "аналитик", "проблем", "авари", "диагност"]
LOGS_KEYWORDS = ["лог", "log", "ошибк", "error"]
CONFIG_KEYWORDS = ["конфигуратор", "настройки", "настроить"]
```

Если сообщение содержит health-ключи → вызывается `handle_health_query()`.
Если содержит logs-ключи → LLM использует tool `analyze_logs`.
Иначе → общий диалог с LLM.

### Tool Calling

Для health-запросов **не используется** tool calling — данные собираются детерминированно.

Для logs-запросов **используется** tool calling:
1. LLM получает system prompt с описанием tools
2. LLM решает вызвать `analyze_logs`
3. Backend выполняет tool
4. Результат передаётся обратно LLM
5. LLM генерирует финальный ответ

### Время ответа

- **Health анализ:** 2-5 секунд (зависит от объёма данных в БД)
- **Logs анализ:** 5-15 секунд (LLM processing)
- **Простой диалог:** 1-3 секунды
"""

(docs_dir / 'CHAT_EXAMPLES.md').write_text(chat_examples_content, encoding='utf-8')
print('✓ Создан: docs/CHAT_EXAMPLES.md')

# ============================================================================
# 5. ARCHITECTURE.md — архитектура системы
# ============================================================================
architecture_content = """# Архитектура SCADA.AI

## Общая схема

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (Svelte 5)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Home.svelte  │  │ Config.svelte│  │ SystemLogsPanel  │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│           │                  │                    │          │
│           └──────────────────┴────────────────────┘          │
│                              │                               │
│                    POST /chat                                │
│                    GET /health/*                             │
│                    GET /system/info                          │
└──────────────────────────────┼───────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                       │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                    API Routers                        │   │
│  │  /chat  /health  /system  /config  /logs              │   │
│  └──────────────────────────────────────────────────────┘   │
│           │                                                  │
│           ▼                                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Module Registry (auto-discovery)         │   │
│  │  modules/health  modules/hello  modules/logs          │   │
│  └──────────────────────────────────────────────────────┘   │
│           │                                                  │
│           ▼                                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Tool Executor (dispatch)                 │   │
│  │  analyze_logs()  get_health_report()                  │   │
│  └──────────────────────────────────────────────────────┘   │
│           │                                                  │
│           ▼                                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              LLM Provider (YandexGPT)                 │   │
│  │  generate()  generate_with_tools()                    │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────┼───────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                   PostgreSQL (SCADA DB)                      │
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
│   │       └── EnergyPanel.svelte
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
```python
# core/module_registry.py
def discover_modules() -> list[str]:
    for path in modules_dir.iterdir():
        if path.is_dir() and (path / "__init__.py").exists():
            modules.append(path.name)
```

**Загрузка модуля:**
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

---

## Детерминированный vs LLM

### Health модуль

**Детерминированный слой** (analysis.py):
```python
def compute_health_report(data: dict) -> HealthReport:
    # Формулы без LLM
    alarm_idx = _compute_alarm_index(by_priority)
    env_idx = _compute_environmental_index(env)
    # ...
    score = 0.35 * alarm_idx + 0.30 * env_idx + ...
    return HealthReport(score=score, ...)
```

**LLM слой** (prompts.py):
```python
HEALTH_SYSTEM_PROMPT = ```
Ты — инженер-аналитик SCADA-системы.
Верни JSON в формате: {score, status, summary, ...}
```
```

**Когда что используется:**
- Виджеты → детерминированный (быстро, бесплатно)
- Narrative в чате → LLM (медленно, но с анализом)

---

### Logs модуль

**Только LLM:**
```python
# logs/tools.py
async def analyze_logs(limit: int = 100) -> dict:
    logs = system_logger.get_logs(limit=limit)
    return {"logs": logs}
```

LLM получает логи через tool и сама анализирует.

---

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
ENABLED_MODULES=hello,health,logs

# Logging
LOG_POLL_INTERVAL_MS=2000
```

---

## Безопасность

### Текущее состояние

- **Нет авторизации** — все endpoints публичные
- **Нет CORS** — только localhost
- **API ключи** в `.env` (не коммитятся)

### Рекомендации для продакшена

1. Добавить JWT авторизацию
2. Настроить CORS (разрешить только frontend домен)
3. Использовать HTTPS
4. Rate limiting на /chat
5. Валидация входных данных (Pydantic models)

---

## Масштабирование

### Текущие ограничения

- **Single instance** — один backend процесс
- **In-memory module registry** — не распределённый
- **PostgreSQL** — single master

### Для продакшена

1. **Docker Compose** — backend + frontend + postgres
2. **Redis** — кэширование health-отчётов
3. **Celery** — фоновые задачи (scheduled analysis)
4. **Prometheus** — метрики
5. **Grafana** — дашборды

---

## Отладка

### Логи

```bash
# Backend логи
tail -f backend/logs/2026-01-15.log

# Frontend консоль
F12 → Console
```

### Debug endpoints

```bash
# Список всех endpoints
curl http://localhost:8081/api/v1/health/debug

# Проверка БД
curl http://localhost:8081/api/v1/system/info | jq .db_status
```

### Common issues

**"LLM не настроен":**
- Проверь YANDEX_API_KEY в .env
- Убедись что ключ активен

**"Модуль не загружен":**
- Проверь ENABLED_MODULES в .env
- Перезапусти backend

**"DB connection failed":**
- Проверь DB_HOST, DB_PORT, DB_PASSWORD
- Убедись что PostgreSQL запущен
"""

(docs_dir / 'ARCHITECTURE.md').write_text(architecture_content, encoding='utf-8')
print('✓ Создан: docs/ARCHITECTURE.md')

# ============================================================================
# 6. CHANGELOG.md — история изменений
# ============================================================================
changelog_content = """# Changelog

Все значимые изменения в проекте документируются в этом файле.

Формат основан на [Keep a Changelog](https://keepachangelog.com/).

---

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

---

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

---

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

---

## [3.0.0] - 2026-05-29

### Added
- **Первая публичная версия SCADA.AI v3**
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

---

## [2.x.x] - 2025 (Legacy)

Внутренние версии для тестирования. Не публичные.

---

## [1.x.x] - 2024 (Prototype)

Первоначальный прототип на Python + Flask. Переписан в v3.0.0.

---

## Roadmap

### v3.1.0 (Планируется)
- [ ] Модуль `energy_electricity` — расчёт стоимости электроэнергии
- [ ] Модуль `energy_water` — заглушка для будущего расширения
- [ ] Модуль `energy_heat` — заглушка для будущего расширения
- [ ] Интервальные тарифы (tariffs.json)
- [ ] Конфигуратор тегов счётчиков (energy_config.json)
- [ ] Виджет `energy_cost_card` — суммарная стоимость ресурсов

### v3.2.7 (Планируется)
- [ ] Модуль `historical_data` — тренды и сравнение периодов
- [ ] Модуль `predictive_analytics` — прогнозы экономии
- [ ] Boss dashboard — отдельный экран для руководства

### v4.0.0 (Долгосрочно)
- [ ] Ролевая модель (admin, engineer, operator, boss)
- [ ] Зашифрованное хранилище пользователей (users.enc)
- [ ] Multi-tenancy (несколько зданий в одной системе)
- [ ] Mobile app (React Native)
"""

(docs_dir / 'CHANGELOG.md').write_text(changelog_content, encoding='utf-8')
print('✓ Создан: docs/CHANGELOG.md')

print()
print('=' * 60)
print('ДОКУМЕНТАЦИЯ СГЕНЕРИРОВАНА')
print('=' * 60)
print()
print('Создано 6 файлов в backend/docs/:')
print('  • README.md — overview + quickstart')
print('  • MODULES.md — описание модулей с формулами')
print('  • API.md — endpoints с примерами')
print('  • CHAT_EXAMPLES.md — примеры запросов')
print('  • ARCHITECTURE.md — архитектура + flow')
print('  • CHANGELOG.md — история версий + roadmap')
print()
print('ВАЖНО: В файлах код-блоки обозначены ``` вместо ~~~')
print('       Замени ``` на ~~~ или ``` в редакторе если нужно.')
print()
print('Структура RAG-friendly:')
print('  ✓ Атомарные файлы (одна тема на файл)')
print('  ✓ Чёткая иерархия заголовков')
print('  ✓ Consistent терминология')
print('  ✓ Примеры с контекстом')
print('  ✓ Metadata в начале каждого файла')
print()
print('Следующий шаг: проверить контент, потом делать viewer.')