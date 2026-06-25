#!/usr/bin/env python3
"""
fix_downsampling_mismatch.py — увеличивает max_points для single-tag анализа
"""
from pathlib import Path

print('=' * 80)
print('ФИКС: Downsampling mismatch')
print('=' * 80)
print()

# 1. chart_specs.py
cs_path = Path('backend/modules/deep_analysis/visualizers/chart_specs.py')
if cs_path.exists():
    c = cs_path.read_text(encoding='utf-8')
    changed = False
    for old in ['max_points: int = 800', 'max_points: int = 1500']:
        if old in c:
            c = c.replace(old, 'max_points: int = 3000')
            changed = True
            print(f'  chart_specs.py: {old} → max_points: int = 3000')
    if changed:
        cs_path.write_text(c, encoding='utf-8', newline='\n')
        print('  ✅ chart_specs.py сохранён')
    else:
        print('  ℹ️  max_points уже 3000 или другой')
print()

# 2. settings.py
s_path = Path('backend/modules/deep_analysis/settings.py')
if s_path.exists():
    c = s_path.read_text(encoding='utf-8')
    changed = False
    if 'max_points: int = Field(1500' in c:
        c = c.replace(
            'max_points: int = Field(1500, ge=200, le=5000',
            'max_points: int = Field(3000, ge=500, le=10000'
        )
        changed = True
        print('  settings.py: max_points 1500 → 3000')
    elif 'max_points: int = Field(800' in c:
        c = c.replace(
            'max_points: int = Field(800',
            'max_points: int = Field(3000'
        )
        changed = True
        print('  settings.py: max_points 800 → 3000')
    if changed:
        s_path.write_text(c, encoding='utf-8', newline='\n')
        print('  ✅ settings.py сохранён')
print()

# 3. config.yaml
cfg_path = Path('backend/modules/deep_analysis/config.yaml')
if cfg_path.exists():
    c = cfg_path.read_text(encoding='utf-8')
    changed = False
    for old in ['max_points: 800', 'max_points: 1500']:
        if old in c:
            c = c.replace(old, 'max_points: 3000')
            changed = True
            print(f'  config.yaml: {old} → max_points: 3000')
    if changed:
        cfg_path.write_text(c, encoding='utf-8', newline='\n')
        print('  ✅ config.yaml сохранён')
print()

print('=' * 80)
print('ГОТОВО')
print('=' * 80)
print()
print('Изменения:')
print('  • max_points: 800/1500 → 3000 для single-tag')
print('  • Bucket size уменьшится с ~5 до ~2 точек')
print('  • Scatter points будут точно на линии графика')
print()
print('Следующие шаги:')
print('  1. Перезапусти backend')
print('  2. Открой фронтенд → DDA → KITCHEN2-CO2 → анализ')
print('  3. Проверь что точки аномалий на линии графика')
print()
print('Диагностика после фикса:')
print('  curl -s "http://localhost:8081/api/v1/deep_analysis/diagnose/downsampling/KITCHEN2-CO2?period=30" > diag.json')
print('  python -c "import json; d=json.load(open(\'diag.json\')); ds=d[\'downsampling\']; print(ds)"')