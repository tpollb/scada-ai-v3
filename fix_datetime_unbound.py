#!/usr/bin/env python3
"""
fix_datetime_unbound.py — исправляем UnboundLocalError для datetime
"""

from pathlib import Path
import re

print('=' * 70)
print('ФИКС: UnboundLocalError: datetime + td.unit')
print('=' * 70)
print()

api_path = Path('backend/modules/deep_analysis/api.py')
content = api_path.read_text(encoding='utf-8')

# Удаляем проблемный локальный импорт datetime внутри функции
pattern = r'\s*from datetime import datetime\s*\n(\s*)time_series_spec = create_multitag_time_series_spec\('
new_replacement = r'\n\1time_series_spec = create_multitag_time_series_spec('
content_new, count = re.subn(pattern, new_replacement, content)

if count > 0:
    content = content_new
    print(f'✓ Удалён лишний импорт datetime внутри функции ({count} вхождений)')
else:
    # Пробуем альтернативный паттерн
    if 'from datetime import datetime\n            time_series_spec' in content:
        content = content.replace(
            'from datetime import datetime\n            time_series_spec',
            'time_series_spec'
        )
        print('✓ Удалён лишний импорт datetime (alt pattern)')
    else:
        print('⚠ Не удалось найти проблемный импорт')

api_path.write_text(content, encoding='utf-8', newline='\n')

# ============================================================================
# Бонус: tag_resolver.py — убираем td.unit (нет в схеме БД)
# ============================================================================
print()
print('БОНУС: tag_resolver.py (убираем td.unit)')
print('-' * 70)

resolver_path = Path('backend/modules/deep_analysis/collectors/tag_resolver.py')
if resolver_path.exists():
    resolver_content = resolver_path.read_text(encoding='utf-8')
    
    if 'td.unit,' in resolver_content:
        # Убираем td.unit, из основного SELECT
        resolver_content = resolver_content.replace(
            "            td.tag_name,\n            td.unit,\n            (",
            "            td.tag_name,\n            ("
        )
        resolver_path.write_text(resolver_content, encoding='utf-8', newline='\n')
        print('✓ Убран td.unit из SELECT (нет в схеме БД)')
    else:
        print('ℹ td.unit уже не используется')

print()
print('=' * 70)
print('ОБЪЯСНЕНИЕ ПРОБЛЕМЫ:')
print('=' * 70)
print()
print('Когда Python видит `from datetime import datetime` внутри функции,')
print('он помечает `datetime` как ЛОКАЛЬНУЮ переменную для всей функции.')
print()
print('Но до этого локального импорта был вызов `datetime.now()` — ')
print('Python считает что это обращение к локальной переменной,')
print('которая ещё не инициализирована → UnboundLocalError.')
print()
print('Решение: использовать глобальный импорт сверху файла.')
print()
print('=' * 70)
print('ПРОВЕРКА:')
print('=' * 70)
print()
print('Перезапусти backend и проверь:')
print()
print('  curl -X POST http://localhost:8081/api/v1/deep_analysis/run \\')
print('    -H "Content-Type: application/json" \\')
print('    -d \'{"tags": ["KITCHEN2-CO2", "KITCHEN2-Temperature"], "period": 30}\'')
print()
print('Должно вернуться без UnboundLocalError:')
print('  • time_series с линиями обоих тегов')
print('  • scatter points для аномалий по типам')
print('  • anomalies.per_tag с деталями по каждому тегу')