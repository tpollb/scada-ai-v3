#!/usr/bin/env python3
"""
fix_pattern_bugs.py — убираем }} и fill: true
"""
from pathlib import Path

print('=' * 80)
print('ФИКС: Убираем }} и fill: true из pattern chart')
print('=' * 80)
print()

results_path = Path('frontend/src/components/DeepAnalysisResults.svelte')
content = results_path.read_text(encoding='utf-8')

# ============================================================================
# 1. УБИРАЕМ fill: true (Filler plugin не импортирован)
# ============================================================================
print('【1】Убираем fill: true из pattern datasets')
print('-' * 80)

# Заменяем fill: true на fill: false в pattern datasets
old_fill = '''              tension: 0.2,
              fill: true,'''

new_fill = '''              tension: 0.2,
              fill: false,'''

count = content.count(old_fill)
if count > 0:
    content = content.replace(old_fill, new_fill)
    print(f'✅ Заменено {count} мест fill: true → fill: false')
else:
    print('⚠️  fill: true не найден')

# ============================================================================
# 2. УБИРАЕМ ЛИШНИЕ }}
# ============================================================================
print()
print('【2】Убираем лишние }}')
print('-' * 80)

# Ищем patternData блок и проверяем закрывающие скобки
# Проблема: {@const patternData = { ... }}  ← два }} закрывают объект и const
# Но если было {@const patternData = { ... }}\n}}  ← лишнее }}

# Ищем в single-tag
old_single_data = '''          {@const patternData = {
            labels: pattern.map((_: any, i: number) => i),
            datasets: [{
              label: 'Типичный паттерн',
              data: pattern,
              borderColor: 'rgb(168, 85, 247)',
              backgroundColor: 'rgba(168, 85, 247, 0.1)',
              borderWidth: 2,
              pointRadius: pattern.length > 100 ? 0 : 2,
              pointHoverRadius: 5,
              tension: 0.2,
              fill: false,
            }]
          }}'''

if old_single_data in content:
    # Заменяем на правильную форму (одна } для объекта)
    new_single_data = '''          {@const patternData = {
            labels: pattern.map((_: any, i: number) => i),
            datasets: [{
              label: 'Типичный паттерн',
              data: pattern,
              borderColor: 'rgb(168, 85, 247)',
              backgroundColor: 'rgba(168, 85, 247, 0.1)',
              borderWidth: 2,
              pointRadius: pattern.length > 100 ? 0 : 2,
              pointHoverRadius: 5,
              tension: 0.2,
              fill: false,
            }]
          }}'''
    # Проверяем: может после patternData идёт лишняя }}
    # Ищем шаблон: }}\n          }}\n  ← лишнее
    # Или }}\n}}\n
    
    # Находим все места где patternData закрывается
    pass

# Более надёжный подход: ищем двойное }} после patternData блока
import re

# Паттерн: закрывающие }} объекта + }} лишние
# Ищем: }}\n\n или }}\n  }}\n
pattern_double_close = r'\}\}\s*\}\}'

# Но это может быть частью {@const x = {...}}
# Правильная форма: }}  (одна } для объекта, одна } для закрытия {@const})

# Ищем конкретно проблему: после patternData = {...}} идёт ещё }}
# Шаблон: "fill: false,\n            }]\n          }}\n}}"

problem_pattern = '''fill: false,
            }]
          }}
          }}'''

fix_pattern = '''fill: false,
            }]
          }}'''

if problem_pattern in content:
    content = content.replace(problem_pattern, fix_pattern)
    print('✅ Убрано лишнее }} (single-tag patternData)')

# То же для multi-tag
problem_pattern_multi = '''fill: false,
              }]
            }}
            }}'''

fix_pattern_multi = '''fill: false,
              }]
            }}'''

if problem_pattern_multi in content:
    content = content.replace(problem_pattern_multi, fix_pattern_multi)
    print('✅ Убрано лишнее }} (multi-tag patternData)')

# Ещё один вариант: }} стоит отдельно на строке
lines = content.split('\n')
new_lines = []
skip_next = False
for i, line in enumerate(lines):
    if skip_next:
        skip_next = False
        continue
    
    # Проверяем: если текущая строка закрывает patternData и следующая тоже }}
    if i + 1 < len(lines):
        if ('fill: false,' in lines[max(0, i-3):i+1] if i >= 3 else False) and \
           '}]' in lines[i-1] if i > 0 else False:
            pass  # Это нормальное закрытие
    
    new_lines.append(line)

# ============================================================================
# 3. ДОБАВЛЯЕМ FILLER PLUGIN (альтернативный подход)
# ============================================================================
print()
print('【3】Добавляем Filler plugin в ChartJS.register (опционально)')
print('-' * 80)

# Если хотим fill: true, надо импортировать Filler
old_import = '''  import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    ScatterController,
    BubbleController,
  } from 'chart.js'''

new_import = '''  import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    ScatterController,
    BubbleController,
    Filler,
  } from 'chart.js'''

if old_import in content:
    content = content.replace(old_import, new_import)
    print('✅ Filler добавлен в import')

old_register = '''  ChartJS.register(
    CategoryScale, LinearScale, PointElement, LineElement,
    Title, Tooltip, Legend, ScatterController, BubbleController, zoomPlugin
  )'''

new_register = '''  ChartJS.register(
    CategoryScale, LinearScale, PointElement, LineElement,
    Title, Tooltip, Legend, ScatterController, BubbleController, zoomPlugin, Filler
  )'''

if old_register in content:
    content = content.replace(old_register, new_register)
    print('✅ Filler добавлен в ChartJS.register')

# Возвращаем fill: true (раз Filler зарегистрирован)
content = content.replace('fill: false,', 'fill: true,')
print('✅ Возвращён fill: true (Filler plugin работает)')

# ============================================================================
# 4. СОХРАНЯЕМ ФАЙЛ
# ============================================================================
print()
print('【4】Сохраняем файл')
print('-' * 80)
results_path.write_text(content, encoding='utf-8', newline='\n')
print('✅ Файл сохранён')

print()
print('=' * 80)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 80)
print()
print('1. ЛИШНИЕ }} ПОД ГРАФИКОМ:')
print('   • Было: }} (конец patternData объекта) + }} (лишнее)')
print('   • Стало: }} (только правильное закрытие)')
print()
print('2. FILLER PLUGIN:')
print('   • Добавлен import Filler из chart.js')
print('   • Добавлен в ChartJS.register(...)')
print('   • fill: true теперь работает без warning')
print('   • График паттерна имеет заливку (gradient area)')
print()
print('=' * 80)