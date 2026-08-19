<!-- svelte-ignore a11y_label_has_associated_control -->
<script lang="ts">
  import { onMount } from 'svelte'
  import { navigate } from '../stores/ui'
  import { Activity, AlertCircle, ArrowLeft, CheckCircle, Database, DollarSign, Droplet, Edit2, FileText, Flame, Key, Moon, Plus, RefreshCw, Save, Server, Sun, Trash2, Wrench, Zap } from 'lucide-svelte'
  import { theme } from '../stores/theme'
  import { auth, hasAnyPermission, hasAllPermissions } from '../stores/auth'
  import api from '../lib/api'
  import DocsViewer from '../components/DocsViewer.svelte'
  import DDAConfigPanel from '../components/config/DDAConfigPanel.svelte'

  // Проверка прав доступа к конфигурации
  const canViewConfig = hasAnyPermission(['config:view'])
  const canEditConfig = hasAllPermissions(['config:edit'])
  const canManageUsers = hasAllPermissions(['users:create', 'users:edit', 'users:delete'])
  const canViewAudit = hasAnyPermission(['audit:view'])

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

  // === Энергоучёт ===
  interface Tariff {
    id: string
    start_date: string
    end_date: string | null
    price_per_unit: number
    currency: string
    note?: string
  }

  interface Meter {
    id: string
    name: string
    tag_current: string
    tag_last: string
  }

  interface EnergyResourceConfig {
    enabled: boolean
    unit: string
    meters: Meter[]
  }

  interface EnergyConfig {
    electricity: EnergyResourceConfig
    water: EnergyResourceConfig
    heat: EnergyResourceConfig
  }


  let activeTab = $state<'modules' | 'system' | 'docs' | 'energy' | 'dda'>('modules')
  let modules = $state<ModuleInfo[]>([])
  let envConfig = $state<EnvConfig | null>(null)
  let loading = $state(true)
  let selectedModule = $state<string | null>(null)
  let editingPrompt = $state<{name: string, text: string} | null>(null)
  let saving = $state(false)
  let saveMessage = $state('')

  // === Энергоучёт state ===
  let tariffs = $state<Record<string, Tariff[]>>({ electricity: [], water: [], heat: [] })
  let energyConfig = $state<EnergyConfig | null>(null)
  let selectedEnergyResource = $state<'electricity' | 'water' | 'heat'>('electricity')
  let editingTariff = $state<Tariff | null>(null)
  let editingMeter = $state<Meter | null>(null)
  let energyLoading = $state(false)
  let energyMessage = $state<{type: 'success' | 'error', text: string} | null>(null)



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

  // Автозагрузка данных энергоучёта при переключении вкладки
  $effect(() => {
    if (activeTab === 'energy' && !energyConfig) {
      loadEnergyData()
    }
  })

  onMount(async () => {
    await loadLogsConfig()
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

  

  // === Энергоучёт: загрузка данных ===
  async function loadEnergyData() {
    energyLoading = true
    energyMessage = null
    try {
      const [tariffsData, configData] = await Promise.all([
        api.get('energy/tariffs').json(),
        api.get('energy/config').json()
      ])
      tariffs = tariffsData
      energyConfig = configData as EnergyConfig
    } catch (e: any) {
      energyMessage = { type: 'error', text: e?.message || 'Ошибка загрузки данных энергоучёта' }
    } finally {
      energyLoading = false
    }
  }

  // === Энергоучёт: тарифы ===
  function startEditTariff(tariff?: Tariff) {
    editingTariff = tariff ? { ...tariff } : {
      id: '',
      start_date: new Date().toISOString().split('T')[0],
      end_date: null,
      price_per_unit: 0,
      currency: 'RUB',
      note: ''
    }
  }

  async function saveTariff() {
    if (!editingTariff) return
    energyLoading = true
    energyMessage = null
    try {
      if (editingTariff.id) {
        // Update
        await api.put(`energy/tariffs/${selectedEnergyResource}/${editingTariff.id}`, {
          json: {
            start_date: editingTariff.start_date,
            end_date: editingTariff.end_date,
            price_per_unit: editingTariff.price_per_unit,
            currency: editingTariff.currency,
            note: editingTariff.note
          }
        })
        energyMessage = { type: 'success', text: 'Тариф обновлён' }
      } else {
        // Create
        await api.post('energy/tariffs', {
          json: {
            resource: selectedEnergyResource,
            start_date: editingTariff.start_date,
            end_date: editingTariff.end_date,
            price_per_unit: editingTariff.price_per_unit,
            currency: editingTariff.currency,
            note: editingTariff.note
          }
        })
        energyMessage = { type: 'success', text: 'Тариф создан' }
      }
      await loadEnergyData()
      editingTariff = null
      setTimeout(() => energyMessage = null, 3000)
    } catch (e: any) {
      energyMessage = { type: 'error', text: e?.message || 'Ошибка сохранения тарифа' }
    } finally {
      energyLoading = false
    }
  }

  async function deleteTariff(tariffId: string) {
    if (!confirm('Удалить тариф?')) return
    energyLoading = true
    energyMessage = null
    try {
      await api.delete(`energy/tariffs/${selectedEnergyResource}/${tariffId}`)
      energyMessage = { type: 'success', text: 'Тариф удалён' }
      await loadEnergyData()
      setTimeout(() => energyMessage = null, 3000)
    } catch (e: any) {
      energyMessage = { type: 'error', text: e?.message || 'Ошибка удаления тарифа' }
    } finally {
      energyLoading = false
    }
  }

  // === Энергоучёт: счётчики ===
  function startEditMeter(meter?: Meter) {
    editingMeter = meter ? { ...meter } : {
      id: '',
      name: '',
      tag_current: '',
      tag_last: ''
    }
  }

  async function saveMeter() {
    if (!editingMeter || !energyConfig) return
    energyLoading = true
    energyMessage = null
    try {
      const resource = energyConfig[selectedEnergyResource]
      const meters = [...resource.meters]
      const existingIdx = meters.findIndex(m => m.id === editingMeter.id)
      
      if (existingIdx >= 0) {
        meters[existingIdx] = editingMeter
      } else {
        meters.push(editingMeter)
      }

      await api.put(`energy/config/${selectedEnergyResource}`, {
        json: {
          enabled: resource.enabled,
          unit: resource.unit,
          meters: meters
        }
      })
      energyMessage = { type: 'success', text: 'Счётчик сохранён' }
      await loadEnergyData()
      editingMeter = null
      setTimeout(() => energyMessage = null, 3000)
    } catch (e: any) {
      energyMessage = { type: 'error', text: e?.message || 'Ошибка сохранения счётчика' }
    } finally {
      energyLoading = false
    }
  }

  async function deleteMeter(meterId: string) {
    if (!confirm('Удалить счётчик?')) return
    if (!energyConfig) return
    energyLoading = true
    energyMessage = null
    try {
      const resource = energyConfig[selectedEnergyResource]
      const meters = resource.meters.filter(m => m.id !== meterId)

      await api.put(`energy/config/${selectedEnergyResource}`, {
        json: {
          enabled: resource.enabled,
          unit: resource.unit,
          meters: meters
        }
      })
      energyMessage = { type: 'success', text: 'Счётчик удалён' }
      await loadEnergyData()
      setTimeout(() => energyMessage = null, 3000)
    } catch (e: any) {
      energyMessage = { type: 'error', text: e?.message || 'Ошибка удаления счётчика' }
    } finally {
      energyLoading = false
    }
  }

  async function toggleResourceEnabled(enabled: boolean) {
    if (!energyConfig) return
    energyLoading = true
    energyMessage = null
    try {
      const resource = energyConfig[selectedEnergyResource]
      await api.put(`energy/config/${selectedEnergyResource}`, {
        json: {
          enabled: enabled,
          unit: resource.unit,
          meters: resource.meters
        }
      })
      energyMessage = { type: 'success', text: enabled ? 'Ресурс включён' : 'Ресурс выключен' }
      await loadEnergyData()
      setTimeout(() => energyMessage = null, 3000)
    } catch (e: any) {
      energyMessage = { type: 'error', text: e?.message || 'Ошибка изменения состояния' }
    } finally {
      energyLoading = false
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

  // === Управление состоянием модулей ===
  let togglingModule = $state<string | null>(null)
  let moduleMessage = $state<{type: 'success' | 'error' | 'info', text: string} | null>(null)
  
  async function toggleModule(moduleName: string, enabled: boolean) {
    togglingModule = moduleName
    moduleMessage = null
    try {
      const resp: any = await api.put(`config/modules/${moduleName}/enabled`, {
        json: { enabled }
      }).json()
      
      if (resp.status === 'error') {
        moduleMessage = { type: 'error', text: resp.message }
      } else {
        moduleMessage = { 
          type: resp.restart_required ? 'info' : 'success', 
          text: resp.message 
        }
        // Обновляем локально
        const mod = modules.find(m => m.name === moduleName)
        if (mod) {
          mod.enabled = enabled
          mod.status = enabled ? 'loaded' : 'not_loaded'
        }
      }
      
      setTimeout(() => moduleMessage = null, 8000)
    } catch (e: any) {
      moduleMessage = { type: 'error', text: e?.message || 'Ошибка переключения' }
      setTimeout(() => moduleMessage = null, 5000)
    } finally {
      togglingModule = null
    }
  }


  let selected = $derived(modules.find(m => m.name === selectedModule))

  // === Logs module settings ===
  let logPollInterval = $state(2000)
  let logPollSaving = $state(false)
  let logPollMessage = $state<{type: 'success' | 'error', text: string} | null>(null)
  
  async function loadLogsConfig() {
    try {
      const resp: any = await api.get('system/logs/config').json()
      logPollInterval = resp.poll_interval_ms ?? 2000
    } catch (e) {
      console.error('Failed to load logs config:', e)
    }
  }
  
  async function saveLogsPollInterval() {
    logPollSaving = true
    logPollMessage = null
    try {
      const resp: any = await api.put(`system/logs/config?poll_interval_ms=${logPollInterval}`).json()
      logPollMessage = { type: 'success', text: resp.message || 'Сохранено' }
      setTimeout(() => logPollMessage = null, 4000)
    } catch (e: any) {
      logPollMessage = { type: 'error', text: e?.message || 'Ошибка сохранения' }
      setTimeout(() => logPollMessage = null, 5000)
    } finally {
      logPollSaving = false
    }
  }

</script>

<div class="flex flex-col h-screen bg-neutral-50 dark:bg-neutral-900 transition-colors">
  <header class="bg-white border-b border-neutral-200 px-6 py-4 flex items-center gap-4">
    <button type="button" onclick={() => navigate('operator')} class="p-2 rounded hover:bg-neutral-100 transition">
      <ArrowLeft size={20} class="text-neutral-700" />
    </button>
    <div class="flex items-center gap-3 flex-1">
      <h1 class="text-xl font-semibold text-neutral-900">Конфигуратор</h1>
      <span class="text-sm text-neutral-500">v3.2.8.1</span>
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
            onclick={() => activeTab = 'dda'}
            class="px-4 py-2 text-sm font-medium rounded transition {activeTab === 'dda' ? 'bg-white shadow-sm text-neutral-900' : 'text-neutral-600 hover:bg-neutral-100'} flex items-center gap-1.5"
          >
            <Activity size={14} />
            DDA
          </button>
      <button
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
      <button
        type="button"
        onclick={() => activeTab = 'energy'}
        class="px-4 py-1.5 text-sm font-medium rounded transition flex items-center gap-2 {activeTab === 'energy' ? 'bg-white shadow-sm text-neutral-900' : 'text-neutral-600 hover:text-neutral-900'}"
      >
        <DollarSign size={14} />
        Энергоучёт
      </button>
    </div>
  </header>

        {#if moduleMessage}
        <div class="px-6 py-3 border-b text-sm {
          moduleMessage.type === 'error' ? 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800 text-red-900 dark:text-red-100' :
          moduleMessage.type === 'info' ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800 text-blue-900 dark:text-blue-100' :
          'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800 text-green-900 dark:text-green-100'
        }">
          {moduleMessage.text}
        </div>
      {/if}

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
              <div class="flex items-start justify-between gap-2 p-4 hover:bg-neutral-50 transition {selectedModule === mod.name ? 'bg-neutral-100' : ''}">
                <button
                  type="button"
                  onclick={() => selectModule(mod.name)}
                  class="flex-1 text-left min-w-0"
                >
                  <div class="flex items-center gap-2 mb-1">
                    <span class="font-medium text-neutral-900">{mod.name}</span>
                    {#if mod.status === 'loaded'}
                      <CheckCircle size={14} class="text-green-600 flex-shrink-0" />
                    {:else}
                      <AlertCircle size={14} class="text-neutral-400 flex-shrink-0" />
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
                
                <!-- Toggle switch -->
                <label class="relative inline-flex items-center cursor-pointer flex-shrink-0 mt-1">
                  <input 
                    type="checkbox" 
                    class="sr-only peer" 
                    checked={mod.enabled}
                    disabled={togglingModule === mod.name}
                    onchange={(e) => toggleModule(mod.name, e.currentTarget.checked)}
                  />
                  <div class="w-11 h-6 bg-neutral-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-neutral-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600 {togglingModule === mod.name ? 'opacity-50' : ''}"></div>
                </label>
              </div>
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

          <!-- Logs module settings -->
          {#if selected?.name === 'logs'}
            <div class="mt-6 pt-6 border-t border-neutral-200 dark:border-neutral-700">
              <h3 class="text-sm font-semibold text-neutral-900 dark:text-neutral-100 mb-3">
                Настройки
              </h3>

              <div>
                <label class="block">
                  <span class="block text-xs font-semibold text-neutral-900 dark:text-neutral-100 mb-1">
                    Интервал обновления логов (мс)
                  </span>
                  <input
                    type="number"
                    bind:value={logPollInterval}
                    min="500"
                    max="10000"
                    step="500"
                    class="w-full px-3 py-2 border border-neutral-300 dark:border-neutral-600 rounded bg-white dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </label>
                <p class="text-xs text-neutral-500 dark:text-neutral-400 mt-1">
                  От 500 до 10000 мс. Меньше = чаще обновление.
                  Текущее: <span class="font-mono">{logPollInterval}мс ({(logPollInterval / 1000).toFixed(1)}с)</span>
                </p>
                <div class="mt-4 mb-8 flex items-center gap-3">
                  <button
                    type="button"
                    onclick={saveLogsPollInterval}
                    disabled={logPollSaving}
                    class="flex items-center gap-2 px-4 py-2 bg-white dark:bg-neutral-800 border border-neutral-300 dark:border-neutral-600 rounded hover:bg-neutral-50 dark:hover:bg-neutral-700 transition text-sm text-neutral-900 dark:text-neutral-100 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Save size={16} />
                    {logPollSaving ? 'Сохранение...' : 'Сохранить'}
                  </button>
                  {#if logPollMessage}
                    <span class="text-xs {logPollMessage.type === 'error' ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400'}">
                      {logPollMessage.text}
                    </span>
                  {/if}
                </div>
              </div>
            </div>
          {/if}

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
  {:else if activeTab === 'docs'}
    <div class="flex-1 overflow-hidden">
      <DocsViewer />
    </div>
  {:else if activeTab === 'energy'}
    <div class="flex-1 overflow-y-auto p-6">
      <div class="max-w-4xl mx-auto space-y-6">
        {#if energyMessage}
          <div class="px-6 py-3 border-b text-sm {
            energyMessage.type === 'error' ? 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800 text-red-900 dark:text-red-100' :
            'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800 text-green-900 dark:text-green-100'
          }">
            {energyMessage.text}
          </div>
        {/if}

        {#if energyLoading}
          <div class="text-center py-12 text-neutral-500">Загрузка...</div>
        {:else if energyConfig}
          <!-- Селектор ресурса -->
          <section class="bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded">
            <div class="px-4 py-3 border-b border-neutral-200 dark:border-neutral-700 flex items-center justify-between">
              <div class="flex items-center gap-2">
                <Zap size={18} class="text-neutral-600 dark:text-neutral-400" />
                <h3 class="font-semibold text-neutral-900 dark:text-neutral-100">Ресурс</h3>
              </div>
              <label class="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={energyConfig[selectedEnergyResource].enabled}
                  onchange={(e) => toggleResourceEnabled(e.currentTarget.checked)}
                  class="rounded"
                />
                <span class="text-neutral-700 dark:text-neutral-300">Включён</span>
              </label>
            </div>
            <div class="p-4 flex gap-2">
              {#each ['electricity', 'water', 'heat'] as res}
                <button
                  type="button"
                  onclick={() => selectedEnergyResource = res}
                  class="px-4 py-2 text-sm rounded transition {selectedEnergyResource === res ? 'bg-accent text-white' : 'bg-neutral-100 dark:bg-neutral-700 text-neutral-700 dark:text-neutral-300 hover:bg-neutral-200 dark:hover:bg-neutral-600'}"
                >
                  <span class="flex items-center gap-1.5">
                    {#if res === 'electricity'}
                      <Zap size={14} />
                      <span>Электричество</span>
                    {:else if res === 'water'}
                      <Droplet size={14} />
                      <span>Вода</span>
                    {:else}
                      <Flame size={14} />
                      <span>Тепло</span>
                    {/if}
                  </span>
                </button>
              {/each}
            </div>
          </section>

          <!-- Тарифы -->
          <section class="bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded">
            <div class="px-4 py-3 border-b border-neutral-200 dark:border-neutral-700 flex items-center justify-between">
              <h3 class="font-semibold text-neutral-900 dark:text-neutral-100">Тарифы</h3>
              <button
                type="button"
                onclick={() => startEditTariff()}
                class="flex items-center gap-1 px-3 py-1.5 text-sm bg-accent text-white rounded hover:bg-accent/90 transition"
              >
                <Plus size={14} />
                Добавить
              </button>
            </div>
            <div class="p-4">
              {#if tariffs[selectedEnergyResource].length === 0}
                <div class="text-center py-8 text-neutral-500 dark:text-neutral-400 text-sm">
                  Нет тарифов для этого ресурса
                </div>
              {:else}
                <div class="overflow-x-auto">
                  <table class="w-full text-sm">
                    <thead>
                      <tr class="border-b border-neutral-200 dark:border-neutral-700">
                        <th class="text-left py-2 px-2 text-neutral-600 dark:text-neutral-400 font-medium">Начало</th>
                        <th class="text-left py-2 px-2 text-neutral-600 dark:text-neutral-400 font-medium">Конец</th>
                        <th class="text-right py-2 px-2 text-neutral-600 dark:text-neutral-400 font-medium">Цена</th>
                        <th class="text-left py-2 px-2 text-neutral-600 dark:text-neutral-400 font-medium">Валюта</th>
                        <th class="text-left py-2 px-2 text-neutral-600 dark:text-neutral-400 font-medium">Примечание</th>
                        <th class="text-right py-2 px-2 text-neutral-600 dark:text-neutral-400 font-medium">Действия</th>
                      </tr>
                    </thead>
                    <tbody>
                      {#each tariffs[selectedEnergyResource] as tariff}
                        <tr class="border-b border-neutral-100 dark:border-neutral-700/50">
                          <td class="py-2 px-2 font-mono text-xs">{tariff.start_date}</td>
                          <td class="py-2 px-2 font-mono text-xs">{tariff.end_date || '∞'}</td>
                          <td class="py-2 px-2 text-right font-mono font-semibold">{tariff.price_per_unit}</td>
                          <td class="py-2 px-2 text-xs">{tariff.currency}</td>
                          <td class="py-2 px-2 text-xs text-neutral-600 dark:text-neutral-400">{tariff.note || '-'}</td>
                          <td class="py-2 px-2 text-right">
                            <button
                              type="button"
                              onclick={() => startEditTariff(tariff)}
                              class="p-1 text-neutral-500 hover:text-accent transition"
                              title="Редактировать"
                            >
                              <Edit2 size={14} />
                            </button>
                            <button
                              type="button"
                              onclick={() => deleteTariff(tariff.id)}
                              class="p-1 text-neutral-500 hover:text-red-600 transition ml-1"
                              title="Удалить"
                            >
                              <Trash2 size={14} />
                            </button>
                          </td>
                        </tr>
                      {/each}
                    </tbody>
                  </table>
                </div>
              {/if}
            </div>
          </section>

          <!-- Счётчики -->
          <section class="bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded">
            <div class="px-4 py-3 border-b border-neutral-200 dark:border-neutral-700 flex items-center justify-between">
              <h3 class="font-semibold text-neutral-900 dark:text-neutral-100">Счётчики (теги ЛЭРС)</h3>
              <button
                type="button"
                onclick={() => startEditMeter()}
                class="flex items-center gap-1 px-3 py-1.5 text-sm bg-accent text-white rounded hover:bg-accent/90 transition"
              >
                <Plus size={14} />
                Добавить
              </button>
            </div>
            <div class="p-4">
              {#if energyConfig[selectedEnergyResource].meters.length === 0}
                <div class="text-center py-8 text-neutral-500 dark:text-neutral-400 text-sm">
                  Нет счётчиков для этого ресурса
                </div>
              {:else}
                <div class="space-y-2">
                  {#each energyConfig[selectedEnergyResource].meters as meter}
                    <div class="flex items-center justify-between p-3 bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-700 rounded">
                      <div class="flex-1 min-w-0">
                        <div class="font-medium text-sm text-neutral-900 dark:text-neutral-100">{meter.name}</div>
                        <div class="text-xs text-neutral-500 dark:text-neutral-400 font-mono mt-1">
                          ID: {meter.id}
                        </div>
                        <div class="text-xs text-neutral-500 dark:text-neutral-400 font-mono mt-0.5">
                          Текущий: {meter.tag_current}
                        </div>
                        <div class="text-xs text-neutral-500 dark:text-neutral-400 font-mono mt-0.5">
                          Прошлый: {meter.tag_last}
                        </div>
                      </div>
                      <div class="flex gap-1 ml-3">
                        <button
                          type="button"
                          onclick={() => startEditMeter(meter)}
                          class="p-1.5 text-neutral-500 hover:text-accent transition"
                          title="Редактировать"
                        >
                          <Edit2 size={14} />
                        </button>
                        <button
                          type="button"
                          onclick={() => deleteMeter(meter.id)}
                          class="p-1.5 text-neutral-500 hover:text-red-600 transition"
                          title="Удалить"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </div>
                  {/each}
                </div>
              {/if}
            </div>
          </section>
        {/if}
      </div>
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

      {#if activeTab === 'dda'}
        <div class="p-6">
          <DDAConfigPanel />
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

  {#if editingTariff}
    <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div class="bg-white dark:bg-neutral-800 rounded-lg shadow-xl w-full max-w-lg">
        <div class="px-6 py-4 border-b border-neutral-200 dark:border-neutral-700 flex items-center justify-between">
          <h3 class="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
            {editingTariff.id ? 'Редактировать тариф' : 'Новый тариф'}
          </h3>
          <button type="button" onclick={() => editingTariff = null} class="text-neutral-500 hover:text-neutral-700 dark:hover:text-neutral-300 text-xl">×</button>
        </div>
        <div class="p-6 space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <label class="block">
              <span class="block text-xs font-medium text-neutral-600 dark:text-neutral-400 uppercase tracking-wide mb-1">Дата начала</span>
              <input type="date" bind:value={editingTariff.start_date} class="w-full px-3 py-2 border border-neutral-300 dark:border-neutral-600 dark:bg-neutral-900 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </label>
            <label class="block">
              <span class="block text-xs font-medium text-neutral-600 dark:text-neutral-400 uppercase tracking-wide mb-1">Дата окончания</span>
              <input type="date" bind:value={editingTariff.end_date} class="w-full px-3 py-2 border border-neutral-300 dark:border-neutral-600 dark:bg-neutral-900 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
              <span class="text-xs text-neutral-500 mt-1 block">Оставьте пустым для бессрочного</span>
            </label>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <label class="block">
              <span class="block text-xs font-medium text-neutral-600 dark:text-neutral-400 uppercase tracking-wide mb-1">Цена за единицу</span>
              <input type="number" step="0.01" bind:value={editingTariff.price_per_unit} class="w-full px-3 py-2 border border-neutral-300 dark:border-neutral-600 dark:bg-neutral-900 rounded font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </label>
            <label class="block">
              <span class="block text-xs font-medium text-neutral-600 dark:text-neutral-400 uppercase tracking-wide mb-1">Валюта</span>
              <input type="text" bind:value={editingTariff.currency} class="w-full px-3 py-2 border border-neutral-300 dark:border-neutral-600 dark:bg-neutral-900 rounded font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </label>
          </div>
          <label class="block">
            <span class="block text-xs font-medium text-neutral-600 dark:text-neutral-400 uppercase tracking-wide mb-1">Примечание</span>
            <input type="text" bind:value={editingTariff.note} class="w-full px-3 py-2 border border-neutral-300 dark:border-neutral-600 dark:bg-neutral-900 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Тариф 2026 года" />
          </label>
        </div>
        <div class="px-6 py-4 border-t border-neutral-200 dark:border-neutral-700 flex justify-end gap-3">
          <button type="button" onclick={() => editingTariff = null} class="px-4 py-2 border border-neutral-300 dark:border-neutral-600 rounded hover:bg-neutral-50 dark:hover:bg-neutral-700 transition text-sm text-neutral-900 dark:text-neutral-100">
            Отмена
          </button>
          <button
            type="button"
            onclick={saveTariff}
            disabled={energyLoading}
            class="flex items-center gap-2 px-4 py-2 bg-accent text-white rounded hover:bg-accent/90 disabled:opacity-50 transition text-sm font-medium"
          >
            <Save size={16} />
            {energyLoading ? 'Сохранение...' : 'Сохранить'}
          </button>
        </div>
      </div>
    </div>
  {/if}

  {#if editingMeter}
    <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div class="bg-white dark:bg-neutral-800 rounded-lg shadow-xl w-full max-w-lg">
        <div class="px-6 py-4 border-b border-neutral-200 dark:border-neutral-700 flex items-center justify-between">
          <h3 class="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
            {editingMeter.id ? 'Редактировать счётчик' : 'Новый счётчик'}
          </h3>
          <button type="button" onclick={() => editingMeter = null} class="text-neutral-500 hover:text-neutral-700 dark:hover:text-neutral-300 text-xl">×</button>
        </div>
        <div class="p-6 space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <label class="block">
              <span class="block text-xs font-medium text-neutral-600 dark:text-neutral-400 uppercase tracking-wide mb-1">ID</span>
              <input type="text" bind:value={editingMeter.id} disabled={!!editingMeter.id} class="w-full px-3 py-2 border border-neutral-300 dark:border-neutral-600 dark:bg-neutral-900 rounded font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50" placeholder="input_1" />
            </label>
            <label class="block">
              <span class="block text-xs font-medium text-neutral-600 dark:text-neutral-400 uppercase tracking-wide mb-1">Название</span>
              <input type="text" bind:value={editingMeter.name} class="w-full px-3 py-2 border border-neutral-300 dark:border-neutral-600 dark:bg-neutral-900 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Первый ввод" />
            </label>
          </div>
          <label class="block">
            <span class="block text-xs font-medium text-neutral-600 dark:text-neutral-400 uppercase tracking-wide mb-1">Тег текущего месяца</span>
            <input type="text" bind:value={editingMeter.tag_current} class="w-full px-3 py-2 border border-neutral-300 dark:border-neutral-600 dark:bg-neutral-900 rounded font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="LERS.electricity meter current month 1" />
          </label>
          <label class="block">
            <span class="block text-xs font-medium text-neutral-600 dark:text-neutral-400 uppercase tracking-wide mb-1">Тег прошлого месяца</span>
            <input type="text" bind:value={editingMeter.tag_last} class="w-full px-3 py-2 border border-neutral-300 dark:border-neutral-600 dark:bg-neutral-900 rounded font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="LERS.electricity meter last month 1" />
          </label>
        </div>
        <div class="px-6 py-4 border-t border-neutral-200 dark:border-neutral-700 flex justify-end gap-3">
          <button type="button" onclick={() => editingMeter = null} class="px-4 py-2 border border-neutral-300 dark:border-neutral-600 rounded hover:bg-neutral-50 dark:hover:bg-neutral-700 transition text-sm text-neutral-900 dark:text-neutral-100">
            Отмена
          </button>
          <button
            type="button"
            onclick={saveMeter}
            disabled={energyLoading}
            class="flex items-center gap-2 px-4 py-2 bg-accent text-white rounded hover:bg-accent/90 disabled:opacity-50 transition text-sm font-medium"
          >
            <Save size={16} />
            {energyLoading ? 'Сохранение...' : 'Сохранить'}
          </button>
        </div>
      </div>
    </div>
  {/if}

</div>
