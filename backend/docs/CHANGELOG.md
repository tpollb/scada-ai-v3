# Changelog

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

## [2.x.x] - 2025-2026 (Legacy)

Внутренние версии для тестирования. Не публичные.

---

## [1.x.x] - 2025 (Prototype)

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

### v3.2.0 (Планируется)
- [ ] Модуль `historical_data` — тренды и сравнение периодов
- [ ] Модуль `predictive_analytics` — прогнозы экономии
- [ ] Boss dashboard — отдельный экран для руководства

### v4.0.0 (Долгосрочно)
- [ ] Ролевая модель (admin, engineer, operator, boss)
- [ ] Зашифрованное хранилище пользователей (users.enc)
- [ ] Multi-tenancy (несколько зданий в одной системе)
- [ ] Mobile app (React Native)
