#!/usr/bin/env python3
"""
bump_3.2.3.py — бамп версии до 3.2.3 + git commit + push
"""
from pathlib import Path
import subprocess
import sys

print('=' * 80)
print('БУМП ВЕРСИИ 3.2.3 + GIT COMMIT + PUSH')
print('=' * 80)
print()

# 1. Обновляем версию в settings.py
settings_path = Path('backend/config/settings.py')
if settings_path.exists():
    content = settings_path.read_text(encoding='utf-8')
    
    # Ищем app_version
    if 'app_version: str = "3.2.2"' in content:
        content = content.replace('app_version: str = "3.2.2"', 'app_version: str = "3.2.3"')
        settings_path.write_text(content, encoding='utf-8', newline='\n')
        print('✅ 1. Версия обновлена: 3.2.2 → 3.2.3')
    elif 'app_version: str = "3.2.3"' in content:
        print('ℹ️  1. Версия уже 3.2.3')
    else:
        print('⚠️  1. Не удалось найти app_version в settings.py')
else:
    print('❌ 1. settings.py не найден')

print()

# 2. Git status — показываем что будет закоммичено
print('【2】Git status:')
print('-' * 80)
result = subprocess.run(['git', 'status', '--short'], capture_output=True, text=True)
print(result.stdout)

if not result.stdout.strip():
    print('ℹ️  Нет изменений для коммита')
    sys.exit(0)

# 3. Git add
print('【3】Git add:')
print('-' * 80)
result = subprocess.run(['git', 'add', '-A'], capture_output=True, text=True)
if result.returncode == 0:
    print('✅ Все изменения добавлены в staging')
else:
    print(f'❌ Ошибка git add: {result.stderr}')
    sys.exit(1)

print()

# 4. Git commit
print('【4】Git commit:')
print('-' * 80)

commit_message = """feat(dda): конфигуратор настроек Deep Data Analysis (v3.2.3)

Backend:
- Создан config.yaml с 20+ параметрами для модуля deep_analysis
- Добавлена DDASettings Pydantic модель с валидацией
- Создан settings.py с функциями load/save/reload настроек
- Добавлены endpoints:
  * GET /config/modules/deep_analysis/settings
  * PUT /config/modules/deep_analysis/settings
  * POST /config/modules/deep_analysis/settings/reset
- Обновлён anomalies.py — все пороги читаются из конфига:
  * contamination, n_estimators (Isolation Forest)
  * spike_threshold, dip_threshold (классификация)
  * drift_min_duration, drift_min_r_squared, drift_min_relative_change
  * plateau_tolerance, local_window, significant_dip_ratio, zero_threshold_ratio
- Убран adaptive_contamination из api.py (теперь из конфига)
- diagnose_weeks использует настройки из конфига

Frontend:
- Создан DDAConfigPanel.svelte с 4 вкладками:
  * Аномалии (детекция + классификация + дрейф + локальная статистика)
  * Корреляции (resample_freq, pearson_threshold, max_lag)
  * Визуализация (max_points, point_radius, line_width)
  * Цвета (color picker для spike/dip/drift/noise)
- Добавлена вкладка "DDA" в Config.svelte
- Монохромные иконки (убраны цветные эмодзи)
- Стили кнопки DDA синхронизированы с другими вкладками

Архитектура:
- Кнопка DDA (в хедере) — UI конфигуратора + анализ для оператора
- Модуль deep_analysis — будущая LLM интеграция (промпты + tools)
- Чёткое разделение ответственности

Версия: 3.2.2 → 3.2.3
"""

result = subprocess.run(
    ['git', 'commit', '-m', commit_message],
    capture_output=True,
    text=True,
    encoding='utf-8'
)

if result.returncode == 0:
    print('✅ Commit создан')
    print()
    print('Сообщение:')
    print(commit_message)
else:
    print(f'❌ Ошибка git commit: {result.stderr}')
    sys.exit(1)

print()

# 5. Git push
print('【5】Git push:')
print('-' * 80)
result = subprocess.run(['git', 'push'], capture_output=True, text=True)

if result.returncode == 0:
    print('✅ Push выполнен успешно')
    print()
    print('stdout:', result.stdout)
    if result.stderr:
        print('stderr:', result.stderr)
else:
    print(f'❌ Ошибка git push: {result.stderr}')
    print()
    print('Возможные причины:')
    print('  • Нет настроенного remote')
    print('  • Требуется аутентификация')
    print('  • Конфликт с remote branch')
    print()
    print('Попробуй вручную:')
    print('  git push origin main')
    sys.exit(1)

print()
print('=' * 80)
print('ГОТОВО!')
print('=' * 80)
print()
print('Версия: 3.2.3')
print('Commit: создан и запушен')
print()
print('Что было сделано в этой сессии:')
print('  ✅ Backend конфигуратор DDA (config.yaml + endpoints)')
print('  ✅ Frontend UI конфигуратор (4 вкладки)')
print('  ✅ Интеграция математики с конфигом')
print('  ✅ Косметические исправления (монохром, стили)')
print()
print('Следующие шаги:')
print('  • ChartModal (кнопка ⛶ для полноэкранных графиков)')
print('  • Итерация A Day 3-4 (FFT сезонность)')
print('  • Или другая задача?')