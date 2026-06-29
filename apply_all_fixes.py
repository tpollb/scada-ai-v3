#!/usr/bin/env python3
"""
apply_all_fixes.py — применяет все правки за один проход (line-by-line)
"""
from pathlib import Path

print('=' * 80)
print('ПРИМЕНЕНИЕ: Все правки в DeepAnalysisResults.svelte')
print('=' * 80)
print()

results_path = Path('frontend/src/components/DeepAnalysisResults.svelte')
lines = results_path.read_text(encoding='utf-8').splitlines(keepends=True)

print(f'【1】Прочитано {len(lines)} строк')
print()

# Блок сезонности для single-tag (отступ 6 пробелов - уровень single-tag блока)
seasonal_single_tag = '''        <!-- Сезонный анализ -->
        {#if analysisResult?.seasonality?.periods?.detected_periods?.length > 0}
        <div class="mb-4">
          <h3 class="text-sm font-semibold mb-2 flex items-center gap-2">
            <Waves size={16} class="text-purple-500" />
            Сезонность
          </h3>
          
          {#if analysisResult.seasonality.periods.detected_periods.length > 0}
          <div class="mb-3">
            <div class="text-xs text-neutral-600 dark:text-neutral-400 mb-2">Обнаруженные периоды:</div>
            <div class="grid grid-cols-2 gap-2">
              {#each analysisResult.seasonality.periods.detected_periods.slice(0, 4) as period}
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
          {/if}

          {#if analysisResult.seasonality.decomposition?.variance_explained}
          {#let ve = analysisResult.seasonality.decomposition.variance_explained}
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
          {/let}
          {/if}

          {#if analysisResult.seasonality.pattern?.pattern?.length > 0}
          {#let pattern = analysisResult.seasonality.pattern.pattern}
          {#let minVal = Math.min(...pattern.filter(v => v !== null))}
          {#let maxVal = Math.max(...pattern.filter(v => v !== null))}
          {#let range = maxVal - minVal}
          <div class="mb-3">
            <div class="text-xs text-neutral-600 dark:text-neutral-400 mb-2">
              Типичный суточный паттерн (период {analysisResult.seasonality.periods.detected_periods[0].period} точек):
            </div>
            <div class="p-2 bg-neutral-50 dark:bg-neutral-800 rounded border border-neutral-200 dark:border-neutral-700">
              <div class="text-xs text-neutral-600 dark:text-neutral-400 mb-1">
                Мин: {minVal.toFixed(1)} | Макс: {maxVal.toFixed(1)} | Размах: {range.toFixed(1)}
              </div>
              <div class="flex items-end gap-0.5 h-16">
                {#each pattern.slice(0, 48) as val, i}
                  {#if val !== null}
                    <div 
                      class="flex-1 bg-gradient-to-t from-purple-500 to-purple-400 rounded-t transition-all hover:from-purple-600 hover:to-purple-500"
                      style="height: {((val - minVal) / range) * 100}%"
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
          {/let}
          {/let}
          {/let}
          {/let}
          {/if}
        </div>
        {/if}

'''

# Блок сезонности для multi-tag (отступ 8 пробелов - уровень multi-tag блока)
seasonal_multi_tag = '''
        <!-- Сезонный анализ (multi-tag) -->
        {#if analysisResult?.seasonality && Object.keys(analysisResult.seasonality).length > 0}
        <div class="mb-4">
          <h3 class="text-sm font-semibold mb-3 flex items-center gap-2">
            <Waves size={16} class="text-purple-500" />
            Сезонный анализ ({Object.keys(analysisResult.seasonality).length} тегов)
          </h3>
          
          {#each Object.entries(analysisResult.seasonality) as [tagName, tagSeasonality]}
            {#if tagSeasonality?.periods?.detected_periods?.length > 0}
            <div class="mb-4 p-3 bg-neutral-50 dark:bg-neutral-800 rounded border border-neutral-200 dark:border-neutral-700">
              <h4 class="text-sm font-medium mb-2 text-neutral-700 dark:text-neutral-300">{tagName}</h4>
              
              {#if tagSeasonality.periods.detected_periods.length > 0}
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
              {/if}

              {#if tagSeasonality.decomposition?.variance_explained}
              {#let ve = tagSeasonality.decomposition.variance_explained}
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
              {/let}
              {/if}

              {#if tagSeasonality.pattern?.pattern?.length > 0}
              {#let pattern = tagSeasonality.pattern.pattern}
              {#let minVal = Math.min(...pattern.filter(v => v !== null))}
              {#let maxVal = Math.max(...pattern.filter(v => v !== null))}
              {#let range = maxVal - minVal}
              <div class="mb-3">
                <div class="text-xs text-neutral-600 dark:text-neutral-400 mb-2">
                  Типичный суточный паттерн:
                </div>
                <div class="p-2 bg-white dark:bg-neutral-900 rounded border border-neutral-200 dark:border-neutral-700">
                  <div class="text-xs text-neutral-600 dark:text-neutral-400 mb-1">
                    Мин: {minVal.toFixed(1)} | Макс: {maxVal.toFixed(1)} | Размах: {range.toFixed(1)}
                  </div>
                  <div class="flex items-end gap-0.5 h-16">
                    {#each pattern.slice(0, 48) as val, i}
                      {#if val !== null}
                        <div 
                          class="flex-1 bg-gradient-to-t from-purple-500 to-purple-400 rounded-t transition-all hover:from-purple-600 hover:to-purple-500"
                          style="height: {((val - minVal) / range) * 100}%"
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
              {/let}
              {/let}
              {/let}
              {/let}
              {/if}
            </div>
            {/if}
          {/each}
        </div>
        {/if}

'''

changes = []

# 【2】Вставляем seasonal для single-tag ПЕРЕД строкой 527 ({/if} который закрывает overview)
print('【2】Ищем место для вставки seasonal в single-tag')
print('-' * 80)

# Ищем строку 527: "      {/if}" которая находится перед "<!-- ==================== MULTI-TAG"
single_tag_insert_idx = None
for i in range(len(lines) - 1):
    if lines[i].strip() == '{/if}' and i + 1 < len(lines):
        if 'MULTI-TAG: CORRELATIONS' in lines[i + 1] or 'MULTI-TAG: CORRELATIONS' in lines[i + 2]:
            single_tag_insert_idx = i
            print(f'✅ Найдено место для single-tag: строка {i + 1}')
            break

if single_tag_insert_idx is not None:
    lines.insert(single_tag_insert_idx, seasonal_single_tag)
    changes.append(f'Seasonal single-tag вставлен на строке {single_tag_insert_idx + 1}')
    print(f'✅ Блок вставлен')
else:
    print('⚠️  Место для single-tag не найдено')

# 【3】Вставляем seasonal для multi-tag ПОСЛЕ строки с "{#if isMultiTag && activeTab === 'correlations'}"
print()
print('【3】Ищем место для вставки seasonal в multi-tag')
print('-' * 80)

# Ищем строку "{#if isMultiTag && activeTab === 'correlations'}"
multi_tag_insert_idx = None
for i, line in enumerate(lines):
    if "{#if isMultiTag && activeTab === 'correlations'}" in line:
        multi_tag_insert_idx = i + 1  # вставляем СЛЕДУЮЩЕЙ строкой после {#if}
        print(f'✅ Найдено место для multi-tag: строка {i + 1}')
        break

if multi_tag_insert_idx is not None:
    lines.insert(multi_tag_insert_idx, seasonal_multi_tag)
    changes.append(f'Seasonal multi-tag вставлен на строке {multi_tag_insert_idx + 1}')
    print(f'✅ Блок вставлен')
else:
    print('⚠️  Место для multi-tag не найдено')

# 【4】Сохраняем файл
print()
print('【4】Сохраняем файл')
print('-' * 80)
results_path.write_text(''.join(lines), encoding='utf-8', newline='\n')
print(f'✅ Файл сохранён ({len(lines)} строк)')

print()
print('=' * 80)
print('ЧТО СДЕЛАНО:')
print('=' * 80)
for change in changes:
    print(f'  • {change}')
print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Frontend перезагрузится автоматически')
print('2. Запусти анализ для single-tag:')
print('   → Должна появиться секция "Сезонность" после графика')
print('3. Запусти анализ для multi-tag (2+ тега):')
print('   → Должна появиться секция "Сезонный анализ" в начале вкладки "correlations"')
print('4. Кнопки zoom/reset должны работать без ошибок в консоли')