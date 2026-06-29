#!/usr/bin/env python3
"""
final_fix_complete.py — финальный фикс: перемещение multi-tag seasonal + исправление паттерна
"""
from pathlib import Path
import re

print('=' * 80)
print('ФИНАЛЬНЫЙ ПОЛНЫЙ ФИКС: Перемещение + исправление паттерна')
print('=' * 80)
print()

results_path = Path('frontend/src/components/DeepAnalysisResults.svelte')
lines = results_path.read_text(encoding='utf-8').splitlines(keepends=True)

print(f'【1】Прочитано {len(lines)} строк')

# ============================================================================
# 2. НАХОДИМ ТОЧНЫЕ ГРАНИЦЫ MULTI-TAG SEASONAL БЛОКА
# ============================================================================
print()
print('【2】Ищем границы multi-tag seasonal блока')
print('-' * 80)

seasonal_start = None
seasonal_end = None

for i, line in enumerate(lines):
    if '<!-- Сезонный анализ (multi-tag) -->' in line:
        seasonal_start = i
        print(f'   Начало: строка {i + 1}')
    
    if seasonal_start and '<!-- 0. Time series с аномалиями (если есть) -->' in line:
        # Ищем ближайшее {/if} перед этим
        for j in range(i - 1, seasonal_start, -1):
            if lines[j].strip() == '{/if}':
                seasonal_end = j
                print(f'   Конец: строка {j + 1}')
                break
        break

if seasonal_start is None or seasonal_end is None:
    print('❌ Не удалось найти границы multi-tag seasonal блока')
    exit(1)

# Вырезаем multi-tag seasonal блок (включая пустую строку перед Time series)
multi_tag_seasonal_block = lines[seasonal_start:seasonal_end + 1]
print(f'   Вырезано {len(multi_tag_seasonal_block)} строк')

# ============================================================================
# 3. ИСПРАВЛЯЕМ РЕНДЕРИНГ ПАТТЕРНА В MULTI-TAG SEASONAL
# ============================================================================
print()
print('【3】Исправляем рендеринг паттерна в multi-tag seasonal')
print('-' * 80)

multi_tag_seasonal_text = ''.join(multi_tag_seasonal_block)

# Заменяем старый код на новый
old_pattern_code = '''              {#if tagSeasonality.pattern?.pattern?.length > 0}
              {@const pattern = tagSeasonality.pattern.pattern}
              {@const minVal = Math.min(...pattern.filter(v => v !== null))}
              {@const maxVal = Math.max(...pattern.filter(v => v !== null))}
              {@const range = maxVal - minVal}
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
              </div>'''

new_pattern_code = '''              {#if tagSeasonality.pattern?.pattern?.length > 0}
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
              </div>'''

if old_pattern_code in multi_tag_seasonal_text:
    multi_tag_seasonal_text = multi_tag_seasonal_text.replace(old_pattern_code, new_pattern_code)
    print('✅ Multi-tag паттерн исправлен')
else:
    print('⚠️  Старый паттерн не найден (возможно уже исправлен)')

# Заменяем хардкод периодов на formatPeriod
old_period_harcode = '''                        {period.period} точек
                        {#if period.period >= 280 && period.period <= 300}
                          <span class="text-xs text-neutral-500">(~24ч)</span>
                        {:else if period.period >= 2000 && period.period <= 2100}
                          <span class="text-xs text-neutral-500">(~7 дней)</span>
                        {/if}'''

new_period_format = '''                        {period.period} точек
                        <span class="text-xs text-neutral-500">({formatPeriod(period.period)})</span>'''

if old_period_harcode in multi_tag_seasonal_text:
    multi_tag_seasonal_text = multi_tag_seasonal_text.replace(old_period_harcode, new_period_format)
    print('✅ Multi-tag формат периода исправлен')

# ============================================================================
# 4. НАХОДИМ МЕСТО ДЛЯ ВСТАВКИ MULTI-TAG SEASONAL (ПОСЛЕ TIME SERIES)
# ============================================================================
print()
print('【4】Ищем место для вставки multi-tag seasonal (после Time series)')
print('-' * 80)

insert_position = None
for i, line in enumerate(lines):
    if '<!-- 1. Матрица корреляций (кликабельная!) -->' in line:
        insert_position = i
        print(f'   Вставка перед строкой {i + 1}')
        break

if insert_position is None:
    print('❌ Не найдено место для вставки')
    exit(1)

# ============================================================================
# 5. УДАЛЯЕМ СТАРЫЙ MULTI-TAG SEASONAL БЛОК
# ============================================================================
print()
print('【5】Удаляем старый multi-tag seasonal блок')
print('-' * 80)

del lines[seasonal_start:seasonal_end + 1]
print(f'✅ Удалено {seasonal_end + 1 - seasonal_start} строк')

# Обновляем insert_position (так как удалили строки)
if insert_position > seasonal_start:
    insert_position -= (seasonal_end + 1 - seasonal_start)

# ============================================================================
# 6. ВСТАВЛЯЕМ ИСПРАВЛЕННЫЙ MULTI-TAG SEASONAL
# ============================================================================
print()
print('【6】Вставляем исправленный multi-tag seasonal после Time series')
print('-' * 80)

new_multi_tag_lines = multi_tag_seasonal_text.splitlines(keepends=True)
lines[insert_position:insert_position] = ['\n'] + new_multi_tag_lines + ['\n']
print(f'✅ Вставлено {len(new_multi_tag_lines)} строк')

# ============================================================================
# 7. ИСПРАВЛЯЕМ SINGLE-TAG SEASONAL ПАТТЕРН
# ============================================================================
print()
print('【7】Исправляем single-tag seasonal паттерн')
print('-' * 80)

# Ищем single-tag seasonal блок
single_seasonal_start = None
for i, line in enumerate(lines):
    if '<!-- Сезонный анализ -->' in line and i < 700:
        single_seasonal_start = i
        break

if single_seasonal_start:
    # Ищем конец блока
    for i in range(single_seasonal_start, min(single_seasonal_start + 200, len(lines))):
        if lines[i].strip() == '{/if}' and i > single_seasonal_start + 50:
            # Это конец seasonal блока
            single_seasonal_end = i
            
            # Заменяем содержимое
            single_block = ''.join(lines[single_seasonal_start:single_seasonal_end + 1])
            
            # Паттерн для single-tag
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
          </div>'''
            
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
          </div>'''
            
            if old_single_pattern in single_block:
                single_block = single_block.replace(old_single_pattern, new_single_pattern)
                print('✅ Single-tag паттерн исправлен')
            else:
                print('⚠️  Single-tag паттерн не найден')
            
            # Заменяем хардкод периодов
            old_single_period = '''                    {period.period} точек
                    {#if period.period >= 280 && period.period <= 300}
                      <span class="text-xs text-neutral-500">(~24ч)</span>
                    {:else if period.period >= 2000 && period.period <= 2100}
                      <span class="text-xs text-neutral-500">(~7 дней)</span>
                    {/if}'''
            
            new_single_period = '''                    {period.period} точек
                    <span class="text-xs text-neutral-500">({formatPeriod(period.period)})</span>'''
            
            if old_single_period in single_block:
                single_block = single_block.replace(old_single_period, new_single_period)
                print('✅ Single-tag формат периода исправлен')
            
            # Обновляем lines
            new_single_lines = single_block.splitlines(keepends=True)
            lines[single_seasonal_start:single_seasonal_end + 1] = new_single_lines
            break

# ============================================================================
# 8. СОХРАНЯЕМ ФАЙЛ
# ============================================================================
print()
print('【8】Сохраняем файл')
print('-' * 80)
results_path.write_text(''.join(lines), encoding='utf-8', newline='\n')
print(f'✅ Файл сохранён ({len(lines)} строк)')

print()
print('=' * 80)
print('ЧТО СДЕЛАНО:')
print('=' * 80)
print()
print('1. MULTI-TAG SEASONAL ПЕРЕМЕЩЁН:')
print('   • Было: перед графиком временных рядов')
print('   • Стало: после графика временных рядов (со сводкой аномалий)')
print('   • Теперь порядок: Time series → Seasonal → Матрица корреляций → Scatter')
print()
print('2. SINGLE-TAG ПАТТЕРН ИСПРАВЛЕН:')
print('   • pattern.slice(0, 48) → samplePattern(pattern, 200)')
print('   • minVal/maxVal/range → stats.min/stats.max/stats.range')
print('   • Защита от деления на ноль: stats.range > 0')
print('   • Хардкод периодов → formatPeriod(period.period)')
print()
print('3. MULTI-TAG ПАТТЕРН ИСПРАВЛЕН:')
print('   • Те же исправления что и для single-tag')
print('   • Теперь оба используют samplePattern(pattern, 200)')
print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Frontend перезагрузится автоматически')
print('2. Single-tag анализ:')
print('   → Паттерн показывает 200 фаз (не 48)')
print('   → График имеет "волны" вместо прямой линии')
print('3. Multi-tag анализ:')
print('   → Порядок: Time series → Seasonal → Матрица → Scatter')
print('   → Для каждого тега свой корректный паттерн')
print('4. Нет ошибок компиляции')