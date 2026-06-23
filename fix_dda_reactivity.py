from pathlib import Path

print('=== fix_dda_reactivity.py ===')
print()

panel_path = Path('frontend/src/components/DeepAnalysisPanel.svelte')
content = panel_path.read_text(encoding='utf-8')
original = content

changes = []

# 1. Добавляем проверку statistics перед блоком статистики
old_stats_block = '''      <!-- Statistics -->
      <div class="mb-4">
        <h3 class="text-sm font-semibold text-neutral-900 dark:text-neutral-100 mb-2 flex items-center gap-1">
          <TrendingUp size={14} />
          Статистика
        </h3>'''

new_stats_block = '''      <!-- Statistics -->
      {#if analysisResult?.statistics}
      <div class="mb-4">
        <h3 class="text-sm font-semibold text-neutral-900 dark:text-neutral-100 mb-2 flex items-center gap-1">
          <TrendingUp size={14} />
          Статистика
        </h3>'''

if old_stats_block in content:
    content = content.replace(old_stats_block, new_stats_block)
    changes.append('✓ Добавлена проверка: {#if analysisResult?.statistics}')

# 2. Закрываем блок statistics
old_stats_end = '''          </div>
        </div>
      </div>

      <!-- Anomalies -->'''

new_stats_end = '''          </div>
        </div>
      </div>
      {/if}

      <!-- Anomalies -->'''

if old_stats_end in content:
    content = content.replace(old_stats_end, new_stats_end)
    changes.append('✓ Закрыт блок statistics: {/if}')

# 3. Добавляем optional chaining в formatNumber вызовы
content = content.replace('formatNumber(analysisResult.statistics.mean)', 'formatNumber(analysisResult.statistics?.mean ?? 0)')
content = content.replace('formatNumber(analysisResult.statistics.std)', 'formatNumber(analysisResult.statistics?.std ?? 0)')
content = content.replace('formatNumber(analysisResult.statistics.min)', 'formatNumber(analysisResult.statistics?.min ?? 0)')
content = content.replace('formatNumber(analysisResult.statistics.max)', 'formatNumber(analysisResult.statistics?.max ?? 0)')
changes.append('✓ Добавлен optional chaining: analysisResult.statistics?.mean ?? 0')

# 4. Улучшаем проверку anomalies
old_anomalies_block = '''      <!-- Anomalies -->
      {#if analysisResult.anomalies?.total_anomalies > 0}'''

new_anomalies_block = '''      <!-- Anomalies -->
      {#if analysisResult?.anomalies?.total_anomalies > 0}'''

if old_anomalies_block in content:
    content = content.replace(old_anomalies_block, new_anomalies_block)
    changes.append('✓ Улучшена проверка anomalies: analysisResult?.anomalies?')

if content != original:
    panel_path.write_text(content, encoding='utf-8', newline='\n')
    print('✓ DeepAnalysisPanel.svelte обновлён')
else:
    print('ℹ Файл не изменился')

print()
print('=' * 60)
print('ИСПРАВЛЕНИЯ:')
print('=' * 60)
for c in changes:
    print(f'  {c}')

print()
print('=' * 60)
print('СЛЕДУЮЩИЙ ШАГ:')
print('=' * 60)
print()
print('Frontend перезагрузится автоматически (Vite HMR).')
print()
print('Проверка:')
print('  1. Открой фронтенд')
print('  2. Клик Activity → выбери тег → "Запустить анализ"')
print('  3. Увидишь блок статистики (mean, std, min, max)')
print()
print('Примечание: тег AIR0-1-Online — булевый статус (все значения = 1.0).')
print('Поэтому std = 0 и аномалий нет. Это нормально!')