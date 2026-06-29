#!/usr/bin/env python3
"""
fix_const_tag_error.py — исправляем ошибку const_tag_invalid_placement
"""
from pathlib import Path

print('=' * 80)
print('ФИКС: Ошибка const_tag_invalid_placement в DeepAnalysisResults.svelte')
print('=' * 80)
print()

results_path = Path('frontend/src/components/DeepAnalysisResults.svelte')
content = results_path.read_text(encoding='utf-8')

# Ищем проблемный блок
print('【1】Ищем блок с {@const ve = ...}')
print('-' * 80)

old_block = '''          <!-- Variance explained -->
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
          {/if}'''

new_block = '''          <!-- Variance explained -->
          {#if analysisResult.seasonality.decomposition?.variance_explained}
            {@const ve = analysisResult.seasonality.decomposition.variance_explained}
            <div class="mb-3">
              <div class="text-xs text-neutral-600 dark:text-neutral-400 mb-2">Распределение дисперсии:</div>
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
          {/if}'''

if old_block in content:
    content = content.replace(old_block, new_block)
    results_path.write_text(content, encoding='utf-8', newline='\n')
    print('✅ Блок исправлен')
    print('   {@const} теперь является непосредственным ребёнком {#if}')
else:
    print('⚠️  Блок не найден в ожидаемом виде')

print()
print('=' * 80)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 80)
print()
print('Проблема: {@const} не может быть ребёнком <div> в Svelte 5')
print('Решение: переместили {@const} сразу после {#if}, до <div>')
print()
print('Было:')
print('  {#if condition}')
print('    <div>')
print('      {@const ve = ...}  ← ОШИБКА')
print()
print('Стало:')
print('  {#if condition}')
print('    {@const ve = ...}    ← ПРАВИЛЬНО')
print('    <div>')
print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('Frontend должен перезагрузиться автоматически.')
print('Ошибка компиляции должна исчезнуть.')