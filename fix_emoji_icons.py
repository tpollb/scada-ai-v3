from pathlib import Path

print('=== fix_emoji_icons.py ===')
print()

config_path = Path('frontend/src/routes/Config.svelte')
content = config_path.read_text(encoding='utf-8')

changes = []

# 1. Добавляем импорты Droplet и Flame (Zap уже есть)
old_import = "import { ArrowLeft, RefreshCw, Save, AlertCircle, CheckCircle, Server, Database, Key, Sun, Moon, FileText, Wrench, Plus, Trash2, Edit2, DollarSign, Zap } from 'lucide-svelte'"
new_import = "import { ArrowLeft, RefreshCw, Save, AlertCircle, CheckCircle, Server, Database, Key, Sun, Moon, FileText, Wrench, Plus, Trash2, Edit2, DollarSign, Zap, Droplet, Flame } from 'lucide-svelte'"

if old_import in content:
    content = content.replace(old_import, new_import)
    changes.append('✓ Добавлены импорты Droplet, Flame')
else:
    print('⚠ Не нашёл точный паттерн импорта')

# 2. Заменяем эмодзи на иконки
# Старый: {res === 'electricity' ? '⚡ Электричество' : res === 'water' ? '💧 Вода' : '🔥 Тепло'}
# Новый: используем компонент с иконкой
old_emoji_line = "                  {res === 'electricity' ? '⚡ Электричество' : res === 'water' ? '💧 Вода' : '🔥 Тепло'}"

new_icon_line = '''                  <span class="flex items-center gap-1.5">
                    {#if res === 'electricity'}
                      <Zap size={14} />
                      <span>Электричество</span>
                    {:else if res === 'water'}
                      <Droplet size={14} />
                      <span>Вода</span>
                    {:else}
                      <Flame size={14} />
                      <span>Тепло</span>
                    {/if}
                  </span>'''

if old_emoji_line in content:
    content = content.replace(old_emoji_line, new_icon_line)
    changes.append('✓ Эмодзи ⚡💧🔥 заменены на монохромные иконки Zap, Droplet, Flame')
else:
    print('⚠ Не нашёл точный паттерн с эмодзи')

if changes:
    config_path.write_text(content, encoding='utf-8', newline='\n')
    print()
    for change in changes:
        print(f'  {change}')
    print()
    print('Vite подхватит через HMR.')
    print('Открой Конфигуратор → Энергоучёт')
    print('Кнопки ресурсов должны стать монохромными.')
else:
    print('ℹ Изменений не требуется')