#!/usr/bin/env python3
"""
fix_svelte_syntax_final.py — исправляем синтаксис Svelte 5 (убираем {#let}, используем {@const} правильно)
"""
from pathlib import Path

print('=' * 80)
print('ФИНАЛЬНЫЙ ФИКС: Исправляем синтаксис Svelte 5')
print('=' * 80)
print()

results_path = Path('frontend/src/components/DeepAnalysisResults.svelte')
content = results_path.read_text(encoding='utf-8')

# Заменяем все {#let}...{/let} на правильную структуру с {@const}
print('【1】Заменяем {#let} блоки на {@const}')
print('-' * 80)

# Pattern 1: {#let ve = ...} внутри {#if}
old_pattern1 = '''          {#if analysisResult.seasonality.decomposition?.variance_explained}
          {#let ve = analysisResult.seasonality.decomposition.variance_explained}
          <div class="mb-3">'''

new_pattern1 = '''          {#if analysisResult.seasonality.decomposition?.variance_explained}
          {@const ve = analysisResult.seasonality.decomposition.variance_explained}
          <div class="mb-3">'''

if old_pattern1 in content:
    content = content.replace(old_pattern1, new_pattern1)
    print('✅ Pattern 1 исправлен (single-tag variance)')

# Pattern 2: {#let pattern = ...}
old_pattern2 = '''          {#if analysisResult.seasonality.pattern?.pattern?.length > 0}
          {#let pattern = analysisResult.seasonality.pattern.pattern}
          {#let minVal = Math.min(...pattern.filter(v => v !== null))}
          {#let maxVal = Math.max(...pattern.filter(v => v !== null))}
          {#let range = maxVal - minVal}
          <div class="mb-3">'''

new_pattern2 = '''          {#if analysisResult.seasonality.pattern?.pattern?.length > 0}
          {@const pattern = analysisResult.seasonality.pattern.pattern}
          {@const minVal = Math.min(...pattern.filter(v => v !== null))}
          {@const maxVal = Math.max(...pattern.filter(v => v !== null))}
          {@const range = maxVal - minVal}
          <div class="mb-3">'''

if old_pattern2 in content:
    content = content.replace(old_pattern2, new_pattern2)
    print('✅ Pattern 2 исправлен (single-tag pattern)')

# Pattern 3: Закрывающие {/let} теги
content = content.replace('{/let}\n', '')
content = content.replace('{/let}', '')
print('✅ Все {/let} теги удалены')

# Pattern 4: Multi-tag variance
old_pattern4 = '''              {#if tagSeasonality.decomposition?.variance_explained}
              {#let ve = tagSeasonality.decomposition.variance_explained}
              <div class="mb-3">'''

new_pattern4 = '''              {#if tagSeasonality.decomposition?.variance_explained}
              {@const ve = tagSeasonality.decomposition.variance_explained}
              <div class="mb-3">'''

if old_pattern4 in content:
    content = content.replace(old_pattern4, new_pattern4)
    print('✅ Pattern 4 исправлен (multi-tag variance)')

# Pattern 5: Multi-tag pattern
old_pattern5 = '''              {#if tagSeasonality.pattern?.pattern?.length > 0}
              {#let pattern = tagSeasonality.pattern.pattern}
              {#let minVal = Math.min(...pattern.filter(v => v !== null))}
              {#let maxVal = Math.max(...pattern.filter(v => v !== null))}
              {#let range = maxVal - minVal}
              <div class="mb-3">'''

new_pattern5 = '''              {#if tagSeasonality.pattern?.pattern?.length > 0}
              {@const pattern = tagSeasonality.pattern.pattern}
              {@const minVal = Math.min(...pattern.filter(v => v !== null))}
              {@const maxVal = Math.max(...pattern.filter(v => v !== null))}
              {@const range = maxVal - minVal}
              <div class="mb-3">'''

if old_pattern5 in content:
    content = content.replace(old_pattern5, new_pattern5)
    print('✅ Pattern 5 исправлен (multi-tag pattern)')

# Сохраняем файл
print()
print('【2】Сохраняем файл')
print('-' * 80)
results_path.write_text(content, encoding='utf-8', newline='\n')
print('✅ Файл сохранён')

print()
print('=' * 80)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 80)
print()
print('Проблема: В Svelte НЕТ блока {#let}...{/let}')
print()
print('Было (НЕПРАВИЛЬНО):')
print('  {#if condition}')
print('    {#let ve = value}      ← ОШИБКА: {#let} не существует!')
print('    <div>{ve}</div>')
print('  {/let}                   ← ОШИБКА!')
print('  {/if}')
print()
print('Стало (ПРАВИЛЬНО):')
print('  {#if condition}')
print('    {@const ve = value}    ← ПРАВИЛЬНО: {@const} сразу после {#if}')
print('    <div>{ve}</div>')
print('  {/if}')
print()
print('Правила для {@const} в Svelte 5:')
print('  • Должен быть НЕПОСРЕДСТВЕННЫМ ребёнком {#if}, {#each}, {#snippet}')
print('  • НЕ может быть внутри HTML элементов (<div>, <p>, и т.д.)')
print('  • Не требует закрывающего тега')
print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('Frontend должен перезагрузиться автоматически.')
print('Ошибка компиляции должна исчезнуть.')