from pathlib import Path

print('=== update_docs_v310.py ===')
print()

# ============================================================================
# 1. README.md
# ============================================================================
readme_path = Path('README.md')
readme_content = '''# SCADA.AI v3.1.0

AI-ассистент для оператора SCADA-системы промышленного здания

Система анализирует исторические данные из базы PostgreSQL, предоставляет детерминированные отчёты о здоровье системы и позволяет задавать вопросы на естественном языке.

## Быстрый старт

```
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

- **Индекс здоровья системы** — композитная оценка состояния (0-100) с детализацией расчёта
- **Индекс жизнеобеспечения** — параметры среды (CO2, температура, влажность, давление, VOC)
- **Журнал аварий** — приоритеты HIGH/MEDIUM/LOW с детализацией и drilldown
- **Расчёт стоимости ресурсов** — электричество, вода, тепло (текущий и прошлый месяц)
- **Интервальные тарифы** — автоматический выбор тарифа по дате
- **Системные логи** — AI-анализ через tool calling
- **Конфигуратор** — управление модулями, тарифами и тегами счётчиков

## Документация

- [MODULES.md](MODULES.md) — описание модулей (health, energy_*, hello, logs)
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
'''

readme_path.write_text(readme_content, encoding='utf-8', newline='\n')
print('✓ README.md: переписан полностью для v3.1.0')

# ============================================================================
# 2. CHANGELOG.md
# ============================================================================
changelog_path = Path('CHANGELOG.md')
changelog_content = '''# Changelog

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
'''

changelog_path.write_text(changelog_content, encoding='utf-8', newline='\n')
print('✓ CHANGELOG.md: добавлена секция 3.1.0 сверху')

# ============================================================================
# 3. MODULES.md
# ============================================================================
modules_path = Path('MODULES.md')
modules_content = '''# Модули SCADA.AI

Система состоит из независимых модулей, каждый из которых предоставляет свои tools для LLM и endpoints для API.

## Обзор модулей

| Модуль | Назначение | Tools | Виджеты |
|---|---|---|---|
| health | Анализ здоровья системы | get_health_report | health_score, life_support_card, environmental_panel, alarms_panel |
| energy_electricity | Расчёт стоимости электричества | calculate_electricity_cost, get_electricity_consumption | energy_cost_card |
| energy_water | Учёт потребления воды | calculate_water_cost, get_water_consumption | — |
| energy_heat | Учёт потребления тепла | calculate_heat_cost, get_heat_consumption | — |
| hello | Базовые ответы | — | — |
| logs | Анализ системных логов | analyze_logs | — |

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

Композитная формула:
```
score = 0.40 × Аварии + 0.35 × Среда + 0.25 × Оборудование
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

### Индекс жизнеобеспечения (life_support)

Отдельный индекс для параметров среды, ВСЕГДА вычисляется даже если нет данных.

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
Под статусом — детализация расчёта серым моноширинным текстом.

#### life_support_card
Круговая диаграмма с индексом жизнеобеспечения + таблица параметров с весами и статусами.

#### environmental_panel
Карточки 5 параметров среды с drilldown (история по часам, теги, битые датчики).
Сворачиваемый блок (по умолчанию свёрнут).

#### alarms_panel
Сводка аварий по приоритетам (High/Medium/Low) + топ повторяющихся + журнал с фильтрами.
Сворачиваемый блок (по умолчанию свёрнут).

## Модули энергоучёта

### energy_electricity

**Назначение:** Расчёт стоимости электроэнергии на основе тегов ЛЭРС и интервальных тарифов.

**Tools:**
- `get_electricity_consumption()` — потребление за текущий и прошлый месяц (в кВт·ч)
- `calculate_electricity_cost()` — стоимость с учётом тарифов (в ₽)

**Данные:**
- Теги ЛЭРС: `LERS.electricity meter current month N`, `LERS.electricity meter last month N`
- Тарифы: `data/tariffs.json` (интервальные)
- Конфиг счётчиков: `data/energy_config.json`

**Формула:**
```
Стоимость = Σ(Потребление × Тариф на дату)
```

**Пример тарифа:**
```
{
  "start_date": "2026-02-01",
  "end_date": null,
  "price_per_unit": 6.20,
  "currency": "RUB",
  "note": "Тариф 2026"
}
```

### energy_water, energy_heat

**Назначение:** Подготовка инфраструктуры для учёта воды и тепла. Сейчас — заглушки.

**Tools:** аналогично electricity, но для м³ и Гкал.

## Виджет energy_cost_card

Компактный виджет со сводкой по всем ресурсам.

**Отображение:**
- Большая цифра: **прошлый месяц** (полные данные)
- Подпись: "май 2026"
- Мелким текстом: текущий месяц (неполный)
- Детализация: электричество, вода, тепло (только прошлый месяц)

**Кнопка (i):** открывает формулу расчёта + таблицу действующих тарифов.

## Детерминированный vs LLM

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

## Модуль hello

**Назначение:** Базовые ответы на приветствия и общие вопросы.

**Tools:** нет (простые текстовые ответы)

**Примеры:**
- "Привет" → "Здравствуйте! Чем могу помочь?"
- "Как дела?" → "Система работает нормально. Хотите посмотреть отчёт?"

## Модуль logs

**Назначение:** Анализ системных логов через AI tool calling.

### Tools

#### analyze_logs

```
async def analyze_logs(level: str = None, limit: int = 100) -> dict:
    """
    Читает логи из core.logger и передаёт LLM для анализа.
    
    Args:
        level: фильтр по уровню (INFO/WARNING/ERROR)
        limit: максимальное количество строк
    
    Returns:
        {"analysis": "текст анализа от LLM", "log_count": N}
    """
```

**Flow:**
1. Frontend вызывает `POST /chat` с сообщением "проанализируй логи"
2. `chat.py` определяет что это logs-запрос
3. LLM вызывает tool `analyze_logs`
4. Tool читает логи из `core.logger`
5. LLM анализирует логи и возвращает текст
6. Frontend показывает анализ в NarrativePanel

**Пример диалога:**
- User: "проанализируй системный лог"
- → LLM вызывает analyze_logs(limit=100)
- → Tool возвращает 100 строк логов
- → LLM: "В логах за последний час обнаружено 3 ошибки подключения к БД..."

## Управление модулями

### Включение/выключение

Модули включаются через переменную окружения `ENABLED_MODULES`:
```
# .env
ENABLED_MODULES=hello,health,logs,energy_electricity,energy_water,energy_heat
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
```
name: my_module
version: 1.0.0
description: Описание модуля
enabled: true
```

**Пример tools.py:**
```
TOOLS = [
    {
        "name": "my_tool",
        "description": "Описание для LLM",
        "parameters": {
            "type": "object",
            "properties": {
                "param1": { "type": "string", "description": "Описание" }
            },
            "required": ["param1"]
        }
    }
]

async def my_tool(param1: str) -> dict:
    return { "result": f"Processed {param1}" }
```
'''

modules_path.write_text(modules_content, encoding='utf-8', newline='\n')
print('✓ MODULES.md: добавлены модули энергоучёта, обновлены формулы')

# ============================================================================
# 4. API.md
# ============================================================================
api_path = Path('API.md')
api_content = '''# API Reference

Все endpoints доступны на `http://localhost:8081/api/v1/`.

## Health API

### GET /health/ping
Простой health-check.

**Response:**
```
{
  "status": "ok",
  "time": "2026-01-15T10:30:00"
}
```

### GET /health/metrics-summary
Сводка по параметрам среды с агрегацией по зонам.

**Query Parameters:**
- `period_hours` (int, default=24) — период анализа

**Response:**
```
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
        "Зона 1": { "avg": 22.0, "count": 50 },
        "Зона 2": { "avg": 23.0, "count": 100 }
      }
    }
  },
  "text": "## Сводка по параметрам среды..."
}
```

**Использование:** Frontend для environmental_panel виджета.

### GET /health/alarms
Журнал аварий с фильтрами.

**Query Parameters:**
- `period_hours` (int, default=24, min=1, max=168)
- `priority` (string: "all" | "high" | "medium" | "low", default="all")
- `limit` (int, default=200, min=1, max=1000)

**Response:**
```
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

### GET /health/environmental/{param}
Детальный drilldown по параметру среды.

**Path Parameters:**
- `param` (string: "temperature" | "humidity" | "co2" | "pressure" | "voc")

**Query Parameters:**
- `period_hours` (int, default=24)
- `limit` (int, default=5000, min=100, max=20000)

**Response:**
```
{
  "param": "temperature",
  "label": "Температура",
  "unit": "°C",
  "norms": { "opt_min": 18, "opt_max": 24 },
  "validator": { "min": -50, "max": 80 },
  "count": 5000,
  "outliers_count": 3,
  "history": [
    { "tag_id": 1, "tag_name": "temp_1", "value": 22.5, "timestamp": "..." }
  ],
  "hourly": [
    { "hour": "2026-01-15T10", "avg": 22.0, "min": 20.0, "max": 24.0 }
  ],
  "tags_last_values": [
    { "tag_id": 1, "tag_name": "temp_1", "last_value": 22.5, "is_valid": true }
  ],
  "outliers": [
    { "tag_id": 2, "tag_name": "temp_2", "value": -999, "threshold": "-50..80 °C" }
  ]
}
```

**Использование:** Frontend модалка drilldown в environmental_panel.

### GET /health/debug
Список всех доступных endpoints health API.

**Response:**
```
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

## Chat API

### POST /chat
Основной endpoint для диалога с AI.

**Request:**
```
{
  "message": "покажи здоровье здания",
  "session_id": "default"
}
```

**Response:**
```
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
        "data": { "score": 65, "status": "GOOD", "status_ru": "Хорошо" },
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

## System API

### GET /system/info
Информация о системе (для сайдбара).

**Response:**
```
{
  "app_name": "SCADA.AI",
  "app_version": "3.1.0",
  "modules": ["hello", "health", "logs", "energy_electricity", "energy_water", "energy_heat"],
  "tools_count": 8,
  "tools_names": ["analyze_logs", "get_health_report", "calculate_electricity_cost", "get_electricity_consumption", "calculate_water_cost", "get_water_consumption", "calculate_heat_cost", "get_heat_consumption"],
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

## Config API

### GET /config/modules
Список модулей с их статусом.

**Response:**
```
[
  {
    "name": "health",
    "version": "1.0.0",
    "description": "Анализ здоровья системы",
    "enabled": true,
    "status": "loaded",
    "prompts": { "HEALTH_SYSTEM_PROMPT": "..." }
  }
]
```

### PUT /config/modules/{module_name}/enabled
Включить/выключить модуль.

**Request:**
```
{
  "enabled": true
}
```

**Response:**
```
{
  "status": "ok",
  "message": "Модуль 'health' включён. Перезапустите backend.",
  "restart_required": true
}
```

### GET /config/env
Читает системную конфигурацию из `.env`.

**Response:**
```
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

### GET /config/resolve-city?city=Нижний Тагил
Определяет координаты и timezone по названию города (через Nominatim/OpenStreetMap).

**Response:**
```
{
  "city": "Нижний Тагил",
  "latitude": 57.9167,
  "longitude": 59.9750,
  "timezone": "Asia/Yekaterinburg"
}
```

## Energy API

### GET /energy/tariffs
Спис тарифов по всем ресурсам.

**Response:**
```
{
  "electricity": [
    {
      "id": "t1",
      "start_date": "2025-01-01",
      "end_date": "2026-02-01",
      "price_per_unit": 5.50,
      "currency": "RUB",
      "note": "Тариф 2025"
    }
  ],
  "water": [],
  "heat": []
}
```

### POST /energy/tariffs
Создать новый тариф.

**Request:**
```
{
  "resource": "electricity",
  "start_date": "2026-02-01",
  "end_date": null,
  "price_per_unit": 6.20,
  "currency": "RUB",
  "note": "Тариф 2026"
}
```

### PUT /energy/tariffs/{resource}/{id}
Обновить существующий тариф.

### DELETE /energy/tariffs/{resource}/{id}
Удалить тариф.

### GET /energy/config
Конфигурация счётчиков по ресурсам.

**Response:**
```
{
  "electricity": {
    "enabled": true,
    "unit": "кВт·ч",
    "meters": [
      {
        "id": "input_1",
        "name": "Первый ввод",
        "tag_current": "LERS.electricity meter current month 1",
        "tag_last": "LERS.electricity meter last month 1"
      }
    ]
  },
  "water": { "enabled": false, "unit": "м³", "meters": [] },
  "heat": { "enabled": false, "unit": "Гкал", "meters": [] }
}
```

### PUT /energy/config/{resource}
Обновить конфигурацию ресурса (включить/выключить, изменить счётчики).

### GET /energy/summary
Сводка по всем ресурсам: текущий + прошлый месяц + стоимость.

**Response:**
```
{
  "electricity": {
    "current_month": { "consumption_kwh": 4250, "cost_rub": 26350 },
    "last_month": { "consumption_kwh": 18388, "cost_rub": 114005.6 },
    "errors": []
  },
  "water": null,
  "heat": null,
  "total_cost_current": 26350.0,
  "total_cost_last": 114005.6,
  "errors": []
}
```

**Использование:** Frontend виджет `energy_cost_card` и вкладка "Энергоучёт" в конфигураторе.

## Logs API

### GET /logs/files
Список файлов логов.

**Response:**
```
{
  "count": 5,
  "files": [
    { "name": "2026-01-15.log", "size": 1024 },
    { "name": "2026-01-14.log", "size": 2048 }
  ]
}
```

### GET /logs/current?limit=100&level=ERROR
Текущие логи из буфера.

**Response:**
```
{
  "count": 100,
  "logs": [
    { "timestamp": "...", "level": "ERROR", "message": "DB connection failed" }
  ],
  "source": "current",
  "file": "2026-01-15.log"
}
```
'''

api_path.write_text(api_content, encoding='utf-8', newline='\n')
print('✓ API.md: добавлена секция Energy API')

# ============================================================================
# 5. CHAT_EXAMPLES.md
# ============================================================================
chat_path = Path('CHAT_EXAMPLES.md')
chat_content = '''# Примеры запросов к чату

SCADA.AI понимает запросы на естественном русском языке и автоматически определяет какой модуль использовать.

## Модуль health

### Базовые запросы

**"покажи здоровье здания"**
- Триггерит health-анализ
- Возвращает narrative + виджеты (health_score, life_support_card, environmental_panel, alarms_panel)
- Озвучивает краткое резюме

**"проанализируй состояние системы"**
- Аналогично "покажи здоровье здания"

**"что с системой?"**
- Аналогично "покажи здоровье здания"

### Параметры среды

**"температура и влажность"**
- Показывает environmental_panel виджет
- Сводка по 5 параметрам с зонами

**"покажи CO2"**
- Открывает drilldown по CO2
- История по часам, теги, битые датчики

**"давление за последние 48 часов"**
- Drilldown по давлению с period_hours=48

### Аварии

**"какие аварии были сегодня?"**
- Показывает alarms_panel
- Журнал аварий за 24 часа

**"покажи критические аварии"**
- Фильтр priority=high
- Только High-аварии

## Модуль энергоучёта

**"сколько денег потратили на электричество?"**
- Показывает `energy_cost_card` виджет
- Прошлый месяц: 114 005 ₽ (18 388 кВт·ч)
- Текущий: 26 350 ₽ (неполный)

**"покажи затраты на ресурсы"**
- Активирует health-анализ
- В виджетах появляется `energy_cost_card` с суммой по всем ресурсам

**"какой тариф на электричество действует?"**
- LLM отвечает текстом на основе `data/tariffs.json`
- Пример: "Действующий тариф — 6.20 ₽/кВт·ч с 1 февраля 2026"

**"сколько кВт·ч потребили за прошлый месяц?"**
- LLM вызывает tool `get_electricity_consumption`
- Отвечает: "В мае 2026 потребили 18 388 кВт·ч"

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

## Модуль hello

**"привет"**
- Базовое приветствие

**"как дела?"**
- Общий ответ о состоянии системы

**"что ты умеешь?"**
- Список возможностей

## Навигация

**"открой конфигуратор"**
- Переключает на страницу Config
- Эквивалент клика на иконку Settings

**"настройки"**
- Аналогично "открой конфигуратор"

## Комбинированные запросы

**"покажи здоровье и проанализируй логи"**
- Выполняет health-анализ
- Затем вызывает `analyze_logs`
- Возвращает два блока: narrative + logs analysis

## Голосовое управление

Все ответы озвучиваются через `speechSynthesis` API.

**Кнопка "Повторить голосом"** (Volume2 иконка в хедере):
- Повторяет последний voice-ответ
- Используется если не расслышал

**Прерывание:**
- Если status="CRITICAL" → interrupt=true (прерывает текущую речь)
- Если status="WARNING" → priority="alert" (повышенный приоритет)

## Обработка ошибок

**Если БД недоступна:**
- User: "покажи здоровье"
- → Backend: DB connection failed
- → Response: "⚠️ Не удалось собрать данные из БД: connection refused"

**Если LLM не настроен:**
- User: "любой запрос"
- → Backend: YANDEX_API_KEY пустой
- → Response: "⚠️ LLM не настроен: YANDEX_API_KEY is empty"

**Если модуль выключен:**
- User: "проанализируй логи" (но logs module disabled)
- → LLM не видит tool `analyze_logs`
- → Response: "Извините, я не могу проанализировать логи. Модуль logs отключен."

## Технические детали

### Определение типа запроса

Backend использует keyword matching:
```
HEALTH_KEYWORDS = ["здоров", "состояни", "аналитик", "проблем", "авари", "диагност"]
LOGS_KEYWORDS = ["лог", "log", "ошибк", "error"]
CONFIG_KEYWORDS = ["конфигуратор", "настройки", "настроить"]
```

- Если сообщение содержит health-ключи → вызывается `handle_health_query()`
- Если содержит logs-ключи → LLM использует tool `analyze_logs`
- Иначе → общий диалог с LLM

### Tool Calling

**Для health-запросов** не используется tool calling — данные собираются детерминированно.

**Для logs-запросов** используется tool calling:
1. LLM получает system prompt с описанием tools
2. LLM решает вызвать `analyze_logs`
3. Backend выполняет tool
4. Результат передаётся обратно LLM
5. LLM генерирует финальный ответ

### Время ответа

- **Health анализ:** 2-5 секунд (зависит от объёма данных в БД)
- **Logs анализ:** 5-15 секунд (LLM processing)
- **Простой диалог:** 1-3 секунды
'''

chat_path.write_text(chat_content, encoding='utf-8', newline='\n')
print('✓ CHAT_EXAMPLES.md: добавлены примеры для энергоучёта')

# ============================================================================
# 6. ARCHITECTURE.md
# ============================================================================
arch_path = Path('ARCHITECTURE.md')
arch_content = '''# Архитектура SCADA.AI

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
'''
arch_path.write_text(arch_content, encoding='utf-8', newline='\n')
print('✓ ARCHITECTURE.md: обновлена структура, формулы, roadmap')
print()
print('=' * 60)
print('ЧТО ОБНОВЛЕНО:')
print('=' * 60)
print()
print('1. README.md')
print(' • Версия: 3.0.2 → 3.1.0')
print(' • Возможности: добавлен расчёт стоимости ресурсов')
print()
print('2. CHANGELOG.md')
print(' • Добавлена секция 3.1.0 с Added/Changed/Fixed')
print(' • Roadmap: v3.1.0 отмечена как реализованная')
print()
print('3. MODULES.md')
print(' • Таблица: +3 модуля energy_*')
print(' • Формула: убрана Энергия (40+35+25)')
print(' • Удалён energy_panel из виджетов')
print(' • Добавлен раздел "Модули энергоучёта"')
print(' • Добавлен виджет energy_cost_card')
print()
print('4. API.md')
print(' • Добавлена секция Energy API (6 endpoints)')
print(' • CRUD тарифов, конфиг счётчиков, summary')
print()
print('5. CHAT_EXAMPLES.md')
print(' • Добавлен "Модуль энергоучёта" с 4 примерами')
print()
print('6. ARCHITECTURE.md')
print(' • Структура: добавлены modules/energy_*, data/')
print(' • Frontend: EnergyPanel → EnergyCostCard')
print(' • Формула: убрана Энергия')
print(' • Добавлен раздел "Модули энергоучёта"')
print()
print('=' * 60)
print('СЛЕДУЮЩИЙ ШАГ:')
print('=' * 60)
print()
print('Все файлы используют ``` для code blocks.')
print('Открой их в редакторе и замени:')
print(' ``` → ```')
print()
print('После замены:')
print(' git add -A')
print(' git commit -m "docs: обновлена документация для v3.1.0 (модуль Бабло)"')
print()
print('Когда заменишь — скажи "docs ок" и коммитим весь модуль Бабло')