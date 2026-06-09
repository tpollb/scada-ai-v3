from pathlib import Path
import re

print('=== fix_collapsible_panels.py (исправленный) ===')
print()

files_to_fix = [
    'frontend/src/components/health/EnvironmentalPanel.svelte',
    'frontend/src/components/health/AlarmsPanel.svelte',
    'frontend/src/components/health/IssuesList.svelte',
]

# Паттерны которые нужно исправить
patterns = [
    # EnvironmentalPanel / AlarmsPanel: </div></div> {/if}
    ('''    {/each}
  </div>
</div>

  {/if}

<!-- Модалка''',
     '''    {/each}
  </div>
  {/if}
</div>

<!-- Модалка'''),
    
    # AlarmsPanel альтернативный
    ('''    {/if}
  </div>
</div>

  {/if}

<!-- Модалка''',
     '''    {/if}
  </div>
  {/if}
</div>

<!-- Модалка'''),
]

for file_path in files_to_fix:
    path = Path(file_path)
    if not path.exists():
        print(f'⚠ Файл не найден: {file_path}')
        continue
    
    content = path.read_text(encoding='utf-8')
    changed = False
    
    for old_pattern, new_pattern in patterns:
        if old_pattern in content:
            content = content.replace(old_pattern, new_pattern)
            changed = True
            print(f'✓ {path.name}: исправлен паттерн')
    
    if changed:
        path.write_text(content, encoding='utf-8', newline='\n')

# Проверяем структуру
print()
print('=' * 60)
print('ПРОВЕРКА СТРУКТУРЫ:')
print('=' * 60)

for file_path in files_to_fix:
    path = Path(file_path)
    if not path.exists():
        continue
    
    content = path.read_text(encoding='utf-8')
    has_collapsed_if = '{#if !collapsed}' in content
    
    if has_collapsed_if:
        pos_open = content.find('{#if !collapsed}')
        
        if 'Модалка' in content:
            pos_modal = content.find('<!-- Модалка')
            pos_close = content.rfind('{/if}', 0, pos_modal)
            
            if pos_close > pos_open and pos_close < pos_modal:
                print(f'✓ {path.name}: структура корректна')
                print(f'  • {{#if !collapsed}} на строке {content[:pos_open].count(chr(10))+1}')
                print(f'  • {{/if}} на строке {content[:pos_close].count(chr(10))+1}')
                print(f'  • Модалка на строке {content[:pos_modal].count(chr(10))+1} (ВНЕ блока)')
            else:
                print(f'⚠ {path.name}: возможно некорректная структура')
        else:
            print(f'✓ {path.name}: структура проверена')
    else:
        print(f'⚠ {path.name}: {{#if !collapsed}} не найден')

print()
print('Vite подхватит через HMR.')
print('Открой health report — все 3 блока должны быть свёрнуты.')