# A/B Анализ

## Оглавление
- Обзор
- Режимы анализа
- Математическая основа
- API Reference
- Frontend компоненты
- Примеры использования
- Ограничения и edge cases
- Troubleshooting

---

## Обзор

A/B анализ — это статистический метод сравнения двух наборов данных для определения значимости различий между ними. В системе SCADA.AI используется для:

1. **Before/After анализ**: Сравнение одного тега в разные периоды времени (например, до и после изменения параметров)
2. **Equipment Comparison**: Сравнение двух разных тегов (оборудования) в один период времени

### Основные метрики

| Метрика | Описание | Формула |
|---------|----------|---------|
| **Mean Difference** | Разница средних значений | `μ_B - μ_A` |
| **Percentage Change** | Изменение в процентах | `((μ_B - μ_A) / μ_A) × 100%` |
| **P-value** | Вероятность нулевой гипотезы | Welch's t-test |
| **Cohen's d** | Размер эффекта (effect size) | `(μ_B - μ_A) / σ_pooled` |
| **Pattern Correlation** | Корреляция суточных паттернов | Pearson correlation |

---

## Режимы анализа

### Режим 1: Before/After (До/После)

**Цель**: Определить влияние изменений (настроек, условий эксплуатации, внешних факторов) на поведение одного тега.

**Структура запроса**:
```json
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
```

**Типичные сценарии**:
- Оценка эффекта после технического обслуживания
- Анализ влияния сезонных изменений
- Проверка результатов оптимизации процессов

### Режим 2: Equipment Comparison (Сравнение оборудования)

**Цель**: Сравнить поведение двух разных единиц оборудования в одинаковых условиях.

**Структура запроса**:
```json
{
  "snapshot_a": {
    "tag": "R001-Temperature",
    "start": "2026-01-01",
    "end": "2026-03-31"
  },
  "snapshot_b": {
    "tag": "R002-Temperature",
    "start": "2026-01-01",
    "end": "2026-03-31"
  }
}
```

**Типичные сценарии**:
- Сравнение идентичных установок
- Выявление аномального оборудования
- Балансировка нагрузки между единицами

---

## Математическая основа

### 1. Базовая статистика

Для каждого snapshot вычисляются:

```python
def compute_basic_stats(values: list[float]) -> dict:
    """
    Вычисляет базовую статистику для набора данных.
    
    Returns:
        {
            "count": int,
            "mean": float,
            "median": float,
            "std": float,
            "variance": float,
            "min": float,
            "max": float,
            "range": float
        }
    """
```

**Формулы**:

- **Среднее (Mean)**:
  
  μ = (1/n) × Σ xᵢ

- **Дисперсия (Variance)**:
  
  σ² = (1/(n-1)) × Σ (xᵢ - μ)²

- **Стандартное отклонение (Standard Deviation)**:
  
  σ = √σ²

- **Размах (Range)**:
  
  Range = max(X) - min(X)

### 2. Проверка статистической значимости (Welch's t-test)

**Нулевая гипотеза (H₀)**: Средние значения двух выборок равны (μ_A = μ_B)

**Альтернативная гипотеза (H₁)**: Средние значения различаются (μ_A ≠ μ_B)

**T-статистика**:

t = (μ_B - μ_A) / √(σ²_A/n_A + σ²_B/n_B)

**Степени свободы (Welch-Satterthwaite equation)**:

df = (σ²_A/n_A + σ²_B/n_B)² / [(σ²_A/n_A)²/(n_A-1) + (σ²_B/n_B)²/(n_B-1)]

**P-value**: Вероятность получить такое или более экстремальное значение t при условии что H₀ верна.

**Интерпретация**:

| P-value | Интерпретация | Вывод |
|---------|---------------|-------|
| p < 0.001 | Высоко значимо | Сильные доказательства различий |
| 0.001 ≤ p < 0.05 | Значимо | Есть доказательства различий |
| p ≥ 0.05 | Не значимо | Нет доказательств различий |

### 3. Размер эффекта (Cohen's d)

**Цель**: Оценить **практическую значимость** различий (не только статистическую).

**Pooled Standard Deviation**:

σ_pooled = √[(σ²_A + σ²_B) / 2]

**Cohen's d**:

d = (μ_B - μ_A) / σ_pooled

**Интерпретация**:

| Cohen's d | Размер эффекта | Практическое значение |
|-----------|----------------|----------------------|
| \|d\| < 0.2 | Пренебрежимо малый | Различия несущественны |
| 0.2 ≤ \|d\| < 0.5 | Малый | Незначительные различия |
| 0.5 ≤ \|d\| < 0.8 | Средний | Заметные различия |
| \|d\| ≥ 0.8 | Большой | Существенные различия |

### 4. Анализ сезонных паттернов

**Цель**: Сравнить суточные/недельные паттерны поведения.

**Автодетект периода**:
- Используется FFT (Fast Fourier Transform)
- Определяется доминирующий период (обычно 288 точек = 24 часа при 5-минутном интервале)

**Корреляция паттернов**:

r = Σ[(P_A[i] - μ_A) × (P_B[i] - μ_B)] / √[Σ(P_A[i] - μ_A)² × Σ(P_B[i] - μ_B)²]

где P_A и P_B — усреднённые суточные паттерны.

**Интерпретация**:

| Correlation | Сходство паттернов |
|-------------|-------------------|
| r > 0.9 | Очень высокое |
| 0.7 < r ≤ 0.9 | Высокое |
| 0.5 < r ≤ 0.7 | Умеренное |
| r ≤ 0.5 | Низкое |

### 5. Генерация вердикта

Автоматическая оценка результатов на основе:

1. **Процентное изменение среднего**:
   - |Δmean| > 50% → High severity
   - 20% < |Δmean| ≤ 50% → Medium severity
   - |Δmean| ≤ 20% → Low severity

2. **Изменение изменчивости (std)**:
   - |Δstd| > 100% → High severity
   - 50% < |Δstd| ≤ 100% → Medium severity

3. **Статистическая значимость**:
   - p < 0.001 → "highly_significant"
   - p < 0.05 → "significant"
   - p ≥ 0.05 → "not_significant"

4. **Сходство паттернов**:
   - Разные периоды → Medium severity
   - |Δamplitude| > 30% → Medium severity

---

## API Reference

### Endpoint: POST /api/v1/deep_analysis/ab

**Описание**: Выполняет A/B анализ двух snapshots.

**Request Body**:

```json
{
  "snapshot_a": {
    "tag": "string",
    "start": "YYYY-MM-DD",
    "end": "YYYY-MM-DD"
  },
  "snapshot_b": {
    "tag": "string",
    "start": "YYYY-MM-DD",
    "end": "YYYY-MM-DD"
  }
}
```

**Response (200 OK)**:

```json
{
  "mode": "before_after" | "equipment_comparison",
  "snapshot_a": {
    "tag": "R001-Temperature",
    "period": "2026-01-01T00:00:00 - 2026-03-31T23:59:59",
    "data_points": 12960
  },
  "snapshot_b": {
    "tag": "R001-Temperature",
    "period": "2026-04-01T00:00:00 - 2026-06-30T23:59:59",
    "data_points": 13104
  },
  "comparison": {
    "statistics": {
      "a": {
        "count": 12960,
        "mean": 45.23,
        "median": 45.10,
        "std": 3.45,
        "variance": 11.90,
        "min": 35.20,
        "max": 55.80,
        "range": 20.60
      },
      "b": {
        "count": 13104,
        "mean": 48.67,
        "median": 48.50,
        "std": 4.12,
        "variance": 16.97,
        "min": 37.10,
        "max": 60.30,
        "range": 23.20
      },
      "delta": {
        "mean": 7.61,
        "median": 7.54,
        "std": 19.42,
        "min": 5.40,
        "max": 8.07,
        "range": 12.62
      }
    },
    "significance": {
      "t_stat": 12.34,
      "p_value": 0.000000001,
      "cohens_d": 0.89,
      "interpretation": "highly_significant"
    }
  },
  "pattern_comparison": {
    "a": {
      "period": 288,
      "pattern": [...],
      "amplitude": 8.5
    },
    "b": {
      "period": 288,
      "pattern": [...],
      "amplitude": 10.2
    },
    "comparison": {
      "period_match": true,
      "delta_amplitude_pct": 20.0,
      "pattern_correlation": 0.87
    }
  },
  "verdict": {
    "summary": "Обнаружены критические различия",
    "key_findings": [
      "Среднее значение увеличилось на 7.6%",
      "Изменчивость (std) увеличилась на 19.4%",
      "Различие статистически высоко значимо (p < 0.001)",
      "Сезонная амплитуда увеличилась на 20.0%"
    ],
    "recommendations": [
      "⚠️ Обнаружены значительные изменения. Требуется детальный анализ причин.",
      "Проверить условия эксплуатации и внешние факторы."
    ],
    "severity": "high"
  }
}
```

**Error Responses**:

- **400 Bad Request**: Недостаточно данных или некорректные параметры
- **500 Internal Server Error**: Внутренняя ошибка сервера

---

## Frontend компоненты

### ABComparisonModal.svelte

**Расположение**: `frontend/src/components/ABComparisonModal.svelte`

**Props**:

```typescript
interface Props {
  isOpen: boolean
  availableTags: string[]
  defaultTag?: string
  onClose: () => void
  onResult?: (result: any) => void
}
```

**Функционал**:
1. Выбор режима (Before/After или Equipment Comparison)
2. Выбор тегов и периодов
3. Автоматическое заполнение дат (последние 7 дней vs предыдущие 7 дней)
4. Отображение результатов:
   - Вердикт с severity
   - Статистика с процентными изменениями
   - Значимость (p-value, Cohen's d)
   - Сравнение паттернов
5. Кнопка "Использовать в анализе" — передаёт результат в родительский компонент

### Интеграция с DeepAnalysisControls

**Файл**: `frontend/src/components/DeepAnalysisControls.svelte`

Добавлена кнопка "Сравнить периоды (A/B)" которая открывает `ABComparisonModal`.

**Передача результата**:

```typescript
function handleABResult(result: any) {
  // Добавляем ab_comparison в результат анализа
  if (ddaAnalysisResult) {
    ddaAnalysisResult.ab_comparison = result
  } else {
    ddaAnalysisResult = { ab_comparison: result }
  }
  
  // Переключаем на вкладку "Интерпретация"
  ddaForceTab = 'interpretation'
}
```

---

## Примеры использования

### Пример 1: Before/After анализ

**Сценарий**: Оценка эффекта после калибровки датчика температуры.

**Запрос**:

```bash
curl -X POST http://localhost:8081/api/v1/deep_analysis/ab \
  -H "Content-Type: application/json" \
  -d '{
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
  }'
```

**Результат**:

```json
{
  "mode": "before_after",
  "comparison": {
    "statistics": {
      "delta": {
        "mean": -2.3,
        "std": -15.6
      }
    },
    "significance": {
      "p_value": 0.000045,
      "cohens_d": 0.67,
      "interpretation": "highly_significant"
    }
  },
  "verdict": {
    "summary": "Обнаружены заметные различия",
    "key_findings": [
      "Среднее значение уменьшилось на 2.3%",
      "Изменчивость (std) уменьшилась на 15.6%",
      "Различие статистически высоко значимо (p < 0.001)"
    ],
    "severity": "medium"
  }
}
```

**Интерпретация**: После калибровки средняя температура снизилась на 2.3%, а изменчивость уменьшилась на 15.6%. Различия статистически значимы (p < 0.001) с средним размером эффекта (Cohen's d = 0.67).

### Пример 2: Equipment Comparison

**Сценарий**: Сравнение двух идентичных реакторов.

**Запрос**:

```bash
curl -X POST http://localhost:8081/api/v1/deep_analysis/ab \
  -H "Content-Type: application/json" \
  -d '{
    "snapshot_a": {
      "tag": "R001-Pressure",
      "start": "2026-01-01",
      "end": "2026-03-31"
    },
    "snapshot_b": {
      "tag": "R002-Pressure",
      "start": "2026-01-01",
      "end": "2026-03-31"
    }
  }'
```

**Результат**:

```json
{
  "mode": "equipment_comparison",
  "comparison": {
    "statistics": {
      "delta": {
        "mean": 12.5,
        "std": 45.3
      }
    },
    "significance": {
      "p_value": 0.000001,
      "cohens_d": 1.23,
      "interpretation": "highly_significant"
    }
  },
  "verdict": {
    "summary": "Обнаружены критические различия",
    "key_findings": [
      "Среднее значение увеличилось на 12.5%",
      "Изменчивость (std) увеличилась на 45.3%",
      "Различие статистически высоко значимо (p < 0.001)"
    ],
    "recommendations": [
      "⚠️ Оборудование работает по-разному. Проверить настройки и состояние."
    ],
    "severity": "high"
  }
}
```

**Интерпретация**: R002 показывает на 12.5% более высокое среднее давление и на 45.3% большую изменчивость по сравнению с R001. Различия высоко значимы с большим размером эффекта (Cohen's d = 1.23). Требуется проверка оборудования.

---

## Ограничения и edge cases

### 1. Минимальный размер выборки

**Ограничение**: MIN_SAMPLE_SIZE = 10 точек

**Поведение**: Если в одном из snapshot меньше 10 точек, возвращается:

```json
{
  "statistics": {"a": {}, "b": {}, "delta": {}},
  "significance": {
    "interpretation": "insufficient_data",
    "reason": "Sample too small: 5/12 (min 10)"
  }
}
```

### 2. Обработка NaN значений

**Фильтрация**: Перед анализом все NaN/Inf значения удаляются:

```python
def is_valid(x):
    if x is None:
        return False
    try:
        return x == x and abs(x) < 1e15
    except (TypeError, ValueError):
        return False

clean_a = [x for x in data_a if is_valid(x)]
```

**Поведение**: Если после фильтрации осталось меньше MIN_SAMPLE_SIZE точек → `insufficient_data`

### 3. Константные данные

**Проблема**: Если все значения в snapshot одинаковые (σ² = 0), t-test не применим.

**Решение**: Проверка variance перед t-test:

```python
var_a = stats_a.get('variance', 0)
var_b = stats_b.get('variance', 0)
if (var_a is not None and var_a > 0) or (var_b is not None and var_b > 0):
    # Запускаем t-test
else:
    # Константные данные — t-test не применим
    t_stat, p_value = 0.0, 1.0
```

### 4. Корреляция паттернов

**Проблема**: `np.corrcoef` возвращает NaN если один из паттернов — константа.

**Решение**:

```python
try:
    corr_matrix = np.corrcoef(pattern_a, pattern_b)
    corr_val = corr_matrix[0, 1]
    if corr_val is not None and corr_val == corr_val and abs(corr_val) <= 1.0:
        pattern_corr = float(corr_val)
    else:
        pattern_corr = None
except Exception:
    pattern_corr = None
```

### 5. JSON сериализация

**Проблема**: `json.dumps()` не может сериализовать NaN/Inf.

**Решение**: Санитизация через `_safe_float()`:

```python
def _safe_float(v, default=0.0):
    if v is None:
        return default
    try:
        v = float(v)
    except (TypeError, ValueError):
        return default
    if v != v or abs(v) > 1e10:  # isnan или слишком большое
        return default
    return v
```

---

## Troubleshooting

### Проблема 1: Кнопки зума не работают на маленьком графике

**Причина**: `patternChartInstance` не заполняется после рендеринга.

**Решение**: Добавить `$effect` для получения Chart instance:

```javascript
$effect(() => {
  if (analysisResult?.seasonality?.pattern?.pattern?.length > 0) {
    setTimeout(() => {
      const container = document.getElementById(patternChartId)
      if (container) {
        const canvas = container.querySelector('canvas')
        if (canvas) patternChartInstance = ChartJS.getChart(canvas) || null
      }
    }, 200)
  }
})
```

### Проблема 2: P-value = 0

**Причина**: Очень большие различия между выборками.

**Интерпретация**: Различия статистически высоко значимы (p < 0.001). Это **нормально** для больших выборок с существенными различиями.

### Проблема 3: Cohen's d = NaN

**Причина**: Pooled standard deviation = 0 (константные данные).

**Решение**: Проверка перед делением:

```python
pooled_std = np.sqrt(pooled_var) if pooled_var > 0 else 0.0
cohens_d = mean_diff / pooled_std if pooled_std > 1e-10 else 0.0
```

### Проблема 4: Pattern correlation = NaN

**Причина**: Один из паттернов — константа (все значения одинаковые).

**Интерпретация**: Корреляция не определена. Это **нормально** для данных без изменчивости.

### Проблема 5: Ошибка 500 при сравнении оборудования

**Причина**: Разные теги могут иметь разные диапазоны значений → огромные процентные изменения.

**Решение**: Фронтенд ограничивает отображение:

```javascript
function formatDelta(value: number | null | undefined): string {
  if (value === null || value === undefined) return 'N/A'
  if (Number.isNaN(value)) return 'N/A'
  const v = Number(value)
  if (!Number.isFinite(v)) return 'N/A'
  if (Math.abs(v) > 999) {
    return v > 0 ? '>+999%' : '<-999%'
  }
  if (v > 0) return `+${v.toFixed(1)}%`
  return `${v.toFixed(1)}%`
}
```

---

## Best Practices

### 1. Выбор периодов

- **Before/After**: Минимум 7 дней для каждого периода
- **Equipment Comparison**: Одинаковые периоды для обоих тегов
- **Избегайте**: Праздничных дней, плановых остановок, аномальных событий

### 2. Интерпретация результатов

- **Смотрите на p-value**: Статистическая значимость
- **Смотрите на Cohen's d**: Практическая значимость
- **Смотрите на вердикт**: Автоматическая оценка severity
- **Сравнивайте паттерны**: Сходство суточного поведения

### 3. Когда использовать

[x] **Используйте A/B анализ когда**:
- Оцениваете эффект изменений
- Сравниваете идентичное оборудование
- Ищете аномалии в поведении
- Валидируете результаты оптимизации

X **Не используйте A/B анализ когда**:
- Данные содержат много пропусков (>50%)
- Периоды слишком короткие (<7 дней)
- Есть внешние факторы влияющие на оба snapshot
- Теги измеряют разные физические величины

---

## Технические детали

### Зависимости

**Backend**:
- `scipy.stats.ttest_ind` — Welch's t-test
- `numpy.corrcoef` — корреляция паттернов
- `numpy.fft` — автодетект периодов

**Frontend**:
- `chart.js` + `chartjs-plugin-zoom` — графики с zoom
- `lucide-svelte` — иконки

### Производительность

- **FFT**: O(n log n) для автодетекта периодов
- **T-test**: O(n) для вычисления статистик
- **Корреляция**: O(n) для сравнения паттернов

**Типичное время выполнения**:
- 1000 точек: <10ms
- 10000 точек: <50ms
- 100000 точек: <200ms

### Безопасность

- Все входные данные валидируются
- Защита от SQL injection (параметризованные запросы)
- Защита от NaN/Inf в JSON response
- Обработка ошибок с понятными сообщениями

---

## Changelog

### v1.0 (2026-07-01)
- [x] Базовый A/B анализ (Before/After, Equipment Comparison)
- [x] Статистическая значимость (Welch's t-test)
- [x] Размер эффекта (Cohen's d)
- [x] Сравнение сезонных паттернов
- [x] Автоматическая генерация вердиктов
- [x] Frontend модалка с визуализацией
- [x] Интеграция с LLM интерпретацией
- [x] Защита от NaN/Inf/малых выборок
- [x] Корректная обработка edge cases

---

## Ссылки

- [Welch's t-test](https://en.wikipedia.org/wiki/Welch%27s_t-test)
- [Cohen's d](https://en.wikipedia.org/wiki/Effect_size#Cohen's_d)
- [Pearson correlation](https://en.wikipedia.org/wiki/Pearson_correlation_coefficient)
- [Fast Fourier Transform](https://en.wikipedia.org/wiki/Fast_Fourier_transform)
