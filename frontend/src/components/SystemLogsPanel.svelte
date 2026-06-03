<script lang="ts">
  import { onMount, onDestroy } from 'svelte'
  import { X, RefreshCw, Trash2, Download, Clock } from 'lucide-svelte'
  import api from '../lib/api'

  interface Props { onClose?: () => void }
  let { onClose }: Props = $props()

  interface LogEntry {
    timestamp: string
    level: 'debug' | 'info' | 'warning' | 'error' | 'critical'
    message: string
    data?: any
  }
  interface LogFile {
    name: string
    size_bytes: number
    modified: string
    is_current: boolean
  }

  let logs = $state<LogEntry[]>([])
  let files = $state<LogFile[]>([])
  let selectedFile = $state<string>('__current__')
  let autoRefresh = $state(true)
  let filterLevel = $state<string | null>(null)
  let interval: ReturnType<typeof setInterval> | null = null

  const levelConfig = {
    debug: { color: 'text-neutral-500 dark:text-neutral-400', bg: 'bg-neutral-100 dark:bg-neutral-800', border: 'border-l-neutral-400' },
    info: { color: 'text-blue-600 dark:text-blue-400', bg: 'bg-blue-50 dark:bg-blue-900/20', border: 'border-l-blue-500' },
    warning: { color: 'text-amber-600 dark:text-amber-400', bg: 'bg-amber-50 dark:bg-amber-900/20', border: 'border-l-amber-500' },
    error: { color: 'text-red-600 dark:text-red-400', bg: 'bg-red-50 dark:bg-red-900/20', border: 'border-l-red-500' },
    critical: { color: 'text-red-700 dark:text-red-300', bg: 'bg-red-100 dark:bg-red-900/30', border: 'border-l-red-700' }
  }

  async function loadFiles() {
    try {
      const resp: any = await api.get('system/logs/files').json()
      files = resp.files || []
    } catch (e) { console.error('Failed to load files:', e) }
  }

  async function loadLogs() {
    try {
      const url = selectedFile === '__current__'
        ? `system/logs/current?limit=200${filterLevel ? `&level=${filterLevel}` : ''}`
        : `system/logs/file/${selectedFile}?limit=1000`
      const resp: any = await api.get(url).json()
      let loaded = resp.logs || []
      if (selectedFile !== '__current__' && filterLevel) {
        loaded = loaded.filter((l: LogEntry) => l.level === filterLevel)
      }
      logs = loaded
    } catch (e) { console.error('Failed to load logs:', e) }
  }

  async function clearBuffer() {
    try {
      await api.post('system/logs/clear').json()
      if (selectedFile === '__current__') logs = []
    } catch (e) { console.error('Failed to clear buffer:', e) }
  }

  function switchToCurrent() { selectedFile = '__current__'; autoRefresh = true }

  function exportLogs() {
    if (!logs.length) return
    const text = logs.map(l => {
      const ts = l.timestamp || ''
      const lvl = (l.level || 'info').toUpperCase()
      const data = l.data ? ` | ${JSON.stringify(l.data)}` : ''
      return `[${ts}] [${lvl}] ${l.message || ''}${data}`
    }).join('\n')
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = selectedFile === '__current__' ? `current-log-${Date.now()}.txt` : selectedFile.replace('.log', '.txt')
    document.body.appendChild(a); a.click(); document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  function formatTime(iso: string): string {
    if (!iso) return ''
    try {
      const d = new Date(iso)
      return isNaN(d.getTime()) ? (iso.includes('T') ? iso.slice(11, 19) : iso) : d.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    } catch { return iso }
  }

  function formatFileSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / 1048576).toFixed(1)} MB`
  }

  function formatFileName(name: string): string {
    const m = name.match(/^(\d{4}-\d{2}-\d{2})_(\d{2})-(\d{2})-(\d{2})/)
    return m ? `${m[1]} ${m[2]}:${m[3]}:${m[4]}` : name
  }

  onMount(async () => { await loadFiles(); await loadLogs() })

  $effect(() => {
    if (interval) { clearInterval(interval); interval = null }
    if (autoRefresh && selectedFile === '__current__') interval = setInterval(loadLogs, 2000)
    return () => { if (interval) { clearInterval(interval); interval = null } }
  })

  $effect(() => { const _ = selectedFile; const __ = filterLevel; loadLogs() })

  onDestroy(() => { if (interval) clearInterval(interval) })

  let reversedLogs = $derived([...logs].reverse())
</script>

<div class="w-96 border-r border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 flex flex-col h-full">
  <div class="px-4 py-3 border-b border-neutral-200 dark:border-neutral-700 flex items-center justify-between flex-shrink-0">
    <h2 class="text-sm font-semibold text-neutral-900 dark:text-neutral-100 uppercase tracking-wide">Системные логи</h2>
    <div class="flex items-center gap-2">
      <button type="button" onclick={() => autoRefresh = !autoRefresh} disabled={selectedFile !== '__current__'} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition disabled:opacity-30 disabled:cursor-not-allowed {autoRefresh && selectedFile === '__current__' ? 'text-blue-600 dark:text-blue-400' : 'text-neutral-500'}" title={selectedFile === '__current__' ? (autoRefresh ? 'Автообновление вкл' : 'Автообновление выкл') : 'Только для текущего лога'}>
        <RefreshCw size={16} class={autoRefresh && selectedFile === '__current__' ? 'animate-spin' : ''} />
      </button>
      <button type="button" onclick={exportLogs} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition text-neutral-500 hover:text-blue-600" title="Экспорт в TXT"><Download size={16} /></button>
      <button type="button" onclick={clearBuffer} disabled={selectedFile !== '__current__'} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition text-neutral-500 hover:text-red-600 disabled:opacity-30 disabled:cursor-not-allowed" title="Очистить буфер"><Trash2 size={16} /></button>
      {#if onClose}<button type="button" onclick={onClose} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition text-neutral-500 hover:text-neutral-700" title="Закрыть панель"><X size={16} /></button>{/if}
    </div>
  </div>

  <div class="px-4 py-2 border-b border-neutral-200 dark:border-neutral-700 flex-shrink-0">
    <select bind:value={selectedFile} onchange={() => { if (selectedFile === '__current__') autoRefresh = true }} class="w-full px-2 py-1.5 text-xs border border-neutral-300 dark:border-neutral-600 rounded bg-white dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100 font-mono focus:outline-none focus:ring-2 focus:ring-blue-500">
      <option value="__current__">● Текущий лог (live)</option>
      <optgroup label="Архив">
        {#each files as file}<option value={file.name}>{formatFileName(file.name)} ({formatFileSize(file.size_bytes)})</option>{/each}
      </optgroup>
    </select>
    {#if selectedFile !== '__current__'}
      <button type="button" onclick={switchToCurrent} class="mt-2 w-full px-2 py-1 text-xs bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800 rounded hover:bg-blue-100 dark:hover:bg-blue-900/30 transition flex items-center justify-center gap-1">
        <Clock size={12} /> Вернуться к текущему логу
      </button>
    {/if}
  </div>

  <div class="px-4 py-2 border-b border-neutral-200 dark:border-neutral-700 flex gap-1 flex-shrink-0">
    <button type="button" onclick={() => filterLevel = null} class="px-2 py-1 text-xs rounded transition {filterLevel === null ? 'bg-neutral-900 dark:bg-neutral-100 text-white dark:text-neutral-900' : 'bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 hover:bg-neutral-200 dark:hover:bg-neutral-700'}">Все</button>
    {#each ['debug', 'info', 'warning', 'error'] as level}
      {@const cfg = levelConfig[level]}
      <button type="button" onclick={() => filterLevel = level} class="px-2 py-1 text-xs rounded transition {filterLevel === level ? cfg.bg + ' ' + cfg.color + ' font-semibold' : 'bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 hover:bg-neutral-200 dark:hover:bg-neutral-700'}">{level}</button>
    {/each}
  </div>

  <div class="flex-1 overflow-y-auto">
    {#if reversedLogs.length === 0}
      <div class="flex items-center justify-center h-full text-neutral-500 dark:text-neutral-400 text-sm">Нет записей</div>
    {:else}
      <div class="divide-y divide-neutral-100 dark:divide-neutral-800">
        {#each reversedLogs as log, i (`${i}-${log.timestamp}-${log.message}`)}
          {@const cfg = levelConfig[log.level] || levelConfig.info}
          <div class="px-4 py-2 hover:bg-neutral-50 dark:hover:bg-neutral-800 transition border-l-2 {cfg.border}">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-0.5">
                <span class="text-xs font-mono text-neutral-500 dark:text-neutral-400">{formatTime(log.timestamp)}</span>
                <span class="text-xs px-1.5 py-0.5 rounded {cfg.bg} {cfg.color} font-semibold uppercase">{log.level}</span>
              </div>
              <div class="text-sm text-neutral-900 dark:text-neutral-100 break-words">{log.message}</div>
              {#if log.data}<div class="mt-1 text-xs font-mono text-neutral-600 dark:text-neutral-400 bg-neutral-50 dark:bg-neutral-800 rounded p-1.5 overflow-x-auto">{JSON.stringify(log.data, null, 2)}</div>{/if}
            </div>
          </div>
        {/each}
      </div>
    {/if}
  </div>

  <div class="px-4 py-2 border-t border-neutral-200 dark:border-neutral-700 text-xs text-neutral-500 dark:text-neutral-400 flex items-center justify-between flex-shrink-0">
    <span>{reversedLogs.length} записей</span>
    <span class="font-mono">{#if selectedFile === '__current__'}{autoRefresh ? 'live · 2с' : 'пауза'}{:else}{files.find(f => f.name === selectedFile)?.size_bytes ? formatFileSize(files.find(f => f.name === selectedFile)!.size_bytes) : 'файл'}{/if}</span>
  </div>
</div>
