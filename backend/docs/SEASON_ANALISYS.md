# Сезонный анализ

**Модуль:** `backend/modules/deep_analysis/analyzers/seasonal.py`  
**Версия:** 3.2.8  
**Обновлено:** 2026-06-29

---

## Содержание

1. Обзор методов
2. Детекция доминирующих периодов
3. Декомпозиция временного ряда
4. Вычисление типичного паттерна
5. Статистические метрики
6. Интерпретация результатов
7. Ограничения и особенности

---

## Обзор методов

Сезонный анализ решает три основные задачи:

1. **Обнаружение периодичности** — находит доминирующие циклы в данных (сутки, неделя, месяц и т.д.)
2. **Декомпозиция ряда** — разделяет временной ряд на тренд, сезонную компоненту и остаток
3. **Извлечение типичного паттерна** — вычисляет усреднённый профиль одного цикла

Все методы работают для **любой частоты дискретизации** (sampling rate) — не зависят от 5-минутного или 1-часового интервала.

---

## Детекция доминирующих периодов

### Метод: FFT + Автокорреляция

Функция `detect_dominant_periods(values, min_period, max_period)` использует два взаимодополняющих метода:

#### Шаг 1: Быстрое преобразование Фурье (FFT)

Для временного ряда $x = [x_0, x_1, \ldots, x_{N-1}]$ длиной $N$ вычисляется FFT:

$$X_k = \sum_{n=0}^{N-1} x_n \cdot e^{-i \cdot 2\pi k n / N}, \quad k = 0, 1, \ldots, N-1$$

где:
- $x_n$ — значение в момент времени $n$
- $X_k$ — комплексная амплитуда $k$-й частоты
- $i$ — мнимая единица

**Спектр мощности (Power Spectrum):**

$$P_k = |X_k|^2 = \text{Re}(X_k)^2 + \text{Im}(X_k)^2$$

Частоты $f_k$ связаны с периодами $T_k$:

$$f_k = \frac{k}{N \cdot \Delta t}, \quad T_k = \frac{N \cdot \Delta t}{k}$$

где $\Delta t$ — интервал между измерениями (например, 5 минут).

**Нормализация спектра:**

$$\hat{P}_k = \frac{P_k}{\sum_{k} P_k}$$

#### Шаг 2: Автокорреляция (ACF)

Для подтверждения периодов используется автокорреляционная функция:

$$R(\tau) = \frac{1}{N-\tau} \sum_{t=0}^{N-\tau-1} (x_t - \bar{x})(x_{t+\tau} - \bar{x})$$

**Нормализованная автокорреляция:**

$$\rho(\tau) = \frac{R(\tau)}{R(0)}$$

где $\rho(0) = 1$, а $\rho(\tau) \in [-1, 1]$.

**Интерпретация:**
- $\rho(\tau) \approx 1$ — сильная положительная корреляция с лагом $\tau$
- $\rho(\tau) \approx -1$ — сильная отрицательная корреляция (анти-период)
- $\rho(\tau) \approx 0$ — нет линейной зависимости

#### Шаг 3: Объединённая оценка (Confidence Score)

Для каждого периода $T$ вычисляется composite confidence:

$$\text{confidence}(T) = w_1 \cdot \hat{P}_{T} + w_2 \cdot \max(\rho(T), 0) + w_3 \cdot \text{peak\_sharpness}(T)$$

где:
- $w_1 = 0.5$ — вес FFT
- $w_2 = 0.3$ — вес автокорреляции
- $w_3 = 0.2$ — вес "остроты пика" (peak sharpness)

**Peak sharpness** измеряет насколько пик выражен относительно соседей:

$$\text{sharpness}(T) = \frac{\hat{P}_T - \text{median}(\hat{P}_{T-2:T+2})}{\text{std}(\hat{P}_{T-2:T+2}) + \epsilon}$$

#### Шаг 4: Ранжирование и отбор

Периоды ранжируются по confidence и возвращаются **top-K** (обычно K=5):

$$T_{\text{ranked}} = \text{argsort}(\text{confidence})[-K:]$$

**Фильтрация:**
- Периоды вне диапазона $[T_{\min}, T_{\max}]$ отбрасываются
- Периоды короче `min_period` точек отбрасываются (шум)
- Периоды длиннее ряда / 2 отбрасываются (недостаточно данных)

### Псевдокод

```python
def detect_dominant_periods(values, min_period=10, max_period=None):
    N = len(values)
    if max_period is None:
        max_period = N // 2
    
    # Удаляем тренд (detrending)
    detrended = values - rolling_mean(values, window=N//4)
    
    # FFT
    fft_vals = np.fft.fft(detrended)
    power_spectrum = np.abs(fft_vals[:N//2])**2
    power_norm = power_spectrum / power_spectrum.sum()
    
    # Автокорреляция
    acf = np.correlate(detrended, detrended, mode='full')[N-1:]
    acf_norm = acf / acf[0]
    
    # Composite confidence
    confidences = {}
    for T in range(min_period, max_period):
        fft_score = power_norm[N//T] if N//T < len(power_norm) else 0
        acf_score = max(acf_norm[T], 0)
        sharpness = compute_sharpness(power_norm, N//T)
        
        confidences[T] = 0.5*fft_score + 0.3*acf_score + 0.2*sharpness
    
    # Top-K periods
    top_periods = sorted(confidences.items(), key=lambda x: x[1], reverse=True)[:5]
    return top_periods
```

---

## Декомпозиция временного ряда

### Метод: Аддитивная STL-подобная декомпозиция

Функция `decompose_seasonal(values, period)` разделяет ряд на три компоненты:

$$x_t = T_t + S_t + R_t$$

где:
- $T_t$ — трендовая компонента (Trend)
- $S_t$ — сезонная компонента (Seasonal)
- $R_t$ — остаточная компонента (Residual)

### Шаг 1: Оценка тренда (Trend)

Используется **скользящее среднее (rolling mean)** с окном, равным периоду:

$$T_t = \frac{1}{2m+1} \sum_{j=-m}^{m} x_{t+j}$$

где $m = \lfloor \text{period}/2 \rfloor$.

**Для чётных периодов** применяется центрированное скользящее среднее 2×m:

$$T_t = \frac{1}{2} \left( \frac{1}{m} \sum_{j=-(m-1)/2}^{(m+1)/2} x_{t+j} + \frac{1}{m} \sum_{j=-(m+1)/2}^{(m-1)/2} x_{t+j} \right)$$

На практике используется **pandas rolling window** с `center=True`:

```python
trend = pd.Series(values).rolling(window=period, center=True, min_periods=1).mean()
```

**Улучшенный алгоритм:** для уменьшения edge effects применяется `win_type='gaussian'` или LOESS-сглаживание.

### Шаг 2: Detrending

Вычитаем тренд из исходного ряда:

$$D_t = x_t - T_t$$

где $D_t$ — детрендированный ряд.

### Шаг 3: Вычисление сезонной компоненты (Seasonal)

Сезонная компонента вычисляется как **среднее по фазам**:

$$S_p = \frac{1}{K_p} \sum_{k=0}^{K_p-1} D_{p + k \cdot \text{period}}$$

где:
- $p \in [0, \text{period}-1]$ — индекс фазы
- $K_p$ — количество наблюдений в фазе $p$
- $D_{p + k \cdot \text{period}}$ — детрендированные значения в фазе $p$

**Центрирование сезонности** (чтобы сумма по периоду была ≈ 0):

$$\bar{S} = \frac{1}{\text{period}} \sum_{p=0}^{\text{period}-1} S_p$$
$$S'_p = S_p - \bar{S}$$

**Расширение на весь ряд:**

$$S_t = S'_{t \bmod \text{period}}$$

### Шаг 4: Вычисление остатка (Residual)

$$R_t = x_t - T_t - S_t = D_t - S'_t$$

### Variance Explained (Доля объяснённой дисперсии)

Каждая компонента оценивается через долю объяснённой дисперсии:

$$\text{Var}(X) = \frac{1}{N} \sum_{t=0}^{N-1} (x_t - \bar{x})^2$$

**Доля тренда:**

$$\text{Var}_{\text{trend}} = \frac{\text{Var}(T)}{\text{Var}(X)} \cdot 100\%$$

**Доля сезонности:**

$$\text{Var}_{\text{seasonal}} = \frac{\text{Var}(S)}{\text{Var}(X)} \cdot 100\%$$

**Доля остатка:**

$$\text{Var}_{\text{residual}} = \frac{\text{Var}(R)}{\text{Var}(X)} \cdot 100\%$$

**Проверка:** $\text{Var}_{\text{trend}} + \text{Var}_{\text{seasonal}} + \text{Var}_{\text{residual}} \approx 100\%$

### Псевдокод

```python
def decompose_seasonal(values, period):
    N = len(values)
    
    # 1. Trend: rolling mean
    trend = pd.Series(values).rolling(window=period, center=True).mean()
    trend = trend.fillna(method='bfill').fillna(method='ffill')
    
    # 2. Detrending
    detrended = values - trend
    
    # 3. Seasonal: mean by phase
    seasonal_pattern = []
    for phase in range(period):
        phase_values = detrended[phase::period]
        seasonal_pattern.append(np.mean(phase_values))
    
    # Центрирование
    seasonal_pattern = np.array(seasonal_pattern)
    seasonal_pattern -= seasonal_pattern.mean()
    
    # Расширение на весь ряд
    seasonal = np.tile(seasonal_pattern, N // period + 1)[:N]
    
    # 4. Residual
    residual = values - trend - seasonal
    
    # 5. Variance explained
    var_total = np.var(values)
    var_trend = np.var(trend)
    var_seasonal = np.var(seasonal)
    var_residual = np.var(residual)
    
    return {
        "trend": trend.tolist(),
        "seasonal": seasonal.tolist(),
        "residual": residual.tolist(),
        "seasonal_pattern": seasonal_pattern.tolist(),
        "variance_explained": {
            "trend": (var_trend / var_total) * 100,
            "seasonal": (var_seasonal / var_total) * 100,
            "residual": (var_residual / var_total) * 100,
        }
    }
```

---

## Вычисление типичного паттерна

### Метод: Усреднение по фазам

Функция `get_seasonal_pattern(values, period)` возвращает **типичный профиль одного цикла**:

$$\text{pattern}[p] = \frac{1}{K_p} \sum_{k=0}^{K_p-1} x_{p + k \cdot \text{period}}$$

где:
- $p \in [0, \text{period}-1]$ — индекс фазы (0 = начало цикла)
- $K_p = \lfloor (N - p - 1) / \text{period} \rfloor + 1$ — количество наблюдений в фазе $p$
- $x_{p + k \cdot \text{period}}$ — исходные значения (НЕ детрендированные!)

**Важно:** В отличие от декомпозиции, здесь используется **исходный ряд** (не детрендированный), чтобы паттерн сохранял абсолютные значения.

### Стандартное отклонение по фазам

$$\text{std}[p] = \sqrt{\frac{1}{K_p} \sum_{k=0}^{K_p-1} (x_{p + k \cdot \text{period}} - \text{pattern}[p])^2}$$

### Количество наблюдений

$$\text{n\_samples}[p] = K_p$$

### Псевдокод

```python
def get_seasonal_pattern(values, period):
    clean_values = [v for v in values if v is not None and not np.isnan(v)]
    N = len(clean_values)
    
    pattern = []
    stds = []
    counts = []
    
    for phase in range(period):
        # Срез всех значений с данной фазой
        phase_values = clean_values[phase::period]
        
        if len(phase_values) > 0:
            pattern.append(float(np.mean(phase_values)))
            stds.append(float(np.std(phase_values)))
            counts.append(len(phase_values))
        else:
            pattern.append(None)
            stds.append(None)
            counts.append(0)
    
    return {
        "pattern": pattern,      # Среднее по каждой фазе
        "std": stds,             # Стандартное отклонение по каждой фазе
        "n_samples": counts,     # Количество наблюдений
        "period": period,        # Период
    }
```

### Пример: 7-дневный ряд с 5-минутным интервалом

- Длина ряда: $N = 2016$ точек
- Период: $T = 288$ точек (24 часа)
- Количество полных циклов: $K = 2016 / 288 = 7$ (7 суток)

Для фазы $p = 0$ (полночь):
- Точки: $x_0, x_{288}, x_{576}, x_{864}, x_{1152}, x_{1440}, x_{1728}$
- Всего: 7 значений
- $\text{pattern}[0] = \frac{x_0 + x_{288} + x_{576} + \ldots + x_{1728}}{7}$

**Результат:** Паттерн из 288 точек, где каждая точка — это **усреднённое значение за все 7 дней** в данный момент суток.

---

## Статистические метрики

### Confidence Score (Уверенность детекции)

Метрика показывает, насколько **надёжно** обнаружен период:

$$\text{confidence} = \frac{\text{composite\_score} - \text{median}}{\text{std}} \cdot 100\%$$

**Интерпретация:**
- **> 50%** — очень надёжный период (чёткие суточные/недельные циклы)
- **20-50%** — умеренная уверенность (зашумлённые данные)
- **< 20%** — слабая периодичность (возможно, ложное обнаружение)

### Минимум, максимум, размах паттерна

$$\text{min} = \min_{p} \text{pattern}[p]$$
$$\text{max} = \max_{p} \text{pattern}[p]$$
$$\text{range} = \text{max} - \text{min}$$

### Амплитуда сезонности

**Абсолютная:**

$$A_{\text{abs}} = \frac{\text{range}}{2}$$

**Относительная (в % от среднего):**

$$A_{\text{rel}} = \frac{\text{range}}{\text{mean}(\text{pattern})} \cdot 100\%$$

---

## Интерпретация результатов

### Пример: KITCHEN2-CO2 (7 дней, 5-мин интервал)

#### Входные данные:
- Длина ряда: **8581 точек**
- Период: **30 дней**
- Sampling rate: **5 минут** (288 точек/сутки)

#### Результат анализа:

```json
{
  "periods": {
    "detected_periods": [
      {"period": 2016, "confidence": 0.87},   // ~7 дней (неделя)
      {"period": 288, "confidence": 0.72},    // ~24 часа (сутки)
      {"period": 1440, "confidence": 0.45},   // ~5 дней
      {"period": 576, "confidence": 0.32},    // ~2 дня
      {"period": 864, "confidence": 0.18}     // ~3 дня
    ]
  },
  "decomposition": {
    "variance_explained": {
      "trend": 1.5,
      "seasonal": 87.1,
      "residual": 11.2
    }
  },
  "pattern": {
    "period": 288,
    "pattern": [498.1, 493.4, 490.3, ..., 481.0],
    "min": 426.0,
    "max": 642.7,
    "range": 216.7
  }
}
```

#### Интерпретация:

**1. Доминирующие периоды:**
- **288 точек (~24ч)** — основной суточный цикл с уверенностью 72%
- **2016 точек (~7 дней)** — недельный цикл с уверенностью 87% (доминирующий!)

**2. Декомпозиция:**
- **Тренд: 1.5%** — почти нет долгосрочного изменения
- **Сезонность: 87.1%** — подавляющая часть изменчивости объясняется циклами
- **Остаток: 11.2%** — шум и несистематические колебания

**Вывод:** Ряд **высоко периодичен** (87% сезонности) с сильными суточными и недельными циклами.

**3. Типичный паттерн:**
- **Мин: 426 ppm** — ночной минимум CO₂ (низкая активность)
- **Макс: 643 ppm** — дневной пик (рабочие часы на кухне)
- **Размах: 217 ppm** — амплитуда суточных колебаний

### Что означает высокая сезонность?

| Var_seasonal | Интерпретация | Примеры |
|--------------|---------------|---------|
| **> 70%** | Очень периодичный ряд | Температура в здании, нагрузка на энергосистему |
| **40-70%** | Умеренная периодичность | Трафик, потребление воды |
| **< 40%** | Слабая периодичность | Случайные события, шумовые данные |

### Что означает высокий residual?

| Var_residual | Интерпретация | Возможные причины |
|--------------|---------------|-------------------|
| **< 20%** | Чистые данные | Стабильный процесс |
| **20-40%** | Умеренный шум | Нормальная вариативность |
| **> 40%** | Сильный шум | Аномалии, нестабильность, ошибки измерения |

---

## Ограничения и особенности

### 1. Длина ряда

**Минимум:** 50 точек  
**Рекомендуется:** ≥ 3 полных периода

Для обнаружения периода $T$ необходимо минимум $3T$ точек в ряде.

### 2. Пропущенные значения

- **Метод:** `_prepare_values(interpolate=False)` удаляет NaN
- **Последствия:** сокращение эффективной длины ряда
- **Решение:** для больших gap'ов рекомендуется интерполяция перед анализом

### 3. Нестационарность

Методы предполагают, что сезонность **стабильна во времени**. Если паттерн меняется (например, зимний/летний режимы), результаты будут **усреднёнными** и могут не отражать реальность.

**Решение:** использовать скользящее окно или separate analysis по сегментам.

### 4. Edge effects при декомпозиции

**Проблема:** Rolling mean на краях ряда даёт менее точные оценки тренда.

**Решение:** `fillna(method='bfill').fillna(method='ffill')` продлевает тренд, но первые и последние `period/2` точек имеют повышенную неопределённость.

### 5. Кратные периоды

Если ряд имеет **несколько наложенных циклов** (сутки + неделя), FFT покажет оба. Метод возвращает **top-5** периодов, и важно анализировать их вместе.

**Пример:** Период 2016 точек (неделя) часто сопровождается 288 точек (сутки) — это **нормально**, а не дублирование.

### 6. Выбор периода для анализа

**Рекомендация:** использовать **самый короткий устойчивый период** (обычно сутки).

**Обоснование:** Короткий период даёт больше циклов для усреднения → более гладкий паттерн.

```python
# Выбор периода
main_period = periods['detected_periods'][0]['period']  # Самый уверенный

# Но если он слишком длинный — берём следующий
if main_period > 1000 and len(periods['detected_periods']) > 1:
    main_period = periods['detected_periods'][1]['period']
```

---

## Сводная таблица методов

| Метод | Формула | Назначение |
|-------|---------|------------|
| **FFT** | $X_k = \sum x_n e^{-i2\pi kn/N}$ | Частотный анализ |
| **Power Spectrum** | $P_k = \|X_k\|^2$ | Мощность по частотам |
| **ACF** | $\rho(\tau) = R(\tau)/R(0)$ | Автокорреляция |
| **Trend** | $T_t = \text{mean}(x_{t-m:t+m})$ | Скользящее среднее |
| **Seasonal** | $S_p = \text{mean}_k(D_{p+kT})$ | Среднее по фазам |
| **Residual** | $R_t = x_t - T_t - S_t$ | Остаток |
| **Variance Explained** | $\text{Var}(S)/\text{Var}(X)$ | Доля дисперсии |
| **Pattern** | $\text{mean}_k(x_{p+kT})$ | Типичный профиль |
| **Confidence** | $w_1 \hat{P} + w_2 \rho + w_3 \text{sharpness}$ | Уверенность |

---

## Ссылки

1. **Box, G.E.P., Jenkins, G.M., Reinsel, G.C.** (2013). *Time Series Analysis: Forecasting and Control*. Wiley.
2. **Cleveland, R.B., Cleveland, W.S., McRae, J.E., Terpenning, I.** (1990). *STL: A Seasonal-Trend Decomposition Procedure Based on Loess*. Journal of Official Statistics.
3. **Chatfield, C.** (2003). *The Analysis of Time Series: An Introduction*. Chapman & Hall/CRC.

---

## FAQ

### Q: Почему для периода 2016 точек (7 дней) паттерн показывает "волны", а не прямую линию?

**A:** Потому что в данных есть **реальные суточные колебания** (минимум ночью, пик днём). Алгоритм `get_seasonal_pattern` усредняет 7 суток и выявляет эти колебания. Если бы ряд был случайным шумом, паттерн был бы плоским.

### Q: Как понять, что детектированный период реальный, а не артефакт?

**A:** Смотрите на **confidence score**:
- **> 50%** — реальный период
- **20-50%** — вероятно реальный, но зашумлённый
- **< 20%** — возможно, артефакт

Также проверяйте **Var_seasonal** в декомпозиции — если сезонность > 50%, периоды скорее всего реальные.

### Q: Почему seasonal анализ выполняется на всём ряде, а не на отдельных сегментах?

**A:** Это **осознанный выбор**: усреднение по всем циклам даёт **наиболее стабильный и сглаженный** типичный паттерн. Для анализа изменяющейся во времени сезонности потребуется отдельный метод (например, скользящее окно).

### Q: Можно ли использовать для рядов с разной частотой дискретизации?

**A:** Да, алгоритмы **не зависят от sampling rate**. Период 288 точек может быть:
- 24 часа при 5-мин интервале
- 12 часов при 2.5-мин интервале
- 48 часов при 10-мин интервале

Формат `formatPeriod(period)` автоматически определяет, какой это период в часах/днях, исходя из фактической частоты.

### Q: Что делать, если ряд имеет тренд?

**A:** Декомпозиция **автоматически** разделяет тренд и сезонность. Но для `get_seasonal_pattern` используется **исходный ряд** (не детрендированный), поэтому паттерн сохраняет абсолютные значения.

Если нужен "чистый" сезонный паттерн без тренда, используйте `decomposition.seasonal_pattern` вместо `pattern.pattern`.

---