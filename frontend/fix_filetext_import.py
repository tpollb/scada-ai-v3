from pathlib import Path
import re

print('=== fix_filetext_import.py ===')
print()

config_path = Path('src/routes/Config.svelte')
content = config_path.read_text(encoding='utf-8')

# Ищем импорт lucide-svelte (гибкий поиск)
# Паттерн: import { ... } from 'lucide-svelte'
pattern = r"(import\s*\{[^}]*)(\}\s*from\s*['\"]lucide-svelte['\"])"

match = re.search(pattern, content)
if not match:
    print('⚠ Не нашёл импорт lucide-svelte')
    print('Покажи текущее состояние импортов:')
    for i, line in enumerate(content.split('\n')[:20], 1):
        print(f'  {i}: {line}')
else:
    imports_before_closing = match.group(1)
    closing = match.group(2)
    
    # Проверяем что уже импортировано
    if 'FileText' in imports_before_closing:
        print('ℹ FileText уже импортирован')
    else:
        # Добавляем FileText перед закрывающей }
        new_imports = imports_before_closing.rstrip() + ', FileText '
        new_import_line = new_imports + closing
        old_import_line = match.group(0)
        
        content = content.replace(old_import_line, new_import_line, 1)
        print('✓ Добавлен FileText в импорт lucide-svelte')
        
        # Также проверим что DocsViewer импортирован
        if 'DocsViewer' not in content:
            # Добавим импорт DocsViewer после импорта api
            if "import api from '../lib/api'" in content:
                content = content.replace(
                    "import api from '../lib/api'",
                    "import api from '../lib/api'\n  import DocsViewer from '../components/DocsViewer.svelte'"
                )
                print('✓ Добавлен импорт DocsViewer')
            else:
                print('⚠ Не нашёл импорт api для добавления DocsViewer')
        else:
            print('ℹ DocsViewer уже импортирован')
        
        config_path.write_text(content, encoding='utf-8', newline='\n')
        print(f'✓ Сохранён: {config_path}')

print()
print('Проверка: Vite подхватит через HMR, обнови страницу конфигуратора.')