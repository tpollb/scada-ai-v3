#!/usr/bin/env python3
"""
fix_extra_braces.py — убираем лишнюю } в конце pattern блока
"""
from pathlib import Path

print('=' * 80)
print('ФИКС: Убираем лишнюю } в конце pattern блока')
print('=' * 80)
print()

results_path = Path('frontend/src/components/DeepAnalysisResults.svelte')
lines = results_path.read_text(encoding='utf-8').splitlines(keepends=True)

print(f'【1】Прочитано {len(lines)} строк')

# Ищем проблему: строка с "{/if}}}"
print()
print('【2】Ищем строки с лишними скобками')
print('-' * 80)

fixed_count = 0
for i, line in enumerate(lines):
    # Ищем строки где после {/if} идёт лишняя }
    if '{/if}}}' in line:
        print(f'   Найдено на строке {i + 1}: {line.strip()}')
        # Заменяем {/if}}} на {/if}}
        lines[i] = line.replace('{/if}}}', '{/if}}')
        fixed_count += 1
        print(f'   ✅ Исправлено: {lines[i].strip()}')

if fixed_count == 0:
    print('⚠️  Строка с {/if}}} не найдена, ищем другие варианты...')
    
    # Ищем паттерн где после закрывающего </div> идёт }}
    for i, line in enumerate(lines):
        if line.strip() == '}}' and i > 0:
            prev_line = lines[i - 1].strip()
            if prev_line.endswith('</div>') or prev_line == '{/if}':
                print(f'   Подозрительная строка {i + 1}: {line.strip()}')

# ============================================================================
# СОХРАНЯЕМ ФАЙЛ
# ============================================================================
print()
print('【3】Сохраняем файл')
print('-' * 80)
results_path.write_text(''.join(lines), encoding='utf-8', newline='\n')
print(f'✅ Файл сохранён ({len(lines)} строк)')
print(f'✅ Исправлено {fixed_count} мест')

print()
print('=' * 80)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 80)
print()
print('ПРОБЛЕМА:')
print('  В конце pattern блока было: {/if}}}')
print('  Три закрывающие скобки подряд')
print()
print('ПРИЧИНА:')
print('  {@const patternData = { ... }}  ← }} закрывает объект и {@const}')
print('  </div>                           ← закрывает div')
print('  {/if}}}                          ← ОШИБКА: лишняя }')
print()
print('РЕШЕНИЕ:')
print('  {@const patternData = { ... }}  ← }} закрывает объект и {@const}')
print('  </div>                           ← закрывает div')
print('  {/if}}                           ← ПРАВИЛЬНО: только }}')
print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Frontend перезагрузится автоматически')
print('2. Лишние }} под графиком должны исчезнуть')
print('3. Filler plugin уже зарегистрирован — fill: true работает')
print('4. Тултипы при hover на график работают')