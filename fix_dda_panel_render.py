#!/usr/bin/env python3
"""
fix_dda_panel_render.py — добавляем полный рендеринг настроек в DDAConfigPanel
"""
from pathlib import Path

print('=' * 80)
print('ФИКС: Полный рендеринг настроек в DDAConfigPanel')
print('=' * 80)
print()

panel_path = Path('frontend/src/components/config/DDAConfigPanel.svelte')

# Читаем текущий контент
content = panel_path.read_text(encoding='utf-8')

# Проверяем есть ли блок рендеринга настроек
if '{#if settings}' in content:
    print('ℹ️  Блок {#if settings} уже есть в компоненте')
    print('   Возможно проблема в другом месте.')
    print()
    print('Проверь:')
    print('  • Console (F12) на JavaScript ошибки')
    print('  • Network tab — что возвращает API')
else:
    print('❌ Блок {#if settings} НЕ НАЙДЕН!')
    print('   Добавляю полный рендеринг настроек...')
    print()
    
    # Находим где заканчивается loading блок
    loading_end = content.find('{/if}')
    if loading_end == -1:
        print('❌ Не удалось найти конец loading блока')
        exit(1)
    
    # Вставляем блок рендеринга настроек
    settings_render = '''
  {:else if settings}
    <div class="p-6 space-y-6">
      <!-- Секция: Детекция аномалий -->
      <div class="border border-neutral-200 rounded-lg p-4">
        <h3 class="text-lg font-semibold text-neutral-900 mb-4 flex items-center gap-2">
          <Activity size={18} class="text-blue-600" />
          Детекция аномалий
        </h3>
        
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-neutral-700 mb-1">Contamination (доля аномалий)</label>
            <input
              type="number"
              bind:value={settings.anomaly_detection.contamination}
              step="0.01"
              min="0.01"
              max="0.5"
              class="w-full px-3 py-2 border border-neutral-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <p class="text-xs text-neutral-500 mt-1">Ожидаемая доля аномалий (0.01-0.5)</p>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-neutral-700 mb-1">Количество деревьев</label>
            <input
              type="number"
              bind:value={settings.anomaly_detection.n_estimators}
              step="10"
              min="10"
              max="500"
              class="w-full px-3 py-2 border border-neutral-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <p class="text-xs text-neutral-500 mt-1">Количество деревьев в Isolation Forest</p>
          </div>
        </div>
      </div>

      <!-- Секция: Классификация -->
      <div class="border border-neutral-200 rounded-lg p-4">
        <h3 class="text-lg font-semibold text-neutral-900 mb-4 flex items-center gap-2">
          <TrendingUp size={18} class="text-blue-600" />
          Классификация аномалий
        </h3>
        
        <div class="grid grid-cols-3 gap-4">
          <div>
            <label class="block text-sm font-medium text-neutral-700 mb-1">Порог пика (spike)</label>
            <input
              type="number"
              bind:value={settings.anomaly_detection.spike_threshold}
              step="0.1"
              min="1.0"
              max="5.0"
              class="w-full px-3 py-2 border border-neutral-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <p class="text-xs text-neutral-500 mt-1">Z-score для пика</p>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-neutral-700 mb-1">Порог провала (dip)</label>
            <input
              type="number"
              bind:value={settings.anomaly_detection.dip_threshold}
              step="0.1"
              min="1.0"
              max="5.0"
              class="w-full px-3 py-2 border border-neutral-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <p class="text-xs text-neutral-500 mt-1">Z-score для провала</p>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-neutral-700 mb-1">Порог плато</label>
            <input
              type="number"
              bind:value={settings.anomaly_detection.plateau_tolerance}
              step="0.005"
              min="0.001"
              max="0.1"
              class="w-full px-3 py-2 border border-neutral-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <p class="text-xs text-neutral-500 mt-1">Допуск для одинаковых значений</p>
          </div>
        </div>
      </div>

      <!-- Секция: Дрейф -->
      <div class="border border-neutral-200 rounded-lg p-4">
        <h3 class="text-lg font-semibold text-neutral-900 mb-4 flex items-center gap-2">
          <GitBranch size={18} class="text-blue-600" />
          Детекция дрейфа
        </h3>
        
        <div class="grid grid-cols-3 gap-4">
          <div>
            <label class="block text-sm font-medium text-neutral-700 mb-1">Мин. длительность</label>
            <input
              type="number"
              bind:value={settings.anomaly_detection.drift_min_duration}
              step="1"
              min="2"
              max="20"
              class="w-full px-3 py-2 border border-neutral-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <p class="text-xs text-neutral-500 mt-1">Мин. точек для дрейфа</p>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-neutral-700 mb-1">R² тренда</label>
            <input
              type="number"
              bind:value={settings.anomaly_detection.drift_min_r_squared}
              step="0.05"
              min="0.1"
              max="0.95"
              class="w-full px-3 py-2 border border-neutral-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <p class="text-xs text-neutral-500 mt-1">Качество линейного тренда</p>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-neutral-700 mb-1">Мин. изменение</label>
            <input
              type="number"
              bind:value={settings.anomaly_detection.drift_min_relative_change}
              step="0.01"
              min="0.01"
              max="0.5"
              class="w-full px-3 py-2 border border-neutral-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <p class="text-xs text-neutral-500 mt-1">Относительное изменение (%)</p>
          </div>
        </div>
      </div>

      <!-- Секция: Локальная статистика -->
      <div class="border border-neutral-200 rounded-lg p-4">
        <h3 class="text-lg font-semibold text-neutral-900 mb-4 flex items-center gap-2">
          <Eye size={18} class="text-blue-600" />
          Локальная статистика
        </h3>
        
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-neutral-700 mb-1">Размер окна</label>
            <input
              type="number"
              bind:value={settings.anomaly_detection.local_window}
              step="2"
              min="5"
              max="100"
              class="w-full px-3 py-2 border border-neutral-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <p class="text-xs text-neutral-500 mt-1">Точек для локального mean/std</p>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-neutral-700 mb-1">Порог значительного провала</label>
            <input
              type="number"
              bind:value={settings.anomaly_detection.significant_dip_ratio}
              step="0.05"
              min="0.1"
              max="0.9"
              class="w-full px-3 py-2 border border-neutral-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <p class="text-xs text-neutral-500 mt-1">Доля падения от локального mean</p>
          </div>
        </div>
      </div>

      <!-- Секция: Корреляции -->
      <div class="border border-neutral-200 rounded-lg p-4">
        <h3 class="text-lg font-semibold text-neutral-900 mb-4 flex items-center gap-2">
          <GitBranch size={18} class="text-blue-600" />
          Корреляции
        </h3>
        
        <div class="grid grid-cols-3 gap-4">
          <div>
            <label class="block text-sm font-medium text-neutral-700 mb-1">Частота ресемплинга</label>
            <input
              type="text"
              bind:value={settings.correlations.resample_freq}
              class="w-full px-3 py-2 border border-neutral-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <p class="text-xs text-neutral-500 mt-1">Например: 5min, 1h</p>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-neutral-700 mb-1">Порог Пирсона</label>
            <input
              type="number"
              bind:value={settings.correlations.pearson_threshold}
              step="0.05"
              min="0.1"
              max="0.9"
              class="w-full px-3 py-2 border border-neutral-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <p class="text-xs text-neutral-500 mt-1">Минимальный |r| для значимости</p>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-neutral-700 mb-1">Макс. лаг</label>
            <input
              type="number"
              bind:value={settings.correlations.max_lag}
              step="10"
              min="10"
              max="500"
              class="w-full px-3 py-2 border border-neutral-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <p class="text-xs text-neutral-500 mt-1">Максимальный лаг для cross-correlation</p>
          </div>
        </div>
      </div>

      <!-- Секция: Визуализация -->
      <div class="border border-neutral-200 rounded-lg p-4">
        <h3 class="text-lg font-semibold text-neutral-900 mb-4 flex items-center gap-2">
          <Eye size={18} class="text-blue-600" />
          Визуализация
        </h3>
        
        <div class="grid grid-cols-3 gap-4">
          <div>
            <label class="block text-sm font-medium text-neutral-700 mb-1">Макс. точек</label>
            <input
              type="number"
              bind:value={settings.visualization.max_points}
              step="100"
              min="500"
              max="5000"
              class="w-full px-3 py-2 border border-neutral-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <p class="text-xs text-neutral-500 mt-1">Downsampling для графиков</p>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-neutral-700 mb-1">Размер точек аномалий</label>
            <input
              type="number"
              bind:value={settings.visualization.anomaly_point_radius}
              step="1"
              min="2"
              max="15"
              class="w-full px-3 py-2 border border-neutral-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <p class="text-xs text-neutral-500 mt-1">Радиус scatter points</p>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-neutral-700 mb-1">Толщина линии дрейфа</label>
            <input
              type="number"
              bind:value={settings.visualization.drift_line_width}
              step="1"
              min="1"
              max="5"
              class="w-full px-3 py-2 border border-neutral-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <p class="text-xs text-neutral-500 mt-1">Ширина пунктирной линии</p>
          </div>
        </div>
      </div>

      <!-- Секция: Цвета -->
      <div class="border border-neutral-200 rounded-lg p-4">
        <h3 class="text-lg font-semibold text-neutral-900 mb-4 flex items-center gap-2">
          <Palette size={18} class="text-blue-600" />
          Цвета аномалий
        </h3>
        
        <div class="grid grid-cols-4 gap-4">
          <div>
            <label class="block text-sm font-medium text-neutral-700 mb-1">Пики (Spike)</label>
            <input
              type="color"
              bind:value={settings.colors.spike}
              class="w-full h-10 border border-neutral-300 rounded cursor-pointer"
            />
            <p class="text-xs text-neutral-500 mt-1 font-mono">{settings.colors.spike}</p>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-neutral-700 mb-1">Провалы (Dip)</label>
            <input
              type="color"
              bind:value={settings.colors.dip}
              class="w-full h-10 border border-neutral-300 rounded cursor-pointer"
            />
            <p class="text-xs text-neutral-500 mt-1 font-mono">{settings.colors.dip}</p>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-neutral-700 mb-1">Дрейфы (Drift)</label>
            <input
              type="color"
              bind:value={settings.colors.drift}
              class="w-full h-10 border border-neutral-300 rounded cursor-pointer"
            />
            <p class="text-xs text-neutral-500 mt-1 font-mono">{settings.colors.drift}</p>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-neutral-700 mb-1">Шум (Noise)</label>
            <input
              type="color"
              bind:value={settings.colors.noise}
              class="w-full h-10 border border-neutral-300 rounded cursor-pointer"
            />
            <p class="text-xs text-neutral-500 mt-1 font-mono">{settings.colors.noise}</p>
          </div>
        </div>
      </div>
    </div>
'''
    
    # Вставляем после loading блока
    insert_pos = loading_end + len('{/if}')
    content = content[:insert_pos] + settings_render + content[insert_pos:]
    
    panel_path.write_text(content, encoding='utf-8', newline='\n')
    print('✅ Добавлен полный рендеринг настроек')
    print('   • 6 секций: Детекция / Классификация / Дрейф / Локальная статистика / Корреляции / Визуализация')
    print('   • 16 параметров с описаниями')
    print('   • Color picker для 4 цветов')

print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Открой фронтенд → Настройки → вкладка DDA')
print('2. Должны появиться 6 секций с настройками')
print('3. Измени любой параметр (например, contamination)')
print('4. Нажми "Сохранить" — должно появиться зелёное сообщение')
print('5. Запусти анализ и проверь что новые настройки применяются')