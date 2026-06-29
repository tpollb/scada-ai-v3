#!/usr/bin/env python3
"""
fix_pattern_display.py — исправляем отображение длинных паттернов
"""
from pathlib import Path

print('=' * 80)
print('ФИКС: Отображение длинных паттернов (294 фазы)')
print('=' * 80)
print()

results_path = Path('frontend/src/components/DeepAnalysisResults.svelte')
content = results_path.read_text(encoding='utf-8')

# ============================================================================
# 1. SINGLE-TAG: Заменяем flex-1 на фиксированную ширину с горизонтальным скроллом
# ============================================================================
print('【1】Исправляем single-tag pattern отображение')
print('-' * 80)

old_single = '''              <div class="flex items-end gap-0.5 h-20">
                {#each displayPattern as val, i}
                  {#if val !== null && stats.range > 0}
                    <div
                      class="flex-1 bg-gradient-to-t from-purple-500 to-purple-400 rounded-t transition-all hover:from-purple-600 hover:to-purple-500"
                      style="height: {((val - stats.min) / stats.range) * 100}%"
                      title="Фаза {i}: {val.toFixed(1)}"
                    ></div>
                  {/if}
                {/each}
              </div>'''

new_single = '''              <div class="overflow-x-auto">
                <div class="flex items-end gap-px h-20" style="min-width: {Math.max(displayPattern.length * 3, 100)}px">
                  {#each displayPattern as val, i}
                    {#if val !== null && stats.range > 0}
                      <div
                        class="bg-gradient-to-t from-purple-500 to-purple-400 transition-all hover:from-purple-600 hover:to-purple-500"
                        style="width: 3px; min-width: 3px; height: {((val - stats.min) / stats.range) * 100}%"
                        title="Фаза {i}: {val.toFixed(1)}"
                      ></div>
                    {/if}
                  {/each}
                </div>
              </div>'''

if old_single in content:
    content = content.replace(old_single, new_single)
    print('✅ Single-tag pattern исправлен')
else:
    print('⚠️  Single-tag pattern не найден')

# ============================================================================
# 2. MULTI-TAG: То же самое
# ============================================================================
print()
print('【2】Исправляем multi-tag pattern отображение')
print('-' * 80)

old_multi = '''                  <div class="flex items-end gap-0.5 h-20">
                    {#each displayPattern as val, i}
                      {#if val !== null && stats.range > 0}
                        <div
                          class="flex-1 bg-gradient-to-t from-purple-500 to-purple-400 rounded-t transition-all hover:from-purple-600 hover:to-purple-500"
                          style="height: {((val - stats.min) / stats.range) * 100}%"
                          title="Фаза {i}: {val.toFixed(1)}"
                        ></div>
                      {/if}
                    {/each}
                  </div>'''

new_multi = '''                  <div class="overflow-x-auto">
                    <div class="flex items-end gap-px h-20" style="min-width: {Math.max(displayPattern.length * 3, 100)}px">
                      {#each displayPattern as val, i}
                        {#if val !== null && stats.range > 0}
                          <div
                            class="bg-gradient-to-t from-purple-500 to-purple-400 transition-all hover:from-purple-600 hover:to-purple-500"
                            style="width: 3px; min-width: 3px; height: {((val - stats.min) / stats.range) * 100}%"
                            title="Фаза {i}: {val.toFixed(1)}"
                          ></div>
                        {/if}
                      {/each}
                    </div>
                  </div>'''

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
print('• 294 бара с flex-1 и gap-0.5 (2px)')
print('• Gap = 294 × 2px = 588px (больше ширины контейнера)')
print('• Бары сжимались до 0px → выглядели как плоская линия')
print()
print('РЕШЕНИЕ:')
print('• overflow-x-auto — горизонтальный скролл для длинных паттернов')
print('• Фиксированная ширина: 3px на бар')
print('• Gap-px (1px) между барами')
print('• min-width: pattern.length × 3px')
print('• Для 294 фаз: 294 × (3+1) = 1176px → скролл в контейнере ~800px')
print()
print('РЕЗУЛЬТАТ:')
print('• Волны видны чётко (каждый бар 3px шириной)')
print('• При hover — tooltip "Фаза X: Y"')
print('• Горизонтальный скролл для длинных паттернов')
print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Frontend перезагрузится автоматически')
print('2. Запусти анализ (single или multi-tag)')
print('3. Паттерн должен показать ЧЁТКИЕ волны')
print('4. Горизонтальный скролл для длинных паттернов')
print('5. Hover на бары → tooltip "Фаза X: Y"')