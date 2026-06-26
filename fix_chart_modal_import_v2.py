#!/usr/bin/env python3
"""
fix_chart_modal_import_v2.py — точечное добавление импорта ChartModal
"""
from pathlib import Path

print('=' * 80)
print('ФИКС: Добавление импорта ChartModal')
print('=' * 80)
print()

dar_path = Path('frontend/src/components/DeepAnalysisResults.svelte')
content = dar_path.read_text(encoding='utf-8')

# Проверяем что импорт уже есть
if 'import ChartModal from' in content:
    print('✅ Импорт ChartModal уже есть')
    exit(0)

# Ищем точный маркер
marker = "import { Line } from 'svelte-chartjs'"
if marker in content:
    new_import = marker + "\n  import ChartModal from './ChartModal.svelte'"
    content = content.replace(marker, new_import)
    dar_path.write_text(content, encoding='utf-8', newline='\n')
    print('✅ Импорт ChartModal добавлен после import { Line }')
else:
    print('❌ Маркер не найден')
    # Ищем любой import из svelte-chartjs
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        if 'svelte-chartjs' in line:
            print(f'  Нашёл на строке {i}: {line.strip()}')

print()
print('=' * 80)
print('ПРОВЕРКА:')
print('=' * 80)
print()
print('1. Vite автоматически перезагрузит страницу')
print('2. Должна исчезнуть ошибка: ReferenceError: ChartModal is not defined')
print('3. Кнопка ⛶ (Maximize2) должна открывать модалку')