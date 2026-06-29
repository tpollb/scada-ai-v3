<script lang="ts">
  import { onMount } from 'svelte'
  import { getHealth } from '../lib/api'
  import { messages, isLoading, addMessage } from '../stores/chat'
  import { navigate } from '../stores/ui'
  import { theme } from '../stores/theme'
  import Input from '../components/Input.svelte'
  import SystemLogsPanel from '../components/SystemLogsPanel.svelte'
  import DeepAnalysisControls from '../components/DeepAnalysisControls.svelte'
  import DeepAnalysisResults from '../components/DeepAnalysisResults.svelte'
  import NarrativePanel from '../components/NarrativePanel.svelte'
  import WidgetRouter from '../components/WidgetRouter.svelte'
  import api from '../lib/api'
  import { Settings, Volume2, Database, Cpu, Zap, Clock, CheckCircle, XCircle, AlertCircle, Sun, Moon, Terminal, Wrench, Package, ChevronDown, ChevronUp , Activity } from 'lucide-svelte'

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
  let collapsedModules = $state(false)
  let collapsedTools = $state(false)
  let lastVoiceText = $state<string | null>(null)
  let systemInfo = $state<SystemInfo | null>(null)
  let showLogsPanel = $state(false)
  let showDeepAnalysisPanel = $state(false)
  let ddaTags = $state<any[]>([])
  let ddaSelectedTags = $state<string[]>([])
  let ddaPeriod = $state<number>(30)
  let ddaIsAnalyzing = $state(false)
  let ddaAnalysisResult = $state<any>(null)
  let ddaError = $state<string | null>(null)

  onMount(async () => {
    try { health = await getHealth() } catch (e) { console.error('Failed to fetch health:', e) }
    try { systemInfo = await api.get('system/info').json<SystemInfo>() } catch (e) { console.error('Failed to fetch system info:', e) }
  })

  
  async function runDDAAnalysis() {
    if (ddaSelectedTags.length === 0) {
      ddaError = 'Выберите тег для анализа'
      return
    }

    ddaIsAnalyzing = true
    ddaError = null
    ddaAnalysisResult = null

    try {
      const response = await api.post('api/v1/deep_analysis/run', {
        json: {
          tags: ddaSelectedTags,
          period: ddaPeriod,
          anomalies: true,
          correlations: false,
          seasonality: false,
          compare_periods: false,
        }
      }).json()

      console.log('🔍 DDA Analysis response:', response)
      ddaAnalysisResult = response
    } catch (e: any) {
      console.error('DDA Analysis failed:', e)
      ddaError = e?.message || 'Ошибка анализа'
    } finally {
      ddaIsAnalyzing = false
    }
  }

async function handleSend(message: string) {
    const lower = message.toLowerCase()
    if (lower.includes('логи') || lower.includes('log')) {
      showLogsPanel = true
      return
    }

    // Deep Analysis trigger
    if (lower.includes('глубокий анализ') || lower.includes('deep analysis') || lower.includes('проанализируй тег')) {
      showDeepAnalysisPanel = true
      return
    }
    
    if (lower.includes('конфигуратор') || lower.includes('настройки') || lower.includes('настроить')) {
      navigate('config')
      return
    }
    
    addMessage('user', message)
    isLoading.set(true)
    currentWidgets = []
    lastVoiceText = null

    try {
      if (lower.match(/температур|влажност|температура и влажность|давлен|co2|voc|параметр.*сред/i)) {
        try {
          const resp: any = await api.get('health/metrics-summary').json()
          if (resp && resp.params) {
            addMessage('assistant', resp.text || 'Сводка по параметрам среды')
            currentWidgets = [{ type: 'environmental_panel', data: resp.params, size: 'wide' }]
            return
          }
        } catch (e) {
          console.error('Metrics summary failed:', e)
        }
      }
      
      const resp: any = await api.post('chat', { json: { message } }).json()
      addMessage('assistant', resp.response)

      // DEBUG: логируем что пришло с backend
      console.log('Chat response:', {
        status: resp.status,
        has_visual: !!resp.visual,
        visual_widgets: resp.visual?.widgets,
        widgets_count: resp.visual?.widgets?.length || 0
      })
      
      if (resp.visual?.widgets && resp.visual.widgets.length > 0) {
        console.log('Setting widgets:', resp.visual.widgets)
        currentWidgets = resp.visual.widgets
      } else {
        console.log('No widgets to render')
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
  
  function formatTime(iso: string | null): string {
    if (!iso) return '—'
    return new Date(iso).toLocaleTimeString('ru-RU')
  }
  
  const capabilities = $derived(() => {
    const caps: any[] = []
    if (systemInfo?.modules?.includes('health')) {
      caps.push({ text: 'покажи здоровье здания', category: 'Анализ' })
      caps.push({ text: 'проанализируй системный лог', category: 'Анализ' })
      caps.push({ text: 'покажи логи', category: 'Система', action: 'logs' })
    }
    if (systemInfo?.modules?.includes('analytics')) {
      caps.push({ text: 'покажи аналитику', category: 'Анализ', action: 'analytics_panel' })
    }
    if (systemInfo?.modules?.includes('schedules')) {
      caps.push({ text: 'расписания', category: 'Планирование' })
    }
    caps.push({ text: 'открой конфигуратор', category: 'Настройки', action: 'config' })
    return caps
  })

  // Загружаем теги для Deep Analysis при открытии панели
  $effect(() => {
    if (showDeepAnalysisPanel && ddaTags.length === 0) {
      console.log('🔄 Loading DDA tags...')
      api.get('api/v1/deep_analysis/tags').json().then((tags: any[]) => {
        console.log('✓ DDA tags loaded:', tags.length)
        ddaTags = tags
        if (tags.length > 0 && ddaSelectedTags.length === 0) {
          ddaSelectedTags = [tags[0].tag_name]
        }
      }).catch((e: any) => {
        console.error('Failed to fetch DDA tags:', e)
        ddaError = 'Не удалось загрузить список тегов'
      })
    }
  })

</script>

<div class="flex flex-col h-screen bg-neutral-50 dark:bg-neutral-900 transition-colors">
  <header class="bg-neutral-100 dark:bg-neutral-800 border-b border-neutral-200 dark:border-neutral-700 px-6 py-3 flex items-center justify-between flex-shrink-0 transition-colors">
    <div class="flex items-center gap-3">
      <h1 class="text-base font-mono text-neutral-500 dark:text-neutral-400 tracking-tight">
        SCADA.AI <span class="text-neutral-400 dark:text-neutral-500">v3.2.8</span>
      </h1>
    </div>
    <div class="flex items-center gap-2">
      {#if lastVoiceText}
        <button type="button" onclick={() => speak(lastVoiceText!)} class="p-2 rounded hover:bg-neutral-200 dark:hover:bg-neutral-700 transition text-neutral-700 dark:text-neutral-300" title="Повторить голосом">
          <Volume2 size={18} />
        </button>
      {/if}
      <button 
        type="button" 
        onclick={() => showLogsPanel = !showLogsPanel} 
        class="p-2 rounded hover:bg-neutral-200 dark:hover:bg-neutral-700 transition text-neutral-700 dark:text-neutral-300" 
        title={showLogsPanel ? 'Скрыть логи' : 'Показать логи'}
      >
        <Terminal size={18} />
      </button>
      <button
        type="button"
        onclick={() => showDeepAnalysisPanel = !showDeepAnalysisPanel}
        class="p-2 rounded hover:bg-neutral-200 dark:hover:bg-neutral-700 transition text-neutral-700 dark:text-neutral-300"
        title={showDeepAnalysisPanel ? 'Скрыть анализ' : 'Deep Analysis'}
      >
        <Activity size={18} />
      </button>

      <button 
        type="button" 
        onclick={() => theme.toggle()} 
        class="p-2 rounded hover:bg-neutral-200 dark:hover:bg-neutral-700 transition text-neutral-700 dark:text-neutral-300" 
        title={$theme === 'dark' ? 'Светлая тема' : 'Тёмная тема'}
      >
        {#if $theme === 'dark'}
          <Sun size={18} />
        {:else}
          <Moon size={18} />
        {/if}
      </button>
      <button type="button" onclick={() => navigate('config')} class="p-2 rounded hover:bg-neutral-200 dark:hover:bg-neutral-700 transition text-neutral-700 dark:text-neutral-300" title="Конфигуратор">
        <Settings size={18} />
      </button>
      <div class="flex items-center gap-2 text-sm text-neutral-700 dark:text-neutral-300 ml-2">
        <span class="w-2 h-2 rounded-full bg-green-500"></span>
        <span class="font-medium">Online</span>
      </div>
    </div>
  </header>

  <div class="flex-1 flex overflow-hidden">
    {#if showLogsPanel}
      <SystemLogsPanel onClose={() => showLogsPanel = false} />
    {/if}
    {#if showDeepAnalysisPanel}
      <DeepAnalysisControls
        tags={ddaTags}
        selectedTags={ddaSelectedTags}
        period={ddaPeriod}
        isAnalyzing={ddaIsAnalyzing}
        error={ddaError}
        onTagsChange={(tags) => ddaSelectedTags = tags}
        onPeriodChange={(period) => ddaPeriod = period}
        onRunAnalysis={runDDAAnalysis}
        onClose={() => showDeepAnalysisPanel = false}
      />
    {/if}
    <div class="flex-1 flex flex-col bg-white dark:bg-neutral-900 overflow-hidden transition-colors">
      {#if showDeepAnalysisPanel}
        <DeepAnalysisResults
          analysisResult={ddaAnalysisResult}
          isAnalyzing={ddaIsAnalyzing}
        />
      {:else}

      <div class="flex-1 overflow-y-auto">
        <NarrativePanel />
      </div>
      {#if currentWidgets.length > 0}
        <WidgetRouter widgets={currentWidgets} onClose={handleCloseWidgets} />
      {/if}
      <Input onSend={handleSend} />
    {/if}
    </div>
    
    <aside class="w-80 border-l border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-900 hidden lg:flex lg:flex-col flex-shrink-0 overflow-y-auto transition-colors">
      {#if systemInfo}
        <div class="p-4 border-b border-neutral-200 dark:border-neutral-700">
          <h2 class="text-xs font-semibold text-neutral-700 dark:text-neutral-300 uppercase tracking-wide mb-3">
            Система
          </h2>
          <div class="space-y-2 text-sm">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2 text-neutral-700 dark:text-neutral-300">
                <Database size={14} />
                <span>БД</span>
              </div>
              <div class="flex items-center gap-1.5">
                <span class="text-xs font-mono text-neutral-500 dark:text-neutral-400">{systemInfo.db_host}</span>
                {#if systemInfo.db_status === 'ok'}
                  <CheckCircle size={14} class="text-green-600 dark:text-green-400" />
                {:else if systemInfo.db_status === 'error'}
                  <XCircle size={14} class="text-red-600 dark:text-red-400" />
                {:else}
                  <AlertCircle size={14} class="text-neutral-500" />
                {/if}
              </div>
            </div>
            {#if systemInfo.db_stats}
              <div class="text-xs text-neutral-500 dark:text-neutral-400 pl-6">
                Тегов: <span class="font-mono">{systemInfo.db_stats.tags_count.toLocaleString('ru-RU')}</span>
              </div>
            {/if}
            
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2 text-neutral-700 dark:text-neutral-300">
                <Cpu size={14} />
                <span>LLM</span>
              </div>
              <div class="flex items-center gap-1.5">
                <span class="text-xs font-mono text-neutral-500 dark:text-neutral-400 truncate max-w-32">
                  {systemInfo.llm_model.split('/').pop()}
                </span>
                {#if systemInfo.llm_status === 'ok'}
                  <CheckCircle size={14} class="text-green-600 dark:text-green-400" />
                {:else}
                  <XCircle size={14} class="text-red-600 dark:text-red-400" />
                {/if}
              </div>
            </div>
            
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2 text-neutral-700 dark:text-neutral-300">
                <Zap size={14} />
                <span>SCADA</span>
              </div>
              <span class="text-xs font-mono text-neutral-500 dark:text-neutral-400 truncate max-w-40">{systemInfo.scada_url}</span>
            </div>
            
            <button
              type="button"
              onclick={() => collapsedModules = !collapsedModules}
              class="w-full flex items-center justify-between hover:bg-neutral-100 dark:hover:bg-neutral-800 rounded px-1 -mx-1 transition"
            >
              <div class="flex items-center gap-2 text-neutral-700 dark:text-neutral-300">
                <Package size={14} />
                <span>Модули</span>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-xs font-mono text-neutral-500 dark:text-neutral-400">{systemInfo.modules.length} шт</span>
                {#if collapsedModules}
                  <ChevronDown size={14} class="text-neutral-400" />
                {:else}
                  <ChevronUp size={14} class="text-neutral-400" />
                {/if}
              </div>
            </button>
            {#if !collapsedModules}
              <div class="flex flex-wrap gap-1 pl-6 mt-1">
                {#each systemInfo.modules as mod}
                  <span class="px-2 py-0.5 bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded text-xs font-mono text-neutral-700 dark:text-neutral-300">
                    {mod}
                  </span>
                {/each}
              </div>
            {/if}
            
            <button
              type="button"
              onclick={() => collapsedTools = !collapsedTools}
              class="w-full flex items-center justify-between mt-2 hover:bg-neutral-100 dark:hover:bg-neutral-800 rounded px-1 -mx-1 transition"
            >
              <div class="flex items-center gap-2 text-neutral-700 dark:text-neutral-300">
                <Wrench size={14} />
                <span>Инструменты</span>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-xs font-mono text-neutral-500 dark:text-neutral-400">{systemInfo.tools_names?.length ?? systemInfo.tools_count ?? 0} шт</span>
                {#if collapsedTools}
                  <ChevronDown size={14} class="text-neutral-400" />
                {:else}
                  <ChevronUp size={14} class="text-neutral-400" />
                {/if}
              </div>
            </button>
            {#if !collapsedTools && systemInfo.tools_names && systemInfo.tools_names.length > 0}
              <div class="flex flex-wrap gap-1 pl-6 mt-1">
                {#each systemInfo.tools_names as tool}
                  <span class="px-2 py-0.5 bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded text-xs font-mono text-neutral-700 dark:text-neutral-300">
                    {tool}
                  </span>
                {/each}
              </div>
            {/if}
            
            {#if systemInfo.last_health_check?.timestamp}
              <div class="mt-3 pt-3 border-t border-neutral-200 dark:border-neutral-700">
                <div class="flex items-center gap-2 text-neutral-700 dark:text-neutral-300 mb-1">
                  <Clock size={14} />
                  <span class="text-xs font-semibold uppercase tracking-wide">Последний анализ</span>
                </div>
                <div class="pl-6 space-y-0.5 text-xs text-neutral-600 dark:text-neutral-400">
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
      
      {#if capabilities().length > 0}
        <div class="p-4">
          <h2 class="text-xs font-semibold text-neutral-700 dark:text-neutral-300 uppercase tracking-wide mb-3">
            Доступные команды
          </h2>
          <div class="space-y-2">
            {#each capabilities() as cap}
              <button
                type="button"
                onclick={() => handleCapability(cap)}
                class="w-full text-left px-3 py-2 bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded hover:border-neutral-400 dark:hover:border-neutral-500 hover:bg-neutral-50 dark:hover:bg-neutral-700 transition cursor-pointer"
              >
                <div class="flex items-center justify-between gap-2">
                  <span class="text-sm text-neutral-800 dark:text-neutral-200">{cap.text}</span>
                  <span class="text-xs px-1.5 py-0.5 bg-neutral-100 dark:bg-neutral-700 text-neutral-600 dark:text-neutral-300 rounded flex-shrink-0">
                    {cap.category}
                  </span>
                </div>
              </button>
            {/each}
            
            <!-- Переключатель темы в сайдбаре -->
            <button
              type="button"
              onclick={() => theme.toggle()}
              class="w-full text-left px-3 py-2 bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded hover:border-neutral-400 dark:hover:border-neutral-500 hover:bg-neutral-50 dark:hover:bg-neutral-700 transition cursor-pointer mt-3"
            >
              <div class="flex items-center justify-between gap-2">
                <span class="text-sm text-neutral-800 dark:text-neutral-200 flex items-center gap-2">
                  {#if $theme === 'dark'}
                    <Sun size={14} />
                    Светлая тема
                  {:else}
                    <Moon size={14} />
                    Тёмная тема
                  {/if}
                </span>
                <span class="text-xs px-1.5 py-0.5 bg-neutral-100 dark:bg-neutral-700 text-neutral-600 dark:text-neutral-300 rounded flex-shrink-0">
                  Оформление
                </span>
              </div>
            </button>
          </div>
        </div>
      {/if}
    </aside>
  </div>
</div>
