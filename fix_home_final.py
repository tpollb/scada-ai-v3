from pathlib import Path
import re

print('=== fix_home_final.py ===')
print()

home_path = Path('frontend/src/routes/Home.svelte')
content = home_path.read_text(encoding='utf-8')
lines = content.split('\n')

# Печатаем структуру в проблемной области для диагностики
print('СТРУКТУРА ФАЙЛА (строки 270-310):')
print('=' * 80)
for i in range(269, min(310, len(lines))):
    print(f'{i+1:4d}: {lines[i]}')
print('=' * 80)
print()

# Анализируем структуру
print('АНАЛИЗ БАЛАНСА:')
open_divs = 0
open_ifs = 0
for i, line in enumerate(lines, 1):
    open_divs += len(re.findall(r'<div(?:\s|>)', line))
    open_divs -= len(re.findall(r'</div>', line))
    open_ifs += len(re.findall(r'\{#if\b', line))
    open_ifs -= len(re.findall(r'\{/if\}', line))
    
    if 270 <= i <= 310:
        markers = []
        if '<div' in line: markers.append(f'[+{len(re.findall(r"<div", line))}div]')
        if '</div>' in line: markers.append(f'[-{len(re.findall(r"</div>", line))}div]')
        if '{#if' in line: markers.append(f'[+{len(re.findall(r"{#if", line))}if]')
        if '{/if}' in line: markers.append(f'[-{len(re.findall(r"{/if}", line))}if]')
        if '{:else}' in line: markers.append('[:else]')
        if markers:
            print(f'  {i:4d}: div={open_divs:+d} if={open_ifs:+d} {line.strip()[:60]} {" ".join(markers)}')

print()

# ============================================================================
# ИСПРАВЛЕНИЯ
# ============================================================================

changes = []

# 1. Удаляем все дубликаты SystemLogsPanel кроме первого
logs_blocks = list(re.finditer(
    r'\s*\{#if showLogsPanel\}\s*<SystemLogsPanel[^}]*\{/if\}\s*',
    content
))

print(f'Найдено блоков SystemLogsPanel: {len(logs_blocks)}')

if len(logs_blocks) > 1:
    # Удаляем все кроме первого (с конца чтобы индексы не сдвигались)
    for match in reversed(logs_blocks[1:]):
        content = content[:match.start()] + '\n' + content[match.end():]
    changes.append(f'Удалено дубликатов SystemLogsPanel: {len(logs_blocks) - 1}')

# 2. Ищем незакрытый блок {#if showDeepAnalysisPanel} с {:else}
# Он должен закрываться перед </div> основного контента
dda_block_pattern = r'(\{#if showDeepAnalysisPanel\}\s*<DeepAnalysisResults[^{]*\{:else\})'
match = re.search(dda_block_pattern, content, re.DOTALL)

if match:
    print(f'Найден блок DDA с Results на позиции {match.start()}')
    
    # Ищем где заканчивается {:else} часть (это обычный контент)
    # Ищем последний </div> перед <aside
    aside_pos = content.find('<aside class="w-80')
    if aside_pos > 0:
        # Ищем закрывающий </div> основного контента (flex-1 flex flex-col)
        # Он должен быть прямо перед <aside
        before_aside = content[:aside_pos]
        
        # Ищем последовательность: <Input ... /> затем </div> затем </aside>
        # Но нам нужно найти </div> который закрывает основной контент
        
        # Проверяем что {/if} отсутствует между {:else} и <aside
        between = content[match.end():aside_pos]
        
        if '{/if}' not in between:
            # Ищем последний </div> перед <aside
            last_div_close = before_aside.rfind('</div>')
            
            if last_div_close > match.end():
                # Вставляем {/if} после </div> но с правильным отступом
                # Определяем отступ </div>
                line_start = before_aside.rfind('\n', 0, last_div_close) + 1
                indent = ' ' * (last_div_close - line_start)
                
                # Вставляем {/if} с отступом после </div>
                insert_pos = last_div_close + 6  # длина </div>
                content = content[:insert_pos] + f'\n{indent}{{/if}}' + content[insert_pos:]
                changes.append('Добавлен {/if} для закрытия блока showDeepAnalysisPanel')

# 3. Удаляем лишние пустые строки (3+ подряд)
content = re.sub(r'\n{3,}', '\n\n', content)

# Сохраняем
home_path.write_text(content, encoding='utf-8', newline='\n')

print()
print('=' * 70)
print('ИСПРАВЛЕНИЯ:')
print('=' * 70)
for c in changes:
    print(f'  ✓ {c}')

# Финальная проверка баланса
content_check = home_path.read_text(encoding='utf-8')
open_divs = len(re.findall(r'<div(?:\s|>)', content_check))
close_divs = len(re.findall(r'</div>', content_check))
open_ifs = len(re.findall(r'\{#if\b', content_check))
close_ifs = len(re.findall(r'\{/if\}', content_check))

print()
print('БАЛАНС:')
print(f'  <div>: {open_divs} / {close_divs} {("✅" if open_divs == close_divs else "❌")}')
print(f'  {{#if}}: {open_ifs} / {close_ifs} {("✅" if open_ifs == close_ifs else "❌")}')

if open_divs == close_divs and open_ifs == close_ifs:
    print()
    print('✅ БАЛАНС ВОССТАНОВЛЕН — ошибка компиляции должна исчезнуть!')
else:
    print()
    print('⚠ ДИСБАЛАНС СОХРАНЯЕТСЯ')
    print('Скинь вывод следующей команды для диагностики:')
    print('  sed -n "270,310p" frontend/src/routes/Home.svelte')