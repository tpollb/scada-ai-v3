<script lang="ts">
  import { onMount } from 'svelte'
  import { getHealth } from '../lib/api'
  import { messages, isLoading, addMessage } from '../stores/chat'
  import { navigate } from '../stores/ui'
  import Input from '../components/Input.svelte'
  import NarrativePanel from '../components/NarrativePanel.svelte'
  import WidgetRouter from '../components/WidgetRouter.svelte'
  import api from '../lib/api'
  import { Settings, Volume2, Database, Cpu, Zap, Clock, CheckCircle, XCircle, AlertCircle } from 'lucide-svelte'

  interface SystemInfo {
    app_name: string
    app_version: string
    modules: string[]
    tools_count: number
    db_status: 'ok' | 'error' | 'unknown'
    db_stats: { tags_count: number } | null
    db_host: string
    llm_status: 'ok' | 'error' | 'not_configured' | 'unknown'
    llm_model: string
    scada_url: string
    last_health_check: { timestamp: string | null; duration_sec: number | null; score: number | null }
    capabilities: { text: string; category: string; action?: string }[]
    server_time: string
  }

  let health = $state<any>(null)
  let currentWidgets = $state<any[]>([])
  let lastVoiceText = $state<string | null>(null)
  let systemInfo = $state<SystemInfo | null>(null)

  onMount(async () => {
    try { health = await getHealth() } catch (e) { console.error('Failed to fetch health:', e) }
    try { systemInfo = await api.get('system/info').json<SystemInfo>() } catch (e) { console.error('Failed to fetch system info:', e) }
  })

  async function handleSend(message: string) {
    const lower = message.toLowerCase()
    
    // Навигационные команды
    if (lower.includes('конфигуратор') || lower.includes('настройки') || lower.includes('настроить')) {
      navigate('config')
      return
    }
    
    addMessage('user', message)
    isLoading.set(true)
    currentWidgets = []
    lastVoiceText = null

    try {
      // Пробуем специальные intent'ы
      if (lower.match(/температур|влажност|температура и влажность|давлен|co2|voc|параметр.*сред/i)) {
        try {
          const resp: any = await api.get('health/metrics-summary').json()
          if (resp && resp.params) {
            // Отобразить как виджеты
            addMessage('assistant', resp.text || 'Сводка по параметрам среды')
            currentWidgets = [
              { type: 'environmental_panel', data: resp.params, size: 'wide' },
            ]
            return
          }
        } catch (e) {
          console.error('Metrics summary failed, fallback to LLM:', e)
        }
      }
      
      // Обычный запрос к LLM
      const resp: any = await api.post('chat', { json: { message } }).json()
      addMessage('assistant', resp.response)

      if (resp.visual?.widgets && resp.visual.widgets.length > 0) {
        currentWidgets = resp.visual.widgets
      }

      if (resp.voice?.text) {
        lastVoiceText = resp.voice.text
        speak(resp.voice.text)
      }
      
      try { systemInfo = await api.get('system/info').json<SystemInfo>() } catch {}
    } catch (e: any) {
      console.error('Chat error:', e)
      addMessage('system', `Ошибка: ${e?.message || 'неизвестная'}`)
    } finally {
      isLoading.set(false)
    }
  }

  function handleCloseWidgets() {
    currentWidgets = []
  }

  function speak(text: string) {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel()
      const utter = new SpeechSynthesisUtterance(text)
      utter.lang = 'ru-RU'
      utter.rate = 1.0
      window.speechSynthesis.speak(utter)
    }
  }
  
  function handleCapability(cap: any) {
    if (cap.action === 'config') {
      navigate('config')
    } else {
      handleSend(cap.text)
    }
  }
  
  function statusColor(status: string): string {
    if (status === 'ok') return 'text-green-700'
    if (status === 'error') return 'text-red-700'
    if (status === 'not_configured') return 'text-amber-700'
    return 'text-neutral-500'
  }
  
  function formatTime(iso: string | null): string {
    if (!iso) return '—'
    const d = new Date(iso)
    return d.toLocaleTimeString('ru-RU')
  }
  
  // Одна подсказка на модуль + конфигуратор
  const capabilities = $derived(() => {
    const caps: any[] = []
    if (systemInfo?.modules?.includes('health')) {
      caps.push({ text: 'покажи здоровье здания', category: 'Анализ' })
    }
    if (systemInfo?.modules?.includes('schedules')) {
      caps.push({ text: 'расписания', category: 'Планирование' })
    }
    caps.push({ text: 'открой конфигуратор', category: 'Настройки', action: 'config' })
    return caps
  })
</script>

<div class="flex flex-col h-screen bg-neutral-50">
  <header class="bg-neutral-100 border-b border-neutral-200 px-6 py-3 flex items-center justify-between flex-shrink-0">
    <div class="flex items-center gap-3">
      <h1 class="text-base font-mono text-neutral-500 tracking-tight">SCADA.AI <span class="text-neutral-400">v3.0.0</span></h1>
    </div>
    <div class="flex items-center gap-3">
      {#if lastVoiceText}
        <button type="button" onclick={() => speak(lastVoiceText!)} class="p-2 rounded hover:bg-neutral-100 transition" title="Повторить голосом">
          <Volume2 size={20} class="text-neutral-700" />
        </button>
      {/if}
      <button type="button" onclick={() => navigate('config')} class="p-2 rounded hover:bg-neutral-100 transition" title="Конфигуратор">
        <Settings size={20} class="text-neutral-700" />
      </button>
      <div class="flex items-center gap-2 text-sm text-neutral-700">
        <span class="w-2 h-2 rounded-full bg-green-500"></span>
        <span class="font-medium">Online</span>
      </div>
    </div>
  </header>

  <div class="flex-1 flex overflow-hidden">
    <div class="flex-1 flex flex-col bg-white overflow-hidden">
      <div class="flex-1 overflow-y-auto">
        <NarrativePanel />
      </div>
      {#if currentWidgets.length > 0}
        <WidgetRouter widgets={currentWidgets} onClose={handleCloseWidgets} />
      {/if}
      <Input onSend={handleSend} />
    </div>
    
    <aside class="w-80 border-l border-neutral-200 bg-neutral-50 hidden lg:flex lg:flex-col flex-shrink-0 overflow-y-auto">
      {#if systemInfo}
        <div class="p-4 border-b border-neutral-200">
          <h2 class="text-xs font-semibold text-neutral-700 uppercase tracking-wide mb-3">
            Система
          </h2>
          <div class="space-y-2 text-sm">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2 text-neutral-700">
                <Database size={14} />
                <span>БД</span>
              </div>
              <div class="flex items-center gap-1.5">
                <span class="text-xs font-mono text-neutral-500">{systemInfo.db_host}</span>
                {#if systemInfo.db_status === 'ok'}
                  <CheckCircle size={14} class="text-green-700" />
                {:else if systemInfo.db_status === 'error'}
                  <XCircle size={14} class="text-red-700" />
                {:else}
                  <AlertCircle size={14} class="text-neutral-500" />
                {/if}
              </div>
            </div>
            {#if systemInfo.db_stats}
              <div class="text-xs text-neutral-500 pl-6">
                Тегов: <span class="font-mono">{systemInfo.db_stats.tags_count.toLocaleString('ru-RU')}</span>
              </div>
            {/if}
            
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2 text-neutral-700">
                <Cpu size={14} />
                <span>LLM</span>
              </div>
              <div class="flex items-center gap-1.5">
                <span class="text-xs font-mono text-neutral-500 truncate max-w-32">
                  {systemInfo.llm_model.split('/').pop()}
                </span>
                {#if systemInfo.llm_status === 'ok'}
                  <CheckCircle size={14} class="text-green-700" />
                {:else}
                  <XCircle size={14} class="text-red-700" />
                {/if}
              </div>
            </div>
            
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2 text-neutral-700">
                <Zap size={14} />
                <span>SCADA</span>
              </div>
              <span class="text-xs font-mono text-neutral-500 truncate max-w-40">{systemInfo.scada_url}</span>
            </div>
            
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2 text-neutral-700">
                <Cpu size={14} />
                <span>Модули</span>
              </div>
              <span class="text-xs font-mono text-neutral-500">{systemInfo.modules.length} шт</span>
            </div>
            <div class="flex flex-wrap gap-1 pl-6">
              {#each systemInfo.modules as mod}
                <span class="px-2 py-0.5 bg-white border border-neutral-200 rounded text-xs font-mono text-neutral-700">
                  {mod}
                </span>
              {/each}
            </div>
            
            <div class="flex items-center justify-between mt-2">
              <div class="flex items-center gap-2 text-neutral-700">
                <Zap size={14} />
                <span>Tools</span>
              </div>
              <span class="text-xs font-mono text-neutral-500">{health?.tools ?? systemInfo.tools_count ?? 0} шт</span>
            </div>
            
            {#if systemInfo.last_health_check?.timestamp}
              <div class="mt-3 pt-3 border-t border-neutral-200">
                <div class="flex items-center gap-2 text-neutral-700 mb-1">
                  <Clock size={14} />
                  <span class="text-xs font-semibold uppercase tracking-wide">Последний анализ</span>
                </div>
                <div class="pl-6 space-y-0.5 text-xs text-neutral-600">
                  <div>Время: <span class="font-mono">{formatTime(systemInfo.last_health_check.timestamp)}</span></div>
                  <div>Длительность: <span class="font-mono">{systemInfo.last_health_check.duration_sec}с</span></div>
                  {#if systemInfo.last_health_check.score !== null}
                    <div>Оценка: <span class="font-mono font-bold">{systemInfo.last_health_check.score}/100</span></div>
                  {/if}
                </div>
              </div>
            {/if}
          </div>
        </div>
      {/if}
      
      <!-- Подсказки: одна на модуль -->
      {#if capabilities().length > 0}
        <div class="p-4">
          <h2 class="text-xs font-semibold text-neutral-700 uppercase tracking-wide mb-3">
            Доступные команды
          </h2>
          <div class="space-y-2">
            {#each capabilities() as cap}
              <button
                type="button"
                onclick={() => handleCapability(cap)}
                class="w-full text-left px-3 py-2 bg-white border border-neutral-200 rounded hover:border-neutral-400 hover:bg-neutral-50 transition cursor-pointer"
              >
                <div class="flex items-center justify-between gap-2">
                  <span class="text-sm text-neutral-800">{cap.text}</span>
                  <span class="text-xs px-1.5 py-0.5 bg-neutral-100 text-neutral-600 rounded flex-shrink-0">
                    {cap.category}
                  </span>
                </div>
              </button>
            {/each}
          </div>
        </div>
      {/if}
    </aside>
  </div>
</div>
