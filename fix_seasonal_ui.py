#!/usr/bin/env python3
"""
fix_seasonal_ui.py — 1) Chart.js с кнопками + 2) расширенный formatPeriod
"""
from pathlib import Path

print('=' * 80)
print('ФИКС: Chart.js для паттерна + расширенный formatPeriod')
print('=' * 80)
print()

results_path = Path('frontend/src/components/DeepAnalysisResults.svelte')
content = results_path.read_text(encoding='utf-8')

# ============================================================================
# 1. РАСШИРЯЕМ formatPeriod
# ============================================================================
print('【1】Расширяем formatPeriod для покрытия всех периодов')
print('-' * 80)

old_format_period = '''  function formatPeriod(period: number): string {
    if (period >= 270 && period <= 300) return '~24ч'
    if (period >= 560 && period <= 600) return '~12ч'
    if (period >= 1950 && period <= 2100) return '~7 дней'
    if (period >= 1400 && period <= 1500) return '~5 дней'
    if (period >= 1100 && period <= 1200) return '~4 дня'
    if (period >= 850 && period <= 900) return '~3 дня'
    if (period >= 570 && period <= 580) return '~2 дня'
    return `${period} точек`
  }'''

new_format_period = '''  function formatPeriod(period: number): string {
    // 5-мин sampling rate: 12 точек/час, 288/день, 2016/неделя
    const pointsPerDay = 288
    const days = period / pointsPerDay
    const hours = period / 12
    
    // Точные суточные/недельные периоды
    if (period >= 270 && period <= 310) return '~24ч (сутки)'
    if (period >= 135 && period <= 150) return '~12ч'
    if (period >= 560 && period <= 590) return '~2 дня'
    if (period >= 850 && period <= 880) return '~3 дня'
    if (period >= 1140 && period <= 1170) return '~4 дня'
    if (period >= 1420 && period <= 1460) return '~5 дней'
    if (period >= 1710 && period <= 1750) return '~6 дней'
    if (period >= 2000 && period <= 2040) return '~7 дней (неделя)'
    if (period >= 2860 && period <= 2900) return '~10 дней'
    if (period >= 4300 && period <= 4350) return '~15 дней'
    if (period >= 5740 && period <= 5780) return '~20 дней'
    if (period >= 8620 && period <= 8660) return '~30 дней (месяц)'
    
    // Округляем до дней/часов
    if (days >= 1) return `~${days.toFixed(1)} дней`
    if (hours >= 1) return `~${hours.toFixed(1)}ч`
    return `${period} точек`
  }'''

if old_format_period in content:
    content = content.replace(old_format_period, new_format_period)
    print('✅ formatPeriod расширен (покрывает все периоды: 24ч, 2д, 3д, 4д, 5д, 6д, 7д, ...)')
else:
    print('⚠️  formatPeriod не найден в ожидаемом виде')

# ============================================================================
# 2. ДОБАВЛЯЕМ Chart.js ID и функции для паттерна
# ============================================================================
print()
print('【2】Добавляем Chart.js инфраструктуру для паттерна')
print('-' * 80)

# Добавляем patternChartInstance и patternChartId
old_chart_ids = '''  const tsChartId = `dda-ts-${Math.random().toString(36).slice(2, 9)}`
  const scatterChartId = `dda-scatter-${Math.random().toString(36).slice(2, 9)}`'''

new_chart_ids = '''  const tsChartId = `dda-ts-${Math.random().toString(36).slice(2, 9)}`
  const scatterChartId = `dda-scatter-${Math.random().toString(36).slice(2, 9)}`
  const patternChartId = `dda-pattern-${Math.random().toString(36).slice(2, 9)}`
  let patternChartInstance: ChartJS | null = $state(null)'''

if old_chart_ids in content:
    content = content.replace(old_chart_ids, new_chart_ids)
    print('✅ Добавлен patternChartId и patternChartInstance')

# Добавляем функции для pattern chart (после zoomOutTs)
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
      }
    } catch (e) {
      console.warn('Zoom out failed:', e)
    }
  }

  // === Pattern chart controls ===
  function zoomInPattern() {
    try {
      if (patternChartInstance && typeof patternChartInstance.zoom === 'function') {
        patternChartInstance.zoom(1.2)
      }
    } catch (e) { console.warn('Pattern zoom in failed:', e) }
  }
  function zoomOutPattern() {
    try {
      if (patternChartInstance && typeof patternChartInstance.zoom === 'function') {
        patternChartInstance.zoom(0.8)
      }
    } catch (e) { console.warn('Pattern zoom out failed:', e) }
  }
  function resetZoomPattern() {
    try {
      if (patternChartInstance && typeof patternChartInstance.resetZoom === 'function') {
        patternChartInstance.resetZoom()
      }
    } catch (e) { console.warn('Pattern reset zoom failed:', e) }
  }

  function openPatternModal(pattern: number[], title: string) {
    const labels = pattern.map((_: any, i: number) => i)
    modalChartType = 'line'
    modalTitle = title
    modalData = {
      labels,
      datasets: [{
        label: title,
        data: pattern,
        borderColor: 'rgb(168, 85, 247)',
        backgroundColor: 'rgba(168, 85, 247, 0.1)',
        borderWidth: 2,
        pointRadius: 0,
        pointHoverRadius: 4,
        tension: 0.2,
        fill: true,
      }]
    }
    modalOptions = timeSeriesOptions
    modalOpen = true
  }'''

if old_zoom_out in content:
    content = content.replace(old_zoom_out, new_zoom_out)
    print('✅ Добавлены функции управления pattern chart')

# ============================================================================
# 3. ЗАМЕНЯЕМ SVG ПАТТЕРН НА CHART.JS (SINGLE-TAG)
# ============================================================================
print()
print('【3】Заменяем SVG паттерн на Chart.js (single-tag)')
print('-' * 80)

# Ищем начало single-tag pattern блока
single_pattern_start = content.find('{#if analysisResult.seasonality.pattern?.pattern?.length > 0}\n          {@const pattern = analysisResult.seasonality.pattern.pattern}\n          {@const stats = getPatternStats(pattern)}')

if single_pattern_start == -1:
    # Альтернативный поиск
    single_pattern_start = content.find('{#if analysisResult.seasonality.pattern?.pattern?.length > 0}')
    # Ищем тот, который в single-tag (первый)
    single_seasonal_pos = content.find('<!-- Сезонный анализ -->')
    if single_seasonal_pos != -1:
        single_pattern_start = content.find('{#if analysisResult.seasonality.pattern?.pattern?.length > 0}', single_seasonal_pos)

if single_pattern_start != -1:
    # Ищем конец {/if} этого блока
    search_region = content[single_pattern_start:]
    brace_count = 0
    pattern_end = None
    
    for i in range(len(search_region) - 3):
        if search_region[i:i+3] == '{#i':
            brace_count += 1
        elif search_region[i:i+4] == '{/if':
            brace_count -= 1
            if brace_count == 0:
                pattern_end = single_pattern_start + i + 4
                break
    
    if pattern_end:
        # Новый Chart.js блок для single-tag
        new_pattern_block = '''{#if analysisResult.seasonality.pattern?.pattern?.length > 0}
          {@const pattern = analysisResult.seasonality.pattern.pattern}
          {@const stats = getPatternStats(pattern)}
          {@const patternData = {
            labels: pattern.map((_: any, i: number) => i),
            datasets: [{
              label: 'Типичный паттерн',
              data: pattern,
              borderColor: 'rgb(168, 85, 247)',
              backgroundColor: 'rgba(168, 85, 247, 0.1)',
              borderWidth: 2,
              pointRadius: pattern.length > 100 ? 0 : 2,
              pointHoverRadius: 5,
              tension: 0.2,
              fill: true,
            }]
          }}
          <div class="mb-3">
            <div class="flex items-center justify-between mb-2">
              <div class="text-xs text-neutral-600 dark:text-neutral-400">
                Типичный паттерн (период {analysisResult.seasonality.periods.detected_periods[0].period} точек, {formatPeriod(analysisResult.seasonality.periods.detected_periods[0].period)})
              </div>
              <div class="flex items-center gap-1">
                <button type="button" onclick={zoomInPattern} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Приблизить"><ZoomIn size={14} class="text-neutral-600 dark:text-neutral-400" /></button>
                <button type="button" onclick={zoomOutPattern} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Отдалить"><ZoomOut size={14} class="text-neutral-600 dark:text-neutral-400" /></button>
                <button type="button" onclick={resetZoomPattern} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Сбросить"><RotateCcw size={14} class="text-neutral-600 dark:text-neutral-400" /></button>
                <button type="button" onclick={() => downloadPNG(patternChartInstance, 'pattern')} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Скачать PNG"><Download size={14} class="text-neutral-600 dark:text-neutral-400" /></button>
                <button type="button" onclick={() => openPatternModal(pattern, 'Типичный паттерн')} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Полноэкранный режим"><Maximize2 size={14} class="text-neutral-600 dark:text-neutral-400" /></button>
              </div>
            </div>
            <div class="p-2 bg-neutral-50 dark:bg-neutral-800 rounded border border-neutral-200 dark:border-neutral-700">
              <div class="text-xs text-neutral-600 dark:text-neutral-400 mb-1">
                Мин: {stats.min.toFixed(1)} | Макс: {stats.max.toFixed(1)} | Размах: {stats.range.toFixed(1)}
              </div>
              <div id={patternChartId} class="h-40 bg-white dark:bg-neutral-900 rounded">
                <Line data={patternData} options={{...timeSeriesOptions, plugins: {...timeSeriesOptions.plugins, legend: {display: false}}}} key={`pattern-single-${analysisResult?.analysis_id || 'default'}`} />
              </div>
            </div>
          </div>
          {/if}'''
        
        content = content[:single_pattern_start] + new_pattern_block + content[pattern_end:]
        print('✅ Single-tag: SVG заменён на Chart.js с кнопками')
    else:
        print('⚠️  Не найден конец single-tag pattern блока')
else:
    print('⚠️  Single-tag pattern блок не найден')

# ============================================================================
# 4. ЗАМЕНЯЕМ SVG ПАТТЕРН НА CHART.JS (MULTI-TAG)
# ============================================================================
print()
print('【4】Заменяем SVG паттерн на Chart.js (multi-tag)')
print('-' * 80)

# Ищем multi-tag pattern блок (внутри tagSeasonality)
multi_pattern_start = content.find('{#if tagSeasonality.pattern?.pattern?.length > 0}\n              {@const pattern = tagSeasonality.pattern.pattern}\n              {@const stats = getPatternStats(pattern)}')

if multi_pattern_start == -1:
    multi_seasonal_pos = content.find('<!-- Сезонный анализ (multi-tag) -->')
    if multi_seasonal_pos != -1:
        multi_pattern_start = content.find('{#if tagSeasonality.pattern?.pattern?.length > 0}', multi_seasonal_pos)

if multi_pattern_start != -1:
    search_region = content[multi_pattern_start:]
    brace_count = 0
    pattern_end = None
    
    for i in range(len(search_region) - 3):
        if search_region[i:i+3] == '{#i':
            brace_count += 1
        elif search_region[i:i+4] == '{/if':
            brace_count -= 1
            if brace_count == 0:
                pattern_end = multi_pattern_start + i + 4
                break
    
    if pattern_end:
        new_multi_pattern = '''{#if tagSeasonality.pattern?.pattern?.length > 0}
              {@const pattern = tagSeasonality.pattern.pattern}
              {@const stats = getPatternStats(pattern)}
              {@const patternData = {
                labels: pattern.map((_: any, i: number) => i),
                datasets: [{
                  label: tagName,
                  data: pattern,
                  borderColor: 'rgb(168, 85, 247)',
                  backgroundColor: 'rgba(168, 85, 247, 0.1)',
                  borderWidth: 2,
                  pointRadius: pattern.length > 100 ? 0 : 2,
                  pointHoverRadius: 5,
                  tension: 0.2,
                  fill: true,
                }]
              }}
              <div class="mb-3">
                <div class="flex items-center justify-between mb-2">
                  <div class="text-xs text-neutral-600 dark:text-neutral-400">
                    Типичный паттерн (период {tagSeasonality.periods.detected_periods[0].period} точек, {formatPeriod(tagSeasonality.periods.detected_periods[0].period)})
                  </div>
                  <div class="flex items-center gap-1">
                    <button type="button" onclick={zoomInPattern} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Приблизить"><ZoomIn size={14} class="text-neutral-600 dark:text-neutral-400" /></button>
                    <button type="button" onclick={zoomOutPattern} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Отдалить"><ZoomOut size={14} class="text-neutral-600 dark:text-neutral-400" /></button>
                    <button type="button" onclick={resetZoomPattern} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Сбросить"><RotateCcw size={14} class="text-neutral-600 dark:text-neutral-400" /></button>
                    <button type="button" onclick={() => downloadPNG(patternChartInstance, `pattern_${tagName}`)} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Скачать PNG"><Download size={14} class="text-neutral-600 dark:text-neutral-400" /></button>
                    <button type="button" onclick={() => openPatternModal(pattern, `Паттерн: ${tagName}`)} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Полноэкранный режим"><Maximize2 size={14} class="text-neutral-600 dark:text-neutral-400" /></button>
                  </div>
                </div>
                <div class="p-2 bg-white dark:bg-neutral-900 rounded border border-neutral-200 dark:border-neutral-700">
                  <div class="text-xs text-neutral-600 dark:text-neutral-400 mb-1">
                    Мин: {stats.min.toFixed(1)} | Макс: {stats.max.toFixed(1)} | Размах: {stats.range.toFixed(1)}
                  </div>
                  <div id={patternChartId} class="h-40 bg-white dark:bg-neutral-900 rounded">
                    <Line data={patternData} options={{...timeSeriesOptions, plugins: {...timeSeriesOptions.plugins, legend: {display: false}}}} key={`pattern-multi-${tagName}`} />
                  </div>
                </div>
              </div>
              {/if}'''
        
        content = content[:multi_pattern_start] + new_multi_pattern + content[pattern_end:]
        print('✅ Multi-tag: SVG заменён на Chart.js с кнопками')
    else:
        print('⚠️  Не найден конец multi-tag pattern блока')
else:
    print('⚠️  Multi-tag pattern блок не найден')

# ============================================================================
# 5. СОХРАНЯЕМ ФАЙЛ
# ============================================================================
print()
print('【5】Сохраняем файл')
print('-' * 80)
results_path.write_text(content, encoding='utf-8', newline='\n')
print('✅ Файл сохранён')

print()
print('=' * 80)
print('ЧТО СДЕЛАНО:')
print('=' * 80)
print()
print('1. CHART.JS ДЛЯ ПАТТЕРНА (вместо SVG):')
print('   • Используется тот же Line компонент что и для графика аномалий')
print('   • Автоматически работает: zoom (колесо/shift+drag), pan (drag)')
print('   • Hover → tooltip "Фаза X: Y"')
print('   • Добавлены кнопки: (+) (-) (сброс) (PNG) (fullscreen)')
print()
print('2. РАСШИРЕННЫЙ formatPeriod:')
print('   • ~24ч (сутки) — 270-310 точек')
print('   • ~12ч — 135-150')
print('   • ~2 дня — 560-590')
print('   • ~3 дня — 850-880')
print('   • ~4 дня — 1140-1170')
print('   • ~5 дней — 1420-1460')
print('   • ~6 дней — 1710-1750   ← ИСПРАВЛЕНО (было 1727 точек)')
print('   • ~7 дней (неделя) — 2000-2040')
print('   • ~10/15/20/30 дней')
print('   • Fallback: автоматический расчёт дней/часов')
print()
print('3. В КАРТОЧКАХ ПЕРИОДОВ:')
print('   • Было: "1727 точек (1727 точек)" ← ДУБЛЬ')
print('   • Стало: "1727 точек (~6 дней)"')
print()
print('=' * 80)