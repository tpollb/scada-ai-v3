<script lang="ts">
  import { onMount } from 'svelte'
  import { Save, RotateCcw, AlertCircle, CheckCircle, Activity, TrendingUp, GitBranch, Waves, Zap, Palette, Eye } from 'lucide-svelte'
  import api from '../../lib/api'

  interface AnomalyDetection {
    contamination: number
    n_estimators: number
    spike_threshold: number
    dip_threshold: number
    drift_min_duration: number
    drift_min_r_squared: number
    drift_min_relative_change: number
    plateau_tolerance: number
    local_window: number
    significant_dip_ratio: number
    zero_threshold_ratio: number
  }

  interface Correlations {
    resample_freq: string
    pearson_threshold: number
    max_lag: number
  }

  interface Visualization {
    max_points: number
    anomaly_point_radius: number
    drift_line_width: number
  }

  interface Colors {
    spike: string
    dip: string
    drift: string
    noise: string
  }

  interface DDASettings {
    anomaly_detection: AnomalyDetection
    correlations: Correlations
    visualization: Visualization
    colors: Colors
  }

  let settings = $state<DDASettings | null>(null)
  let loading = $state(true)
  let saving = $state(false)
  let message = $state<{type: 'success' | 'error', text: string} | null>(null)
  let activeSection = $state<'anomaly' | 'correlations' | 'visualization' | 'colors'>('anomaly')

  onMount(async () => {
    await loadSettings()
  })

  async function loadSettings() {
    loading = true
    try {
      settings = await api.get('config/modules/deep_analysis/settings').json<DDASettings>()
    } catch (e: any) {
      showMessage('error', 'Не удалось загрузить настройки: ' + (e?.message || 'неизвестная ошибка'))
    } finally {
      loading = false
    }
  }

  async function saveSettings() {
    if (!settings) return
    saving = true
    try {
      const result: any = await api.put('config/modules/deep_analysis/settings', { json: settings }).json()
      showMessage('success', result.message || 'Настройки сохранены')
    } catch (e: any) {
      showMessage('error', 'Ошибка сохранения: ' + (e?.message || 'неизвестная ошибка'))
    } finally {
      saving = false
    }
  }

  async function resetSettings() {
    if (!confirm('Сбросить все настройки к значениям по умолчанию?')) return
    saving = true
    try {
      const result: any = await api.post('config/modules/deep_analysis/settings/reset').json()
      settings = result.settings
      showMessage('success', result.message || 'Настройки сброшены')
    } catch (e: any) {
      showMessage('error', 'Ошибка сброса: ' + (e?.message || 'неизвестная ошибка'))
    } finally {
      saving = false
    }
  }

  function showMessage(type: 'success' | 'error', text: string) {
    message = { type, text }
    setTimeout(() => message = null, 5000)
  }
</script>

<div class="bg-white rounded-lg border border-neutral-200 shadow-sm">
  <!-- Header -->
  <div class="p-4 border-b border-neutral-200 flex items-center justify-between">
    <div class="flex items-center gap-2">
      <Activity size={20} class="text-neutral-900" />
      <h2 class="text-lg font-semibold text-neutral-900">Deep Data Analysis — Настройки</h2>
    </div>
    <div class="flex items-center gap-2">
      <button
        type="button"
        onclick={resetSettings}
        disabled={saving || loading}
        class="px-3 py-1.5 text-sm text-neutral-700 hover:bg-neutral-100 rounded transition disabled:opacity-50 flex items-center gap-1"
        title="Сбросить к дефолтам"
      >
        <RotateCcw size={14} />
        Сбросить
      </button>
      <button
        type="button"
        onclick={saveSettings}
        disabled={saving || loading || !settings}
        class="px-4 py-1.5 text-sm bg-blue-600 text-white hover:bg-blue-700 rounded transition disabled:opacity-50 flex items-center gap-1 font-medium"
      >
        {#if saving}
          <div class="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
        {:else}
          <Save size={14} />
        {/if}
        Сохранить
      </button>
    </div>
  </div>

  {#if message}
    <div class="px-4 py-2 border-b flex items-center gap-2 text-sm {message.type === 'success' ? 'bg-green-50 text-green-800 border-green-200' : 'bg-red-50 text-red-800 border-red-200'}">
      {#if message.type === 'success'}
        <CheckCircle size={14} />
      {:else}
        <AlertCircle size={14} />
      {/if}
      {message.text}
    </div>
  {/if}

  {#if loading}
    <div class="p-12 text-center text-neutral-500">
      <div class="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
      Загрузка настроек...
    </div>
  {:else if settings}
    <!-- Tabs -->
    <div class="flex border-b border-neutral-200">
      <button
        type="button"
        onclick={() => activeSection = 'anomaly'}
        class="px-4 py-2 text-sm font-medium border-b-2 transition {activeSection === 'anomaly' ? 'border-blue-600 text-blue-600' : 'border-transparent text-neutral-600 hover:text-neutral-900'} flex items-center gap-1.5"
      >
        <TrendingUp size={14} />
        Аномалии
      </button>
      <button
        type="button"
        onclick={() => activeSection = 'correlations'}
        class="px-4 py-2 text-sm font-medium border-b-2 transition {activeSection === 'correlations' ? 'border-blue-600 text-blue-600' : 'border-transparent text-neutral-600 hover:text-neutral-900'} flex items-center gap-1.5"
      >
        <GitBranch size={14} />
        Корреляции
      </button>
      <button
        type="button"
        onclick={() => activeSection = 'visualization'}
        class="px-4 py-2 text-sm font-medium border-b-2 transition {activeSection === 'visualization' ? 'border-blue-600 text-blue-600' : 'border-transparent text-neutral-600 hover:text-neutral-900'} flex items-center gap-1.5"
      >
        <Eye size={14} />
        Визуализация
      </button>
      <button
        type="button"
        onclick={() => activeSection = 'colors'}
        class="px-4 py-2 text-sm font-medium border-b-2 transition {activeSection === 'colors' ? 'border-blue-600 text-blue-600' : 'border-transparent text-neutral-600 hover:text-neutral-900'} flex items-center gap-1.5"
      >
        <Palette size={14} />
        Цвета
      </button>
    </div>

    <div class="p-6 space-y-5">
      <!-- Секция: Аномалии -->
      {#if activeSection === 'anomaly'}
        <div class="bg-neutral-50 border border-neutral-200 rounded p-3 text-sm text-neutral-700">
          <AlertCircle size={14} class="inline mr-1 text-neutral-500" />
          Эти параметры управляют тем как алгоритм находит и классифицирует аномалии. После изменения запустите анализ заново.
        </div>

        <div class="border border-neutral-200 rounded-lg p-4">
          <h3 class="text-lg font-semibold text-neutral-900 mb-4">
            Детекция аномалий (Isolation Forest)
          </h3>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label for="contamination" class="block text-sm font-medium text-neutral-700 mb-1">Доля аномалий</label>
              <input
                id="contamination"
                type="number"
                step="0.01"
                min="0.01"
                max="0.50"
                bind:value={settings.anomaly_detection.contamination}
                class="w-full px-3 py-2 border border-neutral-300 rounded text-sm focus:ring-2 focus:ring-blue-500"
              />
              <p class="text-xs text-neutral-500 mt-1">Ожидаемый % аномалий (сейчас: {(settings.anomaly_detection.contamination * 100).toFixed(1)}%)</p>
            </div>
            <div>
              <label for="n_estimators" class="block text-sm font-medium text-neutral-700 mb-1">Количество деревьев</label>
              <input
                id="n_estimators"
                type="number"
                min="10"
                max="500"
                step="10"
                bind:value={settings.anomaly_detection.n_estimators}
                class="w-full px-3 py-2 border border-neutral-300 rounded text-sm focus:ring-2 focus:ring-blue-500"
              />
              <p class="text-xs text-neutral-500 mt-1">Точность Isolation Forest (10-500)</p>
            </div>
          </div>
        </div>

        <div class="border border-neutral-200 rounded-lg p-4">
          <h3 class="text-sm font-semibold text-neutral-900 mb-3 flex items-center gap-1.5">
            <Zap size={14} />
            Классификация: Пики и Провалы
          </h3>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label for="spike" class="block text-xs font-medium text-neutral-700 mb-1 flex items-center gap-1">
                <span class="w-2 h-2 rounded-full bg-red-500"></span>
                Порог пика (z-score)
              </label>
              <input id="spike" type="number" step="0.1" min="1.0" max="5.0" bind:value={settings.anomaly_detection.spike_threshold}
                class="w-full px-2 py-1 border border-neutral-300 rounded text-sm" />
              <p class="text-xs text-neutral-500 mt-1">Отклонение от среднего (1.0-5.0 std)</p>
            </div>
            <div>
              <label for="dip" class="block text-xs font-medium text-neutral-700 mb-1 flex items-center gap-1">
                <span class="w-2 h-2 rounded-full bg-blue-500"></span>
                Порог провала (z-score)
              </label>
              <input id="dip" type="number" step="0.1" min="1.0" max="5.0" bind:value={settings.anomaly_detection.dip_threshold}
                class="w-full px-2 py-1 border border-neutral-300 rounded text-sm" />
              <p class="text-xs text-neutral-500 mt-1">Отклонение от среднего (1.0-5.0 std)</p>
            </div>
            <div>
              <label for="sig_dip" class="block text-xs font-medium text-neutral-700 mb-1">Значительный провал</label>
              <input id="sig_dip" type="number" step="0.05" min="0.10" max="0.80" bind:value={settings.anomaly_detection.significant_dip_ratio}
                class="w-full px-2 py-1 border border-neutral-300 rounded text-sm" />
              <p class="text-xs text-neutral-500 mt-1">{(settings.anomaly_detection.significant_dip_ratio * 100).toFixed(0)}% падения</p>
            </div>
            <div>
              <label for="zero" class="block text-xs font-medium text-neutral-700 mb-1">Порог "нуля"</label>
              <input id="zero" type="number" step="0.01" min="0.01" max="0.20" bind:value={settings.anomaly_detection.zero_threshold_ratio}
                class="w-full px-2 py-1 border border-neutral-300 rounded text-sm" />
              <p class="text-xs text-neutral-500 mt-1">{(settings.anomaly_detection.zero_threshold_ratio * 100).toFixed(0)}% от среднего</p>
            </div>
          </div>
        </div>

        <div class="border border-neutral-200 rounded-lg p-4">
          <h3 class="text-sm font-semibold text-neutral-900 mb-3 flex items-center gap-1.5">
            <Waves size={14} />
            Детекция дрейфа (Drift)
          </h3>
          <div class="grid grid-cols-3 gap-4">
            <div>
              <label for="drift_dur" class="block text-xs font-medium text-neutral-700 mb-1">Мин. точек</label>
              <input id="drift_dur" type="number" min="2" max="20" bind:value={settings.anomaly_detection.drift_min_duration}
                class="w-full px-2 py-1 border border-neutral-300 rounded text-sm" />
            </div>
            <div>
              <label for="drift_r2" class="block text-xs font-medium text-neutral-700 mb-1">R² тренда</label>
              <input id="drift_r2" type="number" step="0.05" min="0.1" max="0.95" bind:value={settings.anomaly_detection.drift_min_r_squared}
                class="w-full px-2 py-1 border border-neutral-300 rounded text-sm" />
            </div>
            <div>
              <label for="drift_chg" class="block text-xs font-medium text-neutral-700 mb-1">Мин. изменение</label>
              <input id="drift_chg" type="number" step="0.01" min="0.01" max="0.50" bind:value={settings.anomaly_detection.drift_min_relative_change}
                class="w-full px-2 py-1 border border-neutral-300 rounded text-sm" />
              <p class="text-xs text-neutral-500 mt-1">{(settings.anomaly_detection.drift_min_relative_change * 100).toFixed(0)}%</p>
            </div>
          </div>
        </div>

        <div class="border border-neutral-200 rounded-lg p-4">
          <h3 class="text-sm font-semibold text-neutral-900 mb-3 flex items-center gap-1.5">
            <Eye size={14} />
            Локальная статистика
          </h3>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label for="plateau" class="block text-xs font-medium text-neutral-700 mb-1">Порог плато</label>
              <input id="plateau" type="number" step="0.005" min="0.001" max="0.10" bind:value={settings.anomaly_detection.plateau_tolerance}
                class="w-full px-2 py-1 border border-neutral-300 rounded text-sm" />
              <p class="text-xs text-neutral-500 mt-1">Одинаковые значения ({(settings.anomaly_detection.plateau_tolerance * 100).toFixed(1)}%)</p>
            </div>
            <div>
              <label for="window" class="block text-xs font-medium text-neutral-700 mb-1">Окно локальной статистики</label>
              <input id="window" type="number" min="5" max="100" bind:value={settings.anomaly_detection.local_window}
                class="w-full px-2 py-1 border border-neutral-300 rounded text-sm" />
              <p class="text-xs text-neutral-500 mt-1">Точек для локального mean/std</p>
            </div>
          </div>
        </div>
      {/if}

      <!-- Секция: Корреляции -->
      {#if activeSection === 'correlations'}
        <div class="bg-neutral-50 border border-neutral-200 rounded p-3 text-sm text-neutral-700">
          <AlertCircle size={14} class="inline mr-1 text-neutral-500" />
          Параметры корреляционного анализа для мульти-теговых запросов.
        </div>
        <div class="border border-neutral-200 rounded-lg p-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label for="resample" class="block text-sm font-medium text-neutral-700 mb-1">Частота ресемплинга</label>
              <select id="resample" bind:value={settings.correlations.resample_freq}
                class="w-full px-3 py-2 border border-neutral-300 rounded text-sm">
                <option value="1min">1 минута</option>
                <option value="5min">5 минут</option>
                <option value="15min">15 минут</option>
                <option value="1h">1 час</option>
              </select>
            </div>
            <div>
              <label for="pearson" class="block text-sm font-medium text-neutral-700 mb-1">Порог значимости Пирсона</label>
              <input id="pearson" type="number" step="0.05" min="0.1" max="0.9" bind:value={settings.correlations.pearson_threshold}
                class="w-full px-3 py-2 border border-neutral-300 rounded text-sm" />
              <p class="text-xs text-neutral-500 mt-1">Минимальный |r| для значимой корреляции</p>
            </div>
            <div>
              <label for="maxlag" class="block text-sm font-medium text-neutral-700 mb-1">Макс. лаг cross-correlation</label>
              <input id="maxlag" type="number" min="10" max="500" bind:value={settings.correlations.max_lag}
                class="w-full px-3 py-2 border border-neutral-300 rounded text-sm" />
              <p class="text-xs text-neutral-500 mt-1">Количество шагов для анализа лага</p>
            </div>
          </div>
        </div>
      {/if}

      <!-- Секция: Визуализация -->
      {#if activeSection === 'visualization'}
        <div class="bg-neutral-50 border border-neutral-200 rounded p-3 text-sm text-neutral-700">
          <AlertCircle size={14} class="inline mr-1 text-neutral-500" />
          Параметры отрисовки графиков.
        </div>
        <div class="border border-neutral-200 rounded-lg p-4">
          <div class="grid grid-cols-3 gap-4">
            <div>
              <label for="maxpts" class="block text-sm font-medium text-neutral-700 mb-1">Downsampling: макс. точек</label>
              <input id="maxpts" type="number" min="200" max="5000" step="100" bind:value={settings.visualization.max_points}
                class="w-full px-3 py-2 border border-neutral-300 rounded text-sm" />
              <p class="text-xs text-neutral-500 mt-1">Больше = точнее, но медленнее</p>
            </div>
            <div>
              <label for="aptr" class="block text-sm font-medium text-neutral-700 mb-1">Размер точек аномалий</label>
              <input id="aptr" type="number" min="2" max="15" bind:value={settings.visualization.anomaly_point_radius}
                class="w-full px-3 py-2 border border-neutral-300 rounded text-sm" />
            </div>
            <div>
              <label for="dlw" class="block text-sm font-medium text-neutral-700 mb-1">Толщина линии дрейфа</label>
              <input id="dlw" type="number" min="1" max="5" bind:value={settings.visualization.drift_line_width}
                class="w-full px-3 py-2 border border-neutral-300 rounded text-sm" />
            </div>
          </div>
        </div>
      {/if}

      <!-- Секция: Цвета -->
      {#if activeSection === 'colors'}
        <div class="bg-neutral-50 border border-neutral-200 rounded p-3 text-sm text-neutral-700">
          <AlertCircle size={14} class="inline mr-1 text-neutral-500" />
          Цветовая схема для различных типов аномалий на графиках.
        </div>
        <div class="grid grid-cols-2 gap-4">
          {#each [['spike', 'Пики (Spike)', '#ef4444'], ['dip', 'Провалы (Dip)', '#3b82f6'], ['drift', 'Дрейфы (Drift)', '#f59e0b'], ['noise', 'Шум (Noise)', '#9ca3af']] as [key, label, defaultColor]}
            <div class="border border-neutral-200 rounded p-3">
              <label for="color-{key}" class="block text-sm font-medium text-neutral-700 mb-2">{label}</label>
              <div class="flex items-center gap-2">
                <input
                  id="color-{key}"
                  type="color"
                  bind:value={settings.colors[key]}
                  class="w-12 h-10 rounded cursor-pointer border border-neutral-300"
                />
                <input
                  type="text"
                  bind:value={settings.colors[key]}
                  class="flex-1 px-2 py-1 border border-neutral-300 rounded text-sm font-mono"
                />
                <button
                  type="button"
                  onclick={() => settings.colors[key] = defaultColor}
                  class="px-2 py-1 text-xs text-neutral-600 hover:bg-neutral-100 rounded"
                  title="По умолчанию"
                >
                  ↺
                </button>
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </div>
  {:else}
    <div class="p-12 text-center text-neutral-500">
      <AlertCircle size={32} class="mx-auto mb-2 text-neutral-400" />
      Не удалось загрузить настройки. Проверьте что модуль deep_analysis запущен.
    </div>
  {/if}
</div>
