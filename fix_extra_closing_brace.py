#!/usr/bin/env python3
"""
fix_extra_closing_brace.py — убираем лишнюю } после {/if} в pattern блоках
"""
from pathlib import Path

print('=' * 80)
print('ФИКС: Убираем лишнюю } после {/if} в pattern блоках')
print('=' * 80)
print()

results_path = Path('frontend/src/components/DeepAnalysisResults.svelte')
content = results_path.read_text(encoding='utf-8')

# Ищем проблему: {/if}} (лишняя } после {/if})
print('【1】Ищем и исправляем {/if}}')
print('-' * 80)

# Подсчитываем сколько раз встречается
count = content.count('{/if}}')
print(f'   Найдено {count} мест с лишней }}')

# Заменяем {/if}} на {/if}
if count > 0:
    content = content.replace('{/if}}', '{/if}')
    print(f'✅ Исправлено {count} мест')
else:
    print('⚠️  Не найдено {/if}}')

# Дополнительная проверка: ищем любые подозрительные }} в конце строк
print()
print('【2】Проверяем другие возможные проблемы')
print('-' * 80)

lines = content.split('\n')
suspicious = []
for i, line in enumerate(lines, 1):
    stripped = line.strip()
    # Ищем строки которые заканчиваются на }} но это не {@const ...}
    if stripped.endswith('}}') and '{@const' not in stripped:
        suspicious.append((i, stripped))

if suspicious:
    print(f'   Найдено {len(suspicious)} подозрительных строк:')
    for line_num, line_text in suspicious[:5]:
        print(f'   Строка {line_num}: {line_text[:80]}')
else:
    print('✅ Других подозрительных }} не найдено')

# Сохраняем файл
print()
print('【3】Сохраняем файл')
print('-' * 80)
results_path.write_text(content, encoding='utf-8', newline='\n')
print('✅ Файл сохранён')

print()
print('=' * 80)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 80)
print()
print('ПРОБЛЕМА:')
print('  На строке 719 (примерно) было: {/if}}')
print('  Две закрывающие скобки после {/if}')
print()
print('ПРИЧИНА:')
print('  </div>           ← закрывает div')
print('  {/if}}           ← ОШИБКА: лишняя }')
print()
print('РЕШЕНИЕ:')
print('  </div>           ← закрывает div')
print('  {/if}            ← ПРАВИЛЬНО: только {/if}')
print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Frontend перезагрузится автоматически')
print('2. Лишняя } после "Мин: ... | Макс: ... | Размах: ..." исчезнет')
print('3. График паттерна работает корректно')
print('4. Кнопки (+) (-) сброс PNG fullscreen работают')
print('5. Hover показывает tooltip с значением')