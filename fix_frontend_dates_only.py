#!/usr/bin/env python3
"""
fix_frontend_dates_only.py — заменяем #idx на даты в DeepAnalysisResults (без f-strings)
"""

from pathlib import Path

print('=' * 70)
print('ФИКС FRONTEND: Дата-время вместо индексов')
print('=' * 70)
print()

results_path = Path('frontend/src/components/DeepAnalysisResults.svelte')
content = results_path.read_text(encoding='utf-8')

# 1. Добавляем функцию форматирования даты если её нет
if 'function formatAnomalyDate' not in content:
    content = content.replace(
        '<script lang="ts">',
        '''<script lang="ts">
  function formatAnomalyDate(timestamp: any): string {
    if (!timestamp) return '—'
    try {
      const d = new Date(timestamp)
      if (isNaN(d.getTime())) return String(timestamp)
      return d.toLocaleString('ru-RU', {
        day: '2-digit', month: '2-digit', year: '2-digit',
        hour: '2-digit', minute: '2-digit'
      })
    } catch {
      return String(timestamp)
    }
  }
'''
    )
    print('✅ Добавлена функция formatAnomalyDate()')

# 2. Single-tag spike блок
old_single = '''                    {@const spikePoints = analysisResult.anomalies.anomaly_indices.filter((idx, i) => analysisResult.anomalies.anomaly_types[i] === 'spike')}
                    <div class="max-h-32 overflow-y-auto space-y-0.5 mt-1">
                      {#each spikePoints.slice(0, 30) as idx, i}
                        {@const val = analysisResult.anomalies.anomaly_values[analysisResult.anomalies.anomaly_indices.indexOf(idx)]}
                        <div class="text-[10px] font-mono text-red-600 dark:text-red-400 flex justify-between">
                          <span>#{idx}</span>
                          <span class="font-semibold">{val !== undefined ? val.toFixed(2) : '—'}</span>
                        </div>
                      {/each}
                    </div>'''

new_single = '''                    <div class="max-h-32 overflow-y-auto space-y-0.5 mt-1">
                      {#each analysisResult.anomalies.anomaly_indices.map((idx, i) => ({idx, val: analysisResult.anomalies.anomaly_values[i], ts: analysisResult.anomalies.anomaly_timestamps?.[i], type: analysisResult.anomalies.anomaly_types?.[i]})).filter(p => p.type === 'spike').slice(0, 30) as p}
                        <div class="text-[10px] font-mono text-red-600 dark:text-red-400 flex justify-between gap-2">
                          <span class="text-neutral-500">{formatAnomalyDate(p.ts)}</span>
                          <span class="font-semibold">{p.val !== undefined && p.val !== null ? p.val.toFixed(2) : '—'}</span>
                        </div>
                      {/each}
                    </div>'''

if old_single in content:
    content = content.replace(old_single, new_single)
    print('✅ Single-tag spike: дата-время вместо #idx')

# 3. Multi-tag блоки для всех 4 типов
types = [
    ('spike', 'red'),
    ('dip', 'blue'),
    ('drift', 'amber'),
    ('noise', 'neutral'),
]

for atype, color in types:
    old = (
        "{@const " + atype + "Points = (tagData.anomaly_indices || []).filter((idx, i) => (tagData.anomaly_types || [])[i] === '" + atype + "')}\n"
        "                      {#if " + atype + "Points.length > 0}\n"
        "                        <div class=\"mt-2\">\n"
        "                          <div class=\"text-[10px] font-semibold text-" + color + "-700 dark:text-" + color + "-300 mb-1\">{tagName} ({" + atype + "Points.length}):</div>\n"
        "                          <div class=\"max-h-32 overflow-y-auto space-y-0.5\">\n"
        "                            {#each " + atype + "Points.slice(0, 20) as idx}\n"
        "                              {@const val = (tagData.anomaly_values || [])[tagData.anomaly_indices.indexOf(idx)]}\n"
        "                              <div class=\"text-[10px] font-mono text-" + color + "-600 dark:text-" + color + "-400 flex justify-between\">\n"
        "                                <span>#{idx}</span>\n"
        "                                <span class=\"font-semibold\">{val !== undefined ? val.toFixed(2) : '—'}</span>\n"
        "                              </div>\n"
        "                            {/each}\n"
        "                            {#if " + atype + "Points.length > 20}\n"
        "                              <div class=\"text-[10px] text-" + color + "-500 italic\">... и ещё {" + atype + "Points.length - 20}</div>\n"
        "                            {/if}\n"
        "                          </div>\n"
        "                        </div>\n"
        "                      {/if}"
    )
    
    new = (
        "{@const " + atype + "Data = (tagData.anomaly_indices || []).map((idx, i) => ({idx, val: (tagData.anomaly_values || [])[i], ts: (tagData.anomaly_timestamps || [])[i], type: (tagData.anomaly_types || [])[i]})).filter(p => p.type === '" + atype + "')}\n"
        "                      {#if " + atype + "Data.length > 0}\n"
        "                        <div class=\"mt-2\">\n"
        "                          <div class=\"text-[10px] font-semibold text-" + color + "-700 dark:text-" + color + "-300 mb-1\">{tagName} ({" + atype + "Data.length}):</div>\n"
        "                          <div class=\"max-h-32 overflow-y-auto space-y-0.5\">\n"
        "                            {#each " + atype + "Data.slice(0, 20) as p}\n"
        "                              <div class=\"text-[10px] font-mono text-" + color + "-600 dark:text-" + color + "-400 flex justify-between gap-2\">\n"
        "                                <span class=\"text-neutral-500\">{formatAnomalyDate(p.ts)}</span>\n"
        "                                <span class=\"font-semibold\">{p.val !== undefined && p.val !== null ? p.val.toFixed(2) : '—'}</span>\n"
        "                              </div>\n"
        "                            {/each}\n"
        "                            {#if " + atype + "Data.length > 20}\n"
        "                              <div class=\"text-[10px] text-" + color + "-500 italic\">... и ещё {" + atype + "Data.length - 20}</div>\n"
        "                            {/if}\n"
        "                          </div>\n"
        "                        </div>\n"
        "                      {/if}"
    )
    
    if old in content:
        content = content.replace(old, new)
        print(f'✅ Multi-tag {atype}: дата-время вместо #idx')
    else:
        print(f'⚠ {atype}: блок не найден (возможно уже исправлен)')

results_path.write_text(content, encoding='utf-8', newline='\n')

print()
print('=' * 70)
print('ГОТОВО')
print('=' * 70)
print()
print('Теперь в раскрывающихся блоках:')
print('  Было: #1190   744.00')
print('  Стало: 23.06.26 14:30   744.00')