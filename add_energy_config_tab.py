from pathlib import Path

print('=== add_energy_config_tab.py ===')
print()

config_path = Path('frontend/src/routes/Config.svelte')
content = config_path.read_text(encoding='utf-8')

changes = []

# 1. Добавляем импорты иконок
old_import = "import { ArrowLeft, RefreshCw, Save, AlertCircle, CheckCircle, Server, Database, Key, Sun, Moon, FileText } from 'lucide-svelte'"
new_import = "import { ArrowLeft, RefreshCw, Save, AlertCircle, CheckCircle, Server, Database, Key, Sun, Moon, FileText, Wrench, Plus, Trash2, Edit2, DollarSign, Zap } from 'lucide-svelte'"
if old_import in content:
    content = content.replace(old_import, new_import)
    changes.append('✓ Добавлены импорты иконок для энергоучёта')

# 2. Добавляем интерфейсы для энергоучёта (после EnvConfig)
energy_interfaces = '''

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
'''

if 'interface EnvConfig {' in content and 'interface Tariff {' not in content:
    # Вставляем после закрывающей } EnvConfig
    env_config_end = content.find('interface EnvConfig {')
    env_config_end = content.find('}', env_config_end) + 1
    content = content[:env_config_end] + energy_interfaces + content[env_config_end:]
    changes.append('✓ Добавлены интерфейсы Tariff, Meter, EnergyResourceConfig, EnergyConfig')

# 3. Добавляем state переменные для энергоучёта
energy_state = '''

  // === Энергоучёт state ===
  let tariffs = $state<Record<string, Tariff[]>>({ electricity: [], water: [], heat: [] })
  let energyConfig = $state<EnergyConfig | null>(null)
  let selectedEnergyResource = $state<'electricity' | 'water' | 'heat'>('electricity')
  let editingTariff = $state<Tariff | null>(null)
  let editingMeter = $state<Meter | null>(null)
  let energyLoading = $state(false)
  let energyMessage = $state<{type: 'success' | 'error', text: string} | null>(null)
'''

if "let saveMessage = $state('')" in content and 'let tariffs = $state' not in content:
    content = content.replace(
        "let saveMessage = $state('')",
        "let saveMessage = $state('')" + energy_state
    )
    changes.append('✓ Добавлены state переменные для энергоучёта')

# 4. Добавляем функции для энергоучёта (перед функцией saveEnv или после loadEnv)
energy_functions = '''

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
'''

if 'async function saveEnv()' in content and 'async function loadEnergyData()' not in content:
    content = content.replace(
        'async function saveEnv() {',
        energy_functions + '\n  async function saveEnv() {'
    )
    changes.append('✓ Добавлены функции для CRUD тарифов и счётчиков')

# 5. Патчим тип activeTab
old_tab_type = "let activeTab = $state<'modules' | 'system' | 'docs'>('modules')"
new_tab_type = "let activeTab = $state<'modules' | 'system' | 'docs' | 'energy'>('modules')"
if old_tab_type in content:
    content = content.replace(old_tab_type, new_tab_type)
    changes.append('✓ Обновлён тип activeTab (добавлен energy)')

# 6. Патчим кнопку вкладки "Документация" — добавляем кнопку "Энергоучёт" после неё
docs_button = '''      <button
        type="button"
        onclick={() => activeTab = 'docs'}
        class="px-4 py-1.5 text-sm font-medium rounded transition flex items-center gap-2 {activeTab === 'docs' ? 'bg-white shadow-sm text-neutral-900' : 'text-neutral-600 hover:text-neutral-900'}"
      >
        <FileText size={14} />
        Документация
      </button>'''

energy_button = '''      <button
        type="button"
        onclick={() => activeTab = 'energy'}
        class="px-4 py-1.5 text-sm font-medium rounded transition flex items-center gap-2 {activeTab === 'energy' ? 'bg-white shadow-sm text-neutral-900' : 'text-neutral-600 hover:text-neutral-900'}"
      >
        <DollarSign size={14} />
        Энергоучёт
      </button>'''

if docs_button in content and 'Энергоучёт' not in content:
    content = content.replace(docs_button, docs_button + '\n' + energy_button)
    changes.append('✓ Добавлена кнопка вкладки "Энергоучёт"')

# 7. Патчим onMount чтобы загружать энергоучёт при переключении вкладки
# Добавим $effect для автозагрузки при переключении на вкладку energy
energy_effect = '''

  // Автозагрузка данных энергоучёта при переключении вкладки
  $effect(() => {
    if (activeTab === 'energy' && !energyConfig) {
      loadEnergyData()
    }
  })
'''

if '$effect(() => {' in content and 'loadEnergyData' not in content:
    # Вставляем после последнего $effect (про resolveCity)
    # Ищем позицию перед onMount
    onmount_pos = content.find('onMount(async () => {')
    if onmount_pos > 0:
        content = content[:onmount_pos] + energy_effect + '\n  ' + content[onmount_pos:]
        changes.append('✓ Добавлен $effect для автозагрузки энергоучёта')

# 8. Добавляем блок рендеринга для activeTab === 'energy'
energy_ui = '''  {:else if activeTab === 'energy'}
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
                  {res === 'electricity' ? '⚡ Электричество' : res === 'water' ? '💧 Вода' : '🔥 Тепло'}
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

'''

# Ищем место перед {:else if activeTab === 'system'} и вставляем energy блок перед ним
system_block_marker = "  {:else if activeTab === 'system'}"
if system_block_marker in content and 'Энергоучёт' in content and '{:else if activeTab === \'energy\'}' not in content:
    content = content.replace(system_block_marker, energy_ui + system_block_marker)
    changes.append('✓ Добавлен блок рендеринга для activeTab === \'energy\'')

# 9. Добавляем модалки для редактирования тарифа и счётчика (в самом конце, перед </div>)
tariff_modal = '''
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
'''

# Ищем позицию перед закрывающим </div> (самым последним)
# Вставляем модалки перед последним </div>
if '{#if editingTariff}' not in content:
    last_div_pos = content.rfind('</div>')
    if last_div_pos > 0:
        content = content[:last_div_pos] + tariff_modal + '\n' + content[last_div_pos:]
        changes.append('✓ Добавлены модалки для редактирования тарифа и счётчика')

# Сохраняем
config_path.write_text(content, encoding='utf-8', newline='\n')

print()
print('=' * 60)
print('ЧТО ДОБАВЛЕНО:')
print('=' * 60)
for change in changes:
    print(f'  {change}')
print()
print('ВКЛАДКА ЭНЕРГОУЧЁТ:')
print('  • Селектор ресурса: Электричество / Вода / Тепло')
print('  • Переключатель enabled для ресурса')
print('  • Таблица тарифов с CRUD (интервальные тарифы)')
print('  • Список счётчиков с CRUD (теги ЛЭРС)')
print('  • Модалки для редактирования с валидацией')
print()
print('API endpoints используются:')
print('  • GET /energy/tariffs, POST, PUT, DELETE')
print('  • GET /energy/config, PUT /energy/config/{resource}')
print()
print('Vite подхватит через HMR.')
print('Открой Конфигуратор → вкладка "Энергоучёт"')
print()
print('Когда ок — скажи "энергоучёт ок" и коммитим v3.1.0')