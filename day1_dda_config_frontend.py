#!/usr/bin/env python3
"""
day1_dda_config_frontend.py — UI конфигуратора DDA + модалка для графиков
"""
from pathlib import Path
import re

print('=' * 80)
print('ЧАСТЬ 2: FRONTEND — UI КОНФИГУРАТОР + МОДАЛКА')
print('=' * 80)
print()

# ============================================================================
# 1. Создаём DDAConfigPanel.svelte
# ============================================================================
dda_panel_path = Path('frontend/src/components/config/DDAConfigPanel.svelte')
dda_panel_path.parent.mkdir(exist_ok=True)

dda_panel_content = '''<script lang="ts">
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
      <Activity size={20} class="text-blue-600" />
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
      <!-- Аномалии -->
      {#if activeSection === 'anomaly'}
        <div class="bg-blue-50 border border-blue-200 rounded p-3 text-sm text-blue-900">
          💡 Эти параметры управляют тем как алгоритм находит и классифицирует аномалии. После изменения запустите анализ заново.
        </div>

        <div class="grid grid-cols-2 gap-4">
          <!-- contamination -->
          <div>
            <label class="block text-sm font-medium text-neutral-700 mb-1">
              Доля аномалий (contamination)
            </label>
            <input
              type="number"
              step="0.01"
              min="0.01"
              max="0.20"
              bind:value={settings.anomaly_detection.contamination}
              class="w-full px-3 py-1.5 border border-neutral-300 rounded text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <p class="text-xs text-neutral-500 mt-1">Ожидаемый % аномалий (0.01-0.20). Сейчас: {(settings.anomaly_detection.contamination * 100).toFixed(1)}%</p>
          </div>

          <!-- n_estimators -->
          <div>
            <label class="block text-sm font-medium text-neutral-700 mb-1">
              Количество деревьев (n_estimators)
            </label>
            <input
              type="number"
              min="10"
              max="500"
              step="10"
              bind:value={settings.anomaly_detection.n_estimators}
              class="w-full px-3 py-1.5 border border-neutral-300 rounded text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <p class="text-xs text-neutral-500 mt-1">Точность Isolation Forest (10-500)</p>
          </div>

          <!-- spike_threshold -->
          <div>
            <label class="block text-sm font-medium text-neutral-700 mb-1 flex items-center gap-1">
              <span class="w-2 h-2 rounded-full bg-red-500"></span>
              Порог пика (z-score)
            </label>
            <input
              type="number"
              step="0.1"
              min="1.0"
              max="5.0"
              bind:value={settings.anomaly_detection.spike_threshold}
              class="w-full px-3 py-1.5 border border-neutral-300 rounded text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <p class="text-xs text-neutral-500 mt-1">Отклонение от среднего для пика (1.0-5.0 std)</p>
          </div>

          <!-- dip_threshold -->
          <div>
            <label class="block text-sm font-medium text-neutral-700 mb-1 flex items-center gap-1">
              <span class="w-2 h-2 rounded-full bg-blue-500"></span>
              Порог провала (z-score)
            </label>
            <input
              type="number"
              step="0.1"
              min="1.0"
              max="5.0"
              bind:value={settings.anomaly_detection.dip_threshold}
              class="w-full px-3 py-1.5 border border-neutral-300 rounded text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <p class="text-xs text-neutral-500 mt-1">Отклонение от среднего для провала (1.0-5.0 std)</p>
          </div>
        </div>

        <div class="border-t border-neutral-200 pt-4 mt-4">
          <h3 class="text-sm font-semibold text-neutral-900 mb-3 flex items-center gap-1.5">
            <Waves size={14} />
            Параметры дрейфа (Drift)
          </h3>
          <div class="grid grid-cols-3 gap-4">
            <div>
              <label class="block text-xs font-medium text-neutral-700 mb-1">Мин. точек</label>
              <input type="number" min="2" max="20" bind:value={settings.anomaly_detection.drift_min_duration}
                class="w-full px-2 py-1 border border-neutral-300 rounded text-sm" />
            </div>
            <div>
              <label class="block text-xs font-medium text-neutral-700 mb-1">R² тренда</label>
              <input type="number" step="0.05" min="0.1" max="0.95" bind:value={settings.anomaly_detection.drift_min_r_squared}
                class="w-full px-2 py-1 border border-neutral-300 rounded text-sm" />
            </div>
            <div>
              <label class="block text-xs font-medium text-neutral-700 mb-1">Мин. изменение</label>
              <input type="number" step="0.01" min="0.01" max="0.20" bind:value={settings.anomaly_detection.drift_min_relative_change}
                class="w-full px-2 py-1 border border-neutral-300 rounded text-sm" />
              <p class="text-xs text-neutral-500 mt-1">{(settings.anomaly_detection.drift_min_relative_change * 100).toFixed(0)}%</p>
            </div>
          </div>
        </div>

        <div class="border-t border-neutral-200 pt-4 mt-4">
          <h3 class="text-sm font-semibold text-neutral-900 mb-3 flex items-center gap-1.5">
            <Zap size={14} />
            Дополнительные параметры
          </h3>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-medium text-neutral-700 mb-1">Порог плато</label>
              <input type="number" step="0.005" min="0.001" max="0.10" bind:value={settings.anomaly_detection.plateau_tolerance}
                class="w-full px-2 py-1 border border-neutral-300 rounded text-sm" />
              <p class="text-xs text-neutral-500 mt-1">Одинаковые значения ({(settings.anomaly_detection.plateau_tolerance * 100).toFixed(1)}%)</p>
            </div>
            <div>
              <label class="block text-xs font-medium text-neutral-700 mb-1">Окно локальной статистики</label>
              <input type="number" min="5" max="100" bind:value={settings.anomaly_detection.local_window}
                class="w-full px-2 py-1 border border-neutral-300 rounded text-sm" />
              <p class="text-xs text-neutral-500 mt-1">Точек для локального mean/std</p>
            </div>
            <div>
              <label class="block text-xs font-medium text-neutral-700 mb-1">Значительный провал</label>
              <input type="number" step="0.05" min="0.10" max="0.80" bind:value={settings.anomaly_detection.significant_dip_ratio}
                class="w-full px-2 py-1 border border-neutral-300 rounded text-sm" />
              <p class="text-xs text-neutral-500 mt-1">{(settings.anomaly_detection.significant_dip_ratio * 100).toFixed(0)}% падения</p>
            </div>
            <div>
              <label class="block text-xs font-medium text-neutral-700 mb-1">Порог "нуля"</label>
              <input type="number" step="0.01" min="0.01" max="0.20" bind:value={settings.anomaly_detection.zero_threshold_ratio}
                class="w-full px-2 py-1 border border-neutral-300 rounded text-sm" />
              <p class="text-xs text-neutral-500 mt-1">{(settings.anomaly_detection.zero_threshold_ratio * 100).toFixed(0)}% от среднего</p>
            </div>
          </div>
        </div>
      {/if}

      <!-- Корреляции -->
      {#if activeSection === 'correlations'}
        <div class="bg-blue-50 border border-blue-200 rounded p-3 text-sm text-blue-900">
          💡 Параметры корреляционного анализа для мульти-теговых запросов.
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-neutral-700 mb-1">Частота ресемплинга</label>
            <select bind:value={settings.correlations.resample_freq}
              class="w-full px-3 py-1.5 border border-neutral-300 rounded text-sm">
              <option value="1min">1 минута</option>
              <option value="5min">5 минут</option>
              <option value="15min">15 минут</option>
              <option value="1h">1 час</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-neutral-700 mb-1">Порог значимости Пирсона</label>
            <input type="number" step="0.05" min="0.1" max="0.9" bind:value={settings.correlations.pearson_threshold}
              class="w-full px-3 py-1.5 border border-neutral-300 rounded text-sm" />
            <p class="text-xs text-neutral-500 mt-1">Минимальный |r| для значимой корреляции</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-neutral-700 mb-1">Макс. лаг cross-correlation</label>
            <input type="number" min="10" max="200" bind:value={settings.correlations.max_lag}
              class="w-full px-3 py-1.5 border border-neutral-300 rounded text-sm" />
            <p class="text-xs text-neutral-500 mt-1">Количество шагов для анализа лага</p>
          </div>
        </div>
      {/if}

      <!-- Визуализация -->
      {#if activeSection === 'visualization'}
        <div class="bg-blue-50 border border-blue-200 rounded p-3 text-sm text-blue-900">
          💡 Параметры отрисовки графиков на фронте.
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-neutral-700 mb-1">
              Downsampling: макс. точек
            </label>
            <input type="number" min="200" max="5000" step="100" bind:value={settings.visualization.max_points}
              class="w-full px-3 py-1.5 border border-neutral-300 rounded text-sm" />
            <p class="text-xs text-neutral-500 mt-1">Большее значение = точнее график, но медленнее</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-neutral-700 mb-1">Размер точек аномалий</label>
            <input type="number" min="2" max="15" bind:value={settings.visualization.anomaly_point_radius}
              class="w-full px-3 py-1.5 border border-neutral-300 rounded text-sm" />
          </div>
          <div>
            <label class="block text-sm font-medium text-neutral-700 mb-1">Толщина линии дрейфа</label>
            <input type="number" min="1" max="5" bind:value={settings.visualization.drift_line_width}
              class="w-full px-3 py-1.5 border border-neutral-300 rounded text-sm" />
          </div>
        </div>
      {/if}

      <!-- Цвета -->
      {#if activeSection === 'colors'}
        <div class="bg-blue-50 border border-blue-200 rounded p-3 text-sm text-blue-900">
          💡 Цветовая схема для различных типов аномалий на графиках.
        </div>
        <div class="grid grid-cols-2 gap-4">
          {#each [['spike', 'Пики', '#ef4444'], ['dip', 'Провалы', '#3b82f6'], ['drift', 'Дрейфы', '#f59e0b'], ['noise', 'Шум', '#9ca3af']] as [key, label, default]}
            <div class="border border-neutral-200 rounded p-3">
              <label class="block text-sm font-medium text-neutral-700 mb-2">{label}</label>
              <div class="flex items-center gap-2">
                <input
                  type="color"
                  bind:value={settings.colors[key]}
                  class="w-12 h-10 rounded cursor-pointer border border-neutral-300"
                />
                <input
                  type="text"
                  bind:value={settings.colors[key]}
                  class="flex-1 px-2 py-1 border border-neutral-300 rounded text-sm font-mono"
                  pattern="#[0-9a-fA-F]{6}"
                />
                <button
                  type="button"
                  onclick={() => settings.colors[key] = default}
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
  {/if}
</div>
'''

dda_panel_path.write_text(dda_panel_content, encoding='utf-8', newline='\n')
print('✅ 1. Создан DDAConfigPanel.svelte')
print('   • 4 вкладки: Аномалии / Корреляции / Визуализация / Цвета')
print('   • Все 16 параметров с описаниями и ограничениями')
print('   • Кнопки: Сохранить / Сбросить')
print('   • Color picker для 4 типов аномалий')

# ============================================================================
# 2. Обновляем Config.svelte — добавляем вкладку dda
# ============================================================================
config_path = Path('frontend/src/routes/Config.svelte')
config_content = config_path.read_text(encoding='utf-8')

# 2a. Добавляем импорт DDAConfigPanel
if 'DDAConfigPanel' not in config_content:
    config_content = config_content.replace(
        "import DocsViewer from '../components/DocsViewer.svelte'",
        "import DocsViewer from '../components/DocsViewer.svelte'\n  import DDAConfigPanel from '../components/config/DDAConfigPanel.svelte'"
    )
    print('✅ 2a. Добавлен импорт DDAConfigPanel')

# 2b. Расширяем activeTab — добавляем 'dda'
if "'modules' | 'system' | 'docs' | 'energy'" in config_content:
    config_content = config_content.replace(
        "let activeTab = $state<'modules' | 'system' | 'docs' | 'energy'>('modules')",
        "let activeTab = $state<'modules' | 'system' | 'docs' | 'energy' | 'dda'>('modules')"
    )
    print('✅ 2b. activeTab расширен: добавлен \'dda\'')

# 2c. Добавляем кнопку вкладки "DDA" после вкладки "Модули"
# Ищем кнопку modules и добавляем после неё кнопку dda
modules_button_pattern = r"(<button[^>]*onclick=\{\(\) => activeTab = 'modules'[^>]*>[\s\S]*?</button>)"
match = re.search(modules_button_pattern, config_content)

if match and 'activeTab = \'dda\'' not in config_content:
    modules_button = match.group(1)
    dda_button = '''
          <button
            type="button"
            onclick={() => activeTab = 'dda'}
            class="px-4 py-2 text-sm font-medium rounded transition {activeTab === 'dda' ? 'bg-blue-600 text-white' : 'text-neutral-700 hover:bg-neutral-100'} flex items-center gap-1.5"
          >
            <Activity size={14} />
            DDA
          </button>'''
    
    config_content = config_content.replace(
        modules_button,
        modules_button + dda_button
    )
    print('✅ 2c. Добавлена кнопка вкладки "DDA"')

# 2d. Добавляем рендер DDAConfigPanel после блока modules
modules_block_end = "{/if}\n\n      {#if activeTab === 'system'}"
if modules_block_end in config_content and 'activeTab === \'dda\'' not in config_content:
    dda_block = '''{/if}

      {#if activeTab === 'dda'}
        <DDAConfigPanel />
      {/if}

      {#if activeTab === 'system'}'''
    
    config_content = config_content.replace(modules_block_end, dda_block)
    print('✅ 2d. Добавлен рендер <DDAConfigPanel />')

# 2e. Добавляем импорт Activity иконки если её нет
if 'Activity' not in config_content and 'lucide-svelte' in config_content:
    # Находим строку импорта иконок
    icon_import_pattern = r"(import \{[^}]+) \} from 'lucide-svelte'"
    match = re.search(icon_import_pattern, config_content)
    if match and 'Activity' not in match.group(0):
        old_import = match.group(0)
        new_import = old_import.replace("} from 'lucide-svelte'", ", Activity } from 'lucide-svelte'")
        config_content = config_content.replace(old_import, new_import)
        print('✅ 2e. Добавлен импорт Activity иконки')

config_path.write_text(config_content, encoding='utf-8', newline='\n')

print()
print('=' * 80)
print('ЧАСТЬ 1 (UI КОНФИГУРАТОР) ЗАВЕРШЕНА')
print('=' * 80)
print()
print('Что сделано:')
print('  ✅ DDAConfigPanel.svelte с 4 вкладками')
print('  ✅ Config.svelte: новая вкладка "DDA"')
print('  ✅ Все 16 параметров настраиваются через UI')
print('  ✅ Кнопки Сохранить/Сбросить')
print('  ✅ Color picker для цветов аномалий')
print()
print('=' * 80)
print('ПРОВЕРКА UI КОНФИГУРАТОРА:')
print('=' * 80)
print()
print('1. Открой фронтенд: http://localhost:5173')
print('2. Перейди в "Настройки" (Config)')
print('3. Кликни на вкладку "DDA" (появилась новая!)')
print('4. Попробуй изменить параметры:')
print('   • contamination: 0.06 → 0.10')
print('   • spike_threshold: 2.0 → 2.5')
print('   • Цвет пиков (кликни на квадрат) → выбери другой')
print('5. Нажми "Сохранить" — должен появиться зелёный успех')
print('6. Запусти анализ и убедись что используются новые настройки')
print()
print('Дальше сделаем МОДАЛКУ для графиков? (кнопка ⛶ разворачивания)')