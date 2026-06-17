from pathlib import Path

print('=== fix_trendchart.py ===')
print()

PROJECT_ROOT = Path('.')

chart_path = PROJECT_ROOT / 'frontend/src/components/analytics/TrendChart.svelte'
if not chart_path.exists():
    print(f'⚠ Файл не найден: {chart_path}')
    exit(1)

chart_content = '''<script lang="ts">
  interface Props {
    data: Array<{ x: number; y: number }>
    label?: string
    unit?: string
    color?: string
    height?: number
  }

  let { data = [], label = '', unit = '', color = '#2563eb', height = 120 }: Props = $props()

  // Правильный синтаксис Svelte 5 runes — отдельные $derived
  let xs = $derived(data.map(d => d.x))
  let ys = $derived(data.map(d => d.y))
  
  let minX = $derived(xs.length ? Math.min(...xs) : 0)
  let maxX = $derived(xs.length ? Math.max(...xs) : 1)
  let minY = $derived(ys.length ? Math.min(...ys) : 0)
  let maxY = $derived(ys.length ? Math.max(...ys) : 1)
  let width = $derived(maxX - minX || 1)

  // Защита от NaN и undefined
  function toSvgX(x: number): number {
    if (width === 0 || isNaN(width) || !isFinite(x)) return 0
    return ((x - minX) / width) * 100
  }

  function toSvgY(y: number): number {
    const range = maxY - minY || 1
    if (isNaN(range) || !isFinite(y)) return height / 2
    return height - ((y - minY) / range) * (height - 20) - 10
  }

  // Генерируем path для линии
  let pathD = $derived(() => {
    if (!data.length) return ''
    const points = data.map((d, i) => {
      const x = toSvgX(d.x)
      const y = toSvgY(d.y)
      if (isNaN(x) || isNaN(y)) return ''
      return `${i === 0 ? 'M' : 'L'} ${x} ${y}`
    }).filter(p => p !== '')
    return points.join(' ')
  })

  // Форматируем значения с защитой от undefined/NaN
  function formatValue(v: number): string {
    if (v === undefined || v === null || isNaN(v) || !isFinite(v)) return '0'
    return Math.abs(v) < 100 ? v.toFixed(2) : v.toFixed(0)
  }
</script>

<div class="w-full">
  {#if label}
    <div class="text-xs font-medium text-neutral-600 dark:text-neutral-400 mb-1">{label}</div>
  {/if}

  <svg viewBox="0 0 100 {height}" class="w-full" style="height: {height}px" preserveAspectRatio="none">
    <!-- Grid lines -->
    <line x1="0" y1="10" x2="100" y2="10" stroke="currentColor" class="text-neutral-200 dark:text-neutral-700" stroke-width="0.3" stroke-dasharray="2,2" />
    <line x1="0" y1="{height - 10}" x2="100" y2="{height - 10}" stroke="currentColor" class="text-neutral-200 dark:text-neutral-700" stroke-width="0.3" stroke-dasharray="2,2" />

    <!-- Data line -->
    {#if pathD}
      <path d="{pathD}" fill="none" stroke={color} stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
    {/if}

    <!-- Y-axis labels -->
    <text x="2" y="12" class="text-[8px] fill-neutral-400 dark:fill-neutral-500">{formatValue(maxY)}{unit}</text>
    <text x="2" y="{height - 8}" class="text-[8px] fill-neutral-400 dark:fill-neutral-500">{formatValue(minY)}{unit}</text>
  </svg>

  {#if data.length}
    <div class="flex justify-between text-[10px] text-neutral-400 dark:text-neutral-500 mt-1">
      <span>{new Date(data[0].x * 86400000).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })}</span>
      <span>{new Date(data[data.length - 1].x * 86400000).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })}</span>
    </div>
  {/if}
</div>
'''

chart_path.write_text(chart_content, encoding='utf-8', newline='\n')
print('✓ TrendChart.svelte: исправлен синтаксис Svelte 5 runes')
print()
print('=' * 60)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 60)
print()
print('1. Синтаксис $derived:')
print('   • Было: let { minX, maxX, minY, maxY } = $derived(() => {...})')
print('   • Стало: отдельные $derived для каждой переменной')
print('   • Это правильный синтаксис Svelte 5')
print()
print('2. Защита от NaN/undefined:')
print('   • formatValue() проверяет undefined/null/NaN/isFinite')
print('   • toSvgX/toSvgY проверяют isNaN и возвращают fallback')
print('   • pathD фильтрует пустые точки')
print()
print('Frontend перезагрузится автоматически (Vite HMR).')
print()
print('Проверка:')
print('  В чате напиши: "покажи аналитику"')
print('  → Должен открыться AnalyticsPanel с графиками')
print('  → Все вкладки должны работать без ошибок в консоли')