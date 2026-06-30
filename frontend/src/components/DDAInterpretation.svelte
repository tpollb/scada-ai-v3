<script lang="ts">
  import { Copy, RefreshCw, Loader2, CheckCircle, AlertCircle, FileText, X, ChevronDown } from 'lucide-svelte'

  interface Props {
    analysisResult: any
  }

  let { analysisResult }: Props = $props()

  // === State ===
  let interpretation = $state<string>('')
  let isGenerating = $state(false)
  let error = $state<string | null>(null)
  let copied = $state(false)
  let hasStarted = $state(false)
  let isCollapsed = $state(false)
  let isVisible = $state(true)

  // === Helpers ===
  function cleanText(text: string): string {
    if (!text) return ''
    return text
      .replace(/[\u{1F300}-\u{1F9FF}]/gu, '')
      .replace(/[\u{2600}-\u{26FF}]/gu, '')
      .replace(/[\u{2700}-\u{27BF}]/gu, '')
      .replace(/[\u{1F600}-\u{1F64F}]/gu, '')
      .replace(/[\u{1F680}-\u{1F6FF}]/gu, '')
      .replace(/[\u{1F1E0}-\u{1F1FF}]/gu, '')
      .replace(/[\u{2300}-\u{23FF}]/gu, '')
      .replace(/[\u{2B50}-\u{2B55}]/gu, '')
      .replace(/[\u{FE00}-\u{FE0F}]/gu, '')
      .replace(/[\u{200D}]/gu, '')
      .replace(/^#+\s*/gm, '')
      .replace(/\*\*([^*#]+)#([^*]+)\*\*/g, '**$1 $2**')
      .replace(/(\S)\s*#\s*(\S)/g, '$1 $2')
      .replace(/\s*#+\s*$/gm, '')
      .replace(/\n{3,}/g, '\n\n')
  }

  function smartAppendChunk(current: string, chunk: string): string {
    if (!chunk) return current
    if (!current) return chunk
    if (chunk.startsWith(current)) return chunk

    const maxOverlap = Math.min(current.length, chunk.length, 500)
    for (let overlap = maxOverlap; overlap > 50; overlap -= 10) {
      if (chunk.startsWith(current.slice(-overlap))) {
        return current + chunk.slice(overlap)
      }
    }
    return current + chunk
  }

  function parseInterpretation(text: string): string {
    if (!text) return ''

    const cleaned = cleanText(text)
    const lines = cleaned.split('\n')
    const sections: { title: string; content: string[] }[] = []
    let currentSection: { title: string; content: string[] } | null = null

    const sectionKeywords = ['РЕЗЮМЕ', 'КЛЮЧЕВЫЕ НАХОДКИ', 'ВОЗМОЖНЫЕ ПРИЧИНЫ', 'РЕКОМЕНДАЦИИ', 'ПРОГНОЗ']

    for (const line of lines) {
      const trimmed = line.trim()
      if (!trimmed) continue

      const upperTrimmed = trimmed.toUpperCase()
      const matchedKeyword = sectionKeywords.find(
        (kw) =>
          upperTrimmed === kw ||
          upperTrimmed.startsWith(kw + ' ') ||
          upperTrimmed.startsWith(kw + ':') ||
          /^\d+\.\s*/.test(upperTrimmed) && upperTrimmed.replace(/^\d+\.\s*/, '').startsWith(kw)
      )

      if (matchedKeyword) {
        if (currentSection) sections.push(currentSection)
        const cleanTitle = trimmed.replace(/^\d+\.\s*/, '').toUpperCase()
        currentSection = { title: cleanTitle, content: [] }
      } else if (currentSection) {
        currentSection.content.push(trimmed)
      } else {
        currentSection = { title: '', content: [trimmed] }
      }
    }

    if (currentSection) sections.push(currentSection)

    let html = ''
    let sectionNumber = 0

    for (const section of sections) {
      if (section.title) {
        sectionNumber++
        html += `<h2 class="section-title"><span class="section-number">${sectionNumber}.</span> ${section.title}</h2>`
      }

      const listItems: string[] = []
      const regularItems: string[] = []

      for (const item of section.content) {
        if (/^\s*[-•*]\s+/.test(item) || /^\s*\d+\.\s+/.test(item)) {
          const cleanItem = item.replace(/^\s*[-•*]\s+/, '').replace(/^\s*\d+\.\s+/, '')
          listItems.push(cleanItem)
        } else {
          regularItems.push(item)
        }
      }

      for (const item of regularItems) {
        html += `<p>${formatInlineMarkdown(item)}</p>`
      }

      if (listItems.length > 0) {
        html += '<ul class="list-items">'
        for (const item of listItems) {
          html += `<li>${formatInlineMarkdown(item)}</li>`
        }
        html += '</ul>'
      }
    }

    return html || `<p>${cleaned.replace(/\n/g, '<br>')}</p>`
  }

  function formatInlineMarkdown(text: string): string {
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*([^*]+)\*/g, '$1')
  }

  // === Actions ===
  async function generateInterpretation() {
    if (isGenerating) return

    isGenerating = true
    interpretation = ''
    error = null
    hasStarted = true
    isCollapsed = false

    try {
      const response = await fetch('http://localhost:8081/api/v1/deep_analysis/interpret/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ analysis_result: analysisResult })
      })

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`HTTP ${response.status}: ${errorText}`)
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('Response body is not readable')
      }

      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value, { stream: true })
        buffer += chunk
        const lines = buffer.split('\n')

        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              if (data.chunk) {
                interpretation = smartAppendChunk(interpretation, data.chunk)
              } else if (data.error) {
                error = data.error
              }
            } catch (e) {
              // ignore
            }
          }
        }
      }
    } catch (e: any) {
      error = e.message || 'Ошибка генерации интерпретации'
    } finally {
      isGenerating = false
    }
  }

  async function copyToClipboard() {
    try {
      await navigator.clipboard.writeText(cleanText(interpretation))
      copied = true
      setTimeout(() => (copied = false), 2000)
    } catch (e) {
      console.error('Failed to copy:', e)
    }
  }

  function handleClose() {
    isVisible = false
  }

  function handleReset() {
    interpretation = ''
    hasStarted = false
    isCollapsed = false
    isVisible = true
    error = null
  }

  let renderedHtml = $derived(parseInterpretation(interpretation))
</script>

{#if !isVisible}
  <div class="interpretation-collapsed">
    <button type="button" onclick={handleReset} class="show-btn">
      <FileText size={16} />
      Показать LLM интерпретацию
    </button>
  </div>
{:else}
  <div class="interpretation-wrapper">
    <div class="interpretation-header">
      <div class="header-title">
        <FileText size={18} class="text-neutral-600 dark:text-neutral-400" />
        <h2>LLM Интерпретация</h2>
        {#if isGenerating}
          <span class="generating-badge">
            <Loader2 size={12} class="animate-spin" />
            генерация...
          </span>
        {/if}
      </div>

      <div class="header-actions">
        {#if interpretation && !isGenerating}
          <button type="button" onclick={copyToClipboard} class="btn-action" title="Копировать">
            {#if copied}
              <CheckCircle size={14} class="text-green-500" />
            {:else}
              <Copy size={14} />
            {/if}
            <span>{copied ? 'Скопировано' : 'Копировать'}</span>
          </button>
          <button type="button" onclick={generateInterpretation} class="btn-action" title="Регенерировать">
            <RefreshCw size={14} />
            <span>Регенерировать</span>
          </button>
        {/if}

        <button
          type="button"
          onclick={() => (isCollapsed = !isCollapsed)}
          class="btn-icon"
          title={isCollapsed ? 'Развернуть' : 'Свернуть'}
        >
          <ChevronDown
            size={16}
            class="transition-transform duration-200 {isCollapsed ? '-rotate-90' : ''}"
          />
        </button>

        <button type="button" onclick={handleClose} class="btn-icon" title="Закрыть">
          <X size={16} />
        </button>
      </div>
    </div>

    {#if !isCollapsed}
      <div class="interpretation-body">
        {#if !hasStarted}
          <div class="empty-state">
            <button type="button" onclick={generateInterpretation} class="generate-btn">
              <FileText size={16} />
              Сгенерировать интерпретацию
            </button>
          </div>
        {:else if error}
          <div class="error-block">
            <div class="error-content">
              <AlertCircle size={16} class="error-icon" />
              <div class="error-text">
                <p>{error}</p>
                <button type="button" onclick={generateInterpretation} class="retry-link">
                  Попробовать снова
                </button>
              </div>
            </div>
          </div>
        {:else if isGenerating && !interpretation}
          <div class="loading-state">
            <Loader2 size={32} class="animate-spin text-neutral-600" />
            <p>Генерация интерпретации...</p>
          </div>
        {:else if interpretation}
          <div class="interpretation-container">
            <div class="prose-content">
              {@html renderedHtml}
            </div>
            {#if isGenerating}
              <div class="generating-footer">
                <Loader2 size={14} class="animate-spin text-neutral-600" />
                <span>Генерация продолжается...</span>
              </div>
            {/if}
          </div>
        {/if}
      </div>
    {/if}
  </div>
{/if}

<style>
  .interpretation-collapsed {
    display: flex;
    justify-content: center;
    padding: 1rem;
  }

  .show-btn {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.625rem 1.25rem;
    background-color: rgb(64 64 64);
    color: white;
    border: none;
    border-radius: 0.375rem;
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: background-color 0.15s;
  }

  .show-btn:hover {
    background-color: rgb(38 38 38);
  }

  :global(.dark .show-btn) {
    background-color: rgb(212 212 216);
    color: rgb(17 24 39);
  }

  :global(.dark .show-btn:hover) {
    background-color: rgb(245 245 245);
  }

  .interpretation-wrapper {
    border: 1px solid rgb(229 231 235);
    border-radius: 0.5rem;
    background-color: rgb(255 255 255);
    overflow: visible;
  }

  :global(.dark .interpretation-wrapper) {
    border-color: rgb(64 64 64);
    background-color: rgb(38 38 38);
  }

  .interpretation-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.75rem 1rem;
    border-bottom: 1px solid rgb(229 231 235);
    background-color: rgb(249 250 251);
    border-radius: 0.5rem 0.5rem 0 0;
  }

  :global(.dark .interpretation-header) {
    border-bottom-color: rgb(64 64 64);
    background-color: rgb(32 32 32);
  }

  .header-title {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .header-title h2 {
    font-size: 1rem;
    font-weight: 600;
    color: rgb(17 24 39);
    margin: 0;
  }

  :global(.dark .header-title h2) {
    color: rgb(245 245 245);
  }

  .generating-badge {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    font-size: 0.75rem;
    color: rgb(107 114 128);
  }

  .header-actions {
    display: flex;
    flex-direction: row;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: nowrap;
  }

  .btn-action {
    display: inline-flex;
    flex-shrink: 0;
    align-items: center;
    gap: 0.375rem;
    padding: 0.375rem 0.75rem;
    font-size: 0.75rem;
    font-weight: 500;
    white-space: nowrap;
    color: rgb(55 65 81);
    background-color: rgb(243 244 246);
    border: 1px solid rgb(209 213 219);
    border-radius: 0.375rem;
    cursor: pointer;
    transition: all 0.15s;
  }

  .btn-action:hover {
    background-color: rgb(229 231 235);
  }

  :global(.dark .btn-action) {
    color: rgb(212 212 216);
    background-color: rgb(55 65 81);
    border-color: rgb(75 85 99);
  }

  :global(.dark .btn-action:hover) {
    background-color: rgb(64 64 64);
  }

  .btn-icon {
    display: inline-flex;
    flex-shrink: 0;
    align-items: center;
    justify-content: center;
    width: 1.75rem;
    height: 1.75rem;
    color: rgb(107 114 128);
    background: transparent;
    border: none;
    border-radius: 0.25rem;
    cursor: pointer;
    transition: all 0.15s;
  }

  .btn-icon:hover {
    background-color: rgb(229 231 235);
    color: rgb(55 65 81);
  }

  :global(.dark .btn-icon) {
    color: rgb(156 163 175);
  }

  :global(.dark .btn-icon:hover) {
    background-color: rgb(55 65 81);
    color: rgb(229 231 235);
  }

  .interpretation-body {
    padding: 1rem;
  }

  .empty-state {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 2rem 0;
  }

  .generate-btn {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.625rem 1.25rem;
    background-color: rgb(64 64 64);
    color: white;
    border: none;
    border-radius: 0.375rem;
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: background-color 0.15s;
  }

  .generate-btn:hover {
    background-color: rgb(38 38 38);
  }

  :global(.dark .generate-btn) {
    background-color: rgb(212 212 216);
    color: rgb(17 24 39);
  }

  :global(.dark .generate-btn:hover) {
    background-color: rgb(245 245 245);
  }

  .error-block {
    padding: 1rem;
    background-color: rgb(254 242 242);
    border: 1px solid rgb(254 202 202);
    border-radius: 0.375rem;
  }

  :global(.dark .error-block) {
    background-color: rgb(127 29 29 / 0.2);
    border-color: rgb(153 27 27);
  }

  .error-content {
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
  }

  .error-icon {
    color: rgb(239 68 68);
    margin-top: 0.125rem;
    flex-shrink: 0;
  }

  .error-text p {
    font-size: 0.875rem;
    color: rgb(127 29 29);
    margin: 0;
  }

  :global(.dark .error-text p) {
    color: rgb(254 202 202);
  }

  .retry-link {
    margin-top: 0.5rem;
    font-size: 0.75rem;
    color: rgb(220 38 38);
    background: none;
    border: none;
    padding: 0;
    cursor: pointer;
    text-decoration: underline;
  }

  :global(.dark .retry-link) {
    color: rgb(252 165 165);
  }

  .loading-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.75rem;
    padding: 3rem 0;
  }

  .loading-state p {
    font-size: 0.875rem;
    color: rgb(107 114 128);
    margin: 0;
  }

  .interpretation-container {
    max-height: 600px;
    min-height: 200px;
    overflow-y: auto;
    overflow-x: hidden;
    scrollbar-width: thin;
    scrollbar-color: rgb(163 163 163) transparent;
    position: relative;
  }

  .interpretation-container::-webkit-scrollbar {
    width: 6px;
  }

  .interpretation-container::-webkit-scrollbar-track {
    background: transparent;
  }

  .interpretation-container::-webkit-scrollbar-thumb {
    background-color: rgb(163 163 163);
    border-radius: 3px;
  }

  .generating-footer {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-top: 1rem;
    padding-top: 1rem;
    border-top: 1px solid rgb(229 231 235);
    font-size: 0.75rem;
    color: rgb(107 114 128);
  }

  :global(.dark .generating-footer) {
    border-top-color: rgb(64 64 64);
  }

  .prose-content {
    font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
      sans-serif;
    font-size: 0.8125rem;
    line-height: 1.7;
    color: rgb(55 65 81);
  }

  :global(.dark .prose-content) {
    color: rgb(212 212 216);
  }

  :global(.prose-content .section-title) {
    display: flex;
    align-items: baseline;
    gap: 0.5rem;
    font-size: 0.8125rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 2rem;
    margin-bottom: 0.75rem;
    padding: 0.625rem 0.75rem;
    color: rgb(17 24 39);
    background-color: rgb(243 244 246);
    border-left: 3px solid rgb(107 114 128);
    border-radius: 0.25rem;
  }

  :global(.prose-content .section-title:first-child) {
    margin-top: 0;
  }

  :global(.dark .prose-content .section-title) {
    color: rgb(245 245 245);
    background-color: rgb(55 65 81);
    border-left-color: rgb(156 163 175);
  }

  :global(.prose-content .section-number) {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 1.25rem;
    height: 1.25rem;
    background-color: rgb(107 114 128);
    color: rgb(255 255 255);
    font-size: 0.6875rem;
    font-weight: 700;
    border-radius: 0.25rem;
  }

  :global(.dark .prose-content .section-number) {
    background-color: rgb(156 163 175);
    color: rgb(17 24 39);
  }

  :global(.prose-content p) {
    margin-top: 0.75rem;
    margin-bottom: 0.75rem;
  }

  :global(.prose-content .list-items) {
    padding-left: 0;
    margin-top: 0.75rem;
    margin-bottom: 1rem;
    list-style-type: none;
  }

  :global(.prose-content .list-items li) {
    position: relative;
    padding-left: 1.5rem;
    margin-top: 0.5rem;
    margin-bottom: 0.5rem;
    line-height: 1.6;
  }

  :global(.prose-content .list-items li::before) {
    content: '';
    position: absolute;
    left: 0.375rem;
    top: 0.625rem;
    width: 0.375rem;
    height: 0.375rem;
    background-color: rgb(107 114 128);
    border-radius: 50%;
  }

  :global(.dark .prose-content .list-items li::before) {
    background-color: rgb(156 163 175);
  }

  :global(.prose-content strong) {
    font-weight: 600;
    color: rgb(17 24 39);
  }

  :global(.dark .prose-content strong) {
    color: rgb(245 245 245);
  }
</style>
