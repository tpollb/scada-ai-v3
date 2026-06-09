from pathlib import Path

print('=== fix_environmental_panel.py ===')
print()

file_path = Path('frontend/src/components/health/EnvironmentalPanel.svelte')
content = file_path.read_text(encoding='utf-8')

# Ищем проблемный паттерн
old_pattern = '''    {/each}
  </div>
</div>

  {/if}

<!-- Модалка drilldown -->'''

new_pattern = '''    {/each}
  </div>
  {/if}
</div>

<!-- Модалка drilldown -->'''

if old_pattern in content:
    content = content.replace(old_pattern, new_pattern)
    file_path.write_text(content, encoding='utf-8', newline='\n')
    print('✓ Исправлена структура {#if !collapsed} в EnvironmentalPanel')
    print()
    print('Было:')
    print('  </div>  ← закрывает grid')
    print('</div>  ← закрывает внешний контейнер')
    print()
    print('  {/if}  ← закрывает {#if !collapsed}')
    print()
    print('Стало:')
    print('  </div>  ← закрывает grid')
    print('  {/if}   ← закрывает {#if !collapsed}')
    print('</div>    ← закрывает внешний контейнер')
    print()
    print('Vite подхватит через HMR.')
    print('Открой health report — все 3 блока должны быть свёрнуты.')
else:
    print('⚠ Паттерн не найден — возможно уже исправлено')
    print()
    print('Проверяю наличие {#if !collapsed}...')
    if '{#if !collapsed}' in content:
        print('✓ {#if !collapsed} найден')
    else:
        print('❌ {#if !collapsed} не найден')