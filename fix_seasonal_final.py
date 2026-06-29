#!/usr/bin/env python3
"""
fix_seasonal_final.py — точечные фиксы для seasonal визуализации
"""
from pathlib import Path

print('=' * 80)
print('ТОЧЕЧНЫЕ ФИКСЫ: Seasonal визуализация')
print('=' * 80)
print()

results_path = Path('frontend/src/components/DeepAnalysisResults.svelte')
content = results_path.read_text(encoding='utf-8')

# ============================================================================
# 1. УДАЛЯЕМ ЛИШНЮЮ </div> ПОСЛЕ {#if isMultiTag && activeTab === 'correlations'}
# ============================================================================
print('【1】Удаляем лишнюю </div>')
print('-' * 80)

old_multitag_start = '''      <!-- ==================== MULTI-TAG: CORRELATIONS ==================== -->
      {#if isMultiTag && activeTab === 'correlations'}
        </div>

        <!-- 2. Scatter plot (интерактивный) -->'''

new_multitag_start = '''      <!-- ==================== MULTI-TAG: CORRELATIONS ==================== -->
      {#if isMultiTag && activeTab === 'correlations'}
        <!-- 2. Scatter plot (интерактивный) -->'''

if old_multitag_start in content:
    content = content.replace(old_multitag_start, new_multitag_start)
    print('✅ Лишняя </div> удалена')
else:
    print('⚠️  Блок не найден')

# ============================================================================
# 2. ИСПРАВЛЯЕМ SINGLE-TAG ПАТТЕРН БЛОК
# ============================================================================
print()
print('【2】Исправляем single-tag паттерн блок')
print('-' * 80)

old_pattern = '''          {#if analysisResult.seasonality.pattern?.pattern?.length > 0}
          {@const pattern = analysisResult.seasonality.pattern.pattern}
          {@const minVal = Math.min(...pattern.filter(v => v !== null))}
          {@const maxVal = Math.max(...pattern.filter(v => v !== null))}
          {@const range = maxVal - minVal}
          <div class="mb-3">
            <div class="text-xs text-neutral-600 dark:text-neutral-400 mb-2">
              Типичный суточный паттерн (период {analysisResult.seasonality.periods.detected_periods[0].period} точек):
            </div>
            <div class="p-2 bg-neutral-50 dark:bg-neutral-800 rounded border border-neutral-200 dark:border-neutral-700">
              <div class="text-xs text-neutral-600 dark:text-neutral-400 mb-1">
                Мин: {minVal.toFixed(1)} | Макс: {maxVal.toFixed(1)} | Размах: {range.toFixed(1)}
              </div>
              <div class="flex items-end gap-0.5 h-16">
                {#each sampled as val, i}
                  {#if val !== null}
                    <div
                      class="flex-1 bg-gradient-to-t from-purple-500 to-purple-400 rounded-t transition-all hover:from-purple-600 hover:to-purple-500"
                      style="height: {((val - stats.min) / stats.range) * 100}%"
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
                                                  {/if}'''

new_pattern = '''          {#if analysisResult.seasonality.pattern?.pattern?.length > 0}
            {@const pattern = analysisResult.seasonality.pattern.pattern}
            {@const sampled = samplePattern(pattern, 200)}
            {@const stats = getPatternStats(pattern)}
            <div class="mb-3">
              <div class="text-xs text-neutral-600 dark:text-neutral-400 mb-2">
                Типичный паттерн (период {analysisResult.seasonality.periods.detected_periods[0].period} точек, показано {sampled.length} фаз):
              </div>
              <div class="p-2 bg-neutral-50 dark:bg-neutral-800 rounded border border-neutral-200 dark:border-neutral-700">
                <div class="text-xs text-neutral-600 dark:text-neutral-400 mb-1">
                  Мин: {stats.min.toFixed(1)} | Макс: {stats.max.toFixed(1)} | Размах: {stats.range.toFixed(1)}
                </div>
                <div class="flex items-end gap-0.5 h-20">
                  {#each sampled as val, i}
                    {#if val !== null && stats.range > 0}
                      <div
                        class="flex-1 bg-gradient-to-t from-purple-500 to-purple-400 rounded-t transition-all hover:from-purple-600 hover:to-purple-500"
                        style="height: {((val - stats.min) / stats.range) * 100}%"
                        title="Фаза {i}: {val.toFixed(1)}"
                      ></div>
                    {/if}
                  {/each}
                </div>
              </div>
            </div>
          {/if}'''

if old_pattern in content:
    content = content.replace(old_pattern, new_pattern)
    print('✅ Single-tag паттерн исправлен')
    print('   • Добавлен: {@const sampled = samplePattern(pattern, 200)}')
    print('   • Добавлен: {@const stats = getPatternStats(pattern)}')
    print('   • Теперь используется stats.min/stats.max/stats.range')
else:
    print('⚠️  Паттерн блок не найден')

# ============================================================================
# 3. СОХРАНЯЕМ ФАЙЛ
# ============================================================================
print()
print('【3】Сохраняем файл')
print('-' * 80)
results_path.write_text(content, encoding='utf-8', newline='\n')
print('✅ Файл сохранён')

print()
print('=' * 80)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 80)
print()
print('1. ЛИШНЯЯ </div>:')
print('   • Удалена закрывающая </div> после {#if isMultiTag && activeTab === "correlations"}')
print('   • Она вызывала ошибку element_invalid_closing_tag')
print()
print('2. SINGLE-TAG ПАТТЕРН:')
print('   • Добавлены переменные: sampled и stats через {@const}')
print('   • Используется samplePattern(pattern, 200) — показывает 200 фаз')
print('   • Используется getPatternStats(pattern) — безопасное вычисление min/max/range')
print('   • Теперь для периода 2016 точек виден полный 7-дневный цикл')
print()
print('3. MULTI-TAG SEASONAL БЛОК:')
print('   • Остаётся ОДИН блок (после Scatter plot)')
print('   • Он уже корректный и использует samplePattern')
print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Frontend перезагрузится автоматически')
print('2. Single-tag анализ (период 30 дней):')
print('   → Паттерн должен показывать 200 фаз')
print('   → График должен иметь "волны" (не прямую линию)')
print('3. Multi-tag анализ:')
print('   → Seasonal блок только ОДИН (после Scatter plot)')
print('   → Нет ошибки element_invalid_closing_tag')
print('4. Проверь что нет ошибок компиляции в консоли')