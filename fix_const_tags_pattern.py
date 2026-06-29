#!/usr/bin/env python3
"""
fix_const_tags_pattern.py — исправляем const_tag_invalid_placement в блоке pattern
"""
from pathlib import Path

print('=' * 80)
print('ФИКС: const_tag_invalid_placement в блоке сезонного паттерна')
print('=' * 80)
print()

results_path = Path('frontend/src/components/DeepAnalysisResults.svelte')
content = results_path.read_text(encoding='utf-8')

# Ищем проблемный блок
print('【1】Ищем блок с {@const pattern = ...}')
print('-' * 80)

old_block = '''          <!-- Типичный паттерн -->
          {#if analysisResult.seasonality.pattern?.pattern}
          <div class="mb-3">
            <div class="text-xs text-neutral-600 dark:text-neutral-400 mb-2">
              Типичный суточный паттерн (период {analysisResult.seasonality.periods.detected_periods[0].period} точек):
            </div>
            <div class="p-2 bg-neutral-50 dark:bg-neutral-800 rounded border border-neutral-200 dark:border-neutral-700">
              {@const pattern = analysisResult.seasonality.pattern.pattern}
              {@const minVal = Math.min(...pattern.filter(v => v !== null))}
              {@const maxVal = Math.max(...pattern.filter(v => v !== null))}
              {@const range = maxVal - minVal}
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
          {/if}'''

new_block = '''          <!-- Типичный паттерн -->
          {#if analysisResult.seasonality.pattern?.pattern}
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
          {/if}'''

if old_block in content:
    content = content.replace(old_block, new_block)
    results_path.write_text(content, encoding='utf-8', newline='\n')
    print('✅ Блок исправлен')
    print('   Все {@const} теги перемещены сразу после {#if}')
else:
    print('⚠️  Блок не найден в ожидаемом виде')
    # Попробуем найти частичное совпадение
    if '{@const pattern = analysisResult.seasonality.pattern.pattern}' in content:
        print('   Найден {@const pattern}, но структура отличается')

print()
print('=' * 80)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 80)
print()
print('Проблема: {@const} не может быть ребёнком <div> в Svelte 5')
print()
print('Было:')
print('  {#if condition}')
print('    <div>')
print('      {@const pattern = ...}  ← ОШИБКА')
print('      {@const minVal = ...}   ← ОШИБКА')
print('      {@const maxVal = ...}   ← ОШИБКА')
print()
print('Стало:')
print('  {#if condition}')
print('    {@const pattern = ...}    ← ПРАВИЛЬНО')
print('    {@const minVal = ...}     ← ПРАВИЛЬНО')
print('    {@const maxVal = ...}     ← ПРАВИЛЬНО')
print('    <div>')
print()
print('Примечание: {@const height = ...} внутри {#each} блока остаётся на месте,')
print('так как {#each} является допустимым родителем для {@const}')
print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('Frontend должен перезагрузиться автоматически.')
print('Ошибка компиляции должна исчезнуть.')