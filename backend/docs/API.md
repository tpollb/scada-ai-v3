# API Reference

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
  "response": "# Отчёт о здоровье системы\n\n**Композитный индекс:** 65/100...",
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
