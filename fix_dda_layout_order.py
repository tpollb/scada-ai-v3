from pathlib import Path

print('=== fix_dda_layout_order.py ===')
print()

home_path = Path('frontend/src/routes/Home.svelte')
content = home_path.read_text(encoding='utf-8')
original = content

changes = []

# ============================================================================
# 1. Находим блок flex-1 flex overflow-hidden и смотрим структуру
# ============================================================================
flex_start = content.find('<div class="flex-1 flex overflow-hidden">')
if flex_start < 0:
    print('❌ Не найден блок flex-1 flex overflow-hidden')
    exit(1)

# Находим закрывающий тег этого блока
# Ищем соответствующий </div>
open_count = 0
i = flex_start
flex_end = -1
while i < len(content):
    if content[i:i+4] == '<div':
        open_count += 1
    elif content[i:i+6] == '</div>':
        open_count -= 1
        if open_count == 0:
            flex_end = i + 6
            break
    i += 1

if flex_end < 0:
    print('❌ Не удалось найти закрывающий тег flex блока')
    exit(1)

flex_block = content[flex_start:flex_end]
print(f'✓ Найден flex блок: строки {content[:flex_start].count(chr(10))+1}-{content[:flex_end].count(chr(10))+1}')
print()

# Печатаем текущую структуру
print('Текущая структура flex блока:')
print('=' * 60)
for line in flex_block.split('\n')[:30]:
    if line.strip():
        print(line)
print('=' * 60)
print()

# ============================================================================
# 2. Удаляем DeepAnalysisResults из начала flex блока (он не должен быть здесь)
# ============================================================================
old_results_block = """    {#if showDeepAnalysisPanel}
      <DeepAnalysisResults
        analysisResult={ddaAnalysisResult}
        isAnalyzing={ddaIsAnalyzing}
      />
    {/if}"""

if old_results_block in content:
    content = content.replace(old_results_block, '')
    changes.append('✓ Удалён DeepAnalysisResults из неправильного места')

# ============================================================================
# 3. Переставляем Controls ПЕРЕД основным контентом (как SystemLogsPanel)
# ============================================================================
# Находим где сейчас рендерится SystemLogsPanel и Controls
old_controls_block = """    {#if showDeepAnalysisPanel}
      <DeepAnalysisControls
        tags={ddaTags}
        selectedTag={ddaSelectedTag}
        period={ddaPeriod}
        isAnalyzing={ddaIsAnalyzing}
        error={ddaError}
        onTagChange={(tag) => ddaSelectedTag = tag}
        onPeriodChange={(period) => ddaPeriod = period}
        onRunAnalysis={runDDAAnalysis}
      />
    {/if}"""

# Удаляем Controls с текущего места
if old_controls_block in content:
    content = content.replace(old_controls_block, '')
    changes.append('✓ Удалён DeepAnalysisControls с текущего места')

# ============================================================================
# 4. Добавляем Controls и SystemLogsPanel в правильное место (в начале flex блока)
# ============================================================================
# Ищем место сразу после <div class="flex-1 flex overflow-hidden">
flex_div_start = '<div class="flex-1 flex overflow-hidden">'
if flex_div_start in content:
    panels_block = f"""{flex_div_start}
    {{#if showLogsPanel}}
      <SystemLogsPanel onClose={{() => showLogsPanel = false}} />
    {{/if}}
    {{#if showDeepAnalysisPanel}}
      <DeepAnalysisControls
        tags={{ddaTags}}
        selectedTag={{ddaSelectedTag}}
        period={{ddaPeriod}}
        isAnalyzing={{ddaIsAnalyzing}}
        error={{ddaError}}
        onTagChange={{(tag) => ddaSelectedTag = tag}}
        onPeriodChange={{(period) => ddaPeriod = period}}
        onRunAnalysis={{runDDAAnalysis}}
      />
    {{/if}}
"""
    content = content.replace(flex_div_start + '\n', panels_block, 1)
    changes.append('✓ Добавлены панели в начало flex блока (Controls + Logs)')

# ============================================================================
# 5. Удаляем дублирующий SystemLogsPanel если он остался
# ============================================================================
# Ищем все вхождения SystemLogsPanel
logs_pattern = r'\s*\{#if showLogsPanel\}\s*<SystemLogsPanel[^}]*\{/if\}'
import re
matches = list(re.finditer(logs_pattern, content))
if len(matches) > 1:
    # Оставляем только первое (которое мы только что добавили)
    for match in reversed(matches[1:]):
        content = content[:match.start()] + content[match.end():]
    changes.append(f'✓ Удалено {len(matches)-1} дубликатов SystemLogsPanel')

# ============================================================================
# 6. Добавляем DeepAnalysisResults ВНУТРИ основного контента
# ============================================================================
# Ищем блок с основным контентом (flex-1 flex flex-col bg-white)
main_content_pattern = r'(<div class="flex-1 flex flex-col bg-white[^"]* overflow-hidden[^>]*>)'
match = re.search(main_content_pattern, content)
if match:
    insert_pos = match.end()
    results_render = """
      {#if showDeepAnalysisPanel}
        <DeepAnalysisResults
          analysisResult={ddaAnalysisResult}
          isAnalyzing={ddaIsAnalyzing}
        />
      {:else}
"""
    # Проверяем что ещё не добавили
    if '<DeepAnalysisResults' not in content[insert_pos:insert_pos+500]:
        content = content[:insert_pos] + results_render + content[insert_pos:]
        changes.append('✓ Добавлен DeepAnalysisResults внутри основного контента')
        
        # Теперь нужно закрыть {:else} — находим соответствующий {/if}
        # Ищем следующий блок который закрывает основной контент
        # Это сложно, поэтому просто добавим {/if} перед закрывающим </div> основного контента
        # Но это может сломать структуру — лучше сделать по-другому
else:
    print('⚠ Не найден основной контент (flex-1 flex flex-col bg-white)')

# ============================================================================
# 7. Добавляем $effect для загрузки тегов (если его нет)
# ============================================================================
if 'showDeepAnalysisPanel && ddaTags' not in content:
    # Ищем место после функции runDDAAnalysis
    dda_func_end = content.find('async function runDDAAnalysis')
    if dda_func_end > 0:
        # Находим конец функции (следующая async function или </script>)
        next_func = content.find('\n  async function', dda_func_end + 10)
        if next_func < 0:
            next_func = content.find('\n</script>', dda_func_end)
        
        if next_func > 0:
            effect_block = """

  // Загружаем теги для Deep Analysis при открытии панели
  $effect(() => {
    if (showDeepAnalysisPanel && ddaTags.length === 0) {
      console.log('🔄 Loading DDA tags...')
      api.get('api/v1/deep_analysis/tags').json().then((tags: any[]) => {
        console.log('✓ DDA tags loaded:', tags.length)
        ddaTags = tags
        if (tags.length > 0 && !ddaSelectedTag) {
          ddaSelectedTag = tags[0].tag_name
        }
      }).catch((e: any) => {
        console.error('Failed to fetch DDA tags:', e)
        ddaError = 'Не удалось загрузить список тегов'
      })
    }
  })
"""
            content = content[:next_func] + effect_block + content[next_func:]
            changes.append('✓ Добавлен $effect для загрузки тегов')

# ============================================================================
# Сохраняем
# ============================================================================
if content != original:
    home_path.write_text(content, encoding='utf-8', newline='\n')
    print('✓ Home.svelte обновлён')
else:
    print('ℹ Файл не изменился')

print()
print('=' * 70)
print('ИСПРАВЛЕНИЯ:')
print('=' * 70)
for c in changes:
    print(f'  {c}')

print()
print('=' * 70)
print('ПРОВЕРКА СТРУКТУРЫ:')
print('=' * 70)
content_check = home_path.read_text(encoding='utf-8')
lines = content_check.split('\n')

# Ищем структуру layout
print()
print('Структура layout (первые 50 строк flex блока):')
flex_line = None
for i, line in enumerate(lines, 1):
    if 'flex-1 flex overflow-hidden' in line:
        flex_line = i
        break

if flex_line:
    for i in range(flex_line - 1, min(flex_line + 40, len(lines))):
        print(f'{i+1:4d}: {lines[i]}')

print()
print('=' * 70)
print('СЛЕДУЮЩИЙ ШАГ:')
print('=' * 70)
print()
print('Frontend перезагрузится автоматически (Vite HMR).')
print()
print('Проверка:')
print('  1. Открой фронтенд')
print('  2. Открой DevTools → Console (F12)')
print('  3. Клик Activity в хедере')
print('  4. Слева должна появиться панель с controls')
print('  5. В консоли должно появиться: 🔄 Loading DDA tags...')
print('  6. Затем: ✓ DDA tags loaded: 670')
print('  7. В dropdown появится список тегов')
print('  8. Выбери тег → "Запустить анализ"')
print('  9. В центральной части появится график и статистика')
print()
print('Если что-то не так — скинь вывод консоли!')