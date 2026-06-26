#!/usr/bin/env python3
"""
integrate_chart_modal.py — интеграция ChartModal в DeepAnalysisResults.svelte
"""
from pathlib import Path

print('=' * 80)
print('ИНТЕГРАЦИЯ: ChartModal в DeepAnalysisResults.svelte')
print('=' * 80)
print()

dar_path = Path('frontend/src/components/DeepAnalysisResults.svelte')
content = dar_path.read_text(encoding='utf-8')

changes = []

# 1. Добавляем импорт ChartModal
print('【1】Добавляем импорт ChartModal')
print('-' * 80)

if 'import ChartModal' not in content:
    # Ищем строку с другими импортами компонентов
    import_marker = "import { Line, Bar } from 'svelte-chartjs'"
    if import_marker in content:
        content = content.replace(
            import_marker,
            import_marker + "\n  import ChartModal from './ChartModal.svelte'"
        )
        changes.append('Добавлен импорт ChartModal')
        print(f'  ✅ {changes[-1]}')
else:
    print('  ℹ️  Импорт уже есть')

# 2. Добавляем импорт Maximize2 иконки
print()
print('【2】Добавляем импорт иконки Maximize2')
print('-' * 80)

if 'Maximize2' not in content:
    # Ищем импорт из lucide-svelte
    import re
    lucide_pattern = r"import \{([^}]+)\} from 'lucide-svelte'"
    match = re.search(lucide_pattern, content)
    if match:
        old_import = match.group(0)
        old_icons = match.group(1)
        if 'Maximize2' not in old_icons:
            new_icons = old_icons.rstrip() + ', Maximize2'
            new_import = old_import.replace(old_icons, new_icons)
            content = content.replace(old_import, new_import)
            changes.append('Добавлена иконка Maximize2')
            print(f'  ✅ {changes[-1]}')
    else:
        print('  ⚠️  Не найден импорт из lucide-svelte')
else:
    print('  ℹ️  Maximize2 уже импортирован')

# 3. Добавляем состояние для модалки
print()
print('【3】Добавляем состояние для модалки')
print('-' * 80)

modal_state = '''
  // ChartModal state
  let modalOpen = $state(false)
  let modalChartType = $state<'line' | 'bar'>('line')
  let modalTitle = $state('')
  let modalData = $state<any>(null)
  let modalOptions = $state<any>(null)

  function openChartModal(type: 'line' | 'bar', title: string, data: any, options: any) {
    modalChartType = type
    modalTitle = title
    modalData = data
    modalOptions = options
    modalOpen = true
  }

  function closeChartModal() {
    modalOpen = false
  }
'''

if 'let modalOpen = $state' not in content:
    # Вставляем после scatterChartId
    marker = "const scatterChartId = `dda-scatter-${Math.random().toString(36).slice(2, 9)}`"
    if marker in content:
        content = content.replace(marker, marker + modal_state)
        changes.append('Добавлено состояние для модалки')
        print(f'  ✅ {changes[-1]}')
    else:
        print('  ⚠️  Маркер scatterChartId не найден')
else:
    print('  ℹ️  Состояние уже есть')

# 4. Добавляем кнопку Maximize рядом с Download на single-tag графике (строка ~495)
print()
print('【4】Добавляем кнопку Maximize на single-tag график')
print('-' * 80)

# Ищем блок с кнопками zoom/download для tsChartInstance
old_ts_buttons = '''              <button type="button" onclick={() => downloadPNG(tsChartInstance, 'timeseries')} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Скачать PNG"><Download size={14} class="text-neutral-600 dark:text-neutral-400" /></button>'''

new_ts_buttons = '''              <button type="button" onclick={() => downloadPNG(tsChartInstance, 'timeseries')} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Скачать PNG"><Download size={14} class="text-neutral-600 dark:text-neutral-400" /></button>
              <button type="button" onclick={() => openChartModal('line', `Временной ряд: ${analysisResult?.tags?.[0] || 'Tag'}`, timeSeriesData, timeSeriesOptions)} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Полноэкранный режим"><Maximize2 size={14} class="text-neutral-600 dark:text-neutral-400" /></button>'''

if old_ts_buttons in content and content.count(old_ts_buttons) >= 1:
    # Заменяем только первое вхождение (single-tag)
    content = content.replace(old_ts_buttons, new_ts_buttons, 1)
    changes.append('Добавлена кнопка Maximize на single-tag график')
    print(f'  ✅ {changes[-1]}')
else:
    print('  ⚠️  Блок кнопок не найден')

# 5. Добавляем кнопку Maximize на multitag графике
print()
print('【5】Добавляем кнопку Maximize на multitag график')
print('-' * 80)

old_mt_buttons = '''              <button type="button" onclick={() => downloadPNG(tsChartInstance, 'multitag_timeseries')} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Скачать PNG"><Download size={14} class="text-neutral-600 dark:text-neutral-400" /></button>'''

new_mt_buttons = '''              <button type="button" onclick={() => downloadPNG(tsChartInstance, 'multitag_timeseries')} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Скачать PNG"><Download size={14} class="text-neutral-600 dark:text-neutral-400" /></button>
              <button type="button" onclick={() => openChartModal('line', 'Временные ряды (мульти-тег)', timeSeriesData, timeSeriesOptions)} class="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition" title="Полноэкранный режим"><Maximize2 size={14} class="text-neutral-600 dark:text-neutral-400" /></button>'''

if old_mt_buttons in content:
    content = content.replace(old_mt_buttons, new_mt_buttons)
    changes.append('Добавлена кнопка Maximize на multitag график')
    print(f'  ✅ {changes[-1]}')
else:
    print('  ⚠️  Блок кнопок multitag не найден')

# 6. Добавляем сам компонент ChartModal в самом конце
print()
print('【6】Добавляем компонент ChartModal в конце')
print('-' * 80)

if '<ChartModal' not in content:
    modal_component = '''
<ChartModal
  isOpen={modalOpen}
  title={modalTitle}
  chartType={modalChartType}
  chartData={modalData}
  chartOptions={modalOptions}
  onClose={closeChartModal}
/>
'''
    content = content.rstrip() + '\n' + modal_component
    changes.append('Добавлен компонент ChartModal в разметку')
    print(f'  ✅ {changes[-1]}')
else:
    print('  ℹ️  ChartModal уже есть в разметке')

# Сохраняем
dar_path.write_text(content, encoding='utf-8', newline='\n')

print()
print('=' * 80)
print('ИТОГО:')
print('=' * 80)
print()
for i, c in enumerate(changes, 1):
    print(f'  {i}. ✅ {c}')

print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Vite автоматически перезагрузит страницу')
print()
print('2. Открой DDA → KITCHEN2-CO2 → анализ')
print()
print('3. У графика времени должна появиться новая кнопка:')
print('   📥 (Download PNG)   ⛶ (Maximize)')
print()
print('4. Кликни на ⛶ — должен открыться полноэкранный график')
print()
print('5. В модалке:')
print('   • Zoom in/out/reset кнопки работают')
print('   • Download PNG скачивает изображение')
print('   • Esc или клик на фон закрывает модалку')
print('   • Колёсико мыши — zoom, Shift+drag — выделение')
print()
print('⚠️  Если Vite выдаёт ошибку компиляции:')
print('   • Скинь ошибку — исправим синтаксис')