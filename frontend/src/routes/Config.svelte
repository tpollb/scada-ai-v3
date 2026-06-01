<script lang="ts">
  import { onMount } from 'svelte'
  import { navigate } from '../stores/ui'
  import { ArrowLeft, RefreshCw, Save, AlertCircle, CheckCircle, Server, Database, Key } from 'lucide-svelte'
  import api from '../lib/api'

  interface ModuleInfo {
    name: string
    version: string
    description: string
    enabled: boolean
    status: string
    error?: string
    prompts: Record<string, string>
  }

  interface EnvConfig {
    db_host: string
    db_port: number
    db_name: string
    db_user: string
    db_password: string
    scada_base_url: string
    yandex_api_key: string
    yandex_folder_id: string
    yandex_gpt_model: string
    llm_temperature: number
    llm_max_tokens: number
    llm_timeout: number
    city: string
    timezone: string
    latitude: number
    longitude: number
  }

  let activeTab = $state<'modules' | 'system'>('modules')
  let modules = $state<ModuleInfo[]>([])
  let envConfig = $state<EnvConfig | null>(null)
  let loading = $state(true)
  let selectedModule = $state<string | null>(null)
  let editingPrompt = $state<{name: string, text: string} | null>(null)
  let saving = $state(false)
  let saveMessage = $state('')


  // === Автоопределение города ===
  let cityResolveTimer: ReturnType<typeof setTimeout> | null = null
  let cityResolving = $state(false)
  let cityResolveError = $state<string | null>(null)
  let cityResolveSuccess = $state<string | null>(null)
  
  function resolveCity() {
    if (!envConfig?.city || envConfig.city.length < 2) return
    
    // Очищаем предыдущий таймер (debounce 800ms)
    if (cityResolveTimer) clearTimeout(cityResolveTimer)
    
    cityResolveTimer = setTimeout(async () => {
      cityResolving = true
      cityResolveError = null
      cityResolveSuccess = null
      try {
        const result: any = await api.get(`config/resolve-city?city=${encodeURIComponent(envConfig!.city)}`).json()
        if (result.error) {
          cityResolveError = result.error
        } else {
          envConfig!.city = result.city
          envConfig!.latitude = result.latitude
          envConfig!.longitude = result.longitude
          envConfig!.timezone = result.timezone
          
          const location = [result.city, result.state, result.country].filter(Boolean).join(', ')
          cityResolveSuccess = `Найдено: ${location} (${result.timezone})`
          setTimeout(() => cityResolveSuccess = null, 5000)
        }
      } catch (e: any) {
        cityResolveError = e?.message || 'Ошибка определения города'
      } finally {
        cityResolving = false
      }
    }, 800)
  }
  
  // Автоматически вызываем resolveCity при изменении города
  $effect(() => {
    const city = envConfig?.city
    if (city) resolveCity()
  })

  onMount(async () => {
    await Promise.all([loadModules(), loadEnv()])
    loading = false
  })

  async function loadModules() {
    try {
      modules = await api.get('config/modules').json<ModuleInfo[]>()
    } catch (e) {
      console.error('Failed to load modules:', e)
    }
  }

  async function loadEnv() {
    try {
      envConfig = await api.get('config/env').json<EnvConfig>()
    } catch (e) {
      console.error('Failed to load env:', e)
    }
  }

  function selectModule(name: string) {
    selectedModule = name
    editingPrompt = null
  }

  function editPrompt(name: string, text: string) {
    editingPrompt = { name, text }
  }

  async function savePrompt() {
    if (!editingPrompt || !selectedModule) return
    saving = true
    try {
      await api.put(`config/modules/${selectedModule}/prompts/${editingPrompt.name}`, {
        json: {
          module: selectedModule,
          prompt_name: editingPrompt.name,
          prompt_text: editingPrompt.text,
        }
      })
      const mod = modules.find(m => m.name === selectedModule)
      if (mod) mod.prompts[editingPrompt.name] = editingPrompt.text
      saveMessage = 'Промпт сохранен'
      setTimeout(() => saveMessage = '', 3000)
      editingPrompt = null
    } catch (e) {
      saveMessage = 'Ошибка сохранения'
    } finally {
      saving = false
    }
  }

  async function saveEnv() {
    if (!envConfig) return
    saving = true
    try {
      await api.put('config/env', { json: envConfig })
      saveMessage = 'Конфигурация сохранена. Перезапустите backend для применения изменений.'
      setTimeout(() => saveMessage = '', 5000)
    } catch (e) {
      saveMessage = 'Ошибка сохранения'
    } finally {
      saving = false
    }
  }

  async function reloadModule(name: string) {
    try {
      await api.post(`config/modules/${name}/reload`)
      await loadModules()
    } catch (e) {
      console.error('Reload failed:', e)
    }
  }

  let selected = $derived(modules.find(m => m.name === selectedModule))
</script>

<div class="flex flex-col h-screen bg-neutral-50">
  <header class="bg-white border-b border-neutral-200 px-6 py-4 flex items-center gap-4">
    <button type="button" onclick={() => navigate('operator')} class="p-2 rounded hover:bg-neutral-100 transition">
      <ArrowLeft size={20} class="text-neutral-700" />
    </button>
    <div class="flex items-center gap-3 flex-1">
      <h1 class="text-xl font-semibold text-neutral-900">Конфигуратор</h1>
      <span class="text-sm text-neutral-500">v3.0.0</span>
    </div>
    <div class="flex gap-1 bg-neutral-100 rounded p-1">
      <button
        type="button"
        onclick={() => activeTab = 'modules'}
        class="px-4 py-1.5 text-sm font-medium rounded transition {activeTab === 'modules' ? 'bg-white shadow-sm text-neutral-900' : 'text-neutral-600 hover:text-neutral-900'}"
      >
        Модули
      </button>
      <button
        type="button"
        onclick={() => activeTab = 'system'}
        class="px-4 py-1.5 text-sm font-medium rounded transition {activeTab === 'system' ? 'bg-white shadow-sm text-neutral-900' : 'text-neutral-600 hover:text-neutral-900'}"
      >
        Система
      </button>
    </div>
  </header>

  {#if saveMessage}
    <div class="px-6 py-3 bg-blue-50 border-b border-blue-200 text-sm text-blue-900">
      {saveMessage}
    </div>
  {/if}

  {#if activeTab === 'modules'}
    <div class="flex-1 flex overflow-hidden">
      <aside class="w-80 border-r border-neutral-200 bg-white overflow-y-auto">
        <div class="p-4 border-b border-neutral-200">
          <h2 class="text-sm font-semibold text-neutral-700 uppercase tracking-wide">
            Модули системы
          </h2>
        </div>
        {#if loading}
          <div class="p-4 text-center text-neutral-500 text-sm">Загрузка...</div>
        {:else}
          <div class="divide-y divide-neutral-100">
            {#each modules as mod}
              <button
                type="button"
                onclick={() => selectModule(mod.name)}
                class="w-full text-left p-4 hover:bg-neutral-50 transition {selectedModule === mod.name ? 'bg-neutral-100' : ''}"
              >
                <div class="flex items-start justify-between mb-1">
                  <span class="font-medium text-neutral-900">{mod.name}</span>
                  {#if mod.status === 'loaded'}
                    <CheckCircle size={16} class="text-green-600 flex-shrink-0" />
                  {:else}
                    <AlertCircle size={16} class="text-neutral-400 flex-shrink-0" />
                  {/if}
                </div>
                <div class="text-xs text-neutral-500 mb-1 font-mono">v{mod.version}</div>
                {#if mod.description}
                  <div class="text-xs text-neutral-600">{mod.description}</div>
                {/if}
                {#if mod.error}
                  <div class="text-xs text-red-600 mt-1">{mod.error}</div>
                {/if}
              </button>
            {/each}
          </div>
        {/if}
      </aside>

      <main class="flex-1 overflow-y-auto">
        {#if !selectedModule}
          <div class="flex items-center justify-center h-full text-neutral-500 text-sm">
            Выберите модуль для настройки
          </div>
        {:else if selected}
          <div class="p-6 max-w-4xl">
            <div class="flex items-center justify-between mb-6">
              <div>
                <h2 class="text-2xl font-semibold text-neutral-900 mb-1">{selected.name}</h2>
                <p class="text-sm text-neutral-600">{selected.description}</p>
              </div>
              <button
                type="button"
                onclick={() => reloadModule(selected.name)}
                class="flex items-center gap-2 px-4 py-2 bg-white border border-neutral-300 rounded hover:bg-neutral-50 transition text-sm"
              >
                <RefreshCw size={16} />
                Перезагрузить
              </button>
            </div>

            <div class="space-y-6">
              {#each Object.entries(selected.prompts) as [name, text]}
                <div class="bg-white border border-neutral-200 rounded">
                  <div class="px-4 py-3 border-b border-neutral-200 flex items-center justify-between">
                    <h3 class="font-mono text-sm font-medium text-neutral-900">{name}</h3>
                    <button
                      type="button"
                      onclick={() => editPrompt(name, text)}
                      class="text-xs font-medium text-blue-600 hover:text-blue-800"
                    >
                      Редактировать
                    </button>
                  </div>
                  <pre class="p-4 text-xs text-neutral-700 overflow-x-auto whitespace-pre-wrap font-mono">{text}</pre>
                </div>
              {/each}
            </div>
          </div>
        {/if}
      </main>
    </div>
  {:else if activeTab === 'system'}
    <div class="flex-1 overflow-y-auto p-6">
      <div class="max-w-3xl mx-auto space-y-6">
        <!-- База данных -->
        <section class="bg-white border border-neutral-200 rounded">
          <div class="px-4 py-3 border-b border-neutral-200 flex items-center gap-2">
            <Database size={18} class="text-neutral-600" />
            <h3 class="font-semibold text-neutral-900">База данных (PostgreSQL)</h3>
          </div>
          <div class="p-4 grid grid-cols-2 gap-4">
            <label class="block">
              <span class="block text-xs font-medium text-neutral-600 uppercase tracking-wide mb-1">Host</span>
              <input type="text" bind:value={envConfig!.db_host} class="w-full px-3 py-2 border border-neutral-300 rounded font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </label>
            <label class="block">
              <span class="block text-xs font-medium text-neutral-600 uppercase tracking-wide mb-1">Port</span>
              <input type="number" bind:value={envConfig!.db_port} class="w-full px-3 py-2 border border-neutral-300 rounded font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </label>
            <label class="block">
              <span class="block text-xs font-medium text-neutral-600 uppercase tracking-wide mb-1">Database</span>
              <input type="text" bind:value={envConfig!.db_name} class="w-full px-3 py-2 border border-neutral-300 rounded font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </label>
            <label class="block">
              <span class="block text-xs font-medium text-neutral-600 uppercase tracking-wide mb-1">User</span>
              <input type="text" bind:value={envConfig!.db_user} class="w-full px-3 py-2 border border-neutral-300 rounded font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </label>
            <label class="block col-span-2">
              <span class="block text-xs font-medium text-neutral-600 uppercase tracking-wide mb-1">Password</span>
              <input type="password" bind:value={envConfig!.db_password} class="w-full px-3 py-2 border border-neutral-300 rounded font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </label>
          </div>
        </section>

        <!-- SCADA -->
        <section class="bg-white border border-neutral-200 rounded">
          <div class="px-4 py-3 border-b border-neutral-200 flex items-center gap-2">
            <Server size={18} class="text-neutral-600" />
            <h3 class="font-semibold text-neutral-900">SCADA REST API</h3>
          </div>
          <div class="p-4">
            <label class="block">
              <span class="block text-xs font-medium text-neutral-600 uppercase tracking-wide mb-1">Base URL</span>
              <input type="text" bind:value={envConfig!.scada_base_url} class="w-full px-3 py-2 border border-neutral-300 rounded font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="http://localhost:9002" />
            </label>
          </div>
        </section>

        <!-- Локация (с автоопределением) -->
        <section class="bg-white border border-neutral-200 rounded">
          <div class="px-4 py-3 border-b border-neutral-200 flex items-center justify-between">
            <div class="flex items-center gap-2">
              <h3 class="font-semibold text-neutral-900">Локация</h3>
              <span class="text-xs text-neutral-500">(для энергоэффективности)</span>
            </div>
            {#if cityResolving}
              <div class="flex items-center gap-2 text-xs text-blue-600">
                <span class="inline-block w-3 h-3 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></span>
                Определяем...
              </div>
            {:else if cityResolveSuccess}
              <div class="text-xs text-green-700 font-medium">{cityResolveSuccess}</div>
            {:else if cityResolveError}
              <div class="text-xs text-red-600">{cityResolveError}</div>
            {/if}
          </div>
          <div class="p-4 space-y-4">
            <!-- Город с автоподстановкой -->
            <div>
              <label class="block">
                <span class="block text-xs font-medium text-neutral-600 uppercase tracking-wide mb-1">
                  Город <span class="text-neutral-400 normal-case">(координаты и timezone определятся автоматически)</span>
                </span>
                <div class="relative">
                  <input
                    type="text"
                    bind:value={envConfig!.city}
                    oninput={() => resolveCity()}
                    class="w-full px-3 py-2 pr-24 border border-neutral-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Нижний Тагил"
                  />
                  <div class="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-2">
                    {#if cityResolving}
                      <span class="inline-block w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></span>
                    {:else}
                      <button
                        type="button"
                        onclick={() => resolveCity()}
                        class="text-xs px-2 py-1 bg-neutral-100 hover:bg-neutral-200 rounded transition text-neutral-700"
                        title="Определить сейчас"
                      >
                        Найти
                      </button>
                    {/if}
                  </div>
                </div>
              </label>
              <p class="mt-1 text-xs text-neutral-500">
                Подсказка: введите город, область (например "Нижний Тагил, Свердловская область")
              </p>
            </div>
            
            <!-- Автоматически определённые параметры (read-only) -->
            <div class="grid grid-cols-3 gap-3 pt-3 border-t border-neutral-100">
              <div>
                <div class="text-xs text-neutral-500 uppercase tracking-wide mb-1">Timezone</div>
                <div class="px-3 py-2 bg-neutral-50 border border-neutral-200 rounded font-mono text-sm text-neutral-700">
                  {envConfig?.timezone || '—'}
                </div>
              </div>
              <div>
                <div class="text-xs text-neutral-500 uppercase tracking-wide mb-1">Широта</div>
                <div class="px-3 py-2 bg-neutral-50 border border-neutral-200 rounded font-mono text-sm text-neutral-700 tabular-nums">
                  {envConfig?.latitude?.toFixed(4) ?? '—'}
                </div>
              </div>
              <div>
                <div class="text-xs text-neutral-500 uppercase tracking-wide mb-1">Долгота</div>
                <div class="px-3 py-2 bg-neutral-50 border border-neutral-200 rounded font-mono text-sm text-neutral-700 tabular-nums">
                  {envConfig?.longitude?.toFixed(4) ?? '—'}
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- LLM -->
        <section class="bg-white border border-neutral-200 rounded">
          <div class="px-4 py-3 border-b border-neutral-200 flex items-center gap-2">
            <Key size={18} class="text-neutral-600" />
            <h3 class="font-semibold text-neutral-900">YandexGPT (LLM)</h3>
          </div>
          <div class="p-4 grid grid-cols-2 gap-4">
            <label class="block col-span-2">
              <span class="block text-xs font-medium text-neutral-600 uppercase tracking-wide mb-1">API Key</span>
              <input type="password" bind:value={envConfig!.yandex_api_key} class="w-full px-3 py-2 border border-neutral-300 rounded font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="AQVN..." />
            </label>
            <label class="block col-span-2">
              <span class="block text-xs font-medium text-neutral-600 uppercase tracking-wide mb-1">Folder ID</span>
              <input type="text" bind:value={envConfig!.yandex_folder_id} class="w-full px-3 py-2 border border-neutral-300 rounded font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="b1gq..." />
            </label>
            <label class="block col-span-2">
              <span class="block text-xs font-medium text-neutral-600 uppercase tracking-wide mb-1">Model</span>
              <input type="text" bind:value={envConfig!.yandex_gpt_model} class="w-full px-3 py-2 border border-neutral-300 rounded font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </label>
            <label class="block">
              <span class="block text-xs font-medium text-neutral-600 uppercase tracking-wide mb-1">Temperature</span>
              <input type="number" step="0.01" bind:value={envConfig!.llm_temperature} class="w-full px-3 py-2 border border-neutral-300 rounded font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </label>
            <label class="block">
              <span class="block text-xs font-medium text-neutral-600 uppercase tracking-wide mb-1">Max Tokens</span>
              <input type="number" bind:value={envConfig!.llm_max_tokens} class="w-full px-3 py-2 border border-neutral-300 rounded font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </label>
            <label class="block col-span-2">
              <span class="block text-xs font-medium text-neutral-600 uppercase tracking-wide mb-1">Timeout (сек)</span>
              <input type="number" bind:value={envConfig!.llm_timeout} class="w-full px-3 py-2 border border-neutral-300 rounded font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </label>
          </div>
        </section>

        <div class="flex justify-end gap-3 sticky bottom-0 bg-neutral-50 py-4 border-t border-neutral-200">
          <button
            type="button"
            onclick={() => loadEnv()}
            class="px-4 py-2 border border-neutral-300 rounded hover:bg-neutral-50 transition text-sm"
          >
            Отменить
          </button>
          <button
            type="button"
            onclick={saveEnv}
            disabled={saving}
            class="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 transition text-sm font-medium"
          >
            <Save size={16} />
            {saving ? 'Сохранение...' : 'Сохранить конфигурацию'}
          </button>
        </div>
      </div>
    </div>
  {/if}

  {#if editingPrompt}
    <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] flex flex-col">
        <div class="px-6 py-4 border-b border-neutral-200 flex items-center justify-between">
          <h3 class="text-lg font-semibold text-neutral-900">Редактирование: {editingPrompt.name}</h3>
          <button type="button" onclick={() => editingPrompt = null} class="text-neutral-500 hover:text-neutral-700 text-xl">x</button>
        </div>
        <div class="flex-1 p-6 overflow-y-auto">
          <textarea
            bind:value={editingPrompt.text}
            class="w-full h-96 p-4 border border-neutral-300 rounded font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            spellcheck="false"
          ></textarea>
        </div>
        <div class="px-6 py-4 border-t border-neutral-200 flex justify-end gap-3">
          <button type="button" onclick={() => editingPrompt = null} class="px-4 py-2 border border-neutral-300 rounded hover:bg-neutral-50 transition text-sm">
            Отмена
          </button>
          <button
            type="button"
            onclick={savePrompt}
            disabled={saving}
            class="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 transition text-sm font-medium"
          >
            <Save size={16} />
            {saving ? 'Сохранение...' : 'Сохранить'}
          </button>
        </div>
      </div>
    </div>
  {/if}
</div>
