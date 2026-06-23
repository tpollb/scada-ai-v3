from pathlib import Path

print('=== fix_home_final_v3.py ===')
print()

home_path = Path('frontend/src/routes/Home.svelte')
content = home_path.read_text(encoding='utf-8')

changes = []

# 1. Удаляем дубликат SystemLogsPanel (строки ~286-288)
duplicate_block = """

    {#if showLogsPanel}
      <SystemLogsPanel onClose={() => showLogsPanel = false} />
    {/if}"""

if duplicate_block in content:
    # Ищем второе вхождение (первое правильное на строке ~270)
    first_pos = content.find(duplicate_block)
    if first_pos >= 0:
        second_pos = content.find(duplicate_block, first_pos + 1)
        if second_pos >= 0:
            content = content[:second_pos] + content[second_pos + len(duplicate_block):]
            changes.append('Удалён дубликат SystemLogsPanel (строки ~286-288)')

# 2. Добавляем {/if} после <Input onSend={handleSend} />
# Ищем паттерн:
#       <Input onSend={handleSend} />
#     </div>
# Должно стать:
#       <Input onSend={handleSend} />
#     {/if}
#     </div>

input_pattern = """      <Input onSend={handleSend} />
    </div>"""

input_fixed = """      <Input onSend={handleSend} />
    {/if}
    </div>"""

if input_pattern in content:
    content = content.replace(input_pattern, input_fixed, 1)
    changes.append('Добавлен {/if} для закрытия блока showDeepAnalysisPanel')

# Сохраняем
home_path.write_text(content, encoding='utf-8', newline='\n')

print('=' * 70)
print('ИСПРАВЛЕНИЯ:')
print('=' * 70)
for c in changes:
    print(f'  ✓ {c}')

print()
print('Frontend должен перезагрузиться автоматически (Vite HMR).')
print('Ошибка компиляции должна исчезнуть.')
print()
print('Проверка:')
print('  1. Клик Activity в хедере')
print('  2. Слева панель с controls (тег, период, кнопка)')
print('  3. В dropdown список тегов')
print('  4. Выбери тег → "Запустить анализ"')
print('  5. В центральной части график и статистика')