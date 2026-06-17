# SCADA.AI Analytics Engine — Техническая документация

**Версия:** 3.2.0  
**Модуль:** `backend/modules/analytics/`  
**Endpoint:** `POST /chat` (триггер "аналитика") · `GET /analytics/report`

---

## 1. Обзор

Analytics Engine — автономный модуль анализа параметров SCADA-системы. Выполняет:

- **Сбор** исторических данных (hourly/daily/raw)
- **Тренд-анализ** (линейная регрессия, R², slope)
- **Поиск корреляций** (Pearson между параметрами)
- **Ранжирование проблем** (top issues с impact score)
- **LLM-инсайты** (YandexGPT summary + рекомендации)
- **Прогнозирование** (экстраполяция тренда + MA-7)
- **Визуализация** (Chart.js с zoom/pan/download)

---

## 2. Архитектура

```
backend/modules/analytics/
├── collectors/
│   └── history.py              # Сбор данных из TimescaleDB
├── analyzers/
│   ├── trends.py               # Тренд-анализ (линейная регрессия)
│   ├── correlations.py         # Матрица корреляций
│   └── aggregators.py          # Ранжирование проблем
├── llm/
│   └── analyzer.py             # LLM insights (YandexGPT + fallback)
└── norms.py                    # Нормативные диапазоны параметров
```

**Поток данных:**

```
TimescaleDB
    ↓
collect_history(days, params, aggregation)
    ↓
{params: {temperature: {data_points, total_raw_count, ...}, ...}}
    ↓
analyze_trends() + find_correlations() + rank_issues()
    ↓
{trends, correlations, top_issues}
    ↓
LLM.analyze() → {summary, insights, recommendations, forecast}
    ↓
/analytics/report → frontend (AnalyticsPanel)
```

---

## 3. Сбор данных (collectors/history.py)

### 3.1. Источники данных

Данные берутся из **TimescaleDB** (гипертаблицы метрик SCADA):

| Параметр | Единицы | Частота измерений |
|----------|---------|-------------------|
| temperature | °C | 1 мин |
| humidity | % | 1 мин |
| co2 | ppm | 1 мин |
| pressure | мм рт. ст. | 1 мин |
| voc | мг/м³ | 1 мин |

### 3.2. Агрегации

```
aggregation = "auto"  # выбирается автоматически по периоду:
  - period ≤ 7 дней   → hourly  (часовые бакеты)
  - period 7-90 дней  → daily   (дневные бакеты)
  - period > 90 дней  → daily + downsampling
```

**Бакет (bucket):** агрегированное значение за интервал времени.

```
data_point = {
    "bucket_start": "2026-06-16T10:00:00",  # начало интервала
    "avg": 24.35,                            # среднее за интервал
    "min": 23.8,                             # минимум
    "max": 25.1,                             # максимум
    "count": 60                              # кол-во сырых измерений
}
```

### 3.3. Выбросы (outliers)

Обнаруживаются через **IQR-метод** (межквартильный размах):

```
Q1 = 25-й перцентиль
Q3 = 75-й перцентиль
IQR = Q3 - Q1
lower_fence = Q1 - 1.5 * IQR
upper_fence = Q3 + 1.5 * IQR

outlier = value < lower_fence OR value > upper_fence
```

---

## 4. Тренд-анализ (analyzers/trends.py)

### 4.1. Линейная регрессия

Для каждого параметра строится модель `y = slope * days + intercept`:

```
n = len(values)
x_mean = mean(days_from_start)
y_mean = mean(values)

numerator = Σ[(x_i - x_mean) * (y_i - y_mean)]
denominator = Σ[(x_i - x_mean)²]

slope_per_day = numerator / denominator   # изменение за день
intercept = y_mean - slope_per_day * x_mean
```

### 4.2. Коэффициент детерминации R²

Показывает насколько хорошо модель объясняет данные:

```
SS_res = Σ[(y_i - y_pred_i)²]    # сумма квадратов остатков
SS_tot = Σ[(y_i - y_mean)²]      # общая сумма квадратов

R² = 1 - (SS_res / SS_tot)
```

**Интерпретация:**
- `R² > 0.7` — сильный тренд (модель объясняет >70% вариации)
- `R² 0.3-0.7` — умеренный тренд
- `R² < 0.3` — слабый тренд (помечается как "Тренд (слабый)")

### 4.3. Направление тренда

```
if |slope_per_day| < 0.01:
    direction = "stable"
elif slope_per_day > 0:
    direction = "rising"
else:
    direction = "falling"
```

### 4.4. Аномалии (Z-score)

Обнаруживаются через **Z-score** (отклонение в стандартных отклонениях):

```
z = |value - avg| / stdev
anomaly = z > 3    # более 3σ от среднего

anomaly_rate = anomalies / len(values)
```

### 4.5. Raw Data для графиков

Адаптивный downsampling для производительности:

```
MAX_POINTS = 500

if len(data_points) ≤ 500:
    raw_data = все точки
else:
    # берём каждую N-ю точку
    step = len(data_points) / MAX_POINTS
    raw_data = [data_points[int(i*step)] for i in range(MAX_POINTS)]
    raw_data.append(data_points[-1])  # ВСЕГДА включаем последнюю
```

---

## 5. Корреляции (analyzers/correlations.py)

### 5.1. Коэффициент Пирсона

Считаем попарные корреляции между параметрами:

```
r = Σ[(x_i - x_mean)(y_i - y_mean)] / √[Σ(x_i - x_mean)² * Σ(y_i - y_mean)²]

Интерпретация:
  r ∈ [-1, 1]
  |r| > 0.7  → сильная корреляция
  |r| ∈ [0.5, 0.7] → умеренная
  |r| < 0.5  → слабая
```

### 5.2. Временной лаг

Для каждой пары параметров ищем лаг с максимальной корреляцией (±24 часа):

```
for lag in range(-24, 25):  # часы
    r = pearson(param1, shift(param2, lag))
    if |r| > best_r:
        best_r, best_lag = r, lag
```

**Результат:**
```
{
    "params": ["temperature", "humidity"],
    "correlation": -0.72,
    "lag_hours": 2,      # влажность реагирует на температуру через 2 часа
    "strength": "strong",
    "direction": "negative"
}
```

---

## 6. Ранжирование проблем (analyzers/aggregators.py)

### 6.1. Impact Score

Каждая проблема получает **компонентный score**:

```
impact = deviation + trend + anomalies + outliers

Где:
  deviation  = штраф за отклонение от оптимального диапазона
  trend      = штраф за тренд к критическому уровню
  anomalies  = штраф за % аномальных значений
  outliers   = штраф за битые датчики
```

### 6.2. Компоненты impact

#### Deviation (отклонение от нормы)

```
if avg < opt_min or avg > opt_max:
    deviation = -weight * |avg - closest_boundary| / range
else:
    deviation = 0
```

#### Trend (тренд к критическому)

```
if slope_per_day != 0:
    days_to_critical = |critical_boundary - avg| / |slope_per_day|
    trend = -weight * (30 / days_to_critical)  # ускоряется при приближении
else:
    trend = 0
```

#### Anomalies (аномалии)

```
anomalies = -weight * (anomaly_rate * 100)
# 1% аномалий → -1 балл
```

#### Outliers (битые датчики)

```
outliers = -weight * (outliers_count / total_raw_count * 100)
# 10% битых → -1 балл
```

### 6.3. Severity classification

```
if |impact| > 10:     severity = "critical"
elif |impact| > 5:    severity = "high"
elif |impact| > 2:    severity = "medium"
else:                 severity = "low"
```

---

## 7. LLM Insights (llm/analyzer.py)

### 7.1. Prompt structure

```
System: Ты — AI-аналитик SCADA-системы. Анализируй тренды и проблемы.
        Отвечай на русском, структурированно.

User:
  trends: {temperature: {slope_per_day: 0.7, r_squared: 0.38, ...}, ...}
  correlations: [{params: [...], correlation: -0.72, ...}, ...]
  top_issues: [{param: "voc", impact: -5.2, reason: "...", ...}, ...]

Expected output (JSON):
  {
    "summary": "краткое резюме",
    "insights": ["инсайт 1", "инсайт 2", ...],
    "recommendations": [
      {"action": "...", "impact": "...", "effort": "low|medium|high", 
       "priority": "critical|high|medium|low"},
      ...
    ],
    "forecast": {
      "7_days": "...",
      "30_days": "...",
      "risk": "high|medium|low"
    }
  }
```

### 7.2. Deterministic fallback

При недоступности LLM генерируем инсайты по правилам:

```
if direction == "rising" and r_squared > 0.3:
    insights.append(f"{param} растёт ({slope}/день, R²={r²})")
elif direction == "falling" and r_squared > 0.3:
    insights.append(f"{param} падает ({slope}/день, R²={r²})")

# Рекомендации из top_issues
for issue in top_issues[:5]:
    if "broken sensors" in reason:
        rec = "Замените или откалибруйте датчики"
    elif "Rising" in reason:
        rec = "Проверьте систему управления"
```

---

## 8. Прогнозирование

### 8.1. Линейная экстраполяция

Для периодов **7 и 30 дней** — используется LLM forecast.

Для периодов **90 и 365 дней** — экстраполяция:

```
projected_value = avg + slope_per_day * days

Пример (temperature, slope = 0.7/день):
  - Через 90 дней:  24.5 + 0.7 * 90  = 87.5°C (CRITICAL)
  - Через 365 дней: 24.5 + 0.7 * 365 = 279.5°C (физически невозможно)
```

### 8.2. Days to Critical

```
days_to_critical = |critical_boundary - current_avg| / |slope_per_day|

Пример:
  avg = 24.5°C, crit_max = 35°C, slope = 0.7/день
  days_to_critical = (35 - 24.5) / 0.7 = 15 дней
```

### 8.3. Визуальный прогноз (MA-7 + extrapolation)

На графике показываются 4 линии:

```
1. Данные (сплошная + fill)       — реальные измерения
2. Тренд (пунктир серая)          — линейная регрессия
3. MA-7 (сплошная серая)          — 7-дневная скользящая средняя
4. Прогноз (пунктир оранжевая)    — экстраполяция на 30% вперёд
```

**MA-7 (Moving Average 7):**

```
MA-7[i] = mean(values[i-6 : i+1])  # среднее за 7 последних точек

Применение:
  - Сглаживает шум и выбросы
  - Показывает реальный тренд на "шумных" данных
  - Начинается с 7-й точки (первые 6 = null)
```

---

## 9. Health Score Impact

### 9.1. Веса параметров

```
param_weights = {
    "temperature": 0.25,   # 25% в общем health score
    "humidity":    0.20,   # 20%
    "co2":         0.20,   # 20%
    "pressure":    0.10,   # 10%
    "voc":         0.25,   # 25%
}
```

### 9.2. Формула impact

```
impact[param] = (deviation + trend + anomalies + outliers) * weight

Пример для VOC:
  deviation  = -0.07
  trend      = -10.35
  anomalies  = 0.0
  outliers   = 0.0
  weight     = 0.25
  
  impact = (-0.07 - 10.35) * 0.25 = -2.6 баллов
```

### 9.3. Агрегация в Health Score

```
health_score = base_score + Σ(impact[param] for all params)

base_score = 100 (максимум)
health_score ∈ [0, 100]

Шкала:
  ≥ 85 → Отлично
  60-84 → Хорошо
  30-59 → Внимание
  < 30 → Критично
```

---

## 10. Визуализация (TrendChart.svelte)

### 10.1. Chart.js + плагины

```
Библиотеки:
  - chart.js:4.x               — основная библиотека
  - svelte-chartjs:3.x          — обёртка для Svelte
  - chartjs-plugin-zoom:2.x     — zoom/pan для интерактивности
```

### 10.2. Фиксированные пределы оси Y

| Параметр | Min | Max | Единицы |
|----------|-----|-----|---------|
| temperature | 0 | 50 | °C |
| humidity | 0 | 100 | % |
| co2 | 300 | 2000 | ppm |
| pressure | 700 | 800 | мм рт. ст. |
| voc | 0 | 1 | мг/м³ |

Используется `suggestedMin`/`suggestedMax` — Chart.js масштабирует вокруг, но показывает все данные.

### 10.3. Цветовая палитра

```
Данные:
  temperature: #ef4444 (красный)
  humidity:    #3b82f6 (синий)
  co2:         #22c55e (зелёный)
  pressure:    #a855f7 (фиолетовый)
  voc:         #f59e0b (оранжевый)

Дополнительные линии:
  Тренд (R²≥0.1): #64748b (тёмно-серый) пунктир 5/5
  Тренд (R²<0.1): #9ca3af (светло-серый) пунктир 5/5
  MA-7:           #9ca3af (светло-серый) сплошная 2px
  Прогноз:        #f97316 (оранжево-красный) пунктир 3/3
```

### 10.4. Интерактивность

```
Zoom:
  - Колёсико мыши → масштаб по оси X
  - Кнопки +/- → zoom(1.2) / zoom(0.8)
  - Pinch (touch) → для мобильных

Pan:
  - Перетаскивание мышью → прокрутка по X

Reset:
  - Кнопка "сброс" → resetZoom()

Export:
  - Кнопка Download → chart.toBase64Image('image/png')
  - Имя файла: scada_{param}_{YYYY-MM-DD}.png
```

---

## 11. API Endpoints

### 11.1. GET /analytics/report

**Параметры:**
```
period: int (1-365)     — период анализа в днях
params: str             — "all" или список через запятую
aggregation: str        — "auto" | "hourly" | "daily" | "raw"
include_llm: bool       — true для LLM insights
```

**Ответ:**
```json
{
  "period_days": 30,
  "aggregation": "hourly",
  "collected_at": "2026-06-17T10:15:27",
  "trends": {
    "temperature": {
      "param": "temperature",
      "bucket_count": 164,
      "total_raw_count": 171845,
      "avg": 24.55,
      "min": 23.2,
      "max": 26.4,
      "stdev": 0.57,
      "slope_per_day": 0.0205,
      "r_squared": 0.005,
      "direction": "rising",
      "anomalies": 2,
      "anomaly_rate": 0.0122,
      "norms": {
        "opt_min": 18, "opt_max": 24,
        "crit_min": 10, "crit_max": 35
      },
      "raw_data": [
        {"timestamp": "2026-06-10T10:00:00", "value": 24.08},
        ...
      ]
    },
    ...
  },
  "correlations": [...],
  "top_issues": [
    {
      "param": "voc",
      "impact": -5.15,
      "reason": "Avg 0.6 outside optimal range, 75.7% broken sensors",
      "severity": "critical",
      "weight": 0.25,
      "days_to_critical": null,
      "components": {
        "deviation": -0.27,
        "trend": 0,
        "anomalies": -4.55,
        "outliers": -0.04
      }
    },
    ...
  ],
  "summary": "Главная проблема: VOC...",
  "insights": ["Параметр VOC имеет...", ...],
  "recommendations": [
    {
      "action": "Замените датчики VOC",
      "impact": "+5.2 баллов здоровья",
      "effort": "medium",
      "priority": "critical"
    },
    ...
  ],
  "forecast": {
    "7_days": "Температура повысится на 0.14°C",
    "30_days": "VOC достигнет критического уровня",
    "risk": "high"
  }
}
```

### 11.2. Триггер через /chat

```
POST /chat
{
  "message": "покажи аналитику",
  "session_id": "default"
}

Backend детектит ключевые слова:
  ANALYTICS_KEYWORDS = [
    "аналитик", "тренд", "прогноз",
    "рекомендац", "корреляц", "analytics"
  ]

Возвращает:
{
  "response": "summary от LLM",
  "status": "success",
  "visual": {
    "widgets": [
      {
        "type": "analytics_panel",
        "data": { ...полный отчёт... },
        "size": "wide"
      }
    ]
  }
}
```

---

## 12. Примеры использования

### 12.1. Базовый запрос

```bash
# Аналитика за последние 30 дней
curl "http://localhost:8081/analytics/report?period=30&params=all&include_llm=true"
```

### 12.2. Контрольные запросы

```bash
# Daily агрегация за 100 дней (без downsampling)
curl "http://localhost:8081/analytics/report?period=100&params=temperature,pressure&aggregation=daily&include_llm=false"

# Проверка конкретного параметра
curl "http://localhost:8081/analytics/report?period=7&params=temperature&include_llm=false"

# Длинный период (downsampling включится автоматически)
curl "http://localhost:8081/analytics/report?period=365&params=all&include_llm=false"
```

### 12.3. Чат-интерфейс

```
Пользователь: "покажи аналитику"
→ Открывается AnalyticsPanel со всеми 4 вкладками:
  1. Тренды — графики с линией тренда и прогнозом
  2. Проблемы — топ-5 с раскрытием деталей
  3. Рекомендации — топ-5 с обоснованием
  4. Прогноз — 7/30/90/365 дней
```

### 12.4. Переключение периода

```
В AnalyticsPanel:
  [7д] [30д] [90д] [365д]

При клике:
  1. period = выбранное значение
  2. fetchData(forceFetch=true)
  3. Backend пересчитывает с новым периодом
  4. Downsampling применяется автоматически
```

---

## 13. Производительность

### 13.1. Benchmarks (типичные значения)

| Период | Агрегация | Raw points | Время ответа |
|--------|-----------|------------|--------------|
| 7 дней | hourly | ~170K | ~30 сек |
| 30 дней | hourly | ~720K | ~60 сек |
| 90 дней | hourly + downsampling | ~500 | ~90 сек |
| 365 дней | daily + downsampling | ~365 | ~120 сек |

### 13.2. Оптимизации

- **Адаптивный downsampling** — ограничение до 500 точек в raw_data
- **Кеширование** — PostgreSQL prepared statements
- **Batch processing** — параллельный сбор параметров
- **Lazy LLM** — `include_llm=false` для быстрых запросов

---

## 14. Ограничения и известные проблемы

### 14.1. Текущие ограничения

- **Линейная модель** — не учитывает сезонность (суточные/недельные циклы)
- **Pearson correlation** — не детектит нелинейные зависимости
- **Z-score аномалий** — чувствителен к распределению (предполагает нормальное)
- **LLM fallback** — при недоступности YandexGPT инсайты менее качественные

### 14.2. Планируемые улучшения (v3.3.0+)

- ARIMA/SARIMA для временных рядов (сезонность)
- Mutual Information для нелинейных корреляций
- Isolation Forest для аномалий
- Локальная LLM (Ollama) для offline режима
- WebSocket для real-time updates
- Экспорт отчётов в PDF/Excel

---

## 15. Мониторинг и отладка

### 15.1. Логи

```
# Уровни логирования
DEBUG — детали сбора данных
INFO  — ключевые этапы анализа
WARN  — проблемы с данными (битые датчики, аномалии)
ERROR — сбои LLM, БД
```

### 15.2. Ключевые метрики

```
bucket_count      — кол-во агрегированных точек
total_raw_count   — кол-во сырых измерений
outliers_count    — кол-во выбросов
anomaly_rate      — % аномальных значений
r_squared         — качество линейной модели
```

### 15.3. DevTools Console (frontend)

```
// При клике на кнопки графика:
"zoomIn called, chartInstance: Chart {...}"
"downloadPNG called, chartInstance: Chart {...}"

// При ошибке:
"Chart instance not available"
```

---

## 16. Changelog

### v3.2.0 (текущая)
- ✅ Chart.js визуализация с zoom/pan/download
- ✅ 4 линии на графиках (данные, тренд, MA-7, прогноз)
- ✅ Прогнозы на 7/30/90/365 дней
- ✅ Раскрывающиеся карточки проблем/рекомендаций
- ✅ Фиксированные пределы оси Y
- ✅ Русификация UI

### v3.1.6
- ✅ Исправлена математика тренда
- ✅ suggestedMin/suggestedMax для корректного масштабирования
- ✅ Нейтральный серый для MA-7

### v3.1.5
- ✅ Initial Analytics Engine
- ✅ collectors/analyzers/LLM pipeline
- ✅ Endpoint /analytics/report

---

**Конец документации.**  
Для вопросов: `backend/modules/analytics/README.md` или issues в репозитории.