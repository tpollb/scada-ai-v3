#!/usr/bin/env python3
"""
apply_seasonal_fixes_final.py — финальные фиксы для seasonal визуализации
"""
from pathlib import Path
import re

print('=' * 80)
print('ФИНАЛЬНЫЕ ФИКСЫ: Seasonal визуализация')
print('=' * 80)
print()

results_path = Path('frontend/src/components/DeepAnalysisResults.svelte')
content = results_path.read_text(encoding='utf-8')

changes = []

# ============================================================================
# 1. ДОБАВЛЯЕМ ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ В <script> СЕКЦИЮ
# ============================================================================
print('【1】Добавляем функции samplePattern и getPatternStats в <script>')
print('-' * 80)

helper_functions = '''
  // === Seasonal analysis helpers ===
  function samplePattern(pattern: number[], maxPoints: number = 200): number[] {
    if (!pattern || pattern.length === 0) return []
    if (pattern.length <= maxPoints) return pattern
    const step = pattern.length / maxPoints
    const result: number[] = []
    for (let i = 0; i < maxPoints; i++) {
      result.push(pattern[Math.floor(i * step)])
    }
    return result
  }

  function getPatternStats(pattern: number[]) {
    const valid = pattern.filter((v: any) => v !== null && v !== undefined)
    if (valid.length === 0) return { min: 0, max: 0, range: 0 }
    const min = Math.min(...valid)
    const max = Math.max(...valid)
    return { min, max, range: max - min }
  }

  function formatPeriod(period: number): string {
    // 5-min sampling rate = 12 points/hour, 288/day, 2016/week
    if (period >= 270 && period <= 300) return '~24ч'
    if (period >= 560 && period <= 600) return '~12ч'
    if (period >= 1950 && period <= 2100) return '~7 дней'
    if (period >= 1400 && period <= 1500) return '~5 дней'
    if (period >= 1100 && period <= 1200) return '~4 дня'
    if (period >= 850 && period <= 900) return '~3 дня'
    if (period >= 570 && period <= 580) return '~2 дня'
    return `${period} точек`
  }
'''

# Ищем место перед "let isMultiTag = $derived" (после импортов и пропсов)
marker = "let isMultiTag = $derived("
if marker in content:
    content = content.replace(marker, helper_functions + '\n  ' + marker)
    changes.append('Добавлены helper функции (samplePattern, getPatternStats, formatPeriod)')
    print('✅ Helper функции добавлены')
else:
    print('⚠️  Маркер не найден')

# ============================================================================
# 2. ЗАМЕНЯЕМ pattern.slice(0, 48) НА samplePattern(pattern) В SINGLE-TAG
# ============================================================================
print()
print('【2】Заменяем pattern.slice(0, 48) на samplePattern(pattern)')
print('-' * 80)

# Single-tag pattern блок - используем samplePattern и getPatternStats
old_single_pattern = '''          {#if analysisResult.seasonality.pattern?.pattern}
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

new_single_pattern = '''          {#if analysisResult.seasonality.pattern?.pattern}
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
    changes.append('Single-tag pattern: samplePattern + getPatternStats')
    print('✅ Single-tag pattern обновлён')
else:
    print('⚠️  Single-tag pattern блок не найден (возможно уже обновлён)')

# ============================================================================
# 3. ЗАМЕНЯЕМ human-readable period в single-tag блоке
# ============================================================================
print()
print('【3】Заменяем хардкод "24ч/7 дней" на formatPeriod()')
print('-' * 80)

old_period_check = '''                    {period.period} точек
                    {#if period.period >= 280 && period.period <= 300}
                      <span class="text-xs text-neutral-500">(~24ч)</span>
                    {:else if period.period >= 2000 && period.period <= 2100}
                      <span class="text-xs text-neutral-500">(~7 дней)</span>
                    {/if}'''

new_period_check = '''                    {period.period} точек
                    <span class="text-xs text-neutral-500">({formatPeriod(period.period)})</span>'''

count = content.count(old_period_check)
if count > 0:
    content = content.replace(old_period_check, new_period_check)
    changes.append(f'Заменено {count} мест с хардкодом периодов на formatPeriod()')
    print(f'✅ Заменено {count} мест')
else:
    print('⚠️  Хардкод периодов не найден')

# ============================================================================
# 4. ВСТАВЛЯЕМ MULTI-TAG SEASONAL БЛОК ПЕРЕД ЗАКРЫВАЮЩИМ {/if} correlations
# ============================================================================
print()
print('【4】Вставляем multi-tag seasonal блок перед закрывающим {/if} correlations')
print('-' * 80)

# Ищем закрывающий {/if} multi-tag correlations блока
# Он должен быть перед строкой {#if isMultiTag && activeTab === 'table'}
table_marker = "      {#if isMultiTag && activeTab === 'table'}"
table_pos = content.find(table_marker)

if table_pos != -1:
    # Ищем ближайший {/if} ПЕРЕД table_marker
    search_region = content[:table_pos]
    last_if_close = search_region.rfind('{/if}')
    
    if last_if_close != -1:
        # Это закрывающий {/if} multi-tag correlations блока
        # Проверяем что перед ним есть отступ 6 пробелов (уровень блока)
        line_start = search_region.rfind('\n', 0, last_if_close) + 1
        indent_match = re.match(r'^(\s*)', search_region[line_start:last_if_close])
        indent = indent_match.group(1) if indent_match else '      '
        
        print(f'   Найдено закрывающее {{/if}} на позиции {last_if_close}')
        print(f'   Отступ: "{indent}" ({len(indent)} пробелов)')
        
        # Multi-tag seasonal блок
        seasonal_multitag = f'''
        <!-- Сезонный анализ (multi-tag) -->
        {indent}{{#if analysisResult?.seasonality && Object.keys(analysisResult.seasonality).length > 0}}
        {indent}<div class="mb-4">
        {indent}  <h3 class="text-sm font-semibold mb-3 flex items-center gap-2">
        {indent}    <Waves size={{16}} class="text-purple-500" />
        {indent}    Сезонный анализ ({{Object.keys(analysisResult.seasonality).length}} тегов)
        {indent}  </h3>
        {indent}  
        {indent}  {{#each Object.entries(analysisResult.seasonality) as [tagName, tagSeasonality]}}
        {indent}    {{#if tagSeasonality?.periods?.detected_periods?.length > 0}}
        {indent}    <div class="mb-4 p-3 bg-neutral-50 dark:bg-neutral-800 rounded border border-neutral-200 dark:border-neutral-700">
        {indent}      <h4 class="text-sm font-medium mb-2 text-neutral-700 dark:text-neutral-300">{{tagName}}</h4>
        {indent}      
        {indent}      <!-- Найденные периоды -->
        {indent}      <div class="mb-3">
        {indent}        <div class="text-xs text-neutral-600 dark:text-neutral-400 mb-2">Обнаруженные периоды:</div>
        {indent}        <div class="grid grid-cols-2 gap-2">
        {indent}          {{#each tagSeasonality.periods.detected_periods.slice(0, 4) as period}}
        {indent}            <div class="p-2 bg-purple-50 dark:bg-purple-900/20 rounded border border-purple-200 dark:border-purple-800">
        {indent}              <div class="text-xs text-neutral-600 dark:text-neutral-400">Период</div>
        {indent}              <div class="text-sm font-semibold text-purple-700 dark:text-purple-300">
        {indent}                {{period.period}} точек
        {indent}                <span class="text-xs text-neutral-500">({{formatPeriod(period.period)}})</span>
        {indent}              </div>
        {indent}              <div class="text-xs text-neutral-500 mt-1">
        {indent}                Уверенность: {{(period.confidence * 100).toFixed(0)}}%
        {indent}              </div>
        {indent}            </div>
        {indent}          {{/each}}
        {indent}        </div>
        {indent}      </div>
        {indent}
        {indent}      <!-- Variance explained -->
        {indent}      {{#if tagSeasonality.decomposition?.variance_explained}}
        {indent}        {{@const ve = tagSeasonality.decomposition.variance_explained}}
        {indent}        <div class="mb-3">
        {indent}          <div class="text-xs text-neutral-600 dark:text-neutral-400 mb-2">Распределение дисперсии:</div>
        {indent}          <div class="space-y-1">
        {indent}            <div class="flex items-center gap-2">
        {indent}              <div class="w-20 text-xs text-neutral-600 dark:text-neutral-400">Тренд:</div>
        {indent}              <div class="flex-1 bg-neutral-200 dark:bg-neutral-700 rounded-full h-4 overflow-hidden">
        {indent}                <div class="bg-blue-500 h-full" style="width: {{ve.trend}}%"></div>
        {indent}              </div>
        {indent}              <div class="w-12 text-xs text-right font-mono">{{ve.trend.toFixed(1)}}%</div>
        {indent}            </div>
        {indent}            <div class="flex items-center gap-2">
        {indent}              <div class="w-20 text-xs text-neutral-600 dark:text-neutral-400">Сезонность:</div>
        {indent}              <div class="flex-1 bg-neutral-200 dark:bg-neutral-700 rounded-full h-4 overflow-hidden">
        {indent}                <div class="bg-purple-500 h-full" style="width: {{ve.seasonal}}%"></div>
        {indent}              </div>
        {indent}              <div class="w-12 text-xs text-right font-mono">{{ve.seasonal.toFixed(1)}}%</div>
        {indent}            </div>
        {indent}            <div class="flex items-center gap-2">
        {indent}              <div class="w-20 text-xs text-neutral-600 dark:text-neutral-400">Остаток:</div>
        {indent}              <div class="flex-1 bg-neutral-200 dark:bg-neutral-700 rounded-full h-4 overflow-hidden">
        {indent}                <div class="bg-neutral-500 h-full" style="width: {{ve.residual}}%"></div>
        {indent}              </div>
        {indent}              <div class="w-12 text-xs text-right font-mono">{{ve.residual.toFixed(1)}}%</div>
        {indent}            </div>
        {indent}          </div>
        {indent}        </div>
        {indent}      {{/if}}
        {indent}
        {indent}      <!-- Типичный паттерн -->
        {indent}      {{#if tagSeasonality.pattern?.pattern?.length > 0}}
        {indent}        {{@const pattern = tagSeasonality.pattern.pattern}}
        {indent}        {{@const sampled = samplePattern(pattern, 200)}}
        {indent}        {{@const stats = getPatternStats(pattern)}}
        {indent}        <div class="mb-3">
        {indent}          <div class="text-xs text-neutral-600 dark:text-neutral-400 mb-2">
        {indent}            Типичный паттерн (период {{tagSeasonality.periods.detected_periods[0].period}} точек, показано {{sampled.length}} фаз):
        {indent}          </div>
        {indent}          <div class="p-2 bg-white dark:bg-neutral-900 rounded border border-neutral-200 dark:border-neutral-700">
        {indent}            <div class="text-xs text-neutral-600 dark:text-neutral-400 mb-1">
        {indent}              Мин: {{stats.min.toFixed(1)}} | Макс: {{stats.max.toFixed(1)}} | Размах: {{stats.range.toFixed(1)}}
        {indent}            </div>
        {indent}            <div class="flex items-end gap-0.5 h-20">
        {indent}              {{#each sampled as val, i}}
        {indent}                {{#if val !== null && stats.range > 0}}
        {indent}                  <div 
        {indent}                    class="flex-1 bg-gradient-to-t from-purple-500 to-purple-400 rounded-t transition-all hover:from-purple-600 hover:to-purple-500"
        {indent}                    style="height: {{((val - stats.min) / stats.range) * 100}}%"
        {indent}                    title="Фаза {{i}}: {{val.toFixed(1)}}"
        {indent}                  ></div>
        {indent}                {{/if}}
        {indent}              {{/each}}
        {indent}            </div>
        {indent}          </div>
        {indent}        </div>
        {indent}      {{/if}}
        {indent}    </div>
        {indent}    {{/if}}
        {indent}  {{/each}}
        {indent}</div>
        {indent}{{/if}}

'''
        
        # Вставляем seasonal блок ПЕРЕД закрывающим {/if} correlations
        content = content[:last_if_close] + seasonal_multitag + content[last_if_close:]
        changes.append('Добавлен multi-tag seasonal блок (перед закрытием correlations)')
        print('✅ Multi-tag seasonal блок вставлен')
    else:
        print('❌ Не найдено закрывающее {/if}')
else:
    print('❌ Table маркер не найден')

# ============================================================================
# 5. СОХРАНЯЕМ ФАЙЛ
# ============================================================================
print()
print('【5】Сохраняем файл')
print('-' * 80)
results_path.write_text(content, encoding='utf-8', newline='\n')
print(f'✅ Файл сохранён')

print()
print('=' * 80)
print('ЧТО СДЕЛАНО:')
print('=' * 80)
for change in changes:
    print(f'  • {change}')

print()
print('=' * 80)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 80)
print()
print('1. ПЛОСКИЙ ПАТТЕРН:')
print('   • Добавлена функция samplePattern(pattern, 200)')
print('   • Для периодов > 200 точек: равномерное сэмплирование')
print('   • Для периодов ≤ 200 точек: показываются все точки')
print('   • Период 2016 точек → 200 фаз (каждая ~10-я точка)')
print()
print('2. ПОЗИЦИЯ В MULTI-TAG:')
print('   • Seasonal блок теперь в КОНЦЕ correlations вкладки')
print('   • После графика временных рядов и сводки по аномалиям')
print('   • Перед закрытием {#if isMultiTag && activeTab === "correlations"}')
print()
print('3. ФОРМАТ ПЕРИОДА:')
print('   • Добавлена функция formatPeriod(period)')
print('   • Автоматически определяет: ~24ч, ~12ч, ~7 дней, ~5 дней, ~4 дня, ~3 дня, ~2 дня')
print('   • Работает для 5-минутного sampling rate (12 точек/час)')
print()
print('4. БЕЗОПАСНЫЕ ВЫЧИСЛЕНИЯ:')
print('   • Добавлена функция getPatternStats(pattern)')
print('   • Возвращает {min, max, range}')
print('   • Защита от деления на ноль: stats.range > 0')
print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Frontend перезагрузится автоматически')
print('2. Запусти анализ для single-tag с периодом 30 дней:')
print('   → Паттерн должен показывать 200 фаз (не 48)')
print('   → График должен иметь "волны" вместо прямой линии')
print('3. Запусти анализ для multi-tag:')
print('   → Seasonal блок должен быть ПОСЛЕ графика временных рядов')
print('   → Для каждого тега свой блок с паттерном')
print('4. Проверь что нет ошибок компиляции в консоли')