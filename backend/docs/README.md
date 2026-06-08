# SCADA.AI v3.0.1

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
