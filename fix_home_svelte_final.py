from pathlib import Path
import re

print('=== fix_home_svelte_final.py ===')
print()

home_path = Path('frontend/src/routes/Home.svelte')
content = home_path.read_text(encoding='utf-8')

changes = []

# ============================================================================
# 1. Добавляем импорт DeepAnalysisPanel (если его нет)
# ============================================================================
if "from '../components/DeepAnalysisPanel.svelte'" not in content:
    # Ищем импорт SystemLogsPanel и добавляем наш после него
    old_import = "import SystemLogsPanel from '../components/SystemLogsPanel.svelte'"
    if old_import in content:
        new_import = old_import + "\n  import DeepAnalysisPanel from '../components/DeepAnalysisPanel.svelte'"
        content = content.replace(old_import, new_import)
        changes.append('✓ Добавлен импорт: DeepAnalysisPanel')
    else:
        # Ищем блок <script> и добавляем в конец
        script_pattern = r"(<script lang=\"ts\">.*?)(</script>)"
        match = re.search(script_pattern, content, re.DOTALL)
        if match:
            script_content = match.group(1)
            insert_pos = match.start(2)
            content = content[:insert_pos] + "\n  import DeepAnalysisPanel from '../components/DeepAnalysisPanel.svelte'\n" + content[insert_pos:]
            changes.append('✓ Добавлен импорт: DeepAnalysisPanel (альтернативный путь)')
        else:
            print('❌ Не удалось добавить импорт компонента')

# ============================================================================
# 2. Добавляем блок рендеринга (если его нет)
# ============================================================================
if '<DeepAnalysisPanel' not in content:
    # Ищем блок с SystemLogsPanel рендерингом
    logs_render_pattern = r'(\{#if showLogsPanel\}\s*<SystemLogsPanel[^}]*\{/if\})'
    match = re.search(logs_render_pattern, content, re.DOTALL)
    if match:
        logs_block = match.group(1)
        dda_block = """
    {#if showDeepAnalysisPanel}
      <DeepAnalysisPanel onClose={() => showDeepAnalysisPanel = false} />
    {/if}"""
        content = content.replace(logs_block, logs_block + dda_block)
        changes.append('✓ Добавлен блок рендеринга: <DeepAnalysisPanel />')
    else:
        # Альтернативный путь — ищем <div class="flex-1 flex overflow-hidden">
        # и вставляем туда
        div_pattern = r'(<div class="flex-1 flex overflow-hidden">)'
        match = re.search(div_pattern, content)
        if match:
            insert_pos = match.end()
            dda_block = """
    {#if showDeepAnalysisPanel}
      <DeepAnalysisPanel onClose={() => showDeepAnalysisPanel = false} />
    {/if}"""
            content = content[:insert_pos] + dda_block + content[insert_pos:]
            changes.append('✓ Добавлен блок рендеринга (альтернативный путь)')
        else:
            print('❌ Не удалось добавить блок рендеринга')

if not changes:
    print('ℹ Все изменения уже применены')
else:
    home_path.write_text(content, encoding='utf-8', newline='\n')
    for c in changes:
        print(c)
    print()
    print('✓ Home.svelte обновлён')

print()
print('=' * 70)
print('ПРОВЕРКА:')
print('=' * 70)

# Проверка после обновления
content_check = home_path.read_text(encoding='utf-8')
print()
print('1. Импорт DeepAnalysisPanel:')
for i, line in enumerate(content_check.split('\n'), 1):
    if 'DeepAnalysisPanel' in line and 'import' in line:
        print(f'   Строка {i}: {line.strip()}')

print()
print('2. Блок рендеринга:')
for i, line in enumerate(content_check.split('\n'), 1):
    if '<DeepAnalysisPanel' in line:
        # Печатаем контекст
        lines = content_check.split('\n')
        for j in range(max(0, i-3), min(len(lines), i+2)):
            marker = '>>>' if j+1 == i else '   '
            print(f'   {marker} Строка {j+1}: {lines[j]}')

print()
print('=' * 70)
print('Frontend перезагрузится автоматически (Vite HMR).')
print()
print('Проверка:')
print('  1. Открой фронтенд')
print('  2. Клик на кнопку Activity (график) в хедере')
print('  3. Должна открыться DeepAnalysisPanel слева')
print('  4. Выбери тег → запусти анализ → увидишь график')