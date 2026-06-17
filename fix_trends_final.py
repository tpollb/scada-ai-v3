from pathlib import Path
import re

print('=== fix_trends_final.py ===')
print()

PROJECT_ROOT = Path('.')
trends_path = PROJECT_ROOT / 'backend/modules/analytics/analyzers/trends.py'

if not trends_path.exists():
    print(f'⚠ Файл не найден: {trends_path}')
    exit(1)

content = trends_path.read_text(encoding='utf-8')

# ============================================================================
# Шаг 1: Удаляем ВСЕ существующие raw_data блоки и поля (начинаем с чистого листа)
# ============================================================================
# Удаляем raw_data = [] блок (с комментарием и циклом)
content = re.sub(
    r'[ \t]*# Добавляем raw_data для графиков.*?\n'
    r'[ \t]*raw_data = \[\]\n'
    r'(?:[ \t]*for p in data_points.*?\n)*?'
    r'(?:[ \t]*if ts is not None.*?\n)?'
    r'(?:[ \t]*raw_data\.append.*?\n)?'
    r'\n',
    '',
    content,
    flags=re.DOTALL
)

# Удаляем list comprehension вариант
content = re.sub(
    r'[ \t]*# Добавляем raw_data для графиков.*?\n'
    r'[ \t]*raw_data = \[.*?\]\n\n',
    '',
    content,
    flags=re.DOTALL
)

# Удаляем поле "raw_data": raw_data из dict
content = re.sub(r'[ \t]*"raw_data":\s*raw_data,?\s*\n', '', content)

print('✓ Удалены все существующие raw_data блоки')

# ============================================================================
# Шаг 2: Ищем главный return по уникальному полю "direction": direction
# ============================================================================
lines = content.split('\n')

# Ищем строку с "direction": direction — она уникальна для главного return
direction_line_idx = -1
for i, line in enumerate(lines):
    if '"direction": direction,' in line:
        direction_line_idx = i
        break

if direction_line_idx == -1:
    print('⚠ Не найдена строка "direction": direction')
    exit(1)

print(f'✓ Найден главный return (строка с "direction": {direction_line_idx + 1})')

# Идём назад чтобы найти начало return {
return_start_idx = -1
for i in range(direction_line_idx, -1, -1):
    if lines[i].strip().startswith('return {'):
        return_start_idx = i
        break

if return_start_idx == -1:
    print('⚠ Не найдено начало return statement')
    exit(1)

# Определяем отступ для кода внутри функции (берём отступ строки return)
return_indent = lines[return_start_idx][:len(lines[return_start_idx]) - len(lines[return_start_idx].lstrip())]
# Отступ внутри return dict (обычно return_indent + 4 пробела)
dict_indent = return_indent + '    '

print(f'✓ Отступ return: "{return_indent}" ({len(return_indent)} пробелов)')
print(f'✓ Отступ dict: "{dict_indent}" ({len(dict_indent)} пробелов)')

# ============================================================================
# Шаг 3: Вставляем raw_data блок ПЕРЕД return statement
# ============================================================================
raw_data_block = (
    f'{return_indent}# Добавляем raw_data для графиков (первые 200 точек)\n'
    f'{return_indent}raw_data = []\n'
    f'{return_indent}for p in data_points[:200]:\n'
    f'{return_indent}    ts = p.get("bucket_start") or p.get("timestamp")\n'
    f'{return_indent}    val = p.get("avg") if "avg" in p else p.get("value")\n'
    f'{return_indent}    if ts is not None and val is not None:\n'
    f'{return_indent}        raw_data.append({{"timestamp": ts, "value": val}})\n'
    f'\n'
)

lines.insert(return_start_idx, raw_data_block)
print(f'✓ Вставлен raw_data блок перед строкой {return_start_idx + 1}')

# Пересчитываем индексы после вставки
offset = raw_data_block.count('\n')
direction_line_idx += offset

# ============================================================================
# Шаг 4: Вставляем "raw_data": raw_data в return dict (после anomaly_rate)
# ============================================================================
# Ищем "anomaly_rate": после строки с direction (идём вперёд)
anomaly_line_idx = -1
for i in range(direction_line_idx, min(direction_line_idx + 20, len(lines))):
    if '"anomaly_rate":' in lines[i]:
        anomaly_line_idx = i
        break

if anomaly_line_idx == -1:
    print('⚠ Не найдена строка с "anomaly_rate"')
    exit(1)

# Вставляем "raw_data": raw_data ПОСЛЕ anomaly_rate
raw_data_field = f'{dict_indent}"raw_data": raw_data,'
lines.insert(anomaly_line_idx + 1, raw_data_field)
print(f'✓ Вставлено "raw_data": raw_data после строки {anomaly_line_idx + 1}')

# ============================================================================
# Шаг 5: Собираем и проверяем синтаксис
# ============================================================================
final_content = '\n'.join(lines)

try:
    compile(final_content, 'trends.py', 'exec')
    print('✓ Python syntax check passed')
except SyntaxError as e:
    print(f'⚠ Syntax error: {e}')
    print(f'  Line {e.lineno}: {e.text}')
    error_lines = final_content.split('\n')
    start = max(0, e.lineno - 5)
    end = min(len(error_lines), e.lineno + 5)
    print(f'\nСтроки {start+1}-{end}:')
    for idx in range(start, end):
        marker = '>>>' if idx == e.lineno - 1 else '   '
        print(f'{marker} {idx+1:4d}: {error_lines[idx]}')
    exit(1)

# ============================================================================
# Шаг 6: Записываем файл
# ============================================================================
trends_path.write_text(final_content, encoding='utf-8', newline='\n')
print('✓ Файл сохранён')

print()
print('=' * 60)
print('ЧТО ИСПРАВЛЕНО (финально):')
print('=' * 60)
print()
print('1. Удалены ВСЕ предыдущие неправильные вставки raw_data')
print('2. Главный return найден по уникальному полю "direction": direction')
print('3. raw_data блок вставлен ПЕРЕД return statement (вне dict)')
print('4. "raw_data": raw_data вставлен ВНУТРЬ return dict')
print('5. Отступы определены автоматически по существующему коду')
print('6. Синтаксис проверен через compile()')
print()
print('Backend перезагрузится автоматически (hot-reload).')
print()
print('Проверка:')
print('  curl "http://localhost:8081/analytics/report?period=7&params=temperature"')