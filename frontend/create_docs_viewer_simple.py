from pathlib import Path

print('=== create_docs_viewer_simple.py ===')
print()

# ============================================================================
# 1. Создаём src/components/DocsViewer.svelte
# ============================================================================
docs_viewer_content = '''<script lang="ts">
  import { onMount } from 'svelte'
  import { marked } from 'marked'
  import api from '../lib/api'
  import { FileText, Loader2 } from 'lucide-svelte'

  interface DocFile {
    filename: string
    title: string
    size: number
  }

  let files = $state<DocFile[]>([])
  let selectedFile = $state<string | null>(null)
  let content = $state<string>('')
  let loading = $state(false)
  let error = $state<string | null>(null)

  // Настройка marked
  marked.setOptions({
    breaks: true,
    gfm: true,
  })

  onMount(async () => {
    try {
      const resp: any = await api.get('docs/list').json()
      files = resp.files || []
      if (files.length > 0) {
        selectedFile = files[0].filename
        await loadDoc(files[0].filename)
      }
    } catch (e: any) {
      error = e?.message || 'Ошибка загрузки списка документов'
    }
  })

  async function loadDoc(filename: string) {
    loading = true
    error = null
    content = ''
    try {
      const resp: any = await api.get(`docs/${filename}`).json()
      content = marked.parse(resp.content || '')
    } catch (e: any) {
      error = e?.message || 'Ошибка загрузки документа'
    } finally {
      loading = false
    }
  }

  function selectFile(filename: string) {
    selectedFile = filename
    loadDoc(filename)
  }

  let renderedHtml = $derived(content)
</script>

<div class="flex h-full">
  <!-- Sidebar со списком файлов -->
  <aside class="w-72 border-r border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 overflow-y-auto">
    <div class="p-4 border-b border-neutral-200 dark:border-neutral-700">
      <h2 class="text-sm font-semibold text-neutral-700 dark:text-neutral-300 uppercase tracking-wide">
        Документация
      </h2>
    </div>
    
    {#if files.length === 0}
      <div class="p-4 text-center text-neutral-500 dark:text-neutral-400 text-sm">
        Нет доступных документов
      </div>
    {:else}
      <div class="divide-y divide-neutral-100 dark:divide-neutral-700">
        {#each files as file}
          <button
            type="button"
            onclick={() => selectFile(file.filename)}
            class="w-full text-left p-4 hover:bg-neutral-50 dark:hover:bg-neutral-700 transition {selectedFile === file.filename ? 'bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-600' : 'border-l-4 border-transparent'}"
          >
            <div class="flex items-start gap-2">
              <FileText size={16} class="text-neutral-400 dark:text-neutral-500 flex-shrink-0 mt-0.5" />
              <div class="flex-1 min-w-0">
                <div class="font-medium text-sm text-neutral-900 dark:text-neutral-100 truncate">
                  {file.title}
                </div>
                <div class="text-xs text-neutral-500 dark:text-neutral-400 font-mono mt-0.5">
                  {file.filename} • {(file.size / 1024).toFixed(1)} KB
                </div>
              </div>
            </div>
          </button>
        {/each}
      </div>
    {/if}
  </aside>

  <!-- Main area с контентом -->
  <main class="flex-1 overflow-y-auto p-8 bg-neutral-50 dark:bg-neutral-900">
    {#if loading}
      <div class="flex items-center justify-center h-full">
        <div class="flex flex-col items-center gap-3 text-neutral-500 dark:text-neutral-400">
          <Loader2 size={32} class="animate-spin" />
          <div class="text-sm">Загрузка документа...</div>
        </div>
      </div>
    {:else if error}
      <div class="max-w-2xl mx-auto">
        <div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded p-4">
          <div class="font-semibold text-red-900 dark:text-red-100 mb-2">Ошибка загрузки</div>
          <div class="text-sm text-red-700 dark:text-red-300">{error}</div>
        </div>
      </div>
    {:else if !selectedFile}
      <div class="flex items-center justify-center h-full text-neutral-500 dark:text-neutral-400 text-sm">
        Выберите документ из списка слева
      </div>
    {:else}
      <div class="max-w-4xl mx-auto">
        <article class="prose prose-neutral dark:prose-invert max-w-none">
          {@html renderedHtml}
        </article>
      </div>
    {/if}
  </main>
</div>

<style>
  :global(.prose) {
    @apply text-neutral-900 dark:text-neutral-100;
  }
  :global(.prose h1) {
    @apply text-3xl font-bold mb-6 pb-2 border-b border-neutral-200 dark:border-neutral-700;
  }
  :global(.prose h2) {
    @apply text-2xl font-semibold mt-8 mb-4 pb-2 border-b border-neutral-200 dark:border-neutral-700;
  }
  :global(.prose h3) {
    @apply text-xl font-semibold mt-6 mb-3;
  }
  :global(.prose h4) {
    @apply text-lg font-semibold mt-4 mb-2;
  }
  :global(.prose p) {
    @apply mb-4 leading-relaxed;
  }
  :global(.prose ul), :global(.prose ol) {
    @apply mb-4 pl-6;
  }
  :global(.prose li) {
    @apply mb-2;
  }
  :global(.prose code) {
    @apply px-1.5 py-0.5 bg-neutral-100 dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded text-sm font-mono;
  }
  :global(.prose pre) {
    @apply p-4 bg-neutral-100 dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded overflow-x-auto mb-4;
  }
  :global(.prose pre code) {
    @apply px-0 py-0 bg-transparent border-0;
  }
  :global(.prose a) {
    @apply text-blue-600 dark:text-blue-400 hover:underline;
  }
  :global(.prose blockquote) {
    @apply pl-4 border-l-4 border-neutral-300 dark:border-neutral-600 italic text-neutral-700 dark:text-neutral-300 mb-4;
  }
  :global(.prose table) {
    @apply w-full mb-4 border-collapse;
  }
  :global(.prose th) {
    @apply text-left font-semibold px-3 py-2 border border-neutral-200 dark:border-neutral-700 bg-neutral-100 dark:bg-neutral-800;
  }
  :global(.prose td) {
    @apply px-3 py-2 border border-neutral-200 dark:border-neutral-700;
  }
  :global(.prose hr) {
    @apply my-8 border-neutral-200 dark:border-neutral-700;
  }
  :global(.prose strong) {
    @apply font-semibold;
  }
</style>
'''

docs_viewer_path = Path('src/components/DocsViewer.svelte')
docs_viewer_path.write_text(docs_viewer_content, encoding='utf-8', newline='\n')
print(f'✓ Создан: {docs_viewer_path}')

# ============================================================================
# 2. Патчим src/routes/Config.svelte
# ============================================================================
config_path = Path('src/routes/Config.svelte')
config = config_path.read_text(encoding='utf-8')

# 2.1. Добавляем импорт DocsViewer
old_imports = '''import { ArrowLeft, RefreshCw, Save, AlertCircle, CheckCircle, Server, Database, Key, Sun, Moon } from 'lucide-svelte'
  import { theme } from '../stores/theme'
  import api from '../lib/api' '''

new_imports = '''import { ArrowLeft, RefreshCw, Save, AlertCircle, CheckCircle, Server, Database, Key, Sun, Moon, FileText } from 'lucide-svelte'
  import { theme } from '../stores/theme'
  import api from '../lib/api'
  import DocsViewer from '../components/DocsViewer.svelte' '''

if old_imports in config:
    config = config.replace(old_imports, new_imports)
    print('✓ Config.svelte: добавлен импорт DocsViewer и FileText')
elif 'DocsViewer' in config:
    print('ℹ Config.svelte: импорт DocsViewer уже есть')
else:
    print('⚠ Config.svelte: не нашёл точный паттерн импортов')

# 2.2. Обновляем тип activeTab
old_tab_type = "let activeTab = $state<'modules' | 'system'>('modules')"
new_tab_type = "let activeTab = $state<'modules' | 'system' | 'docs'>('modules')"

if old_tab_type in config:
    config = config.replace(old_tab_type, new_tab_type)
    print('✓ Config.svelte: тип activeTab обновлён (добавлен docs)')
elif "'docs'" in config and 'activeTab' in config:
    print('ℹ Config.svelte: тип activeTab уже обновлён')
else:
    print('⚠ Config.svelte: не нашёл точный паттерн activeTab')

# 2.3. Добавляем кнопку "Документация" в табы
old_tabs = '''      <button
        type="button"
        onclick={() => activeTab = 'system'}
        class="px-4 py-1.5 text-sm font-medium rounded transition {activeTab === 'system' ? 'bg-white shadow-sm text-neutral-900' : 'text-neutral-600 hover:text-neutral-900'}"
      >
        Система
      </button>
    </div>'''

new_tabs = '''      <button
        type="button"
        onclick={() => activeTab = 'system'}
        class="px-4 py-1.5 text-sm font-medium rounded transition {activeTab === 'system' ? 'bg-white shadow-sm text-neutral-900' : 'text-neutral-600 hover:text-neutral-900'}"
      >
        Система
      </button>
      <button
        type="button"
        onclick={() => activeTab = 'docs'}
        class="px-4 py-1.5 text-sm font-medium rounded transition flex items-center gap-2 {activeTab === 'docs' ? 'bg-white shadow-sm text-neutral-900' : 'text-neutral-600 hover:text-neutral-900'}"
      >
        <FileText size={14} />
        Документация
      </button>
    </div>'''

if old_tabs in config:
    config = config.replace(old_tabs, new_tabs)
    print('✓ Config.svelte: добавлена кнопка "Документация"')
elif 'Документация' in config:
    print('ℹ Config.svelte: кнопка "Документация" уже есть')
else:
    print('⚠ Config.svelte: не нашёл точный паттерн табов')

# 2.4. Добавляем блок рендеринга docs после блока system
old_system_end = '''  {:else if activeTab === 'system'}
    <div class="flex-1 overflow-y-auto p-6">
      <div class="max-w-3xl mx-auto space-y-6">'''

new_system_end = '''  {:else if activeTab === 'docs'}
    <div class="flex-1 overflow-hidden">
      <DocsViewer />
    </div>
  {:else if activeTab === 'system'}
    <div class="flex-1 overflow-y-auto p-6">
      <div class="max-w-3xl mx-auto space-y-6">'''

if old_system_end in config:
    config = config.replace(old_system_end, new_system_end)
    print('✓ Config.svelte: добавлен блок рендеринга docs')
elif '<DocsViewer />' in config:
    print('ℹ Config.svelte: блок docs уже есть')
else:
    print('⚠ Config.svelte: не нашёл точный паттерн system блока')

config_path.write_text(config, encoding='utf-8', newline='\n')
print(f'✓ Обновлён: {config_path}')

print()
print('=' * 60)
print('ЧТО СДЕЛАНО:')
print('=' * 60)
print('1. Создан src/components/DocsViewer.svelte:')
print('   • Sidebar со списком файлов (fetch /docs/list)')
print('   • Main area с markdown рендерингом (marked)')
print('   • Стили для заголовков, кода, таблиц, ссылок')
print('   • Loading state и error handling')
print()
print('2. Обновлён src/routes/Config.svelte:')
print('   • Добавлен импорт DocsViewer и FileText')
print('   • Тип activeTab: modules | system | docs')
print('   • Кнопка "Документация" в хедере')
print('   • Блок рендеринга <DocsViewer /> для activeTab === docs')
print()
print('ВАЖНО: Установи marked вручную перед запуском:')
print('  cd /c/dev/SCADA.AI/scada-ai-v3/frontend')
print('  npm install marked')
print()
print('ПРОВЕРКА:')
print('  1. Vite подхватит автоматически (HMR)')
print('  2. Открой Конфигуратор')
print('  3. Кликни на вкладку "Документация"')
print('  4. Должен загрузиться список файлов и README.md')
print()
print('Когда проверишь — скажи "docs viewer ок"')