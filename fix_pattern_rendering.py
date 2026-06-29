#!/usr/bin/env python3
"""
fix_pattern_rendering.py — исправляем рендеринг паттерна (не сэмплировать короткие паттерны)
"""
from pathlib import Path

print('=' * 80)
print('ФИКС: Рендеринг паттерна (не сэмплировать короткие паттерны)')
print('=' * 80)
print()

results_path = Path('frontend/src/components/DeepAnalysisResults.svelte')
content = results_path.read_text(encoding='utf-8')

# ============================================================================
# 1. ИСПРАВЛЯЕМ SINGLE-TAG PATTERNS
# ============================================================================
print('【1】Исправляем single-tag pattern рендеринг')
print('-' * 80)

# Старый код с samplePattern
old_single = '''          {#if analysisResult.seasonality.pattern?.pattern?.length > 0}
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

# Новый код: показывать все точки если паттерн короткий
new_single = '''          {#if analysisResult.seasonality.pattern?.pattern?.length > 0}
          {@const pattern = analysisResult.seasonality.pattern.pattern}
          {@const stats = getPatternStats(pattern)}
          {@const useSampled = pattern.length > 500}
          {@const displayPattern = useSampled ? samplePattern(pattern, 200) : pattern}
          <div class="mb-3">
            <div class="text-xs text-neutral-600 dark:text-neutral-400 mb-2">
              Типичный паттерн (период {analysisResult.seasonality.periods.detected_periods[0].period} точек, показано {displayPattern.length} фаз):
            </div>
            <div class="p-2 bg-neutral-50 dark:bg-neutral-800 rounded border border-neutral-200 dark:border-neutral-700">
              <div class="text-xs text-neutral-600 dark:text-neutral-400 mb-1">
                Мин: {stats.min.toFixed(1)} | Макс: {stats.max.toFixed(1)} | Размах: {stats.range.toFixed(1)}
              </div>
              <div class="flex items-end gap-0.5 h-20">
                {#each displayPattern as val, i}
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

if old_single in content:
    content = content.replace(old_single, new_single)
    print('✅ Single-tag pattern исправлен')
else:
    print('⚠️  Single-tag pattern не найден')

# ============================================================================
# 2. ИСПРАВЛЯЕМ MULTI-TAG PATTERNS
# ============================================================================
print()
print('【2】Исправляем multi-tag pattern рендеринг')
print('-' * 80)

old_multi = '''              {#if tagSeasonality.pattern?.pattern?.length > 0}
              {@const pattern = tagSeasonality.pattern.pattern}
              {@const sampled = samplePattern(pattern, 200)}
              {@const stats = getPatternStats(pattern)}
              <div class="mb-3">
                <div class="text-xs text-neutral-600 dark:text-neutral-400 mb-2">
                  Типичный паттерн (период {tagSeasonality.periods.detected_periods[0].period} точек, показано {sampled.length} фаз):
                </div>
                <div class="p-2 bg-white dark:bg-neutral-900 rounded border border-neutral-200 dark:border-neutral-700">
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

new_multi = '''              {#if tagSeasonality.pattern?.pattern?.length > 0}
              {@const pattern = tagSeasonality.pattern.pattern}
              {@const stats = getPatternStats(pattern)}
              {@const useSampled = pattern.length > 500}
              {@const displayPattern = useSampled ? samplePattern(pattern, 200) : pattern}
              <div class="mb-3">
                <div class="text-xs text-neutral-600 dark:text-neutral-400 mb-2">
                  Типичный паттерн (период {tagSeasonality.periods.detected_periods[0].period} точек, показано {displayPattern.length} фаз):
                </div>
                <div class="p-2 bg-white dark:bg-neutral-900 rounded border border-neutral-200 dark:border-neutral-700">
                  <div class="text-xs text-neutral-600 dark:text-neutral-400 mb-1">
                    Мин: {stats.min.toFixed(1)} | Макс: {stats.max.toFixed(1)} | Размах: {stats.range.toFixed(1)}
                  </div>
                  <div class="flex items-end gap-0.5 h-20">
                    {#each displayPattern as val, i}
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

if old_multi in content:
    content = content.replace(old_multi, new_multi)
    print('✅ Multi-tag pattern исправлен')
else:
    print('⚠️  Multi-tag pattern не найден')

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
print('ПРОБЛЕМА:')
print('• samplePattern(pattern, 200) для паттерна длиной 294 точки')
print('  "размазывает" данные, сэмплируя каждую ~1.47 точку')
print('• Это превращает колебания в плавную линию')
print()
print('РЕШЕНИЕ:')
print('• Если паттерн ≤ 500 точек: показывать ВСЕ точки (без сэмплирования)')
print('• Если паттерн > 500 точек: использовать samplePattern(pattern, 200)')
print()
print('КОД:')
print('  {@const useSampled = pattern.length > 500}')
print('  {@const displayPattern = useSampled ? samplePattern(pattern, 200) : pattern}')
print('  {#each displayPattern as val, i} ... {/each}')
print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Frontend перезагрузится автоматически')
print('2. Запусти single-tag анализ (период 7 дней)')
print('3. Паттерн должен показывать 294 фаз (все точки)')
print('4. График должен иметь ЧЁТКИЕ волны (не плавную линию)')
print('5. Multi-tag — то же самое для каждого тега')