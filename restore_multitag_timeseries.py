#!/usr/bin/env python3
"""
restore_multitag_timeseries.py — возвращаем график временных рядов для multi-tag
"""
from pathlib import Path

print('=' * 80)
print('ВОССТАНОВЛЕНИЕ: График временных рядов для multi-tag')
print('=' * 80)
print()

results_path = Path('frontend/src/components/DeepAnalysisResults.svelte')
content = results_path.read_text(encoding='utf-8')

# Находим маркер Scatter plot
print('【1】Ищем маркер Scatter plot')
print('-' * 80)

scatter_marker = '          <!-- 2. Scatter plot (интерактивный) -->'
scatter_pos = content.find(scatter_marker)

if scatter_pos == -1:
    print('❌ Маркер Scatter plot не найден')
    exit(1)

print(f'✅ Найден на позиции {scatter_pos}')

# Блок с графиком временных рядов для multi-tag (из оригинального файла)
timeseries_block = '''        <!-- 0. Time series с аномалиями (если есть) -->
        {#if analysisResult?.visualizations?.time_series?.data?.datasets?.length > 0}
        <div class="mb-4">
          <div class="flex items-center justify-between mb-2">
            <h3 class="text-sm font-semibold">
              Временные ряды ({analysisResult.tags.length} тегов) с аномалиями
            </h3>
            <div class="flex items-center gap-1">
              <button type="button" onclick={zoomInTs} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Приблизить"><ZoomIn size={14} class="text-neutral-600 dark:text-neutral-400" /></button>
              <button type="button" onclick={zoomOutTs} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Отдалить"><ZoomOut size={14} class="text-neutral-600 dark:text-neutral-400" /></button>
              <button type="button" onclick={resetZoomTs} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Сбросить"><RotateCcw size={14} class="text-neutral-600 dark:text-neutral-400" /></button>
              <button type="button" onclick={() => downloadPNG(tsChartInstance, 'multitag_timeseries')} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Скачать PNG"><Download size={14} class="text-neutral-600 dark:text-neutral-400" /></button>
              <button type="button" onclick={() => openChartModal('line', 'Временные ряды (мульти-тег)', timeSeriesData, timeSeriesOptions)} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Полноэкранный режим"><Maximize2 size={14} class="text-neutral-600 dark:text-neutral-400" /></button>
            </div>
          </div>
          <div class="text-xs text-neutral-500 dark:text-neutral-400 mb-2 flex items-center gap-1.5">
            <Lightbulb size={12} />
            <span>Колёсико — zoom · Shift+drag — область · Drag — прокрутка</span>
          </div>
          <div id={tsChartId} class="h-[300px] bg-white dark:bg-neutral-800 rounded border border-neutral-200 dark:border-neutral-700 p-3">
            <Line data={timeSeriesData} options={timeSeriesOptions} key={analysisResult?.analysis_id || 'multitag'} />
          </div>

          <!-- Сводка по типам аномалий -->
          {#if analysisResult?.anomalies?.type_counts}
            {@const tc = analysisResult.anomalies.type_counts}
            <div class="mt-3 space-y-2">
              <div class="text-[11px] text-neutral-600 dark:text-neutral-400 p-2 bg-neutral-50 dark:bg-neutral-800/50 rounded">
                💡 Каждый тип аномалии имеет свою причину. Кликните на тип чтобы увидеть детали.
              </div>

              {#if tc.get('spike', 0) > 0}
                <button
                  type="button"
                  onclick={() => expandedType = expandedType === 'spike' ? null : 'spike'}
                  class="w-full text-left p-2 bg-orange-50 dark:bg-orange-900/20 hover:bg-orange-100 dark:hover:bg-orange-900/30 rounded border border-orange-200 dark:border-orange-800 transition"
                >
                  <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2">
                      <Zap size={14} class="text-orange-500" />
                      <span class="text-sm font-medium text-orange-700 dark:text-orange-300">Пики (spike)</span>
                      <span class="text-xs px-1.5 py-0.5 bg-orange-200 dark:bg-orange-800 text-orange-800 dark:text-orange-200 rounded font-mono">{tc.get('spike', 0)}</span>
                    </div>
                    <ChevronDown size={14} class="text-orange-500 transition-transform {expandedType === 'spike' ? 'rotate-180' : ''}" />
                  </div>
                  {#if expandedType === 'spike'}
                    <div class="mt-2 text-xs text-orange-600 dark:text-orange-400">
                      <p class="mb-2"><strong>Причина:</strong> Резкие кратковременные скачки. Обычно вызваны сбоями датчиков, электрическими помехами или переходными процессами.</p>
                      <div class="max-h-32 overflow-y-auto space-y-1">
                        {#if analysisResult?.anomalies?.per_tag}
                          {#each Object.entries(analysisResult.anomalies.per_tag) as [tagName, tagData]}
                            {#if tagData.type_counts?.spike > 0}
                              <div class="p-1.5 bg-white dark:bg-neutral-900 rounded">
                                <div class="font-mono text-[10px] text-neutral-500 mb-1">{tagName} ({tagData.type_counts.spike})</div>
                                <div class="space-y-0.5">
                                  {#each tagData.anomaly_indices.filter(idx => tagData.anomaly_types[idx] === 'spike').slice(0, 5) as idx}
                                    <div class="flex justify-between text-[10px]">
                                      <span class="text-neutral-600 dark:text-neutral-400">{formatAnomalyDate(tagData.anomaly_timestamps[idx])}</span>
                                      <span class="font-mono text-orange-600 dark:text-orange-400">{formatNumber(tagData.anomaly_values[idx])}</span>
                                    </div>
                                  {/each}
                                </div>
                              </div>
                            {/if}
                          {/each}
                        {/if}
                      </div>
                    </div>
                  {/if}
                </button>
              {/if}

              {#if tc.get('dip', 0) > 0}
                <button
                  type="button"
                  onclick={() => expandedType = expandedType === 'dip' ? null : 'dip'}
                  class="w-full text-left p-2 bg-blue-50 dark:bg-blue-900/20 hover:bg-blue-100 dark:hover:bg-blue-900/30 rounded border border-blue-200 dark:border-blue-800 transition"
                >
                  <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2">
                      <ArrowDownCircle size={14} class="text-blue-500" />
                      <span class="text-sm font-medium text-blue-700 dark:text-blue-300">Провалы (dip)</span>
                      <span class="text-xs px-1.5 py-0.5 bg-blue-200 dark:bg-blue-800 text-blue-800 dark:text-blue-200 rounded font-mono">{tc.get('dip', 0)}</span>
                    </div>
                    <ChevronDown size={14} class="text-blue-500 transition-transform {expandedType === 'dip' ? 'rotate-180' : ''}" />
                  </div>
                  {#if expandedType === 'dip'}
                    <div class="mt-2 text-xs text-blue-600 dark:text-blue-400">
                      <p class="mb-2"><strong>Причина:</strong> Резкие кратковременные падения. Могут быть вызваны отключением оборудования, потерей сигнала или физическими процессами.</p>
                      <div class="max-h-32 overflow-y-auto space-y-1">
                        {#if analysisResult?.anomalies?.per_tag}
                          {#each Object.entries(analysisResult.anomalies.per_tag) as [tagName, tagData]}
                            {#if tagData.type_counts?.dip > 0}
                              <div class="p-1.5 bg-white dark:bg-neutral-900 rounded">
                                <div class="font-mono text-[10px] text-neutral-500 mb-1">{tagName} ({tagData.type_counts.dip})</div>
                                <div class="space-y-0.5">
                                  {#each tagData.anomaly_indices.filter(idx => tagData.anomaly_types[idx] === 'dip').slice(0, 5) as idx}
                                    <div class="flex justify-between text-[10px]">
                                      <span class="text-neutral-600 dark:text-neutral-400">{formatAnomalyDate(tagData.anomaly_timestamps[idx])}</span>
                                      <span class="font-mono text-blue-600 dark:text-blue-400">{formatNumber(tagData.anomaly_values[idx])}</span>
                                    </div>
                                  {/each}
                                </div>
                              </div>
                            {/if}
                          {/each}
                        {/if}
                      </div>
                    </div>
                  {/if}
                </button>
              {/if}

              {#if tc.get('drift', 0) > 0}
                <button
                  type="button"
                  onclick={() => expandedType = expandedType === 'drift' ? null : 'drift'}
                  class="w-full text-left p-2 bg-yellow-50 dark:bg-yellow-900/20 hover:bg-yellow-100 dark:hover:bg-yellow-900/30 rounded border border-yellow-200 dark:border-yellow-800 transition"
                >
                  <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2">
                      <TrendingUp size={14} class="text-yellow-500" />
                      <span class="text-sm font-medium text-yellow-700 dark:text-yellow-300">Дрейф (drift)</span>
                      <span class="text-xs px-1.5 py-0.5 bg-yellow-200 dark:bg-yellow-800 text-yellow-800 dark:text-yellow-200 rounded font-mono">{tc.get('drift', 0)}</span>
                    </div>
                    <ChevronDown size={14} class="text-yellow-500 transition-transform {expandedType === 'drift' ? 'rotate-180' : ''}" />
                  </div>
                  {#if expandedType === 'drift'}
                    <div class="mt-2 text-xs text-yellow-600 dark:text-yellow-400">
                      <p class="mb-2"><strong>Причина:</strong> Медленное постепенное отклонение от нормы. Часто связано с износом оборудования, калибровкой датчиков или изменением условий среды.</p>
                      <div class="max-h-32 overflow-y-auto space-y-1">
                        {#if analysisResult?.anomalies?.per_tag}
                          {#each Object.entries(analysisResult.anomalies.per_tag) as [tagName, tagData]}
                            {#if tagData.type_counts?.drift > 0}
                              <div class="p-1.5 bg-white dark:bg-neutral-900 rounded">
                                <div class="font-mono text-[10px] text-neutral-500 mb-1">{tagName} ({tagData.type_counts.drift})</div>
                                <div class="space-y-0.5">
                                  {#each tagData.anomaly_indices.filter(idx => tagData.anomaly_types[idx] === 'drift').slice(0, 5) as idx}
                                    <div class="flex justify-between text-[10px]">
                                      <span class="text-neutral-600 dark:text-neutral-400">{formatAnomalyDate(tagData.anomaly_timestamps[idx])}</span>
                                      <span class="font-mono text-yellow-600 dark:text-yellow-400">{formatNumber(tagData.anomaly_values[idx])}</span>
                                    </div>
                                  {/each}
                                </div>
                              </div>
                            {/if}
                          {/each}
                        {/if}
                      </div>
                    </div>
                  {/if}
                </button>
              {/if}

              {#if tc.get('noise', 0) > 0}
                <button
                  type="button"
                  onclick={() => expandedType = expandedType === 'noise' ? null : 'noise'}
                  class="w-full text-left p-2 bg-neutral-50 dark:bg-neutral-800/50 hover:bg-neutral-100 dark:hover:bg-neutral-800 rounded border border-neutral-200 dark:border-neutral-700 transition"
                >
                  <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2">
                      <Activity size={14} class="text-neutral-500" />
                      <span class="text-sm font-medium text-neutral-700 dark:text-neutral-300">Шум (noise)</span>
                      <span class="text-xs px-1.5 py-0.5 bg-neutral-200 dark:bg-neutral-700 text-neutral-800 dark:text-neutral-200 rounded font-mono">{tc.get('noise', 0)}</span>
                    </div>
                    <ChevronDown size={14} class="text-neutral-500 transition-transform {expandedType === 'noise' ? 'rotate-180' : ''}" />
                  </div>
                  {#if expandedType === 'noise'}
                    <div class="mt-2 text-xs text-neutral-600 dark:text-neutral-400">
                      <p class="mb-2"><strong>Причина:</strong> Высокочастотные случайные колебания. Обычно вызваны электрическими помехами, вибрацией или низким качеством сигнала.</p>
                      <div class="max-h-32 overflow-y-auto space-y-1">
                        {#if analysisResult?.anomalies?.per_tag}
                          {#each Object.entries(analysisResult.anomalies.per_tag) as [tagName, tagData]}
                            {#if tagData.type_counts?.noise > 0}
                              <div class="p-1.5 bg-white dark:bg-neutral-900 rounded">
                                <div class="font-mono text-[10px] text-neutral-500 mb-1">{tagName} ({tagData.type_counts.noise})</div>
                                <div class="space-y-0.5">
                                  {#each tagData.anomaly_indices.filter(idx => tagData.anomaly_types[idx] === 'noise').slice(0, 5) as idx}
                                    <div class="flex justify-between text-[10px]">
                                      <span class="text-neutral-600 dark:text-neutral-400">{formatAnomalyDate(tagData.anomaly_timestamps[idx])}</span>
                                      <span class="font-mono">{formatNumber(tagData.anomaly_values[idx])}</span>
                                    </div>
                                  {/each}
                                </div>
                              </div>
                            {/if}
                          {/each}
                        {/if}
                      </div>
                    </div>
                  {/if}
                </button>
              {/if}
            </div>
          {/if}
        </div>
        {/if}

'''

# Вставляем блок ПЕРЕД Scatter plot
print()
print('【2】Вставляем блок временных рядов перед Scatter plot')
print('-' * 80)

content = content[:scatter_pos] + timeseries_block + content[scatter_pos:]
print(f'✅ Блок вставлен ({len(timeseries_block)} символов)')

# Сохраняем файл
print()
print('【3】Сохраняем файл')
print('-' * 80)
results_path.write_text(content, encoding='utf-8', newline='\n')
print('✅ Файл сохранён')

print()
print('=' * 80)
print('ЧТО СДЕЛАНО:')
print('=' * 80)
print()
print('1. ВОЗВРАЩЁН график временных рядов для multi-tag:')
print('   • Вставлен перед Scatter plot')
print('   • Показывает все теги с аномалиями')
print('   • Кнопки zoom/reset/download работают')
print()
print('2. ВОЗВРАЩЕНА сводка по типам аномалий:')
print('   • Пики (spike) — оранжевый')
print('   • Провалы (dip) — синий')
print('   • Дрейф (drift) — жёлтый')
print('   • Шум (noise) — серый')
print('   • Раскрывающиеся блоки с деталями')
print()
print('3. НЕ ТРОНУТЫ:')
print('   • Single-tag seasonal (работает корректно)')
print('   • Multi-tag seasonal (один блок на строке 719)')
print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Frontend перезагрузится автоматически')
print('2. Multi-tag анализ:')
print('   → График временных рядов должен появиться ПЕРЕД Scatter plot')
print('   → Сводка по типам аномалий должна быть под графиком')
print('   → Seasonal блок остаётся ПОСЛЕ Scatter plot')