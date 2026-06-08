<script lang="ts">
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
</style>
