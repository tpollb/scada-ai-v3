#!/usr/bin/env python3
"""
fix_pattern_svg.py — заменяем flex-бары на SVG polyline (работает для любого количества точек)
"""
from pathlib import Path

print('=' * 80)
print('ФИКС: Паттерн через SVG (вместо flex-баров)')
print('=' * 80)
print()

results_path = Path('frontend/src/components/DeepAnalysisResults.svelte')
content = results_path.read_text(encoding='utf-8')

# ============================================================================
# 1. SINGLE-TAG: Заменяем паттерн блок на SVG
# ============================================================================
print('【1】Исправляем single-tag pattern (SVG)')
print('-' * 80)

# Ищем текущий блок паттерна в single-tag
# Начинается с "{@const pattern = analysisResult.seasonality.pattern.pattern}"
# Заканчивается закрывающим {/if} pattern блока

# Ищем начало single-tag seasonal блока
single_seasonal_start = content.find('<!-- Сезонный анализ -->\n        {#if analysisResult?.seasonality?.periods?.detected_periods?.length > 0}')
if single_seasonal_start == -1:
    single_seasonal_start = content.find('<!-- Сезонный анализ -->')

if single_seasonal_start != -1:
    # Ищем блок паттерна внутри single-tag seasonal
    pattern_start = content.find('{#if analysisResult.seasonality.pattern?.pattern?.length > 0}', single_seasonal_start)
    
    if pattern_start != -1:
        # Ищем конец этого {#if} блока
        # Нужно найти соответствующее {/if}
        search_region = content[pattern_start:]
        brace_count = 0
        pattern_end = None
        
        for i, char in enumerate(search_region):
            if search_region[i:i+3] == '{#i':
                brace_count += 1
            elif search_region[i:i+4] == '{/if':
                brace_count -= 1
                if brace_count == 0:
                    pattern_end = pattern_start + i + 4
                    break
        
        if pattern_end:
            # Вырезаем старый блок паттерна
            old_pattern_block = content[pattern_start:pattern_end]
            
            # Создаём новый SVG блок
            new_pattern_block = '''{#if analysisResult.seasonality.pattern?.pattern?.length > 0}
          {@const pattern = analysisResult.seasonality.pattern.pattern}
          {@const stats = getPatternStats(pattern)}
          <div class="mb-3">
            <div class="text-xs text-neutral-600 dark:text-neutral-400 mb-2">
              Типичный паттерн (период {analysisResult.seasonality.periods.detected_periods[0].period} точек):
            </div>
            <div class="p-2 bg-neutral-50 dark:bg-neutral-800 rounded border border-neutral-200 dark:border-neutral-700">
              <div class="text-xs text-neutral-600 dark:text-neutral-400 mb-1">
                Мин: {stats.min.toFixed(1)} | Макс: {stats.max.toFixed(1)} | Размах: {stats.range.toFixed(1)}
              </div>
              <div class="relative h-24">
                <svg viewBox="0 0 {pattern.length} 100" preserveAspectRatio="none" class="w-full h-full">
                  <!-- Фоновая сетка -->
                  <line x1="0" y1="50" x2="{pattern.length}" y2="50" stroke="currentColor" stroke-opacity="0.1" stroke-dasharray="4,4" />
                  
                  <!-- Линия паттерна -->
                  <polyline
                    fill="none"
                    stroke="rgb(168, 85, 247)"
                    stroke-width="2"
                    vector-effect="non-scaling-stroke"
                    points="{pattern.filter(v => v !== null).map((v, i) => `${i},${100 - ((v - stats.min) / stats.range) * 100}`).join(' ')}"
                  />
                  
                  <!-- Точки для тултипов (каждая 6-я чтобы не перегружать) -->
                  {#each pattern.filter((v, i) => v !== null && i % 6 === 0) as val, idx}
                    {@const i = idx * 6}
                    {@const y = 100 - ((val - stats.min) / stats.range) * 100}
                    <circle
                      cx="{i}"
                      cy="{y}"
                      r="3"
                      fill="rgb(168, 85, 247)"
                      class="hover:fill-purple-700 cursor-pointer"
                      vector-effect="non-scaling-stroke"
                    >
                      <title>Фаза {i}: {val.toFixed(1)}</title>
                    </circle>
                  {/each}
                </svg>
                
                <!-- Подписи времени -->
                <div class="flex justify-between text-xs text-neutral-500 mt-1">
                  <span>0</span>
                  <span>{Math.floor(pattern.length / 4)}</span>
                  <span>{Math.floor(pattern.length / 2)}</span>
                  <span>{Math.floor(pattern.length * 3 / 4)}</span>
                  <span>{pattern.length}</span>
                </div>
              </div>
            </div>
          </div>
          {/if}'''
            
            # Заменяем старый блок на новый
            content = content[:pattern_start] + new_pattern_block + content[pattern_end:]
            print('✅ Single-tag pattern заменён на SVG')
        else:
            print('⚠️  Не найден конец single-tag pattern блока')
    else:
        print('⚠️  Single-tag pattern блок не найден')
else:
    print('⚠️  Single-tag seasonal блок не найден')

# ============================================================================
# 2. MULTI-TAG: То же самое
# ============================================================================
print()
print('【2】Исправляем multi-tag pattern (SVG)')
print('-' * 80)

# Ищем multi-tag seasonal блок
multi_seasonal_start = content.find('<!-- Сезонный анализ (multi-tag) -->')

if multi_seasonal_start != -1:
    # Ищем блок паттерна внутри multi-tag seasonal
    # В multi-tag он начинается с "{#if tagSeasonality.pattern?.pattern?.length > 0}"
    pattern_start = content.find('{#if tagSeasonality.pattern?.pattern?.length > 0}', multi_seasonal_start)
    
    if pattern_start != -1:
        # Ищем конец этого {#if} блока
        search_region = content[pattern_start:]
        brace_count = 0
        pattern_end = None
        
        for i, char in enumerate(search_region):
            if search_region[i:i+3] == '{#i':
                brace_count += 1
            elif search_region[i:i+4] == '{/if':
                brace_count -= 1
                if brace_count == 0:
                    pattern_end = pattern_start + i + 4
                    break
        
        if pattern_end:
            # Создаём новый SVG блок для multi-tag
            new_multi_pattern_block = '''{#if tagSeasonality.pattern?.pattern?.length > 0}
              {@const pattern = tagSeasonality.pattern.pattern}
              {@const stats = getPatternStats(pattern)}
              <div class="mb-3">
                <div class="text-xs text-neutral-600 dark:text-neutral-400 mb-2">
                  Типичный паттерн (период {tagSeasonality.periods.detected_periods[0].period} точек):
                </div>
                <div class="p-2 bg-white dark:bg-neutral-900 rounded border border-neutral-200 dark:border-neutral-700">
                  <div class="text-xs text-neutral-600 dark:text-neutral-400 mb-1">
                    Мин: {stats.min.toFixed(1)} | Макс: {stats.max.toFixed(1)} | Размах: {stats.range.toFixed(1)}
                  </div>
                  <div class="relative h-24">
                    <svg viewBox="0 0 {pattern.length} 100" preserveAspectRatio="none" class="w-full h-full">
                      <!-- Фоновая сетка -->
                      <line x1="0" y1="50" x2="{pattern.length}" y2="50" stroke="currentColor" stroke-opacity="0.1" stroke-dasharray="4,4" />
                      
                      <!-- Линия паттерна -->
                      <polyline
                        fill="none"
                        stroke="rgb(168, 85, 247)"
                        stroke-width="2"
                        vector-effect="non-scaling-stroke"
                        points="{pattern.filter(v => v !== null).map((v, i) => `${i},${100 - ((v - stats.min) / stats.range) * 100}`).join(' ')}"
                      />
                      
                      <!-- Точки для тултипов (каждая 6-я) -->
                      {#each pattern.filter((v, i) => v !== null && i % 6 === 0) as val, idx}
                        {@const i = idx * 6}
                        {@const y = 100 - ((val - stats.min) / stats.range) * 100}
                        <circle
                          cx="{i}"
                          cy="{y}"
                          r="3"
                          fill="rgb(168, 85, 247)"
                          class="hover:fill-purple-700 cursor-pointer"
                          vector-effect="non-scaling-stroke"
                        >
                          <title>Фаза {i}: {val.toFixed(1)}</title>
                        </circle>
                      {/each}
                    </svg>
                    
                    <!-- Подписи -->
                    <div class="flex justify-between text-xs text-neutral-500 mt-1">
                      <span>0</span>
                      <span>{Math.floor(pattern.length / 4)}</span>
                      <span>{Math.floor(pattern.length / 2)}</span>
                      <span>{Math.floor(pattern.length * 3 / 4)}</span>
                      <span>{pattern.length}</span>
                    </div>
                  </div>
                </div>
              </div>
              {/if}'''
            
            # Заменяем старый блок на новый
            content = content[:pattern_start] + new_multi_pattern_block + content[pattern_end:]
            print('✅ Multi-tag pattern заменён на SVG')
        else:
            print('⚠️  Не найден конец multi-tag pattern блока')
    else:
        print('⚠️  Multi-tag pattern блок не найден')
else:
    print('⚠️  Multi-tag seasonal блок не найден')

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
print('• 294 бара с flex-1 не помещаются на экран')
print('• Бары сжимаются до 0px → плоская линия')
print('• Тултипы не работают')
print()
print('РЕШЕНИЕ: SVG polyline вместо flex-баров')
print('• SVG viewBox масштабирует все точки под ширину контейнера')
print('• preserveAspectRatio="none" растягивает график по ширине')
print('• vector-effect="non-scaling-stroke" — линия всегда 2px')
print('• SVG <circle> элементы с <title> для тултипов')
print('• Каждая 6-я точка имеет тултип (чтобы не перегружать)')
print()
print('РЕЗУЛЬТАТ:')
print('• Чёткая линия паттерна (не плоская)')
print('• Волны видны для 294 точек')
print('• Hover на точки → тултип "Фаза X: Y"')
print('• Подписи 0, 25%, 50%, 75%, 100% под графиком')
print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Frontend перезагрузится автоматически')
print('2. Запусти анализ (single или multi-tag)')
print('3. Паттерн должен показать ЛИНИЮ с волнами (не бары)')
print('4. Hover на фиолетовые точки → тултип "Фаза X: Y"')
print('5. График масштабируется под ширину контейнера')