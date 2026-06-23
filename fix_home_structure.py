from pathlib import Path

print('=== fix_home_structure.py ===')
print()

home_path = Path('frontend/src/routes/Home.svelte')
content = home_path.read_text(encoding='utf-8')
original = content

changes = []

# ============================================================================
# 1. Удаляем дублирующийся SystemLogsPanel
# ============================================================================
# Ищем все вхождения блока SystemLogsPanel
import re
logs_pattern = r'\s*\{#if showLogsPanel\}\s*<SystemLogsPanel[^}]*\{/if\}\s*'
matches = list(re.finditer(logs_pattern, content))

print(f'Найдено {len(matches)} блоков SystemLogsPanel')

if len(matches) > 1:
    # Оставляем только первый (строка ~280)
    # Удаляем все последующие (строка ~288 и далее)
    for match in reversed(matches[1:]):
        content = content[:match.start()] + content[match.end():]
        print(f'✓ Удалён дубликат SystemLogsPanel на позиции {match.start()}')
    changes.append(f'✓ Удалено {len(matches)-1} дубликатов SystemLogsPanel')

# ============================================================================
# 2. Закрываем незакрытый блок {#if showDeepAnalysisPanel}
# ============================================================================
# Ищем где он открывается с DeepAnalysisResults
dda_results_pattern = r'\{#if showDeepAnalysisPanel\}\s*<DeepAnalysisResults[^}]*\{:else\}'
match = re.search(dda_results_pattern, content)

if match:
    print(f'✓ Найден блок {{#if showDeepAnalysisPanel}} с DeepAnalysisResults')
    
    # Теперь нужно найти где заканчивается основной контент (который в {:else})
    # Ищем <aside class="w-80 border-l — это следующий sibling после основного контента
    aside_pattern = r'<aside class="w-80 border-l'
    aside_match = re.search(aside_pattern, content)
    
    if aside_match:
        # Вставляем {/if} перед <aside>
        insert_pos = aside_match.start()
        
        # Ищем закрывающий </div> основного контента (flex-1 flex flex-col)
        # Он должен быть прямо перед <aside>
        # Находим последнее </div> перед aside_match.start()
        before_aside = content[:insert_pos]
        last_div_close = before_aside.rfind('</div>')
        
        if last_div_close > 0:
            # Проверяем что {/if} ещё нет
            check_region = content[last_div_close:insert_pos]
            if '{/if}' not in check_region:
                # Вставляем {/if} после последнего </div>
                content = content[:last_div_close + 6] + '\n      {/if}\n' + content[last_div_close + 6:]
                changes.append('✓ Добавлен {/if} для закрытия блока DeepAnalysisPanel')
                print(f'✓ Добавлен {{/if}} после строки с </div>')
            else:
                print('ℹ {/if} уже есть')
        else:
            print('⚠ Не найден закрывающий </div> перед <aside>')
    else:
        print('⚠ Не найден <aside class="w-80">')
else:
    print('⚠ Не найден блок {#if showDeepAnalysisPanel} с DeepAnalysisResults')

# ============================================================================
# 3. Удаляем лишние пустые строки
# ============================================================================
content = re.sub(r'\n{3,}', '\n\n', content)

# ============================================================================
# Сохраняем
# ============================================================================
if content != original:
    home_path.write_text(content, encoding='utf-8', newline='\n')
    print('✓ Home.svelte обновлён')
else:
    print('ℹ Файл не изменился')

print()
print('=' * 70)
print('ИСПРАВЛЕНИЯ:')
print('=' * 70)
for c in changes:
    print(f'  {c}')

# Проверяем баланс
content_check = home_path.read_text(encoding='utf-8')
open_ifs = len(re.findall(r'\{#if\b', content_check))
close_ifs = len(re.findall(r'\{/if\}', content_check))
open_divs = len(re.findall(r'<div(?:\s|>)', content_check))
close_divs = len(re.findall(r'</div>', content_check))

print()
print('=' * 70)
print('ПРОВЕРКА БАЛАНСА:')
print('=' * 70)
print(f'  <div>: {open_divs} открыто / {close_divs} закрыто')
print(f'  {{#if}}: {open_ifs} открыто / {close_ifs} закрыто')

if open_divs == close_divs and open_ifs == close_ifs:
    print()
    print('✅ БАЛАНС ВОССТАНОВЛЕН!')
else:
    print()
    print('⚠ ВСЁ ЕЩЁ ЕСТЬ ДИСБАЛАНС')

print()
print('=' * 70)
print('СЛЕДУЮЩИЙ ШАГ:')
print('=' * 70)
print()
print('Frontend должен перезагрузиться автоматически (Vite HMR).')
print('Если ошибка компиляции исчезла — проверь:')
print('  1. Клик Activity в хедере')
print('  2. Слева должна появиться панель с controls')
print('  3. В dropdown появится список тегов')
print('  4. Выбери тег → "Запустить анализ"')
print('  5. В центральной части появится график')