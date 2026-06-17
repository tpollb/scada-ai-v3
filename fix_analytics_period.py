from pathlib import Path
import re

print('=== fix_analytics_period.py ===')
print()

PROJECT_ROOT = Path('.')

# ============================================================================
# 1. Backend: адаптивный raw_data (downsampling для больших данных)
# ============================================================================
trends_path = PROJECT_ROOT / 'backend/modules/analytics/analyzers/trends.py'
content = trends_path.read_text(encoding='utf-8')

# Заменяем блок с raw_data на адаптивный (берём все точки если <500, иначе downsampling)
old_block = '''    # Добавляем raw_data для графиков (первые 200 точек)
    raw_data = []
    for p in data_points[-200:]:
        ts = p.get("bucket_start") or p.get("timestamp")
        val = p.get("avg") if "avg" in p else p.get("value")
        if ts is not None and val is not None:
            raw_data.append({"timestamp": ts, "value": val})'''

new_block = '''    # Добавляем raw_data для графиков (адаптивно: все точки если <500, иначе downsampling)
    raw_data_all = []
    for p in data_points:
        ts = p.get("bucket_start") or p.get("timestamp")
        val = p.get("avg") if "avg" in p else p.get("value")
        if ts is not None and val is not None:
            raw_data_all.append({"timestamp": ts, "value": val})

    # Downsampling если точек слишком много (лимит 500 для производительности)
    MAX_POINTS = 500
    if len(raw_data_all) <= MAX_POINTS:
        raw_data = raw_data_all
    else:
        # Берём каждую N-ю точку, но ВСЕГДА включаем последнюю
        step = len(raw_data_all) / MAX_POINTS
        raw_data = []
        i = 0.0
        while int(i) < len(raw_data_all) - 1:
            raw_data.append(raw_data_all[int(i)])
            i += step
        # Гарантированно добавляем последнюю точку
        raw_data.append(raw_data_all[-1])'''

if old_block in content:
    content = content.replace(old_block, new_block)
    trends_path.write_text(content, encoding='utf-8', newline='\n')
    print('✓ trends.py: адаптивный raw_data (downsampling если >500 точек)')
else:
    print('⚠ Не найден блок raw_data для замены')

# ============================================================================
# 2. Frontend: AnalyticsPanel — при смене периода всегда делаем новый fetch
# ============================================================================
panel_path = PROJECT_ROOT / 'frontend/src/components/analytics/AnalyticsPanel.svelte'
content = panel_path.read_text(encoding='utf-8')

# Исправляем fetchData: НЕ проверяем initialData (он больше не обновляется)
# Вместо этого используем локальный стейт hasInitialData
old_fetch = '''  async function fetchData() {
    if (initialData) {
      data = initialData
      return
    }

    loading = true'''

new_fetch = '''  // Локальный стейт: получили ли мы initialData при первом рендере
  let useInitialData = $state(true)

  async function fetchData(forceFetch = false) {
    // Используем initialData только при первом рендере (если он есть)
    if (useInitialData && initialData && !forceFetch) {
      data = initialData
      useInitialData = false
      return
    }

    // При смене периода или явном обновлении — всегда делаем fetch
    useInitialData = false

    loading = true'''

if old_fetch in content:
    content = content.replace(old_fetch, new_fetch)
    print('✓ AnalyticsPanel.svelte: fetchData теперь корректно обрабатывает initialData')
else:
    print('⚠ Не найден блок fetchData для замены')

# Исправляем onMount
old_mount = '''  onMount(() => {
    if (!initialData) {
      fetchData()
    }
  })'''

new_mount = '''  onMount(() => {
    fetchData()
  })'''

if old_mount in content:
    content = content.replace(old_mount, new_mount)
    print('✓ AnalyticsPanel.svelte: onMount упрощён')

# Исправляем PeriodSelector onValueChange — принудительный fetch
old_period = '''<PeriodSelector value={period} onValueChange={(v) => { period = v; initialData = null; fetchData() }} />'''
new_period = '''<PeriodSelector value={period} onValueChange={(v) => { period = v; fetchData(true) }} />'''

if old_period in content:
    content = content.replace(old_period, new_period)
    print('✓ AnalyticsPanel.svelte: PeriodSelector делает принудительный fetch')

# Исправляем кнопку обновления — тоже force fetch
old_refresh = '''    <button
      type="button"
      onclick={fetchData}
      disabled={loading}
      class="p-2 rounded hover:bg-neutral-100 dark:hover:bg-neutral-700 transition text-neutral-500 disabled:opacity-50"
      title="Обновить"
    >'''
new_refresh = '''    <button
      type="button"
      onclick={() => fetchData(true)}
      disabled={loading}
      class="p-2 rounded hover:bg-neutral-100 dark:hover:bg-neutral-700 transition text-neutral-500 disabled:opacity-50"
      title="Обновить"
    >'''

if old_refresh in content:
    content = content.replace(old_refresh, new_refresh)
    print('✓ AnalyticsPanel.svelte: кнопка обновления делает force fetch')

panel_path.write_text(content, encoding='utf-8', newline='\n')

print()
print('=' * 60)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 60)
print()
print('1. Backend (trends.py):')
print('   • raw_data возвращает ВСЕ точки если их < 500')
print('   • Если точек > 500 — делает downsampling (каждую N-ю)')
print('   • ВСЕГДА включает последнюю точку (для актуальности)')
print('   • Было: 200 точек → ~8 дней для hourly')
print('   • Стало: до 500 точек → полный период')
print()
print('2. Frontend (AnalyticsPanel.svelte):')
print('   • Добавлен локальный стейт useInitialData')
print('   • initialData используется ТОЛЬКО при первом рендере')
print('   • При смене периода — всегда делается новый fetch')
print('   • Кнопка обновления — всегда force fetch')
print()
print('Проверка:')
print('  1. В чате: "покажи аналитику"')
print('  2. Графики должны показывать ПОЛНЫЙ период (30 дней)')
print('  3. Переключи на 7 дней → загрузятся данные за 7 дней')
print('  4. Переключи на 90 дней → загрузятся данные за 90 дней (с downsampling)')