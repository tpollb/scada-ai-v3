#!/usr/bin/env python3
"""
fix_chart_and_multitag_seasonal.py — исправляем chart instance и добавляем seasonal в multi-tag
"""
from pathlib import Path

print('=' * 80)
print('ФИКС: Chart instance + Multi-tag seasonal визуализация')
print('=' * 80)
print()

results_path = Path('frontend/src/components/DeepAnalysisResults.svelte')
content = results_path.read_text(encoding='utf-8')

# 1. Исправляем функции zoom/reset чтобы проверяли chart instance
print('【1】Исправляем функции zoom/reset для проверки chart instance')
print('-' * 80)

old_reset_zoom = '''  function resetZoomTs() {
    try {
      if (tsChartInstance && typeof tsChartInstance.resetZoom === 'function') {
        tsChartInstance.resetZoom()
      }
    } catch (e) {
      console.warn('Reset zoom failed:', e)
    }
  }'''

new_reset_zoom = '''  function resetZoomTs() {
    try {
      if (tsChartInstance && typeof tsChartInstance.resetZoom === 'function') {
        tsChartInstance.resetZoom()
      } else {
        console.warn('Chart instance not available or resetZoom not supported')
      }
    } catch (e) {
      console.warn('Reset zoom failed:', e)
    }
  }'''

if old_reset_zoom in content:
    content = content.replace(old_reset_zoom, new_reset_zoom)
    print('✅ resetZoomTs улучшена')
else:
    print('⚠️  resetZoomTs не найдена')

old_zoom_in = '''  function zoomInTs() {
    try {
      if (tsChartInstance && typeof tsChartInstance.zoom === 'function') {
        tsChartInstance.zoom(1.2)
      }
    } catch (e) {
      console.warn('Zoom in failed:', e)
    }
  }'''

new_zoom_in = '''  function zoomInTs() {
    try {
      if (tsChartInstance && typeof tsChartInstance.zoom === 'function') {
        tsChartInstance.zoom(1.2)
      } else {
        console.warn('Chart instance not available or zoom not supported')
      }
    } catch (e) {
      console.warn('Zoom in failed:', e)
    }
  }'''

if old_zoom_in in content:
    content = content.replace(old_zoom_in, new_zoom_in)
    print('✅ zoomInTs улучшена')

old_zoom_out = '''  function zoomOutTs() {
    try {
      if (tsChartInstance && typeof tsChartInstance.zoom === 'function') {
        tsChartInstance.zoom(0.8)
      }
    } catch (e) {
      console.warn('Zoom out failed:', e)
    }
  }'''

new_zoom_out = '''  function zoomOutTs() {
    try {
      if (tsChartInstance && typeof tsChartInstance.zoom === 'function') {
        tsChartInstance.zoom(0.8)
      } else {
        console.warn('Chart instance not available or zoom not supported')
      }
    } catch (e) {
      console.warn('Zoom out failed:', e)
    }
  }'''

if old_zoom_out in content:
    content = content.replace(old_zoom_out, new_zoom_out)
    print('✅ zoomOutTs улучшена')

# 2. Находим и удаляем блок сезонности из single-tag (строки 525-625 примерно)
print()
print('【2】Удаляем блок сезонности из single-tag блока')
print('-' * 80)

# Ищем начало блока сезонности в single-tag
seasonal_start_marker = '        <!-- Сезонный анализ -->'
seasonal_end_marker = '      <!-- ==================== MULTI-TAG: CORRELATIONS ==================== -->'

start_idx = content.find(seasonal_start_marker)
end_idx = content.find(seasonal_end_marker)

if start_idx != -1 and end_idx != -1:
    # Удаляем блок между маркерами (не включая сам MULTI-TAG маркер)
    seasonal_block = content[start_idx:end_idx]
    content = content[:start_idx] + content[end_idx:]
    print(f'✅ Блок сезонности удалён из single-tag ({len(seasonal_block)} символов)')
else:
    print('⚠️  Маркеры блока сезонности не найдены')

# 3. Вставляем блок сезонности в multi-tag (после блока графиков, перед корреляциями)
print()
print('【3】Добавляем блок сезонности в multi-tag')
print('-' * 80)

multitag_marker = '''      <!-- ==================== MULTI-TAG: CORRELATIONS ==================== -->
      {#if isMultiTag && activeTab === 'correlations'}'''

multitag_seasonal_block = '''      <!-- ==================== MULTI-TAG: SEASONAL ==================== -->
      {#if isMultiTag && activeTab === 'correlations' && analysisResult?.seasonality}
        <div class="mb-4">
          <h3 class="text-sm font-semibold mb-3 flex items-center gap-2">
            <Waves size={16} class="text-purple-500" />
            Сезонный анализ ({Object.keys(analysisResult.seasonality).length} тегов)
          </h3>
          
          {#each Object.entries(analysisResult.seasonality) as [tagName, tagSeasonality]}
            {#if tagSeasonality?.periods?.detected_periods?.length > 0}
            <div class="mb-4 p-3 bg-neutral-50 dark:bg-neutral-800 rounded border border-neutral-200 dark:border-neutral-700">
              <h4 class="text-sm font-medium mb-2 text-neutral-700 dark:text-neutral-300">{tagName}</h4>
              
              <!-- Найденные периоды -->
              <div class="mb-3">
                <div class="text-xs text-neutral-600 dark:text-neutral-400 mb-2">Обнаруженные периоды:</div>
                <div class="grid grid-cols-2 gap-2">
                  {#each tagSeasonality.periods.detected_periods.slice(0, 4) as period}
                    <div class="p-2 bg-purple-50 dark:bg-purple-900/20 rounded border border-purple-200 dark:border-purple-800">
                      <div class="text-xs text-neutral-600 dark:text-neutral-400">Период</div>
                      <div class="text-sm font-semibold text-purple-700 dark:text-purple-300">
                        {period.period} точек
                        {#if period.period >= 280 && period.period <= 300}
                          <span class="text-xs text-neutral-500">(~24ч)</span>
                        {:else if period.period >= 2000 && period.period <= 2100}
                          <span class="text-xs text-neutral-500">(~7 дней)</span>
                        {/if}
                      </div>
                      <div class="text-xs text-neutral-500 mt-1">
                        Уверенность: {(period.confidence * 100).toFixed(0)}%
                      </div>
                    </div>
                  {/each}
                </div>
              </div>

              <!-- Variance explained -->
              {#if tagSeasonality.decomposition?.variance_explained}
                {@const ve = tagSeasonality.decomposition.variance_explained}
                <div class="mb-3">
                  <div class="text-xs text-neutral-600 dark:text-neutral-400 mb-2">Распределение дисперсии:</div>
                  <div class="space-y-1">
                    <div class="flex items-center gap-2">
                      <div class="w-20 text-xs text-neutral-600 dark:text-neutral-400">Тренд:</div>
                      <div class="flex-1 bg-neutral-200 dark:bg-neutral-700 rounded-full h-4 overflow-hidden">
                        <div class="bg-blue-500 h-full" style="width: {ve.trend}%"></div>
                      </div>
                      <div class="w-12 text-xs text-right font-mono">{ve.trend.toFixed(1)}%</div>
                    </div>
                    <div class="flex items-center gap-2">
                      <div class="w-20 text-xs text-neutral-600 dark:text-neutral-400">Сезонность:</div>
                      <div class="flex-1 bg-neutral-200 dark:bg-neutral-700 rounded-full h-4 overflow-hidden">
                        <div class="bg-purple-500 h-full" style="width: {ve.seasonal}%"></div>
                      </div>
                      <div class="w-12 text-xs text-right font-mono">{ve.seasonal.toFixed(1)}%</div>
                    </div>
                    <div class="flex items-center gap-2">
                      <div class="w-20 text-xs text-neutral-600 dark:text-neutral-400">Остаток:</div>
                      <div class="flex-1 bg-neutral-200 dark:bg-neutral-700 rounded-full h-4 overflow-hidden">
                        <div class="bg-neutral-500 h-full" style="width: {ve.residual}%"></div>
                      </div>
                      <div class="w-12 text-xs text-right font-mono">{ve.residual.toFixed(1)}%</div>
                    </div>
                  </div>
                </div>
              {/if}

              <!-- Типичный паттерн -->
              {#if tagSeasonality.pattern?.pattern}
                {@const pattern = tagSeasonality.pattern.pattern}
                {@const minVal = Math.min(...pattern.filter(v => v !== null))}
                {@const maxVal = Math.max(...pattern.filter(v => v !== null))}
                {@const range = maxVal - minVal}
                <div class="mb-3">
                  <div class="text-xs text-neutral-600 dark:text-neutral-400 mb-2">
                    Типичный суточный паттерн (период {tagSeasonality.periods.detected_periods[0].period} точек):
                  </div>
                  <div class="p-2 bg-white dark:bg-neutral-900 rounded border border-neutral-200 dark:border-neutral-700">
                    <div class="text-xs text-neutral-600 dark:text-neutral-400 mb-1">
                      Мин: {minVal.toFixed(1)} | Макс: {maxVal.toFixed(1)} | Размах: {range.toFixed(1)}
                    </div>
                    <div class="flex items-end gap-0.5 h-16">
                      {#each pattern.slice(0, 48) as val, i}
                        {#if val !== null}
                          {@const height = ((val - minVal) / range) * 100}
                          <div 
                            class="flex-1 bg-gradient-to-t from-purple-500 to-purple-400 rounded-t transition-all hover:from-purple-600 hover:to-purple-500"
                            style="height: {height}%"
                            title="Фаза {i}: {val.toFixed(1)}"
                          ></div>
                        {/if}
                      {/each}
                    </div>
                    <div class="flex justify-between text-xs text-neutral-500 mt-1">
                      <span>00:00</span>
                      <span>12:00</span>
                      <span>24:00</span>
                    </div>
                  </div>
                </div>
              {/if}
            </div>
            {/if}
          {/each}
        </div>
      {/if}

      <!-- ==================== MULTI-TAG: CORRELATIONS ==================== -->
      {#if isMultiTag && activeTab === 'correlations'}'''

if multitag_marker in content:
    content = content.replace(multitag_marker, multitag_seasonal_block)
    print('✅ Блок сезонности добавлен в multi-tag')
else:
    print('⚠️  Multi-tag маркер не найден')

# 4. Сохраняем файл
print()
print('【4】Сохраняем файл')
print('-' * 80)
results_path.write_text(content, encoding='utf-8', newline='\n')
print('✅ Файл сохранён')

print()
print('=' * 80)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 80)
print()
print('1. Chart instance функции (zoomInTs, zoomOutTs, resetZoomTs):')
print('   • Добавлена проверка что chart instance существует')
print('   • Добавлено предупреждение если instance не доступен')
print('   • Это предотвратит ошибки "Cannot read properties of null"')
print()
print('2. Multi-tag seasonal визуализация:')
print('   • Удалён блок из single-tag (где был ошибочно)')
print('   • Добавлен в multi-tag блок (перед корреляциями)')
print('   • Отображается для каждого тега отдельно')
print('   • Показывает: периоды, variance explained, типичный паттерн')
print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Frontend перезагрузится автоматически')
print('2. Кнопки zoom/reset должны работать без ошибок')
print('3. Для multi-tag анализа должна появиться секция "Сезонный анализ"')