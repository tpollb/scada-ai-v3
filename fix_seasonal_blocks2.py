#!/usr/bin/env python3
"""
fix_seasonal_blocks.py — удаляем дублирующий multi-tag блок и исправляем single-tag
"""
from pathlib import Path

print('=' * 80)
print('ФИКС: Seasonal блоки в DeepAnalysisResults.svelte')
print('=' * 80)
print()

results_path = Path('frontend/src/components/DeepAnalysisResults.svelte')
content = results_path.read_text(encoding='utf-8')

# ============================================================================
# 1. УДАЛЯЕМ ПЕРВЫЙ MULTI-TAG SEASONAL БЛОК (дубль)
# ============================================================================
print('【1】Удаляем ПЕРВЫЙ multi-tag seasonal блок (дубль)')
print('-' * 80)

# Ищем начало первого блока
first_multi_start = content.find('        {#if isMultiTag && activeTab === \'correlations\'}\n\n          <!-- Сезонный анализ (multi-tag) -->')
if first_multi_start != -1:
    # Ищем конец этого блока — это строка перед scatter plot или вторым seasonal блоком
    # Ищем маркер конца первого блока
    first_multi_end_marker = '      <!-- ==================== MULTI-TAG: TABLE ==================== -->'
    first_multi_end = content.find(first_multi_end_marker, first_multi_start)
    
    if first_multi_end != -1:
        # Находим где заканчивается весь multi-tag correlations блок (перед table)
        # Ищем ближайший {/if} перед table маркером
        search_region = content[first_multi_start:first_multi_end]
        
        # Ищем последний {/if} в этом регионе
        last_if_pos = search_region.rfind('{/if}')
        
        if last_if_pos != -1:
            # Вырезаем весь регион от начала correlations до конца
            # Но оставляем маркер table
            content = content[:first_multi_start] + content[first_multi_end:]
            print('✅ ПЕРВЫЙ multi-tag seasonal блок удалён')
        else:
            print('⚠️  Не найдено закрывающее {/if}')
    else:
        print('⚠️  Не найден маркер конца блока')
else:
    print('⚠️  ПЕРВЫЙ multi-tag блок не найден')

# ============================================================================
# 2. ИСПРАВЛЯЕМ SINGLE-TAG SEASONAL БЛОК
# ============================================================================
print()
print('【2】Исправляем single-tag seasonal блок (slice(0, 48) → samplePattern)')
print('-' * 80)

# Заменяем блок с pattern.slice(0, 48) на правильный с samplePattern
old_single_pattern = '''          {#if analysisResult.seasonality.pattern?.pattern?.length > 0}
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
                                                    {/if}'''

new_single_pattern = '''          {#if analysisResult.seasonality.pattern?.pattern?.length > 0}
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

if old_single_pattern in content:
    content = content.replace(old_single_pattern, new_single_pattern)
    print('✅ Single-tag pattern исправлен (slice(0, 48) → samplePattern)')
else:
    print('⚠️  Single-tag pattern блок не найден (возможно уже исправлен)')

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
print('ЧТО СДЕЛАНО:')
print('=' * 80)
print()
print('1. УДАЛЁН ПЕРВЫЙ multi-tag seasonal блок:')
print('   • Был дублем ВТОРОГО блока')
print('   • Находился ПЕРЕД графиком временных рядов')
print('   • Использовал старый slice(0, 48)')
print()
print('2. ИСПРАВЛЕН single-tag seasonal блок:')
print('   • Заменено: pattern.slice(0, 48) → samplePattern(pattern, 200)')
print('   • Заменено: Math.min/max → getPatternStats(pattern)')
print('   • Теперь показывает 200 фаз вместо 48')
print('   • Для периода 2016 точек: каждая ~10-я точка → виден полный цикл')
print()
print('3. ВТОРОЙ multi-tag seasonal блок ОСТАЛСЯ:')
print('   • Находится ПОСЛЕ Scatter plot (правильное место)')
print('   • Использует samplePattern(pattern, 200)')
print('   • Корректно отображает паттерны')
print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Frontend перезагрузится автоматически')
print('2. Single-tag анализ (период 30 дней):')
print('   → Паттерн должен показывать 200 фаз')
print('   → График должен иметь "волны" вместо прямой линии')
print('3. Multi-tag анализ:')
print('   → Seasonal блок должен быть ТОЛЬКО ОДИН (после Scatter plot)')
print('   → НЕ должен дублироваться')
print('   → Для каждого тега свой корректный паттерн')