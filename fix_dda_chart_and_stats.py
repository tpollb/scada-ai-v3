from pathlib import Path

print('=== fix_dda_chart_and_stats.py ===')
print()

panel_path = Path('frontend/src/components/DeepAnalysisPanel.svelte')
content = panel_path.read_text(encoding='utf-8')
original = content

changes = []

# 1. Заменяем $derived.by на простой $derived + $effect для Chart.js
old_chart_data = '''  // Chart.js конфигурация
  let chartData = $derived.by(() => {
    if (!analysisResult?.visualizations?.time_series) {
      return { labels: [], datasets: [] }
    }

    const spec = analysisResult.visualizations.time_series
    return spec.data
  })'''

new_chart_data = '''  // Chart.js данные
  let chartData = $derived(
    analysisResult?.visualizations?.time_series?.data || { labels: [], datasets: [] }
  )

  // Отладка: логируем что приходит в chartData
  $effect(() => {
    if (chartData.labels.length > 0) {
      console.log('📊 Chart data received:', {
        labels_count: chartData.labels.length,
        datasets_count: chartData.datasets?.length,
        first_label: chartData.labels[0],
        first_dataset: chartData.datasets?.[0]
      })
    }
  })'''

if old_chart_data in content:
    content = content.replace(old_chart_data, new_chart_data)
    changes.append('✓ Заменён $derived.by на $derived + $effect с логированием')

# 2. Добавляем ключ для перерисовки компонента Line (заставляет Chart.js пересоздаваться)
old_line_component = '''      {#if chartData.labels.length > 0}
        <Line data={chartData} options={chartOptions} />'''

new_line_component = '''      {#if chartData.labels.length > 0}
        <Line 
          data={chartData} 
          options={chartOptions}
          key={analysisResult?.analysis_id || 'default'}
        />'''

if old_line_component in content:
    content = content.replace(old_line_component, new_line_component)
    changes.append('✓ Добавлен key для перерисовки Line компонента')

# 3. Улучшаем проверку статистики - показываем только если есть валидные данные
old_stats_block = '''      <!-- Statistics -->
      {#if analysisResult?.statistics}
      <div class="mb-4">
        <h3 class="text-sm font-semibold text-neutral-900 dark:text-neutral-100 mb-2 flex items-center gap-1">
          <TrendingUp size={14} />
          Статистика
        </h3>
        <div class="grid grid-cols-2 gap-2 text-xs">'''

new_stats_block = '''      <!-- Statistics -->
      {#if analysisResult?.statistics && analysisResult.statistics.count > 0}
      <div class="mb-4">
        <h3 class="text-sm font-semibold text-neutral-900 dark:text-neutral-100 mb-2 flex items-center gap-1">
          <TrendingUp size={14} />
          Статистика
        </h3>
        <div class="grid grid-cols-2 gap-2 text-xs">'''

if old_stats_block in content:
    content = content.replace(old_stats_block, new_stats_block)
    changes.append('✓ Улучшена проверка: statistics && count > 0')

# 4. Добавляем отладку в runAnalysis
old_run_analysis_try = '''    try {
      const response = await api.post('api/v1/deep_analysis/run', {
        json: {
          tags: [selectedTag],
          period: period,
          anomalies: true,
          correlations: false,
          seasonality: false,
          compare_periods: false,
        }
      })

      analysisResult = response'''

new_run_analysis_try = '''    try {
      const response = await api.post('api/v1/deep_analysis/run', {
        json: {
          tags: [selectedTag],
          period: period,
          anomalies: true,
          correlations: false,
          seasonality: false,
          compare_periods: false,
        }
      })

      console.log('🔍 Analysis response:', response)
      analysisResult = response
      
      console.log('📈 Visualization data:', {
        has_visualizations: !!response.visualizations,
        has_time_series: !!response.visualizations?.time_series,
        has_data: !!response.visualizations?.time_series?.data,
        labels_count: response.visualizations?.time_series?.data?.labels?.length || 0
      })'''

if old_run_analysis_try in content:
    content = content.replace(old_run_analysis_try, new_run_analysis_try)
    changes.append('✓ Добавлено логирование ответа API')

if content != original:
    panel_path.write_text(content, encoding='utf-8', newline='\n')
    print('✓ DeepAnalysisPanel.svelte обновлён')
else:
    print('ℹ Файл не изменился')

print()
print('=' * 60)
print('ИСПРАВЛЕНИЯ:')
print('=' * 60)
for c in changes:
    print(f'  {c}')

print()
print('=' * 60)
print('СЛЕДУЮЩИЙ ШАГ:')
print('=' * 60)
print()
print('Frontend перезагрузится автоматически (Vite HMR).')
print()
print('Проверка:')
print('  1. Открой фронтенд')
print('  2. Открой DevTools → Console (F12)')
print('  3. Клик Activity → выбери R203-Temperature → "Запустить анализ"')
print('  4. Смотри в консоль браузера — должны появиться логи:')
print('     🔍 Analysis response: {...}')
print('     📈 Visualization data: {...}')
print('     📊 Chart data received: {...}')
print()
print('Скинь вывод консоли — я увижу что именно не так с данными!')