from pathlib import Path

print('=== add_energy_effect.py ===')
print()

config_path = Path('frontend/src/routes/Config.svelte')
content = config_path.read_text(encoding='utf-8')

# Проверяем что уже есть
if 'if (activeTab === \'energy\')' in content and 'loadEnergyData()' in content:
    print('ℹ $effect для energy уже есть')
    exit(0)

# Ищем $effect для resolveCity и вставляем после него новый $effect для energy
effect_pattern = '''  // Автоматически вызываем resolveCity при изменении города
  $effect(() => {
    const city = envConfig?.city
    if (city) resolveCity()
  })'''

new_effect = '''  // Автоматически вызываем resolveCity при изменении города
  $effect(() => {
    const city = envConfig?.city
    if (city) resolveCity()
  })

  // Автозагрузка данных энергоучёта при переключении вкладки
  $effect(() => {
    if (activeTab === 'energy' && !energyConfig) {
      loadEnergyData()
    }
  })'''

if effect_pattern in content:
    content = content.replace(effect_pattern, new_effect)
    config_path.write_text(content, encoding='utf-8', newline='\n')
    print('✓ Добавлен $effect для автозагрузки энергоучёта')
    print()
    print('Vite подхватит через HMR.')
    print('Открой Конфигуратор → вкладка "Энергоучёт"')
    print('Должны загрузиться тарифы и счётчики.')
else:
    print('⚠ Не нашёл точный паттерн $effect для resolveCity')
    print('Ищу альтернативу...')
    
    # Пробуем найти по другому паттерну
    if 'resolveCity()' in content and '$effect' in content:
        # Ищем позицию где есть $effect с resolveCity
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'resolveCity()' in line and '$effect' in ''.join(lines[max(0,i-5):i]):
                print(f'  Нашёл resolveCity в строке {i+1}')
                # Вставляем после закрывающей } этого $effect
                # Ищем следующую пустую строку или следующую функцию
                for j in range(i, min(len(lines), i+10)):
                    if lines[j].strip() == '})' or lines[j].strip() == '})':
                        # Нашли конец $effect
                        insert_pos = j + 1
                        new_lines = lines[:insert_pos] + [
                            '',
                            '  // Автозагрузка данных энергоучёта при переключении вкладки',
                            '  $effect(() => {',
                            '    if (activeTab === \'energy\' && !energyConfig) {',
                            '      loadEnergyData()',
                            '    }',
                            '  })',
                        ] + lines[insert_pos:]
                        content = '\n'.join(new_lines)
                        config_path.write_text(content, encoding='utf-8', newline='\n')
                        print('✓ Добавлен $effect для автозагрузки энергоучёта (альтернативный метод)')
                        break
                break