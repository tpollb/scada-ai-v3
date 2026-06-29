#!/usr/bin/env python3
"""
add_seasonal_visualization.py — добавляем визуализацию сезонности в DeepAnalysisResults
"""
from pathlib import Path

print('=' * 80)
print('ДОБАВЛЕНИЕ: Визуализация сезонности в DeepAnalysisResults.svelte')
print('=' * 80)
print()

results_path = Path('frontend/src/components/DeepAnalysisResults.svelte')
content = results_path.read_text(encoding='utf-8')

# 1. Вставка для single-tag (после блока График, перед закрывающим {/if})
print('【1】Добавляем секцию сезонности для single-tag')
print('-' * 80)

single_tag_marker = '''          </div>
        </div>
      {/if}

      <!-- ==================== MULTI-TAG: CORRELATIONS ==================== -->'''

seasonal_single_tag = '''          </div>
        </div>

        <!-- Сезонный анализ -->
        {#if analysisResult?.seasonality?.periods?.detected_periods?.length > 0}
        <div class="mb-4">
          <h3 class="text-sm font-semibold mb-2 flex items-center gap-2">
            <Waves size={16} class="text-purple-500" />
            Сезонность
          </h3>
          
          <!-- Найденные периоды -->
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

          <!-- Variance explained -->
          {#if analysisResult.seasonality.decomposition?.variance_explained}
          <div class="mb-3">
            <div class="text-xs text-neutral-600 dark:text-neutral-400 mb-2">Распределение дисперсии:</div>
            {@const ve = analysisResult.seasonality.decomposition.variance_explained}
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
          {/if}

          <!-- Типичный паттерн -->
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
          {/if}
        </div>
        {/if}
      {/if}

      <!-- ==================== MULTI-TAG: CORRELATIONS ==================== -->'''

if single_tag_marker in content:
    content = content.replace(single_tag_marker, seasonal_single_tag)
    print('✅ Секция сезонности добавлена для single-tag')
else:
    print('⚠️  Маркер для single-tag не найден')

# 2. Сохраняем файл
print()
print('【2】Сохраняем файл')
print('-' * 80)
results_path.write_text(content, encoding='utf-8', newline='\n')
print('✅ Файл сохранён')

print()
print('=' * 80)
print('ЧТО ДОБАВЛЕНО:')
print('=' * 80)
print()
print('Для single-tag анализа:')
print('  1. Блок "Сезонность" с иконкой Waves')
print('  2. Карточки найденных периодов (до 4 штук)')
print('     - Показывает количество точек и human-readable формат (~24ч, ~7 дней)')
print('     - Уверенность в процентах')
print('  3. Progress bars для variance explained:')
print('     - Тренд (синий)')
print('     - Сезонность (фиолетовый)')
print('     - Остаток (серый)')
print('  4. Визуализация типичного суточного паттерна:')
print('     - Bar chart с 48 фазами (первые 2 суток)')
print('     - Градиент от фиолетового к светло-фиолетовому')
print('     - Hover показывает точное значение')
print('     - Подпись времени: 00:00, 12:00, 24:00')
print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Frontend перезагрузится сам (если включён hot-reload)')
print('2. Запусти анализ для single-tag через UI')
print('3. В результатах должна появиться секция "Сезонность"')
print('4. Проверь что отображаются:')
print('   - Найденные периоды (294 точки ≈ 24ч)')
print('   - Variance explained (например: Trend 30%, Seasonal 55%, Residual 15%)')
print('   - Бар чарт типичного паттерна')