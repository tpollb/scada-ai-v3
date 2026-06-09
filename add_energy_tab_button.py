from pathlib import Path

print('=== add_energy_tab_button.py ===')
print()

config_path = Path('frontend/src/routes/Config.svelte')
content = config_path.read_text(encoding='utf-8')

# Ищем кнопку "Документация" и вставляем "Энергоучёт" после неё
docs_button_pattern = '''      <button
        type="button"
        onclick={() => activeTab = 'docs'}
        class="px-4 py-1.5 text-sm font-medium rounded transition flex items-center gap-2 {activeTab === 'docs' ? 'bg-white shadow-sm text-neutral-900' : 'text-neutral-600 hover:text-neutral-900'}"
      >
        <FileText size={14} />
        Документация
      </button>'''

energy_button = '''      <button
        type="button"
        onclick={() => activeTab = 'energy'}
        class="px-4 py-1.5 text-sm font-medium rounded transition flex items-center gap-2 {activeTab === 'energy' ? 'bg-white shadow-sm text-neutral-900' : 'text-neutral-600 hover:text-neutral-900'}"
      >
        <DollarSign size={14} />
        Энергоучёт
      </button>'''

if docs_button_pattern in content:
    # Проверяем что кнопка energy уже есть
    if 'onclick={() => activeTab = \'energy\'}' in content:
        print('ℹ Кнопка "Энергоучёт" уже есть')
    else:
        content = content.replace(docs_button_pattern, docs_button_pattern + '\n' + energy_button)
        config_path.write_text(content, encoding='utf-8', newline='\n')
        print('✓ Кнопка "Энергоучёт" добавлена после "Документация"')
        print()
        print('Vite подхватит через HMR.')
        print('Открой Конфигуратор — должна появиться 4-я вкладка "Энергоучёт" с иконкой $.')
else:
    print('⚠ Не нашёл точный паттерн кнопки "Документация"')
    print('Ищу альтернативные паттерны...')
    
    # Пробуем найти по ключевым словам
    if 'Документация' in content and 'FileText' in content:
        print('✓ Нашёл "Документация" и FileText в файле')
        # Показываем контекст
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'Документация' in line:
                print(f'  Строка {i+1}: {line.strip()}')
                print(f'  Контекст (±3 строки):')
                for j in range(max(0, i-3), min(len(lines), i+4)):
                    marker = '→' if j == i else ' '
                    print(f'    {marker} {j+1}: {lines[j]}')
                break
    else:
        print('❌ Не нашёл "Документация" в файле')

print()
print('Проверка блока рендеринга:')
if '{:else if activeTab === \'energy\'}' in content:
    print('✓ Блок рендеринга для activeTab === \'energy\' есть')
else:
    print('❌ Блок рендеринга для activeTab === \'energy\' отсутствует')