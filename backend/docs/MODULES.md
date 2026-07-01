# Модули SCADA.AI

Система состоит из независимых модулей, каждый из которых предоставляет свои tools для LLM и endpoints для API.

## Обзор модулей

| Модуль | Назначение | Tools | Виджеты |
|--------|-----------|-------|---------|
| health | Анализ здоровья системы | get_health_report | health_score, life_support_card, environmental_panel, alarms_panel |
| energy_electricity | Расчёт стоимости электричества | calculate_electricity_cost, get_electricity_consumption | energy_cost_card |
| energy_water | Учёт потребления воды | calculate_water_cost, get_water_consumption | — |
| energy_heat | Учёт потребления тепла | calculate_heat_cost, get_heat_consumption | — |
| hello | Базовые ответы | — | — |
| logs | Анализ системных логов | analyze_logs | — |
| analytics | Тренд-анализ, прогнозы, корреляции | (через /chat) | analytics_panel |
| **deep_analysis** | **Глубокий анализ SCADA-данных** | **(через API)** | **dda_panel** |

---

## Модуль deep_analysis

**Назначение**: Полноценный движок глубокого анализа SCADA-данных с детекцией аномалий, анализом сезонных паттернов, корреляционным анализом и статистическим A/B сравнением.

### Архитектура

```text
modules/deep_analysis/
├── __init__.py                    # Регистрация модуля
├── api.py                         # FastAPI endpoints
├── core.py                        # Оркестрация анализа
└── analyzers/
    ├── anomaly_detection.py       # Isolation Forest, Z-score, IQR
    ├── correlation.py             # Pearson correlation matrix
    ├── seasonal.py                # FFT, seasonal pattern extraction
    ├── stats.py                   # compute_basic_stats, downsampling
    └── ab.py                      # A/B анализ (Welch's t-test, Cohen's d)
```

### Основные возможности

#### 1. Детекция аномалий
Три алгоритма работают параллельно, результаты объединяются с типизацией:

| Алгоритм | Назначение | Параметры |
|----------|-----------|-----------|
| **Isolation Forest** | Многомерные аномалии | contamination=0.05 |
| **Z-score** | Выбросы по амплитуде | threshold=3σ |
| **IQR** | Робастная детекция | Q1-1.5×IQR, Q3+1.5×IQR |

**Типы аномалий**:
- `spike` — резкий пик (1-2 точки)
- `dip` — резкое падение
- `drift` — плавный уход от нормы
- `noise` — шумовая аномалия (серия точек)

#### 2. Сезонный анализ (FFT)
**Автодетект доминирующих периодов** через Fast Fourier Transform:

- Декомпозиция сигнала на частотные компоненты
- Выделение пиков в спектре мощности (PSD)
- Определение основного периода (обычно 288 точек = 24 часа при 5-мин интервале)

**Извлечение типичного паттерна**:
- Фолдинг данных по найденному периоду
- Усреднение по фазам → эталонный суточный профиль
- Вычисление амплитуды, min/max, размаха

**Интерпретация периодов**:
- 288 точек ≈ 24 часа (суточный)
- 2016 точек ≈ 7 дней (недельный)
- 8640 точек ≈ 30 дней (месячный)

#### 3. Корреляционный анализ (Multi-Tag)
**Pearson correlation matrix** для всех выбранных тегов:
- Матрица попарных корреляций
- Тепловая карта с цветовой кодировкой
- Scatter plot с линией регрессии для выбранных пар
- Временной лаг ±24 часа для поиска запаздывающих зависимостей

**Интерпретация**:
- |r| > 0.9 — очень сильная корреляция
- 0.7 < |r| ≤ 0.9 — сильная
- 0.5 < |r| ≤ 0.7 — умеренная
- |r| ≤ 0.5 — слабая

#### 4. A/B Анализ (v3.2.9)
Статистическое сравнение двух snapshots (периодов или оборудования).

**Режимы**:
- **Before/After**: один тег, разные периоды (оценка эффекта изменений)
- **Equipment Comparison**: два тега, один период (сравнение оборудования)

**Математическая основа**:

```text
Welch's t-test:    t = (μ_B - μ_A) / √(σ²_A/n_A + σ²_B/n_B)
Cohen's d:         d = (μ_B - μ_A) / σ_pooled
Pattern correlation: Pearson на усреднённых суточных паттернах
```

**Генерация вердикта**:
- **Severity**: low / medium / high
- **Key findings**: автоматический список наблюдений
- **Recommendations**: действия на основе severity

**Защита от edge cases**:
- Минимальный размер выборки: 10 точек
- Фильтрация NaN/Inf перед анализом
- Обработка константных данных (σ² = 0)
- Санитизация JSON (NaN → null)

### API Endpoints

#### `POST /api/v1/deep_analysis/analyze`
Основной endpoint глубокого анализа.

**Request**:
```json
{
  "tags": ["R001-Temperature"],
  "period": "30 days",
  "params": {
    "anomaly_detection": true,
    "seasonal_analysis": true,
    "correlation_matrix": true
  }
}
```

**Response**: statistics, anomalies, seasonality, correlations, visualizations.

#### `POST /api/v1/deep_analysis/ab`
A/B анализ двух snapshots.

**Request**:
```json
{
  "snapshot_a": {"tag": "R001-T", "start": "2026-01-01", "end": "2026-03-31"},
  "snapshot_b": {"tag": "R001-T", "start": "2026-04-01", "end": "2026-06-30"}
}
```

**Response**: mode, statistics (a/b/delta), significance (p-value, Cohen's d), pattern_comparison, verdict.

#### `GET /api/v1/deep_analysis/tags`
Список доступных тегов для анализа.

### Frontend компоненты

| Компонент | Назначение |
|-----------|-----------|
| **DeepAnalysisControls** | Выбор тегов, периода, запуск анализа |
| **DeepAnalysisResults** | 4 вкладки: Обзор, Корреляции, Таблица пар, Интерпретация |
| **ABComparisonModal** | Модалка A/B анализа с выбором режима/периодов |
| **ChartModal** | Полноэкранный просмотр графиков с zoom/pan |
| **DDAInterpretation** | LLM-интерпретация результатов через YandexGPT |

### Технические детали

**Зависимости**:
- Backend: `scipy.stats`, `numpy.fft`, `sklearn.ensemble.IsolationForest`
- Frontend: `chart.js`, `chartjs-plugin-zoom`, `svelte-chartjs`

**Производительность**:
- Downsampling до 500 точек для графиков
- FFT: O(n log n)
- T-test: O(n)
- Типичное время анализа 30 дней данных: <500ms

**Интеграция с LLM**:
- Результаты анализа автоматически передаются в DDAInterpretation
- LLM получает структурированные данные (статистика, аномалии, паттерны, A/B вердикт)
- Генерирует человекочитаемую интерпретацию на русском языке

---

## Модуль analytics

**Назначение**: Полноценный движок аналитики SCADA-системы с трендами, прогнозами и визуализацией.

### Архитектура

```text
modules/analytics/
├── __init__.py              # Регистрация модуля
├── collectors/
│   └── history.py           # Сбор данных из TimescaleDB
├── analyzers/
│   ├── trends.py            # Линейная регрессия, R², slope
│   ├── correlations.py      # Pearson + временной лаг
│   └── aggregators.py       # Ранжирование проблем
├── llm/
│   └── analyzer.py          # YandexGPT + deterministic fallback
└── norms.py                 # Нормативные диапазоны
```

### Ключевые метрики

- **Тренды**: slope_per_day, r_squared, direction (rising/falling/stable)
- **Аномалии**: Z-score > 3σ от среднего
- **Корреляции**: Pearson (r ∈ [-1, 1]) с временным лагом ±24 часа
- **Impact Score**: deviation + trend + anomalies + outliers
- **Прогнозы**: экстраполяция тренда на 7/30/90/365 дней

---

## Модуль health

**Назначение**: Детерминированный анализ состояния системы на основе исторических данных из PostgreSQL.

### Архитектура

```text
modules/health/
├── __init__.py              # Регистрация модуля
├── prompts.py               # HEALTH_SYSTEM_PROMPT для LLM
├── data_collectors.py       # SQL-запросы к БД
├── analysis.py              # Детерминированные формулы
├── renderers.py             # Генерация narrative/voice/visual
└── tools.py                 # Tools для tool calling
```

### Индекс здоровья системы (health_score)

**Композитная формула**:
```text
score = 0.40 × Аварии + 0.35 × Среда + 0.25 × Оборудование
```

#### Под-индексы:

**1. Индекс аварий (alarms)**
```text
score = 100 - min(high × 15, 50) - min(medium × 4, 25) - min(low × 0.5, 10)
```

Штрафы:
- High авария: -15 (макс -50)
- Medium авария: -4 (макс -25)
- Low авария: -0.5 (макс -10)

**2. Индекс среды (environmental)**

Веса: CO2 (30%), Температура (25%), VOC (20%), Влажность (15%), Давление (10%)

Статусы: OK=100, WARNING=55, CRITICAL=15

Нормативы:
- Температура: оптимум 18-24°C, критично <10 или >35
- Влажность: оптимум 30-60%, критично <20 или >80
- CO2: оптимум 400-800 ppm, критично >2000
- Давление: оптимум 720-780 мм рт.ст.
- VOC: оптимум <220 ppb, критично >660 ppb

**3. Индекс оборудования (equipment)**

Штрафы:
- Битый датчик: до -40
- Офлайн тег: до -30
- Дребезжащий тег: до -15
- Залипший тег: до -10

### Индекс жизнеобеспечения (life_support)

Отдельный индекс для параметров среды, ВСЕГДА вычисляется даже если нет данных.

Статусы: ≥85=EXCELLENT, 60-84=GOOD, 30-59=WARNING, <30=CRITICAL

### Виджеты

- **health_score** — круговая диаграмма композитного индекса (0-100) + детализация расчёта
- **life_support_card** — индекс жизнеобеспечения + таблица параметров с весами
- **environmental_panel** — карточки 5 параметров среды с drilldown
- **alarms_panel** — сводка аварий по приоритетам + журнал с фильтрами

---

## Модули энергоучёта

### energy_electricity

**Назначение**: Расчёт стоимости электроэнергии на основе тегов ЛЭРС и интервальных тарифов.

**Tools**:
- `get_electricity_consumption()` — потребление за текущий/прошлый месяц (кВт·ч)
- `calculate_electricity_cost()` — стоимость с учётом тарифов (₽)

**Данные**:
- Теги ЛЭРС: `LERS.electricity meter current month N`
- Тарифы: `data/tariffs.json` (интервальные)
- Конфиг: `data/energy_config.json`

**Формула**: `Стоимость = Σ(Потребление × Тариф на дату)`

### energy_water, energy_heat

**Назначение**: Подготовка инфраструктуры для учёта воды и тепла. Сейчас — заглушки.

### Виджет energy_cost_card

Компактный виджет со сводкой по всем ресурсам:
- Большая цифра: прошлый месяц (полные данные)
- Мелким текстом: текущий месяц (неполный)
- Кнопка (i): формула расчёта + таблица тарифов

---

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

---

## Модуль hello

**Назначение**: Базовые ответы на приветствия и общие вопросы.

**Примеры**:
- "Привет" → "Здравствуйте! Чем могу помочь?"
- "Как дела?" → "Система работает нормально. Хотите посмотреть отчёт?"

---

## Модуль logs

**Назначение**: Анализ системных логов через AI tool calling.

### Tools

#### analyze_logs

```python
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

### Flow

1. Frontend вызывает `POST /chat` с сообщением "проанализируй логи"
2. `chat.py` определяет что это logs-запрос
3. LLM вызывает tool `analyze_logs`
4. Tool читает логи из `core.logger`
5. LLM анализирует логи и возвращает текст
6. Frontend показывает анализ в NarrativePanel

---

## Управление модулями

### Включение/выключение

Модули включаются через переменную окружения `ENABLED_MODULES`:

```bash
# .env
ENABLED_MODULES=hello,health,logs,energy_electricity,energy_water,energy_heat,analytics,deep_analysis
```

Изменение через UI: Конфигуратор → Модули → переключатель.

**Важно**: После изменения требуется перезапуск backend.

### Добавление нового модуля

1. Создать папку `modules/my_module/`
2. Создать `__init__.py` (можно пустой)
3. Создать `config.yaml` с metadata
4. Создать `tools.py` с `TOOLS = [...]`
5. Создать `prompts.py` с системными промптами
6. Добавить `my_module` в `ENABLED_MODULES`
7. Перезапустить backend

**Пример config.yaml**:

```yaml
name: my_module
version: 1.0.0
description: Описание модуля
enabled: true
```

**Пример tools.py**:

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