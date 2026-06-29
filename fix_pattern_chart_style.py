#!/usr/bin/env python3
"""
fix_pattern_chart_style.py - применяем единый стиль для графика паттерна
"""
from pathlib import Path

print('=' * 80)
print('ФИКС: Единый стиль для графика паттерна')
print('=' * 80)
print()

results_path = Path('frontend/src/components/DeepAnalysisResults.svelte')
content = results_path.read_text(encoding='utf-8')

# Ищем и исправляем single-tag pattern блок
print('【1】Исправляем single-tag pattern стиль')
print('-' * 80)

old_single = '''            <div class="p-2 bg-neutral-50 dark:bg-neutral-800 rounded border border-neutral-200 dark:border-neutral-700">
              <div class="text-xs text-neutral-600 dark:text-neutral-400 mb-1">
                Мин: {stats.min.toFixed(1)} | Макс: {stats.max.toFixed(1)} | Размах: {stats.range.toFixed(1)}
              </div>
              <div id={patternChartId} class="h-40 bg-white dark:bg-neutral-900 rounded">
                <Line data={patternData} options={{...timeSeriesOptions, plugins: {...timeSeriesOptions.plugins, legend: {display: false}}}} key={`pattern-single-${analysisResult?.analysis_id || 'default'}`} />
              </div>
            </div>'''

new_single = '''            <div class="text-xs text-neutral-600 dark:text-neutral-400 mb-2">
              Мин: {stats.min.toFixed(1)} | Макс: {stats.max.toFixed(1)} | Размах: {stats.range.toFixed(1)}
            </div>
            <div id={patternChartId} class="h-40 bg-white dark:bg-neutral-800 rounded border border-neutral-200 dark:border-neutral-700 p-3">
              <Line data={patternData} options={{...timeSeriesOptions, plugins: {...timeSeriesOptions.plugins, legend: {display: false}}}} key={`pattern-single-${analysisResult?.analysis_id || 'default'}`} />
            </div>'''

if old_single in content:
    content = content.replace(old_single, new_single)
    print('✅ Single-tag pattern стиль исправлен')
else:
    print('⚠️  Single-tag pattern блок не найден')

# Ищем и исправляем multi-tag pattern блок
print()
print('【2】Исправляем multi-tag pattern стиль')
print('-' * 80)

old_multi = '''                <div class="p-2 bg-white dark:bg-neutral-900 rounded border border-neutral-200 dark:border-neutral-700">
                  <div class="text-xs text-neutral-600 dark:text-neutral-400 mb-1">
                    Мин: {stats.min.toFixed(1)} | Макс: {stats.max.toFixed(1)} | Размах: {stats.range.toFixed(1)}
                  </div>
                  <div id={patternChartId} class="h-40 bg-white dark:bg-neutral-900 rounded">
                    <Line data={patternData} options={{...timeSeriesOptions, plugins: {...timeSeriesOptions.plugins, legend: {display: false}}}} key={`pattern-multi-${tagName}`} />
                  </div>
                </div>'''

new_multi = '''                <div class="text-xs text-neutral-600 dark:text-neutral-400 mb-2">
                  Мин: {stats.min.toFixed(1)} | Макс: {stats.max.toFixed(1)} | Размах: {stats.range.toFixed(1)}
                </div>
                <div id={patternChartId} class="h-40 bg-white dark:bg-neutral-800 rounded border border-neutral-200 dark:border-neutral-700 p-3">
                  <Line data={patternData} options={{...timeSeriesOptions, plugins: {...timeSeriesOptions.plugins, legend: {display: false}}}} key={`pattern-multi-${tagName}`} />
                </div>'''

if old_multi in content:
    content = content.replace(old_multi, new_multi)
    print('✅ Multi-tag pattern стиль исправлен')
else:
    print('⚠️  Multi-tag pattern блок не найден')

# Сохраняем файл
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
print('  График паттерна имел чёрную окантовку (dark:bg-neutral-900)')
print('  и серый фон (bg-neutral-50 dark:bg-neutral-800)')
print()
print('РЕШЕНИЕ:')
print('  Применили тот же стиль что у графика аномалий:')
print('  • bg-white dark:bg-neutral-800 - светлый фон в обоих темах')
print('  • border border-neutral-200 dark:border-neutral-700 - серый border')
print('  • p-3 - одинаковый padding')
print('  • rounded - скруглённые углы')
print()
print('РЕЗУЛЬТАТ:')
print('  • Единый стиль для всех графиков')
print('  • Нет чёрной окантовки')
print('  • Визуальная консистентность')
print()
print('=' * 80)