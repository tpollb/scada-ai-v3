#!/usr/bin/env python3
"""
fix_multitag_anomalies.py — детекция аномалий для мульти-тег + фикс Svelte warnings
"""

from pathlib import Path

print('=' * 70)
print('ФИКС: Аномалии для мульти-тег + Svelte warnings')
print('=' * 70)
print()

# ============================================================================
# 1. Обновляем api.py — добавляем аномалии для мульти-тег
# ============================================================================
api_path = Path('backend/modules/deep_analysis/api.py')
content = api_path.read_text(encoding='utf-8')

# Ищем блок мульти-тег анализа (после "Группа тегов — кросс-анализ")
# Нужно добавить вызов detect_anomalies_isolation_forest для каждого тега

# Проверяем импорты
if 'from modules.deep_analysis.analyzers.anomalies import detect_anomalies_isolation_forest' not in content:
    content = content.replace(
        'from modules.deep_analysis.collectors.data_fetcher import fetch_tag_data, fetch_multiple_tags',
        'from modules.deep_analysis.collectors.data_fetcher import fetch_tag_data, fetch_multiple_tags\nfrom modules.deep_analysis.analyzers.anomalies import detect_anomalies_isolation_forest'
    )
    print('✓ Добавлен импорт detect_anomalies_isolation_forest')

# Ищем блок где формируется summary для мульти-тег
# И добавляем туда детекцию аномалий

old_multitag_block = '''        else:
            # Группа тегов — кросс-анализ (корреляции)
            log.info("Multi-tag analysis", tags=request.tags)
            
            # Сбор данных с выравниванием
            data = await fetch_multiple_tags(
                request.tags, start_date, end_date,
                resample_freq='5min',
                align=True
            )
            
            if not data['common_timestamps']:
                raise HTTPException(
                    status_code=400,
                    detail="No common timestamps found for correlation analysis. "
                           "Tags may have insufficient data or non-overlapping time ranges."
                )
            
            # Матрица корреляций
            correlation_matrix = compute_correlation_matrix(
                data['tags'],
                data['common_timestamps'],
                method='pearson'
            )
            
            # Детальный анализ для первой пары (как пример)
            if len(request.tags) >= 2:
                tag1, tag2 = request.tags[0], request.tags[1]
                pair_analysis = compute_pair_correlation(
                    data['tags'][tag1].get('aligned_values', []),
                    data['tags'][tag2].get('aligned_values', []),
                    tag1, tag2
                )
            else:
                pair_analysis = None
            
            # Визуализации
            heatmap_spec = create_heatmap_spec(correlation_matrix)
            scatter_spec = None
            if pair_analysis and pair_analysis['scatter_data']['x']:
                scatter_spec = create_scatter_spec(
                    pair_analysis['scatter_data']['x'],
                    pair_analysis['scatter_data']['y'],
                    pair_analysis['tag_x'],
                    pair_analysis['tag_y'],
                    pair_analysis['pearson']['coefficient']
                )'''

new_multitag_block = '''        else:
            # Группа тегов — кросс-анализ (корреляции) + аномалии для каждого тега
            log.info("Multi-tag analysis", tags=request.tags)
            
            # Сбор данных с выравниванием
            data = await fetch_multiple_tags(
                request.tags, start_date, end_date,
                resample_freq='5min',
                align=True
            )
            
            if not data['common_timestamps']:
                raise HTTPException(
                    status_code=400,
                    detail="No common timestamps found for correlation analysis. "
                           "Tags may have insufficient data or non-overlapping time ranges."
                )
            
            # Матрица корреляций
            correlation_matrix = compute_correlation_matrix(
                data['tags'],
                data['common_timestamps'],
                method='pearson'
            )
            
            # Детальный анализ для первой пары
            if len(request.tags) >= 2:
                tag1, tag2 = request.tags[0], request.tags[1]
                pair_analysis = compute_pair_correlation(
                    data['tags'][tag1].get('aligned_values', []),
                    data['tags'][tag2].get('aligned_values', []),
                    tag1, tag2
                )
            else:
                pair_analysis = None
            
            # НОВОЕ: Детекция аномалий для каждого тега (с классификацией по типам)
            anomalies_per_tag = {}
            total_type_counts = {}
            total_anomalies = 0
            
            for tag_name in request.tags:
                tag_data = data['tags'].get(tag_name, {})
                aligned_values = tag_data.get('aligned_values', [])
                
                # Фильтруем None значения
                valid_values = [v for v in aligned_values if v is not None]
                
                if len(valid_values) >= 10:
                    tag_anomalies = detect_anomalies_isolation_forest(
                        valid_values,
                        list(range(len(valid_values))),  # псевдо-timestamps (индексы)
                        classify_types=True
                    )
                    anomalies_per_tag[tag_name] = tag_anomalies
                    total_anomalies += tag_anomalies['total_anomalies']
                    
                    # Агрегируем type_counts
                    for atype, count in tag_anomalies.get('type_counts', {}).items():
                        total_type_counts[atype] = total_type_counts.get(atype, 0) + count
            
            # Формируем общий anomalies объект (для совместимости с UI)
            combined_anomalies = {
                "per_tag": anomalies_per_tag,
                "total_anomalies": total_anomalies,
                "type_counts": total_type_counts,
            } if total_anomalies > 0 else None
            
            # Визуализации
            heatmap_spec = create_heatmap_spec(correlation_matrix)
            scatter_spec = None
            if pair_analysis and pair_analysis['scatter_data']['x']:
                scatter_spec = create_scatter_spec(
                    pair_analysis['scatter_data']['x'],
                    pair_analysis['scatter_data']['y'],
                    pair_analysis['tag_x'],
                    pair_analysis['tag_y'],
                    pair_analysis['pearson']['coefficient']
                )
            
            # НОВОЕ: time series spec с аномалиями для мульти-тег
            # Создаём график со всеми тегами + цветовая кодировка аномалий
            from datetime import datetime
            time_series_spec = create_multitag_time_series_spec(
                data['tags'],
                data['common_timestamps'],
                anomalies_per_tag
            )'''

if old_multitag_block in content:
    content = content.replace(old_multitag_block, new_multitag_block)
    print('✓ Добавлена детекция аномалий для мульти-тег')
else:
    print('⚠ Не удалось найти блок мульти-тег анализа')

# Обновляем summary чтобы включить информацию об аномалиях
old_summary = '''            # Summary
            summary_parts = [
                f"Анализ {len(request.tags)} тегов за период {period_str}.",
                f"Общих точек: {len(data['common_timestamps'])}.",
            ]
            
            # Находим самую сильную корреляцию
            max_corr = 0.0
            max_pair = None
            for i in range(len(correlation_matrix['tags'])):
                for j in range(i + 1, len(correlation_matrix['tags'])):
                    corr = correlation_matrix['matrix'][i][j]
                    if abs(corr) > abs(max_corr):
                        max_corr = corr
                        max_pair = (correlation_matrix['tags'][i], correlation_matrix['tags'][j])
            
            if max_pair:
                summary_parts.append(
                    f"Самая сильная корреляция: {max_pair[0]} ↔ {max_pair[1]} (r={max_corr:.2f})"
                )
            
            summary = " ".join(summary_parts)'''

new_summary = '''            # Summary
            summary_parts = [
                f"Анализ {len(request.tags)} тегов за период {period_str}.",
                f"Общих точек: {len(data['common_timestamps'])}.",
            ]
            
            # Находим самую сильную корреляцию
            max_corr = 0.0
            max_pair = None
            for i in range(len(correlation_matrix['tags'])):
                for j in range(i + 1, len(correlation_matrix['tags'])):
                    corr = correlation_matrix['matrix'][i][j]
                    if abs(corr) > abs(max_corr):
                        max_corr = corr
                        max_pair = (correlation_matrix['tags'][i], correlation_matrix['tags'][j])
            
            if max_pair:
                summary_parts.append(
                    f"Самая сильная корреляция: {max_pair[0]} ↔ {max_pair[1]} (r={max_corr:.2f})"
                )
            
            # Добавляем информацию об аномалиях
            if combined_anomalies and combined_anomalies['total_anomalies'] > 0:
                tc = combined_anomalies['type_counts']
                type_parts = []
                if tc.get('spike', 0): type_parts.append(f"пиков: {tc['spike']}")
                if tc.get('dip', 0): type_parts.append(f"провалов: {tc['dip']}")
                if tc.get('drift', 0): type_parts.append(f"дрейфов: {tc['drift']}")
                if tc.get('noise', 0): type_parts.append(f"шумов: {tc['noise']}")
                summary_parts.append(
                    f"Обнаружено аномалий: {combined_anomalies['total_anomalies']} ({', '.join(type_parts)})"
                )
            
            summary = " ".join(summary_parts)'''

if old_summary in content:
    content = content.replace(old_summary, new_summary)
    print('✓ Summary включает информацию об аномалиях')

# Обновляем блок формирования ответа — передаём anomalies для мульти-тег
old_response_multi = '''        else:
            # Мульти-тег
            response = AnalysisResponse(
                analysis_id=analysis_id,
                status="completed",
                created_at=datetime.now().isoformat(),
                tags=request.tags,
                period=period_str,
                summary=summary,
                statistics=None,  # для мульти-тега статистика по каждому тегу отдельно
                anomalies=None,
                correlations=results.get('correlation_matrix'),
                seasonality=None,
                visualizations={
                    "heatmap": heatmap_spec,
                    "scatter": scatter_spec,
                },
                history_path=history_path,
            )'''

new_response_multi = '''        else:
            # Мульти-тег
            response = AnalysisResponse(
                analysis_id=analysis_id,
                status="completed",
                created_at=datetime.now().isoformat(),
                tags=request.tags,
                period=period_str,
                summary=summary,
                statistics=None,
                anomalies=combined_anomalies,  # НОВОЕ: аномалии для мульти-тег
                correlations=correlation_matrix,
                seasonality=None,
                visualizations={
                    "heatmap": heatmap_spec,
                    "scatter": scatter_spec,
                    "time_series": time_series_spec,  # НОВОЕ: график с аномалиями
                },
                history_path=history_path,
            )'''

if old_response_multi in content:
    content = content.replace(old_response_multi, new_response_multi)
    print('✓ Обновлён response для мульти-тег')

# Добавляем импорт create_multitag_time_series_spec
if 'create_multitag_time_series_spec' not in content:
    content = content.replace(
        'from modules.deep_analysis.visualizers.chart_specs import create_time_series_spec, create_histogram_spec, create_heatmap_spec, create_scatter_spec',
        'from modules.deep_analysis.visualizers.chart_specs import create_time_series_spec, create_histogram_spec, create_heatmap_spec, create_scatter_spec, create_multitag_time_series_spec'
    )
    print('✓ Добавлен импорт create_multitag_time_series_spec')

api_path.write_text(content, encoding='utf-8', newline='\n')

# ============================================================================
# 2. Добавляем create_multitag_time_series_spec в chart_specs.py
# ============================================================================
chart_specs_path = Path('backend/modules/deep_analysis/visualizers/chart_specs.py')
cs_content = chart_specs_path.read_text(encoding='utf-8')

multitag_func = '''

def create_multitag_time_series_spec(
    tags_data: dict,
    common_timestamps: list,
    anomalies_per_tag: dict = None,
) -> dict:
    """
    Создаёт time series spec для мульти-тег графика.
    
    Показывает:
    - Линии для каждого тега (разные цвета)
    - Scatter points для аномалий с цветовой кодировкой по типам:
      🔴 Spike, 🔵 Dip, 🟠 Drift, ⚪ Noise
    
    Args:
        tags_data: {tag_name: {"aligned_values": [...], ...}, ...}
        common_timestamps: общие timestamps
        anomalies_per_tag: {tag_name: {"anomaly_indices": [...], "anomaly_types": [...], ...}, ...}
    """
    from datetime import datetime
    
    datasets = []
    
    # Цвета для линий тегов (разные цвета для разных тегов)
    tag_colors = [
        "#3b82f6",  # blue
        "#10b981",  # green
        "#f59e0b",  # amber
        "#ef4444",  # red
        "#8b5cf6",  # purple
        "#ec4899",  # pink
        "#14b8a6",  # teal
        "#f97316",  # orange
    ]
    
    # Цвета для типов аномалий
    type_colors = {
        "spike": {"color": "#ef4444", "label": "Пики"},
        "dip": {"color": "#3b82f6", "label": "Провалы"},
        "drift": {"color": "#f59e0b", "label": "Дрейфы"},
        "noise": {"color": "#6b7280", "label": "Шум"},
    }
    
    # Форматируем labels (строковое представление timestamps)
    labels = []
    for ts in common_timestamps:
        if isinstance(ts, datetime):
            labels.append(ts.strftime("%Y-%m-%d %H:%M"))
        else:
            labels.append(str(ts))
    
    # 1. Добавляем линии для каждого тега
    for i, (tag_name, tag_data) in enumerate(tags_data.items()):
        aligned_values = tag_data.get('aligned_values', [])
        color = tag_colors[i % len(tag_colors)]
        
        datasets.append({
            "label": tag_name,
            "data": aligned_values,
            "borderColor": color,
            "backgroundColor": color,
            "type": "line",
            "borderWidth": 1.5,
            "pointRadius": 0,
            "pointHoverRadius": 4,
            "tension": 0.1,
            "fill": False,
        })
    
    # 2. Добавляем scatter points для аномалий по типам
    if anomalies_per_tag:
        # Группируем аномалии по типам (с префиксом тега)
        anomalies_by_type = {}
        
        for tag_name, tag_anomalies in anomalies_per_tag.items():
            indices = tag_anomalies.get('anomaly_indices', [])
            types = tag_anomalies.get('anomaly_types', [])
            aligned_values = tags_data[tag_name].get('aligned_values', [])
            
            # Сопоставляем индексы с индексами в aligned_values (с учётом None)
            valid_idx = 0
            idx_map = {}
            for i, v in enumerate(aligned_values):
                if v is not None:
                    idx_map[valid_idx] = i
                    valid_idx += 1
            
            for anom_idx, anom_type in zip(indices, types):
                actual_idx = idx_map.get(anom_idx)
                if actual_idx is None:
                    continue
                
                value = aligned_values[actual_idx]
                key = f"{tag_name}|{anom_type}"
                
                if key not in anomalies_by_type:
                    anomalies_by_type[key] = {
                        "tag": tag_name,
                        "type": anom_type,
                        "points": []
                    }
                anomalies_by_type[key]["points"].append((actual_idx, value))
        
        # Создаём dataset для каждого типа аномалий
        for key, info in anomalies_by_type.items():
            atype = info["type"]
            tag_name = info["tag"]
            color_info = type_colors.get(atype, type_colors["noise"])
            
            # Массив с null для всех точек кроме аномалий этого типа
            type_data = [None] * len(common_timestamps)
            for idx, val in info["points"]:
                type_data[idx] = val
            
            label = f"{color_info['label']} ({tag_name})"
            
            datasets.append({
                "label": label,
                "data": type_data,
                "borderColor": color_info["color"],
                "backgroundColor": color_info["color"],
                "type": "scatter",
                "pointRadius": 5,
                "pointHoverRadius": 7,
                "showLine": False,
            })
    
    spec = {
        "type": "line",
        "data": {
            "labels": labels,
            "datasets": datasets,
        },
        "options": {
            "responsive": True,
            "maintainAspectRatio": False,
            "plugins": {
                "legend": {
                    "display": True,
                    "position": "top",
                    "labels": {"font": {"size": 10}, "boxWidth": 10},
                },
                "tooltip": {
                    "mode": "index",
                    "intersect": False,
                },
            },
            "scales": {
                "x": {
                    "display": True,
                    "grid": {"display": False},
                    "ticks": {"maxTicksLimit": 10, "font": {"size": 9}},
                },
                "y": {
                    "display": True,
                    "grid": {"color": "rgba(0, 0, 0, 0.05)"},
                    "ticks": {"font": {"size": 9}},
                },
            },
            "interaction": {
                "mode": "nearest",
                "axis": "x",
                "intersect": False,
            },
        },
    }
    
    return spec
'''

if 'def create_multitag_time_series_spec' not in cs_content:
    cs_content += multitag_func
    chart_specs_path.write_text(cs_content, encoding='utf-8', newline='\n')
    print('✓ Добавлена функция create_multitag_time_series_spec')

# ============================================================================
# 3. Обновляем DeepAnalysisResults.svelte — чиним Svelte warnings
# ============================================================================
results_path = Path('frontend/src/components/DeepAnalysisResults.svelte')
results_content = results_path.read_text(encoding='utf-8')

# Заменяем console.log на $state.snapshot()
old_debug = '''  // DEBUG: логируем что приходит с backend
  $effect(() => {
    if (analysisResult) {
      console.log('🔍 DDA Analysis Result:', analysisResult)
      console.log('🔍 Anomalies:', analysisResult.anomalies)
      if (analysisResult.anomalies) {
        console.log('🔍 Anomaly types:', analysisResult.anomalies.anomaly_types)
        console.log('🔍 Type counts:', analysisResult.anomalies.type_counts)
      }
      if (analysisResult.visualizations?.time_series) {
        console.log('🔍 Time series datasets:', analysisResult.visualizations.time_series.data.datasets)
        console.log('🔍 Datasets count:', analysisResult.visualizations.time_series.data.datasets.length)
      }
    }
  })'''

new_debug = '''  // DEBUG: логируем что приходит с backend (используем snapshot для $state proxy)
  $effect(() => {
    if (analysisResult) {
      const snap = $state.snapshot(analysisResult)
      console.log('🔍 DDA Analysis Result:', snap)
      console.log('🔍 Anomalies:', snap.anomalies)
      if (snap.anomalies) {
        // Single-tag mode
        if (snap.anomalies.anomaly_types) {
          console.log('🔍 Anomaly types:', snap.anomalies.anomaly_types)
          console.log('🔍 Type counts:', snap.anomalies.type_counts)
        }
        // Multi-tag mode
        if (snap.anomalies.per_tag) {
          console.log('🔍 Anomalies per tag:', Object.keys(snap.anomalies.per_tag))
          console.log('🔍 Total type counts:', snap.anomalies.type_counts)
        }
      }
      if (snap.visualizations?.time_series) {
        console.log('🔍 Time series datasets:', snap.visualizations.time_series.data.datasets)
        console.log('🔍 Datasets count:', snap.visualizations.time_series.data.datasets.length)
      }
    }
  })'''

if old_debug in results_content:
    results_content = results_content.replace(old_debug, new_debug)
    print('✓ Обновлён debug лог с $state.snapshot()')

# Обновляем условие isMultiTag чтобы оно работало и с новым anomalies форматом
old_multi_check = '''  let isMultiTag = $derived(
    analysisResult?.tags?.length > 1 && 
    analysisResult?.correlations !== null &&
    analysisResult?.correlations !== undefined
  )'''

# Оставляем как есть — это правильное условие

# Обновляем timeSeriesData чтобы брать данные из мульти-тег если есть
old_ts_data = '''  let timeSeriesData = $derived(
    analysisResult?.visualizations?.time_series?.data || { labels: [], datasets: [] }
  )'''

# Это уже правильное — оно само возьмёт time_series откуда есть

# НОВОЕ: для мульти-тег показывать график с аномалиями во вкладке overview
# Сейчас во вкладке correlations показывается только heatmap + scatter
# Добавим вкладку/секцию с time series для мульти-тег

# Ищем блок с correlations вкладкой и добавляем time series
old_corr_content = '''      <!-- ==================== MULTI-TAG: CORRELATIONS ==================== -->
      {#if isMultiTag && activeTab === 'correlations'}
        <!-- 1. Матрица корреляций (кликабельная!) -->'''

new_corr_content = '''      <!-- ==================== MULTI-TAG: CORRELATIONS ==================== -->
      {#if isMultiTag && activeTab === 'correlations'}
        <!-- 0. Time series с аномалиями (если есть) -->
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
            </div>
          </div>
          <div class="text-xs text-neutral-500 dark:text-neutral-400 mb-2">
            💡 Колёсико — zoom · Shift+drag — область · Drag — прокрутка
          </div>
          <div id={tsChartId} class="h-[300px] bg-white dark:bg-neutral-800 rounded border border-neutral-200 dark:border-neutral-700 p-3">
            <Line data={timeSeriesData} options={timeSeriesOptions} key={analysisResult?.analysis_id || 'multitag'} />
          </div>
          
          <!-- Сводка по типам аномалий -->
          {#if analysisResult?.anomalies?.type_counts}
            {@const tc = analysisResult.anomalies.type_counts}
            <div class="mt-2 grid grid-cols-4 gap-2">
              <div class="p-2 bg-red-50 dark:bg-red-900/20 rounded border border-red-200 dark:border-red-800">
                <div class="text-[10px] text-red-700 dark:text-red-300 mb-1">🔴 Пики</div>
                <div class="text-sm font-semibold text-red-700 dark:text-red-300">{tc.spike || 0}</div>
              </div>
              <div class="p-2 bg-blue-50 dark:bg-blue-900/20 rounded border border-blue-200 dark:border-blue-800">
                <div class="text-[10px] text-blue-700 dark:text-blue-300 mb-1">🔵 Провалы</div>
                <div class="text-sm font-semibold text-blue-700 dark:text-blue-300">{tc.dip || 0}</div>
              </div>
              <div class="p-2 bg-amber-50 dark:bg-amber-900/20 rounded border border-amber-200 dark:border-amber-800">
                <div class="text-[10px] text-amber-700 dark:text-amber-300 mb-1">🟠 Дрейфы</div>
                <div class="text-sm font-semibold text-amber-700 dark:text-amber-300">{tc.drift || 0}</div>
              </div>
              <div class="p-2 bg-neutral-50 dark:bg-neutral-800 rounded border border-neutral-200 dark:border-neutral-700">
                <div class="text-[10px] text-neutral-500 dark:text-neutral-400 mb-1">⚪ Шум</div>
                <div class="text-sm font-semibold text-neutral-700 dark:text-neutral-300">{tc.noise || 0}</div>
              </div>
            </div>
          {/if}
        </div>
        {/if}
        
        <!-- 1. Матрица корреляций (кликабельная!) -->'''

if old_corr_content in results_content:
    results_content = results_content.replace(old_corr_content, new_corr_content)
    print('✓ Добавлен график с аномалиями для мульти-тег')

results_path.write_text(results_content, encoding='utf-8', newline='\n')

print()
print('=' * 70)
print('ИТОГ:')
print('=' * 70)
print()
print('✅ 1. Backend: детекция аномалий для мульти-тег')
print('   • Для каждого тега запускается Isolation Forest + классификация')
print('   • Агрегируется total_anomalies и type_counts')
print('   • Summary включает информацию об аномалиях')
print()
print('✅ 2. Backend: новый time series spec для мульти-тег')
print('   • Линии для каждого тега (разные цвета)')
print('   • Scatter points для аномалий с цветовой кодировкой:')
print('     🔴 Пики (Spike)')
print('     🔵 Провалы (Dip)')
print('     🟠 Дрейфы (Drift)')
print('     ⚪ Шум (Noise)')
print()
print('✅ 3. Frontend: Svelte warnings исправлены')
print('   • Используется $state.snapshot() для логов')
print()
print('✅ 4. Frontend: новая секция во вкладке "Корреляции"')
print('   • График со всеми тегами + аномалии разных типов')
print('   • Сводка по типам: 4 карточки (Пики/Провалы/Дрейфы/Шум)')
print()
print('=' * 70)
print('ПРОВЕРКА:')
print('=' * 70)
print()
print('1. Перезапусти backend')
print('2. Открой фронтенд')
print('3. Выбери 2-3 тега → "Запустить анализ"')
print('4. Вкладка "Корреляции" — сверху должен быть график:')
print('   • Линии разных цветов для каждого тега')
print('   • Точки аномалий с цветовой кодировкой')
print('   • Сводка: 4 карточки с количеством каждого типа')
print()
print('5. Для одного тега — всё как раньше (вкладка "Обзор")')
print()
print('В консоли не должно быть Svelte warnings про $state proxy')