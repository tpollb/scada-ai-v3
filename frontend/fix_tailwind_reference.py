from pathlib import Path

print('=== fix_tailwind_reference.py ===')
print()

viewer_path = Path('src/components/DocsViewer.svelte')
content = viewer_path.read_text(encoding='utf-8')

# Проверяем есть ли уже @reference
if '@reference' in content:
    print('ℹ @reference уже есть в DocsViewer.svelte')
else:
    # Добавляем @reference в начало <style> блока
    old_style = '<style>'
    new_style = '<style>\n  @reference "../app.css";'
    
    if old_style in content:
        content = content.replace(old_style, new_style, 1)
        viewer_path.write_text(content, encoding='utf-8', newline='\n')
        print('✓ Добавлен @reference "../app.css" в начало <style>')
        print('  Это импортирует тему Tailwind без дублирования CSS')
        print('  Путь ../app.css — относительно от src/components/')
    else:
        print('⚠ Не нашёл <style> блок')

print()
print('=' * 60)
print('ЧТО ПРОИСХОДИТ:')
print('=' * 60)
print('Tailwind v4 требует @reference при использовании @apply')
print('в <style> блоках Svelte/Vue компонентов.')
print()
print('@reference "../app.css":')
print('  • Импортирует тему (цвета, шрифты, breakpoints)')
print('  • НЕ дублирует CSS в выводе (только для reference)')
print('  • Делает @apply рабочим в этом компоненте')
print()
print('Vite подхватит через HMR. Ошибка должна исчезнуть.')