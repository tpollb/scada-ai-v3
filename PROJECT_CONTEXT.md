# SCADA.AI - Контекст проекта и план развития

**Версия документа:** 1.0  
**Дата актуализации:** 2026-07-08  
**Текущая версия системы:** v3.2.9.1

---

## 1. Обзор системы

**SCADA.AI v3.2.9** — AI-ассистент для оператора SCADA-системы промышленного здания. Система анализирует исторические данные из PostgreSQL/TimescaleDB, предоставляет детерминированные отчёты о здоровье системы, выполняет глубокий анализ данных (DDA) с детекцией аномалий, сезонных паттернов и A/B сравнениями, а также позволяет задавать вопросы на естественном языке.

### 1.1 Технологический стек

**Backend:**
- FastAPI + asyncpg (PostgreSQL / TimescaleDB)
- YandexGPT 5.1 (tool calling, function calls)
- scipy (статистика: Welch's t-test, FFT, корреляции)
- numpy (числовые вычисления, линейная алгебра)
- scikit-learn (Isolation Forest для детекции аномалий)
- structlog (структурированное логирование)

**Frontend:**
- Svelte 5 + runes (reactive state management)
- Tailwind CSS (utility-first styling)
- Chart.js + chartjs-plugin-zoom (интерактивные графики)
- svelte-chartjs (Chart.js wrapper)
- ky (HTTP client)
- lucide-svelte (иконки)
- marked (Markdown рендеринг)

**База данных:**
- PostgreSQL + TimescaleDB (time-series данные)
- Таблицы: `tags_value`, `alarm_events_history`, `anomaly_events`

---

## 2. Архитектура системы

### 2.1 Модульная структура

Система построена на основе **Module Registry** с автообнаружением модулей:

```
backend/
├── main.py                      # FastAPI app + middleware
├── api/routes/                  # HTTP endpoints
├── core/
│   ├── module_registry.py       # Автообнаружение модулей
│   ├── tool_executor.py         # Dispatch tool calls
│   ├── db.py                    # asyncpg pool
│   ├── logger.py                # Файловое логирование
│   └── llm/                     # LLM провайдеры
├── modules/                     # Бизнес-модули
│   ├── health/                  # Детерминированный анализ здоровья
│   ├── deep_analysis/           # Глубокий анализ (DDA)
│   ├── analytics/               # Тренды, прогнозы, impact scoring
│   ├── energy_electricity/      # Учёт электроэнергии
│   ├── energy_water/            # Учёт воды
│   ├── energy_heat/             # Учёт тепла
│   ├── logs/                    # Анализ системных логов
│   └── hello/                   # Базовые ответы
├── data/                        # Конфигурационные файлы
└── config/                      # Настройки приложения
```

### 2.2 Основные модули

| Модуль | Назначение | Тип |
|--------|-----------|-----|
| **health** | Детерминированный анализ здоровья системы (alarms, environmental, equipment) | Det + LLM |
| **deep_analysis** | Глубокий анализ: аномалии, сезонность, корреляции, A/B сравнения | Det |
| **analytics** | Тренды, прогнозы, impact scoring | Det + LLM |
| **energy_electricity** | Расчёт стоимости электроэнергии по тегам ЛЭРС | Det |
| **energy_water** | Учёт потребления воды (инфраструктура) | Det |
| **energy_heat** | Учёт потребления тепла (инфраструктура) | Det |
| **logs** | Анализ системных логов через AI tool calling | LLM |
| **hello** | Базовые ответы на приветствия | Text |

*Det = Детерминированный, LLM = AI-генерация*

---

## 3. Ключевые возможности

### 3.1 Мониторинг здоровья системы
- **Индекс здоровья системы** — композитная оценка (0-100) с детализацией расчёта
- **Индекс жизнеобеспечения** — параметры среды (CO2, температура, влажность, давление, VOC)
- **Журнал аварий** — приоритеты HIGH/MEDIUM/LOW с детализацией и drilldown
- **Детекция битых/офлайн/дребезжащих/залипших датчиков** — автоматическая диагностика оборудования

### 3.2 Глубокий анализ данных (Deep Data Analysis)
- **Детекция аномалий** — три алгоритма (Isolation Forest, Z-score, IQR) с типизацией (spike/dip/drift/noise)
- **Сезонный анализ (FFT)** — автодетект доминирующих периодов через Fast Fourier Transform
- **Типичные паттерны** — извлечение суточных/недельных профилей поведения
- **Корреляционный анализ** — Pearson correlation matrix для multi-tag сравнений
- **Scatter plots** — визуализация попарных зависимостей с линией регрессии
- **Тепловая карта корреляций** — интерактивная визуализация связей между параметрами
- **A/B анализ** — статистическое сравнение двух периодов или оборудования (Welch's t-test, Cohen's d)

### 3.3 Аналитика и прогнозы
- **Тренд-анализ** — линейная регрессия с slope_per_day и R²
- **Прогнозирование** — экстраполяция трендов на 7/30/90/365 дней
- **Корреляции параметров** — Pearson + временной лаг ±24 часа между метриками
- **Impact Score** — ранжирование проблем по комплексной оценке

### 3.4 Энергоучёт
- **Расчёт стоимости ресурсов** — электричество, вода, тепло (текущий и прошлый месяц)
- **Интервальные тарифы** — автоматический выбор тарифа по дате
- **Интеграция с ЛЭРС** — consumption через теги счётчиков

### 3.5 AI-функции
- **Системные логи** — AI-анализ через tool calling (YandexGPT 5.1)
- **Естественный язык** — задавайте вопросы о системе в чате
- **LLM-интерпретация** — человекочитаемые отчёты по результатам DDA
- **Tool calling** — вызов функций анализа из диалога

---

## 4. Приоритеты дальнейшей разработки

### 4.1 Приоритет 1: Ролевая модель (с отсечением функционала)

**Цель:** Внедрение системы разграничения прав доступа с фильтрацией функциональности на уровне UI и API.

#### Требования:
1. **Определение ролей:**
   - `admin` — полный доступ ко всем функциям системы
   - `engineer` — доступ к аналитике, настройкам, конфигурации
   - `operator` — базовый мониторинг, просмотр health, работа с чатом
   - `boss` — только дашборды, отчёты, энергоучёт (без деталей)

2. **Отсечение функционала:**
   - Скрытие UI-компонентов в зависимости от роли
   - Блокировка API endpoints на уровне middleware
   - Фильтрация данных в ответах (например, boss не видит сырые данные датчиков)

3. **Хранение пользователей:**
   - Зашифрованное хранилище `users.enc` (AES-256)
   - Интеграция с существующей системой аутентификации
   - Сессионные токены с claims ролей

4. **Точки интеграции:**
   - Backend: middleware в `main.py` для проверки ролей
   - Frontend: HOC/wrapper для условного рендеринга компонентов
   - Database: таблица `users` с полями `role`, `permissions`

#### Оценка сложности: Высокая
#### Зависимости: Отсутствуют
#### Риски: Требуется рефакторинг текущей архитектуры безопасности

---

### 4.2 Приоритет 2: RAG (Retrieval-Augmented Generation) механизм

**Цель:** Создание базы знаний по объекту с возможностью семантического поиска и генерации ответов на основе контекста.

#### Требования:
1. **База знаний:**
   - Хранение записей о событиях объекта (аварии, обслуживания, модернизации)
   - Пример: "10.08.2026 произошло аварийное отключение оборудования на 2м этаже"
   - Метаданные: дата, тип события, локализация, описание, теги

2. **Логирование операций:**
   - Audit log всех CRUD-операций с записями БЗ
   - Поля: `created_at`, `created_by`, `updated_at`, `updated_by`, `action_type`
   - Версионирование записей (хранение истории изменений)

3. **Векторный поиск:**
   - Embedding записей через YandexGPT или альтернативу
   - Векторное хранилище (pgvector или отдельное решение)
   - Семантический поиск по запросу пользователя

4. **Интеграция с чатом:**
   - Расширение system prompt контекстом из БЗ
   - Tool calling для поиска релевантных записей
   - Цитирование источников в ответах AI

5. **UI компоненты:**
   - Интерфейс управления БЗ (CRUD)
   - Поиск по базе знаний
   - Timeline событий объекта
   - Фильтры по типу/дате/локации

#### Оценка сложности: Средняя
#### Зависимости: Отсутствуют
#### Риски: Требуется выбор векторного хранилища

---

### 4.3 Приоритет 3: LoRA (Low-Rank Adaptation) механизм

**Цель:** Адаптация языковой модели под специфику объекта без полного дообучения.

#### Требования:
1. **Сбор данных для fine-tuning:**
   - Экспорт диалогов из chat history
   - Разметка качественных ответов
   - Формирование dataset в формате instruction-response

2. **Генерация LoRA адаптеров:**
   - Интеграция с YandexGPT API (если поддерживается)
   - Или локальное дообучение через Ollama/Llama.cpp
   - Версионирование адаптеров по объектам

3. **Применение адаптеров:**
   - Динамическая загрузка LoRA weights при запросе
   - Привязка адаптеров к объектам/зданиям
   - Fallback на базовую модель при отсутствии адаптера

4. **Оценка качества:**
   - A/B тестирование ответов с LoRA и без
   - Метрики: relevance, accuracy, user satisfaction
   - Механизм обратной связи от операторов

#### Оценка сложности: Очень высокая
#### Зависимости: Поддержка LoRA со стороны LLM провайдера
#### Риски: Ограниченная поддержка LoRA облачными провайдерами

---

## 5. Технические детали реализации

### 5.1 Ролевая модель — схема БД

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'engineer', 'operator', 'boss')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE role_permissions (
    role VARCHAR(20) PRIMARY KEY,
    can_configure BOOLEAN DEFAULT FALSE,
    can_view_analytics BOOLEAN DEFAULT TRUE,
    can_manage_energy BOOLEAN DEFAULT FALSE,
    can_access_raw_data BOOLEAN DEFAULT FALSE,
    can_manage_users BOOLEAN DEFAULT FALSE,
    can_view_audit_logs BOOLEAN DEFAULT FALSE
);

CREATE TABLE audit_log (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    action VARCHAR(50) NOT NULL,
    resource VARCHAR(100),
    resource_id UUID,
    old_value JSONB,
    new_value JSONB,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);
```

### 5.2 RAG — схема БД

```sql
CREATE TABLE knowledge_base_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    event_date DATE NOT NULL,
    event_type VARCHAR(50) NOT NULL, -- 'emergency', 'maintenance', 'upgrade', 'inspection'
    location VARCHAR(100), -- '2 этаж', 'Зона 1', etc.
    tags TEXT[], -- массив тегов для фильтрации
    embedding VECTOR(1024), -- YandexGPT embedding
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE knowledge_base_versions (
    id BIGSERIAL PRIMARY KEY,
    record_id UUID REFERENCES knowledge_base_records(id),
    content TEXT NOT NULL,
    version INT NOT NULL,
    changed_by UUID REFERENCES users(id),
    changed_at TIMESTAMPTZ DEFAULT NOW(),
    change_reason TEXT
);

-- Индекс для векторного поиска (при использовании pgvector)
CREATE INDEX kb_records_embedding_idx ON knowledge_base_records USING ivfflat (embedding vector_cosine_ops);
```

### 5.3 API Endpoints для новых функций

```yaml
# Ролевая модель
POST   /api/v1/auth/login          # Аутентификация
POST   /api/v1/auth/logout         # Выход
GET    /api/v1/users/me            # Текущий пользователь
GET    /api/v1/users               # Список пользователей (admin only)
POST   /api/v1/users               # Создание пользователя (admin only)
PUT    /api/v1/users/{id}          # Обновление пользователя
DELETE /api/v1/users/{id}          # Удаление пользователя

# RAG - База знаний
GET    /api/v1/knowledge-base      # Поиск записей (semantic search)
POST   /api/v1/knowledge-base      # Создание записи
GET    /api/v1/knowledge-base/{id} # Получение записи
PUT    /api/v1/knowledge-base/{id} # Обновление записи
DELETE /api/v1/knowledge-base/{id} # Удаление записи
GET    /api/v1/knowledge-base/{id}/versions  # История версий

# LoRA - Адаптеры
GET    /api/v1/lora/adapters       # Список доступных адаптеров
POST   /api/v1/lora/adapters/train # Запуск обучения адаптера
GET    /api/v1/lora/adapters/{id}  # Статус адаптера
DELETE /api/v1/lora/adapters/{id}  # Удаление адаптера
```

---

## 6. Roadmap

### Q3 2026 (Июль-Сентябрь)
- [ ] **Ролевая модель** (Приоритет 1)
  - [ ] Схема БД и миграции
  - [ ] Backend middleware для авторизации
  - [ ] Frontend HOC для условного рендеринга
  - [ ] Шифрование хранилища пользователей
  - [ ] Audit log для всех критических операций

- [ ] **RAG механизм** (Приоритет 2)
  - [ ] Модель данных для БЗ
  - [ ] CRUD API для записей
  - [ ] Векторный поиск (pgvector интеграция)
  - [ ] UI управления БЗ
  - [ ] Интеграция с chat (context retrieval)

### Q4 2026 (Октябрь-Декабрь)
- [ ] **LoRA механизм** (Приоритет 3)
  - [ ] Исследование поддержки LoRA провайдером
  - [ ] Сбор dataset из chat history
  - [ ] Пайплайн дообучения
  - [ ] A/B тестирование качества

- [ ] **Улучшения RAG**
  - [ ] Мультиязычная поддержка
  - [ ] Извлечение знаний из документов (PDF, DOCX)
  - [ ] Автоматическое тегирование записей

### 2027 (Долгосрочно)
- [ ] Multi-tenancy (несколько зданий в одной системе)
- [ ] Mobile app (React Native)
- [ ] Boss dashboard — отдельный экран для руководства
- [ ] Экспорт отчётов в PDF/Excel
- [ ] WebSocket для real-time updates

---

## 7. Известные проблемы (Known Issues)

1. **Health модуль:** если SCADA не пишет данные последние 24 часа, отображаются нули (данные есть, но старые)
2. **Производительность DDA:** анализ 90+ дней данных может занимать до 90 секунд
3. **LLM fallback:** при недоступности YandexGPT инсайты менее качественные

---

## 8. Контакты и поддержка

**Разработчик:** Усков Сергей Евгеньевич  
**Лицензия:** Proprietary. Все права защищены.

---

## Приложение A: Примеры использования

### A.1 RAG - Добавление записи об аварии

```bash
curl -X POST http://localhost:8081/api/v1/knowledge-base \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Аварийное отключение оборудования",
    "content": "Произошло аварийное отключение вентиляционной системы на 2м этаже здания. Причина: короткое замыкание в электрощите. Оборудование восстановлено через 3 часа.",
    "event_date": "2026-08-10",
    "event_type": "emergency",
    "location": "2 этаж",
    "tags": ["вентиляция", "электрика", "авария"]
  }'
```

### A.2 RAG - Семантический поиск

```bash
curl "http://localhost:8081/api/v1/knowledge-base?q=отключение%20вентиляции&limit=5" \
  -H "Authorization: Bearer <token>"
```

**Response:**
```json
{
  "results": [
    {
      "id": "uuid-123",
      "title": "Аварийное отключение оборудования",
      "content": "Произошло аварийное отключение вентиляционной системы...",
      "event_date": "2026-08-10",
      "similarity_score": 0.89
    }
  ]
}
```

### A.3 Chat с RAG контекстом

```text
User: "Какие были аварии с вентиляцией?"

AI: (выполняет semantic search в БЗ)
    "На основе записей базы знаний:
    
    1. **10.08.2026** — Аварийное отключение вентиляционной системы на 2м этаже. 
       Причина: короткое замыкание в электрощите. Время восстановления: 3 часа.
       
     Рекомендую проверить состояние электрощитов на всех этажах."
```

---

*Документ создан на основе анализа документации в `/backend/docs/`*
