#!/usr/bin/env python3
"""
fix_sampled_undefined.py — точечный фикс для sampled/stats не определены
"""
from pathlib import Path

print('=' * 80)
print('ТОЧЕЧНЫЙ ФИКС: sampled/stats не определены')
print('=' * 80)
print()

results_path = Path('frontend/src/components/DeepAnalysisResults.svelte')
content = results_path.read_text(encoding='utf-8')

# Находим проблемный блок с minVal/maxVal/range
print('【1】Ищем блок с minVal/maxVal/range в single-tag')
print('-' * 80)

old_block = '''          {#if analysisResult.seasonality.pattern?.pattern?.length > 0}
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
          </div>'''

new_block = '''          {#if analysisResult.seasonality.pattern?.pattern?.length > 0}
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

if old_block in content:
    content = content.replace(old_block, new_block)
    print('✅ Блок заменён — sampled и stats теперь объявлены')
else:
    print('⚠️  Точный блок не найден, делаю line-by-line правки...')
    
    # Заменяем line-by-line
    replacements = [
        ('{@const minVal = Math.min(...pattern.filter(v => v !== null))}',
         '{@const sampled = samplePattern(pattern, 200)}'),
        ('{@const maxVal = Math.max(...pattern.filter(v => v !== null))}',
         '{@const stats = getPatternStats(pattern)}'),
        ('{@const range = maxVal - minVal}',
         ''),  # удалить
        ('Мин: {minVal.toFixed(1)} | Макс: {maxVal.toFixed(1)} | Размах: {range.toFixed(1)}',
         'Мин: {stats.min.toFixed(1)} | Макс: {stats.max.toFixed(1)} | Размах: {stats.range.toFixed(1)}'),
        ('{#if val !== null}',
         '{#if val !== null && stats.range > 0}'),
    ]
    
    for old, new in replacements:
        if old in content:
            content = content.replace(old, new, 1)  # только первое вхождение (single-tag)
            print(f'   ✅ Заменено: {old[:60]}...')
        else:
            print(f'   ℹ️  Не найдено (уже заменено?): {old[:60]}...')
    
    # Удаляем пустые строки с {@const range
    content = content.replace('\n          \n', '\n')

# ============================================================================
# 2. СОХРАНЯЕМ ФАЙЛ
# ============================================================================
print()
print('【2】Сохраняем файл')
print('-' * 80)
results_path.write_text(content, encoding='utf-8', newline='\n')
print('✅ Файл сохранён')

print()
print('=' * 80)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 80)
print()
print('1. ОШИБКА: ReferenceError: sampled is not defined')
print('   • Причина: в шаблоне использовались sampled и stats,')
print('     но они не были объявлены через {@const}')
print()
print('2. РЕШЕНИЕ:')
print('   • {@const sampled = samplePattern(pattern, 200)}')
print('   • {@const stats = getPatternStats(pattern)}')
print('   • Защита от деления на ноль: stats.range > 0')
print()
print('3. ТЕПЕРЬ:')
print('   • Для периода 2016 точек (7 дней) показывается 200 фаз')
print('   • Каждая ~10-я точка паттерна')
print('   • График имеет "волны" вместо прямой линии')
print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Frontend перезагрузится автоматически')
print('2. Запусти single-tag анализ')
print('3. Проверь что:')
print('   → Нет ошибки ReferenceError в консоли')
print('   → Паттерн показывает 200 фаз')
print('   → График имеет волны (не прямую линию)')