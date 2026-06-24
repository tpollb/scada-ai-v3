#!/usr/bin/env python3
"""
add_debug_logs.py — добавляем console.log в DeepAnalysisResults для диагностики
"""

from pathlib import Path

print('=' * 70)
print('ДОБАВЛЕНИЕ DEBUG LOGS ВО ФРОНТЕНД')
print('=' * 70)
print()

results_path = Path('frontend/src/components/DeepAnalysisResults.svelte')
content = results_path.read_text(encoding='utf-8')

# Ищем где у нас определён timeSeriesData
# Добавляем $effect который логирует данные при изменении analysisResult
debug_effect = '''
  // DEBUG: логируем что приходит с backend
  $effect(() => {
    if (analysisResult) {
      console.log('🔍 DDA Analysis Result:', analysisResult)
      console.log('🔍 Anomalies:', analysisResult.anomalies)
      if (analysisResult.anomalies) {
        console.log('🔍 Anomaly types:', analysisResult.anomalies.anomaly_types)
        console.log('🔍 Type counts:', analysisResult.anomalies.type_counts)
      }
      if (analysisResult.visualizations?.time_series) {
        console.log('🔍 Time series datasets:', analysisResult.visualizations.time_series.data.datasets)
        console.log('🔍 Datasets count:', analysisResult.visualizations.time_series.data.datasets.length)
      }
    }
  })
'''

# Ищем где уже есть timeSeriesData и вставляем debug effect после
if "// DEBUG: логируем что приходит с backend" not in content:
    # Вставляем после определения timeSeriesData
    marker = "let timeSeriesData = $derived(\n    analysisResult?.visualizations?.time_series?.data || { labels: [], datasets: [] }\n  )"
    if marker in content:
        content = content.replace(marker, marker + "\n" + debug_effect)
        results_path.write_text(content, encoding='utf-8', newline='\n')
        print('✓ Добавлен $effect с debug logs')
        print()
        print('Что будет логироваться в DevTools Console:')
        print('  🔍 DDA Analysis Result: {...}')
        print('  🔍 Anomalies: {...}')
        print('  🔍 Anomaly types: ["spike", "dip", ...]')
        print('  🔍 Type counts: {spike: 12, dip: 3, ...}')
        print('  🔍 Time series datasets: [{...}, {...}, {...}, {...}]')
        print('  🔍 Datasets count: N')
        print()
        print('=' * 70)
        print('ПРОВЕРКА:')
        print('=' * 70)
        print()
        print('1. Открой фронтенд')
        print('2. Открой DevTools → Console (F12)')
        print('3. Activity → выбери R203-CO2 → "Запустить анализ"')
        print('4. Смотри в консоль:')
        print()
        print('   Если видишь:')
        print('     🔍 Anomaly types: ["spike", "dip", ...]')
        print('     🔍 Datasets count: 5  (1 основной + 4 типа аномалий)')
        print('   → Backend работает правильно, проблема во фронте')
        print()
        print('   Если видишь:')
        print('     🔍 Anomaly types: undefined')
        print('   → Backend не возвращает типы, нужно проверить anomalies.py')
        print()
        print('   Если видишь:')
        print('     🔍 Datasets count: 1  (только основной)')
        print('   → chart_specs.py не создаёт datasets по типам')
    else:
        print('⚠ Не удалось найти маркер для вставки debug logs')
else:
    print('ℹ Debug logs уже добавлены')

print()
print('Также запусти curl для проверки backend:')
print()
print('  curl -s -X POST http://localhost:8081/api/v1/deep_analysis/run \\')
print('    -H "Content-Type: application/json" \\')
print('    -d \'{"tags": ["R203-CO2"], "period": 30}\' \\')
print('    | python -c "import sys, json; d=json.load(sys.stdin); print(\'anomaly_types:\', d[\'anomalies\'].get(\'anomaly_types\', \'MISSING\')); print(\'type_counts:\', d[\'anomalies\'].get(\'type_counts\', \'MISSING\')); print(\'datasets count:\', len(d[\'visualizations\'][\'time_series\'][\'data\'][\'datasets\']))"')