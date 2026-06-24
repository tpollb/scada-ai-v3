#!/usr/bin/env python3
"""
create_test_dda_panel.py — создаём минимальный тестовый компонент
"""
from pathlib import Path

print('=' * 80)
print('СОЗДАНИЕ ТЕСТОВОГО КОМПОНЕНТА')
print('=' * 80)
print()

panel_path = Path('frontend/src/components/config/DDAConfigPanel.svelte')

# Создаём минимальный компонент который ТОЧНО отрендерится
minimal_content = '''<script lang="ts">
  import { onMount } from 'svelte'
  import api from '../../lib/api'
  
  let settings = $state<any>(null)
  let loading = $state(true)
  let error = $state<string | null>(null)
  
  onMount(async () => {
    try {
      console.log('DDAConfigPanel: загружаю настройки...')
      const response = await api.get('config/modules/deep_analysis/settings').json()
      console.log('DDAConfigPanel: настройки загружены', response)
      settings = response
    } catch (e: any) {
      console.error('DDAConfigPanel: ошибка загрузки', e)
      error = e?.message || 'Неизвестная ошибка'
    } finally {
      loading = false
    }
  })
</script>

<div class="bg-white rounded-lg border border-neutral-200 shadow-sm p-6">
  <h2 class="text-xl font-bold text-neutral-900 mb-4">🔧 Deep Data Analysis — ТЕСТОВЫЙ КОМПОНЕНТ</h2>
  
  {#if loading}
    <div class="text-center py-8">
      <div class="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
      <p class="text-neutral-600">Загрузка настроек...</p>
    </div>
  {:else if error}
    <div class="bg-red-50 border border-red-200 rounded p-4">
      <h3 class="text-red-800 font-semibold mb-2">❌ Ошибка загрузки</h3>
      <p class="text-red-700 text-sm">{error}</p>
      <p class="text-red-600 text-xs mt-2">Проверьте что backend запущен и endpoint доступен</p>
    </div>
  {:else if settings}
    <div class="space-y-4">
      <div class="bg-green-50 border border-green-200 rounded p-3">
        <p class="text-green-800 font-medium">✅ Настройки успешно загружены!</p>
      </div>
      
      <div class="border border-neutral-200 rounded p-4">
        <h3 class="font-semibold text-neutral-900 mb-2">Текущие настройки:</h3>
        <pre class="text-xs bg-neutral-50 p-3 rounded overflow-auto">{JSON.stringify(settings, null, 2)}</pre>
      </div>
      
      <div class="grid grid-cols-2 gap-4">
        <div class="border border-neutral-200 rounded p-3">
          <h4 class="font-medium text-neutral-900 mb-2">Детекция аномалий</h4>
          <p class="text-sm text-neutral-600">Contamination: <strong>{settings.anomaly_detection?.contamination}</strong></p>
          <p class="text-sm text-neutral-600">Spike threshold: <strong>{settings.anomaly_detection?.spike_threshold}</strong></p>
          <p class="text-sm text-neutral-600">Dip threshold: <strong>{settings.anomaly_detection?.dip_threshold}</strong></p>
        </div>
        
        <div class="border border-neutral-200 rounded p-3">
          <h4 class="font-medium text-neutral-900 mb-2">Дрейф</h4>
          <p class="text-sm text-neutral-600">Min duration: <strong>{settings.anomaly_detection?.drift_min_duration}</strong></p>
          <p class="text-sm text-neutral-600">R² threshold: <strong>{settings.anomaly_detection?.drift_min_r_squared}</strong></p>
        </div>
      </div>
    </div>
  {:else}
    <div class="bg-yellow-50 border border-yellow-200 rounded p-4">
      <p class="text-yellow-800">⚠️ Неожиданное состояние: loading={loading}, error={error}, settings={settings}</p>
    </div>
  {/if}
</div>
'''

panel_path.write_text(minimal_content, encoding='utf-8', newline='\n')

print('✅ Создан минимальный тестовый компонент')
print()
print('Что он делает:')
print('  1. Показывает заголовок "🔧 Deep Data Analysis — ТЕСТОВЫЙ КОМПОНЕНТ"')
print('  2. Пытается загрузить настройки из API')
print('  3. Показывает одно из 4 состояний:')
print('     • loading — спиннер')
print('     • error — красная ошибка')
print('     • settings — зелёный успех + JSON настроек')
print('     • else — жёлтое предупреждение (неожиданное состояние)')
print()
print('В консоли браузера (F12) будут логи:')
print('  • "DDAConfigPanel: загружаю настройки..."')
print('  • "DDAConfigPanel: настройки загружены" или "ошибка загрузки"')
print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Vite автоматически перезагрузит страницу')
print('2. Открой: Настройки → вкладка DDA')
print('3. Что ты должен увидеть:')
print('   • Заголовок "🔧 Deep Data Analysis — ТЕСТОВЫЙ КОМПОНЕНТ"')
print('   • Одно из 4 состояний (loading/error/settings/else)')
print('4. Открой DevTools (F12) → Console:')
print('   • Должны быть логи "DDAConfigPanel: ..."')
print()
print('Если видишь:')
print('  ✅ Заголовок + состояние — компонент работает, проблема была в старом коде')
print('  ❌ Пустая вкладка — компонент не рендерится (проблема с импортом)')
print('  ❌ Ошибка загрузки — API не отвечает (проблема с backend)')