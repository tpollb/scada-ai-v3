from pathlib import Path
import re

print('=== fix_docs_viewer_styles.py ===')
print()

viewer_path = Path('src/components/DocsViewer.svelte')
if not viewer_path.exists():
    print(f'❌ Файл не найден: {viewer_path}')
    exit(1)

content = viewer_path.read_text(encoding='utf-8')

# Новый стиль: explicit CSS без @apply в :global()
new_style = '''<style>
  @reference "../app.css";
  
  /* Базовый цвет текста */
  :global(.prose) {
    color: var(--color-neutral-900);
    line-height: 1.75;
  }
  :global(.dark .prose) {
    color: var(--color-neutral-100);
  }

  /* Заголовки */
  :global(.prose h1, .prose h2, .prose h3, .prose h4) {
    color: var(--color-neutral-900);
    font-weight: 700;
    margin-top: 2rem;
    margin-bottom: 1rem;
  }
  :global(.dark .prose h1, .dark .prose h2, .dark .prose h3, .dark .prose h4) {
    color: var(--color-neutral-100);
  }
  :global(.prose h1) { font-size: 1.875rem; border-bottom: 1px solid var(--color-neutral-200); padding-bottom: 0.5rem; }
  :global(.prose h2) { font-size: 1.5rem; border-bottom: 1px solid var(--color-neutral-200); padding-bottom: 0.5rem; }
  :global(.dark .prose h1, .dark .prose h2) { border-color: var(--color-neutral-700); }

  /* Параграфы, списки, ячейки */
  :global(.prose p, .prose li, .prose td, .prose th) {
    color: var(--color-neutral-800);
    margin-bottom: 0.75rem;
  }
  :global(.dark .prose p, .dark .prose li, .dark .prose td, .dark .prose th) {
    color: var(--color-neutral-200);
  }

  /* Код */
  :global(.prose code) {
    background: var(--color-neutral-100);
    color: var(--color-neutral-900);
    padding: 0.2em 0.4em;
    border-radius: 0.25rem;
    font-size: 0.875em;
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  }
  :global(.dark .prose code) {
    background: var(--color-neutral-800);
    color: var(--color-neutral-100);
  }

  /* Блоки кода */
  :global(.prose pre) {
    background: var(--color-neutral-100);
    border: 1px solid var(--color-neutral-200);
    border-radius: 0.5rem;
    padding: 1rem;
    overflow-x: auto;
    margin: 1rem 0;
  }
  :global(.dark .prose pre) {
    background: var(--color-neutral-800);
    border-color: var(--color-neutral-700);
  }
  :global(.prose pre code) {
    background: transparent;
    padding: 0;
    color: inherit;
    border: none;
  }

  /* Ссылки */
  :global(.prose a) {
    color: var(--color-blue-600);
    text-decoration: underline;
    text-underline-offset: 2px;
  }
  :global(.dark .prose a) {
    color: var(--color-blue-400);
  }

  /* Таблицы */
  :global(.prose table) {
    width: 100%;
    border-collapse: collapse;
    margin: 1rem 0;
  }
  :global(.prose th, .prose td) {
    border: 1px solid var(--color-neutral-300);
    padding: 0.5rem 0.75rem;
    text-align: left;
  }
  :global(.dark .prose th, .dark .prose td) {
    border-color: var(--color-neutral-700);
  }
  :global(.prose th) {
    background: var(--color-neutral-100);
    font-weight: 600;
  }
  :global(.dark .prose th) {
    background: var(--color-neutral-800);
  }

  /* Разделители */
  :global(.prose hr) {
    border: none;
    border-top: 1px solid var(--color-neutral-300);
    margin: 2rem 0;
  }
  :global(.dark .prose hr) {
    border-color: var(--color-neutral-700);
  }

  /* Цитаты */
  :global(.prose blockquote) {
    border-left: 4px solid var(--color-neutral-300);
    padding-left: 1rem;
    font-style: italic;
    color: var(--color-neutral-700);
    margin: 1rem 0;
  }
  :global(.dark .prose blockquote) {
    border-color: var(--color-neutral-600);
    color: var(--color-neutral-300);
  }

  /* Жирный текст */
  :global(.prose strong) {
    font-weight: 600;
    color: var(--color-neutral-900);
  }
  :global(.dark .prose strong) {
    color: var(--color-neutral-100);
  }
</style>'''

# Заменяем весь <style>...</style> блок
pattern = r'<style>[\s\S]*?</style>'
if re.search(pattern, content):
    content = re.sub(pattern, new_style, content, count=1)
    viewer_path.write_text(content, encoding='utf-8', newline='\n')
    print('✓ DocsViewer.svelte: стили заменены на explicit CSS')
    print('  • Убран @apply из :global() (источник бага)')
    print('  • Явные цвета через var(--color-neutral-*)')
    print('  • Корректное наследование для p, li, td, th, code')
    print('  • Полная поддержка light/dark тем')
else:
    print('⚠ Не найден <style> блок в DocsViewer.svelte')
    exit(1)

print()
print('=' * 60)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 60)
print('Корень бага: @apply внутри :global() в Tailwind v4 + Svelte')
print('не всегда пробрасывает цвета на дочерние элементы.')
print()
print('Решение: explicit CSS с CSS-переменными Tailwind v4.')
print('Цвета жёстко заданы для каждого типа элемента.')
print()
print('Vite подхватит через HMR. Обнови страницу конфигуратора.')
print('Проверь документацию в светлой и тёмной теме.')
print()
print('Когда ок — скажи "стили ок"')