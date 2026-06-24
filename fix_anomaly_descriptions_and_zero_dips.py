#!/usr/bin/env python3
"""
fix_anomaly_descriptions_and_zero_dips.py
1. Добавляет описания типов аномалий
2. Добавляет детекцию падений в ноль (zero dips)
3. Делает блок сводки раскрываемым с деталями
"""

from pathlib import Path

print('=' * 70)
print('ДОРАБОТКА: Описание типов + Zero Dips + Раскрывающийся блок')
print('=' * 70)
print()

# ============================================================================
# 1. BACKEND: Добавляем детекцию падений в ноль (zero dips)
# ============================================================================
anomalies_path = Path('backend/modules/deep_analysis/analyzers/anomalies.py')
anom_content = anomalies_path.read_text(encoding='utf-8')

# Добавляем функцию detect_zero_dips после detect_anomalies_isolation_forest
zero_dips_func = '''

def detect_zero_dips(
    values: list[float],
    timestamps: list,
    zero_threshold_ratio: float = 0.05,  # 5% от среднего
    min_duration: int = 1,
) -> dict:
    """
    Детектирует падения значений в ноль или близко к нулю.
    
    ЭТО ВАЖНО: Isolation Forest часто пропускает падения в ноль,
    если они регулярные (например, датчик периодически выключается).
    Эта функция находит такие случаи эвристически.
    
    Args:
        values: массив значений
        timestamps: массив timestamps
        zero_threshold_ratio: порог "нуля" как % от среднего значения
        min_duration: минимальная длительность провала (в точках)
    
    Returns:
        {
            "anomaly_indices": list[int],
            "anomaly_values": list[float],
            "events": list[{start, end, duration, min_value}],
        }
    """
    if len(values) < 5:
        return {"anomaly_indices": [], "anomaly_values": [], "events": []}
    
    # Вычисляем порог нуля
    mean_value = np.mean([v for v in values if v is not None])
    zero_threshold = abs(mean_value) * zero_threshold_ratio
    
    # Находим все точки ниже порога
    zero_indices = []
    for i, v in enumerate(values):
        if v is not None and abs(v) <= zero_threshold:
            zero_indices.append(i)
    
    if not zero_indices:
        return {"anomaly_indices": [], "anomaly_values": [], "events": []}
    
    # Группируем подряд идущие нули в события
    events = []
    current_event_indices = [zero_indices[0]]
    
    for i in range(1, len(zero_indices)):
        if zero_indices[i] - zero_indices[i-1] == 1:
            current_event_indices.append(zero_indices[i])
        else:
            if len(current_event_indices) >= min_duration:
                events.append({
                    "start_idx": current_event_indices[0],
                    "end_idx": current_event_indices[-1],
                    "duration": len(current_event_indices),
                    "min_value": float(min(values[i] for i in current_event_indices if values[i] is not None)),
                    "indices": list(current_event_indices),
                })
            current_event_indices = [zero_indices[i]]
    
    # Последнее событие
    if len(current_event_indices) >= min_duration:
        events.append({
            "start_idx": current_event_indices[0],
            "end_idx": current_event_indices[-1],
            "duration": len(current_event_indices),
            "min_value": float(min(values[i] for i in current_event_indices if values[i] is not None)),
            "indices": list(current_event_indices),
        })
    
    # Собираем все индексы
    all_indices = []
    for event in events:
        all_indices.extend(event["indices"])
    
    all_values = [values[i] for i in all_indices]
    
    log.info(
        "Zero dips detected",
        total_events=len(events),
        total_points=len(all_indices),
        threshold=zero_threshold
    )
    
    return {
        "anomaly_indices": all_indices,
        "anomaly_values": all_values,
        "events": events,
    }


'''

# Вставляем после функции detect_anomalies_isolation_forest
if 'def detect_zero_dips' not in anom_content:
    # Находим конец detect_anomalies_isolation_forest (следующая функция)
    marker = 'def group_anomaly_events('
    if marker in anom_content:
        anom_content = anom_content.replace(marker, zero_dips_func + marker)
        print('✅ 1. Добавлена функция detect_zero_dips()')
        print('   • Детектирует падения в ноль или близко к нулю')
        print('   • Эвристика: значение < 5% от среднего')
        print('   • Группирует подряд идущие нули в события')

# Обновляем detect_anomalies_isolation_forest чтобы комбинировать с zero_dips
old_return_block = '''    if classify_types and len(anomaly_indices) > 0:
        types_result = classify_anomaly_types(
            values=values,
            anomaly_indices=anomaly_indices,
            anomaly_values=anomaly_values
        )
        anomaly_types = types_result['types']
        type_counts = types_result['counts']
    else:
        anomaly_types = ["unknown"] * len(anomaly_indices)

    result = {
        "anomaly_indices": anomaly_indices,
        "anomaly_timestamps": anomaly_timestamps,
        "anomaly_values": anomaly_values,
        "anomaly_scores": anomaly_scores,
        "anomaly_types": anomaly_types,
        "type_counts": type_counts,
        "total_anomalies": len(anomaly_indices),
        "anomaly_rate": len(anomaly_indices) / len(values),
    }'''

new_return_block = '''    # КОМБИНИРУЕМ: Isolation Forest + zero dips (падения в ноль)
    zero_dips = detect_zero_dips(values, timestamps, zero_threshold_ratio=0.05, min_duration=1)
    zero_indices_set = set(zero_dips['anomaly_indices'])
    if_indices_set = set(anomaly_indices)
    
    # Находим zero dips которых НЕТ в Isolation Forest
    new_zero_indices = sorted(zero_indices_set - if_indices_set)
    
    if new_zero_indices:
        # Добавляем их к списку аномалий
        for idx in new_zero_indices:
            anomaly_indices.append(idx)
            anomaly_timestamps.append(timestamps[idx])
            anomaly_values.append(values[idx])
            anomaly_scores.append(-0.5)  # псевдо-score для zero dips
    
    # Сортируем по индексам
    combined = sorted(zip(anomaly_indices, anomaly_timestamps, anomaly_values, anomaly_scores), key=lambda x: x[0])
    if combined:
        anomaly_indices, anomaly_timestamps, anomaly_values, anomaly_scores = zip(*combined)
        anomaly_indices = list(anomaly_indices)
        anomaly_timestamps = list(anomaly_timestamps)
        anomaly_values = list(anomaly_values)
        anomaly_scores = list(anomaly_scores)
    else:
        anomaly_indices, anomaly_timestamps, anomaly_values, anomaly_scores = [], [], [], []
    
    # Помечаем какие индексы были zero dips
    zero_dip_set = set(new_zero_indices)
    
    if classify_types and len(anomaly_indices) > 0:
        types_result = classify_anomaly_types(
            values=values,
            anomaly_indices=anomaly_indices,
            anomaly_values=anomaly_values,
            zero_dip_indices=zero_dip_set,  # передаём явно zero dips
        )
        anomaly_types = types_result['types']
        type_counts = types_result['counts']
    else:
        anomaly_types = ["unknown"] * len(anomaly_indices)

    result = {
        "anomaly_indices": anomaly_indices,
        "anomaly_timestamps": anomaly_timestamps,
        "anomaly_values": anomaly_values,
        "anomaly_scores": anomaly_scores,
        "anomaly_types": anomaly_types,
        "type_counts": type_counts,
        "zero_dips_events": zero_dips.get('events', []),  # детали провалов в ноль
        "total_anomalies": len(anomaly_indices),
        "anomaly_rate": len(anomaly_indices) / len(values),
    }'''

if old_return_block in anom_content:
    anom_content = anom_content.replace(old_return_block, new_return_block)
    print('✅ 2. detect_anomalies_isolation_forest комбинируется с zero_dips')

# Обновляем classify_anomaly_types чтобы принимать zero_dip_indices
old_classify_sig = '''def classify_anomaly_types(
    values: list[float],
    anomaly_indices: list[int],
    anomaly_values: list[float],
) -> dict:'''

new_classify_sig = '''def classify_anomaly_types(
    values: list[float],
    anomaly_indices: list[int],
    anomaly_values: list[float],
    zero_dip_indices: set = None,
) -> dict:'''

if old_classify_sig in anom_content:
    anom_content = anom_content.replace(old_classify_sig, new_classify_sig)
    print('✅ 3. classify_anomaly_types принимает zero_dip_indices')

# Добавляем обработку zero_dip_indices в начале classify_anomaly_types
old_types_map = '''    types_map = {}
    
    for event in events:'''

new_types_map = '''    types_map = {}
    zero_dip_indices = zero_dip_indices or set()
    
    # ПРИОРИТЕТ: все точки из zero_dip_indices помечаем как "dip" (провал в ноль)
    # Это надёжнее чем эвристики с z-score
    for idx in anomaly_indices:
        if idx in zero_dip_indices:
            types_map[idx] = "dip"
    
    for event in events:'''

if old_types_map in anom_content:
    anom_content = anom_content.replace(old_types_map, new_types_map)
    print('✅ 4. Zero dips получают приоритет типа "dip"')

# В цикле классификации пропускаем уже помеченные zero dips
old_assign = '''        # Назначаем тип всем точкам события
        for idx in indices:
            types_map[idx] = event_type'''

new_assign = '''        # Назначаем тип всем точкам события (кроме уже помеченных как zero dips)
        for idx in indices:
            if idx not in types_map:  # не перезаписываем zero dips
                types_map[idx] = event_type'''

if old_assign in anom_content:
    anom_content = anom_content.replace(old_assign, new_assign)
    print('✅ 5. Zero dips не перезаписываются другими типами')

anomalies_path.write_text(anom_content, encoding='utf-8', newline='\n')

# ============================================================================
# 2. FRONTEND: Раскрывающийся блок + описания типов
# ============================================================================
results_path = Path('frontend/src/components/DeepAnalysisResults.svelte')
results_content = results_path.read_text(encoding='utf-8')

# 2a. Добавляем состояние для аккордеона
# Ищем где определены другие состояния
if 'let expandedType' not in results_content:
    # Ищем место где определены другие state переменные
    marker = "let activeTab = $state"
    if marker in results_content:
        insert = "let expandedType = $state<string | null>(null)\n  "
        results_content = results_content.replace(marker, insert + marker)
        print('✅ 6. Добавлен state expandedType для аккордеона')

# 2b. Заменяем блок сводки на раскрывающийся с описаниями
old_summary = '''<div class="mt-2 grid grid-cols-4 gap-2">
              <div class="p-2 bg-red-50 dark:bg-red-900/20 rounded border border-red-200 dark:border-red-800">
                <div class="text-[10px] text-red-700 dark:text-red-300 mb-1 flex items-center gap-1">
                  <ArrowUpCircle size={11} class="text-red-500" />
                  Пики
                </div>
                <div class="text-sm font-semibold text-red-700 dark:text-red-300">{tc.spike || 0}</div>
              </div>
              <div class="p-2 bg-blue-50 dark:bg-blue-900/20 rounded border border-blue-200 dark:border-blue-800">
                <div class="text-[10px] text-blue-700 dark:text-blue-300 mb-1 flex items-center gap-1">
                  <ArrowDownCircle size={11} class="text-blue-500" />
                  Провалы
                </div>
                <div class="text-sm font-semibold text-blue-700 dark:text-blue-300">{tc.dip || 0}</div>
              </div>
              <div class="p-2 bg-amber-50 dark:bg-amber-900/20 rounded border border-amber-200 dark:border-amber-800">
                <div class="text-[10px] text-amber-700 dark:text-amber-300 mb-1 flex items-center gap-1">
                  <Waves size={11} class="text-amber-500" />
                  Дрейфы
                </div>
                <div class="text-sm font-semibold text-amber-700 dark:text-amber-300">{tc.drift || 0}</div>
              </div>
              <div class="p-2 bg-neutral-50 dark:bg-neutral-800 rounded border border-neutral-200 dark:border-neutral-700">
                <div class="text-[10px] text-neutral-500 dark:text-neutral-400 mb-1 flex items-center gap-1">
                  <Zap size={11} class="text-neutral-500" />
                  Шум
                </div>
                <div class="text-sm font-semibold text-neutral-700 dark:text-neutral-300">{tc.noise || 0}</div>
              </div>
            </div>'''

new_summary = '''<!-- Раскрывающаяся сводка с описаниями типов и списком значений -->
            <div class="mt-3 space-y-2">
              <!-- Заголовок-подсказка -->
              <div class="text-[11px] text-neutral-600 dark:text-neutral-400 p-2 bg-neutral-50 dark:bg-neutral-800/50 rounded">
                💡 Кликните на тип аномалии чтобы увидеть подробности и список значений
              </div>

              <!-- Пики -->
              <details class="border border-red-200 dark:border-red-800 rounded bg-red-50 dark:bg-red-900/10" open={expandedType === 'spike'}>
                <summary class="p-2 cursor-pointer hover:bg-red-100 dark:hover:bg-red-900/30 transition flex items-center justify-between" onclick={(e) => { e.preventDefault(); expandedType = expandedType === 'spike' ? null : 'spike'; }}>
                  <div class="flex items-center gap-2">
                    <ArrowUpCircle size={14} class="text-red-500" />
                    <span class="text-sm font-semibold text-red-700 dark:text-red-300">Пики (Spike)</span>
                    <span class="text-xs px-1.5 py-0.5 bg-red-200 dark:bg-red-900/40 text-red-800 dark:text-red-200 rounded">{tc.spike || 0}</span>
                  </div>
                  <ChevronDown size={14} class="text-red-500 transition-transform" class:rotate-180={expandedType === 'spike'} />
                </summary>
                <div class="p-2 border-t border-red-200 dark:border-red-800">
                  <p class="text-[11px] text-red-700 dark:text-red-300 mb-2">
                    <strong>Пик (Spike)</strong> — резкий одиночный скачок значения вверх относительно соседей. 
                    Обычно вызван кратковременным сбоем датчика, электромагнитной помехой или мгновенным событием в системе.
                    Математика: локальный z-score &gt; 1.5 (отклонение больше 1.5 стандартных отклонений от локального среднего).
                  </p>
                  {#if analysisResult?.anomalies?.per_tag}
                    {#each Object.entries(analysisResult.anomalies.per_tag) as [tagName, tagData]}
                      {@const spikePoints = (tagData.anomaly_indices || []).filter((idx, i) => (tagData.anomaly_types || [])[i] === 'spike')}
                      {#if spikePoints.length > 0}
                        <div class="mt-2">
                          <div class="text-[10px] font-semibold text-red-700 dark:text-red-300 mb-1">{tagName} ({spikePoints.length}):</div>
                          <div class="max-h-32 overflow-y-auto space-y-0.5">
                            {#each spikePoints.slice(0, 20) as idx, i}
                              {@const val = (tagData.anomaly_values || [])[tagData.anomaly_indices.indexOf(idx)]}
                              <div class="text-[10px] font-mono text-red-600 dark:text-red-400 flex justify-between">
                                <span>#{idx}</span>
                                <span class="font-semibold">{val !== undefined ? val.toFixed(2) : '—'}</span>
                              </div>
                            {/each}
                            {#if spikePoints.length > 20}
                              <div class="text-[10px] text-red-500 italic">... и ещё {spikePoints.length - 20}</div>
                            {/if}
                          </div>
                        </div>
                      {/if}
                    {/each}
                  {:else if analysisResult?.anomalies?.anomaly_indices}
                    {@const spikePoints = analysisResult.anomalies.anomaly_indices.filter((idx, i) => analysisResult.anomalies.anomaly_types[i] === 'spike')}
                    <div class="max-h-32 overflow-y-auto space-y-0.5 mt-1">
                      {#each spikePoints.slice(0, 30) as idx, i}
                        {@const val = analysisResult.anomalies.anomaly_values[analysisResult.anomalies.anomaly_indices.indexOf(idx)]}
                        <div class="text-[10px] font-mono text-red-600 dark:text-red-400 flex justify-between">
                          <span>#{idx}</span>
                          <span class="font-semibold">{val !== undefined ? val.toFixed(2) : '—'}</span>
                        </div>
                      {/each}
                    </div>
                  {/if}
                </div>
              </details>

              <!-- Провалы -->
              <details class="border border-blue-200 dark:border-blue-800 rounded bg-blue-50 dark:bg-blue-900/10" open={expandedType === 'dip'}>
                <summary class="p-2 cursor-pointer hover:bg-blue-100 dark:hover:bg-blue-900/30 transition flex items-center justify-between" onclick={(e) => { e.preventDefault(); expandedType = expandedType === 'dip' ? null : 'dip'; }}>
                  <div class="flex items-center gap-2">
                    <ArrowDownCircle size={14} class="text-blue-500" />
                    <span class="text-sm font-semibold text-blue-700 dark:text-blue-300">Провалы (Dip)</span>
                    <span class="text-xs px-1.5 py-0.5 bg-blue-200 dark:bg-blue-900/40 text-blue-800 dark:text-blue-200 rounded">{tc.dip || 0}</span>
                  </div>
                  <ChevronDown size={14} class="text-blue-500 transition-transform" class:rotate-180={expandedType === 'dip'} />
                </summary>
                <div class="p-2 border-t border-blue-200 dark:border-blue-800">
                  <p class="text-[11px] text-blue-700 dark:text-blue-300 mb-2">
                    <strong>Провал (Dip)</strong> — резкое падение значения вниз, в том числе <strong>падение в ноль</strong>.
                    Типичные причины: отключение датчика, обрыв связи, кратковременный сбой оборудования, потеря питания.
                    Детектируется двумя способами: (1) падение в ноль (&lt;5% от среднего значения) — эвристика, 
                    (2) локальный z-score &lt; -1.5 (сильное отклонение вниз).
                  </p>
                  {#if analysisResult?.anomalies?.zero_dips_events && analysisResult.anomalies.zero_dips_events.length > 0}
                    <div class="mt-2 p-2 bg-blue-100 dark:bg-blue-900/30 rounded">
                      <div class="text-[10px] font-semibold text-blue-800 dark:text-blue-200 mb-1">
                        📉 Падения в ноль ({analysisResult.anomalies.zero_dips_events.length} событий):
                      </div>
                      <div class="max-h-32 overflow-y-auto space-y-0.5">
                        {#each analysisResult.anomalies.zero_dips_events.slice(0, 20) as event}
                          <div class="text-[10px] font-mono text-blue-700 dark:text-blue-300 flex justify-between">
                            <span>#{event.start_idx}–#{event.end_idx}</span>
                            <span>длит: {event.duration}</span>
                            <span class="font-semibold">min: {event.min_value.toFixed(2)}</span>
                          </div>
                        {/each}
                      </div>
                    </div>
                  {/if}
                  {#if analysisResult?.anomalies?.per_tag}
                    {#each Object.entries(analysisResult.anomalies.per_tag) as [tagName, tagData]}
                      {@const dipPoints = (tagData.anomaly_indices || []).filter((idx, i) => (tagData.anomaly_types || [])[i] === 'dip')}
                      {#if dipPoints.length > 0}
                        <div class="mt-2">
                          <div class="text-[10px] font-semibold text-blue-700 dark:text-blue-300 mb-1">{tagName} ({dipPoints.length}):</div>
                          <div class="max-h-32 overflow-y-auto space-y-0.5">
                            {#each dipPoints.slice(0, 20) as idx}
                              {@const val = (tagData.anomaly_values || [])[tagData.anomaly_indices.indexOf(idx)]}
                              <div class="text-[10px] font-mono text-blue-600 dark:text-blue-400 flex justify-between">
                                <span>#{idx}</span>
                                <span class="font-semibold">{val !== undefined ? val.toFixed(2) : '—'}</span>
                              </div>
                            {/each}
                            {#if dipPoints.length > 20}
                              <div class="text-[10px] text-blue-500 italic">... и ещё {dipPoints.length - 20}</div>
                            {/if}
                          </div>
                        </div>
                      {/if}
                    {/each}
                  {/if}
                </div>
              </details>

              <!-- Дрейфы -->
              <details class="border border-amber-200 dark:border-amber-800 rounded bg-amber-50 dark:bg-amber-900/10" open={expandedType === 'drift'}>
                <summary class="p-2 cursor-pointer hover:bg-amber-100 dark:hover:bg-amber-900/30 transition flex items-center justify-between" onclick={(e) => { e.preventDefault(); expandedType = expandedType === 'drift' ? null : 'drift'; }}>
                  <div class="flex items-center gap-2">
                    <Waves size={14} class="text-amber-500" />
                    <span class="text-sm font-semibold text-amber-700 dark:text-amber-300">Дрейфы (Drift)</span>
                    <span class="text-xs px-1.5 py-0.5 bg-amber-200 dark:bg-amber-900/40 text-amber-800 dark:text-amber-200 rounded">{tc.drift || 0}</span>
                  </div>
                  <ChevronDown size={14} class="text-amber-500 transition-transform" class:rotate-180={expandedType === 'drift'} />
                </summary>
                <div class="p-2 border-t border-amber-200 dark:border-amber-800">
                  <p class="text-[11px] text-amber-700 dark:text-amber-300 mb-2">
                    <strong>Дрейф (Drift)</strong> — постепенное монотонное смещение уровня сигнала от нормы.
                    В отличие от пика (резкий скачок), дрейф развивается во времени — значение медленно уходит вверх или вниз.
                    Типичные причины: старение датчика, засорение, калибровочный сдвиг, накопление отложений.
                    Математика: минимум 5 подряд идущих аномальных точек + монотонность (&gt;75% в одну сторону) + R² линейного тренда &gt; 0.6.
                  </p>
                  {#if analysisResult?.anomalies?.per_tag}
                    {#each Object.entries(analysisResult.anomalies.per_tag) as [tagName, tagData]}
                      {@const driftPoints = (tagData.anomaly_indices || []).filter((idx, i) => (tagData.anomaly_types || [])[i] === 'drift')}
                      {#if driftPoints.length > 0}
                        <div class="mt-2">
                          <div class="text-[10px] font-semibold text-amber-700 dark:text-amber-300 mb-1">{tagName} ({driftPoints.length}):</div>
                          <div class="max-h-32 overflow-y-auto space-y-0.5">
                            {#each driftPoints.slice(0, 20) as idx}
                              {@const val = (tagData.anomaly_values || [])[tagData.anomaly_indices.indexOf(idx)]}
                              <div class="text-[10px] font-mono text-amber-600 dark:text-amber-400 flex justify-between">
                                <span>#{idx}</span>
                                <span class="font-semibold">{val !== undefined ? val.toFixed(2) : '—'}</span>
                              </div>
                            {/each}
                            {#if driftPoints.length > 20}
                              <div class="text-[10px] text-amber-500 italic">... и ещё {driftPoints.length - 20}</div>
                            {/if}
                          </div>
                        </div>
                      {/if}
                    {/each}
                  {/if}
                </div>
              </details>

              <!-- Шум -->
              <details class="border border-neutral-200 dark:border-neutral-700 rounded bg-neutral-50 dark:bg-neutral-800/50" open={expandedType === 'noise'}>
                <summary class="p-2 cursor-pointer hover:bg-neutral-100 dark:hover:bg-neutral-800 transition flex items-center justify-between" onclick={(e) => { e.preventDefault(); expandedType = expandedType === 'noise' ? null : 'noise'; }}>
                  <div class="flex items-center gap-2">
                    <Zap size={14} class="text-neutral-500" />
                    <span class="text-sm font-semibold text-neutral-700 dark:text-neutral-300">Шум (Noise)</span>
                    <span class="text-xs px-1.5 py-0.5 bg-neutral-200 dark:bg-neutral-700 text-neutral-800 dark:text-neutral-200 rounded">{tc.noise || 0}</span>
                  </div>
                  <ChevronDown size={14} class="text-neutral-500 transition-transform" class:rotate-180={expandedType === 'noise'} />
                </summary>
                <div class="p-2 border-t border-neutral-200 dark:border-neutral-700">
                  <p class="text-[11px] text-neutral-700 dark:text-neutral-300 mb-2">
                    <strong>Шум (Noise)</strong> — быстрые хаотичные колебания значения без выраженного тренда.
                    В отличие от дрейфа (монотонный уход) или пика (одиночный выброс), шум — это беспорядочные 
                    колебания вокруг некоторого уровня. Типичные причины: электромагнитные помехи, плохой контакт,
                    вибрация, квантование АЦП, флуктуации процесса.
                    Математика: высокая производная (быстрые скачки) + низкий R² (нет линейного тренда).
                  </p>
                  {#if analysisResult?.anomalies?.per_tag}
                    {#each Object.entries(analysisResult.anomalies.per_tag) as [tagName, tagData]}
                      {@const noisePoints = (tagData.anomaly_indices || []).filter((idx, i) => (tagData.anomaly_types || [])[i] === 'noise')}
                      {#if noisePoints.length > 0}
                        <div class="mt-2">
                          <div class="text-[10px] font-semibold text-neutral-700 dark:text-neutral-300 mb-1">{tagName} ({noisePoints.length}):</div>
                          <div class="max-h-32 overflow-y-auto space-y-0.5">
                            {#each noisePoints.slice(0, 20) as idx}
                              {@const val = (tagData.anomaly_values || [])[tagData.anomaly_indices.indexOf(idx)]}
                              <div class="text-[10px] font-mono text-neutral-600 dark:text-neutral-400 flex justify-between">
                                <span>#{idx}</span>
                                <span class="font-semibold">{val !== undefined ? val.toFixed(2) : '—'}</span>
                              </div>
                            {/each}
                            {#if noisePoints.length > 20}
                              <div class="text-[10px] text-neutral-500 italic">... и ещё {noisePoints.length - 20}</div>
                            {/if}
                          </div>
                        </div>
                      {/if}
                    {/each}
                  {/if}
                </div>
              </details>
            </div>'''

if old_summary in results_content:
    results_content = results_content.replace(old_summary, new_summary)
    print('✅ 7. Блок сводки заменён на раскрывающийся с описаниями')
else:
    print('⚠ Не удалось найти старый блок сводки для замены')

# Добавляем импорт ChevronDown если его нет
if 'ChevronDown' not in results_content:
    results_content = results_content.replace(
        ', Lightbulb, Circle,',
        ', Lightbulb, Circle, ChevronDown,'
    )
    print('✅ 8. Добавлен импорт ChevronDown для аккордеона')

results_path.write_text(results_content, encoding='utf-8', newline='\n')

print()
print('=' * 70)
print('ИТОГ:')
print('=' * 70)
print()
print('✅ 1. Добавлена детекция падений в ноль (Zero Dips)')
print('   • Новая функция detect_zero_dips()')
print('   • Эвристика: значение < 5% от среднего')
print('   • Группирует подряд идущие нули в события')
print('   • Комбинируется с Isolation Forest')
print()
print('✅ 2. Zero Dips получают приоритет типа "dip"')
print('   • Если Isolation Forest не пометил точку, но это zero dip → "dip"')
print('   • Теперь падения в ноль всегда отображаются как провалы')
print()
print('✅ 3. Блок сводки раскрывающийся')
print('   • <details> / <summary> HTML5 аккордеон')
print('   • Клик на тип → раскрывается с описанием + список значений')
print('   • ChevronDown иконка показывает состояние (повёрнута/нет)')
print()
print('✅ 4. Описания каждого типа:')
print('   • Пик: резкий одиночный скачок вверх, локальный z-score > 1.5')
print('   • Провал: падение вниз, в т.ч. в ноль (эвристика + z-score < -1.5)')
print('   • Дрейф: монотонное смещение (5+ точек, R² > 0.6, монотонность > 75%)')
print('   • Шум: хаотичные колебания без тренда (высокая производная + R² < 0.3)')
print()
print('✅ 5. Детали падений в ноль')
print('   • Отдельный блок "📉 Падения в ноль" внутри Провалов')
print('   • Список событий: #{start}-#{end}, длительность, min значение')
print()
print('=' * 70)
print('ПРОВЕРКА:')
print('=' * 70)
print()
print('1. Перезапусти backend')
print('2. Открой фронтенд → выбери 1-3 тега (в т.ч. с падениями в 0) → анализ')
print()
print('Ожидаемое поведение:')
print('  • Видишь 4 карточки: Пики / Провалы / Дрейфы / Шум')
print('  • Провалы теперь НЕ 0 если есть падения значений в ноль')
print('  • Клик на "Провалы" → раскрывается:')
print('     - Описание что это такое')
print('     - Блок "📉 Падения в ноль (N событий)" с деталями')
print('     - Список значений по каждому тегу')
print('  • Клик на другой тип → аналогично с описанием и списком')
print()
print('В логах backend:')
print('  [info] Zero dips detected total_events=5 total_points=23 threshold=24.85')
print('  [info] Anomalies detected total=400 types={spike: 24, dip: 50, drift: 85, noise: 241}')