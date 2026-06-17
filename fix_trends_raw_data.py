from pathlib import Path

print('=== fix_trends_raw_data.py ===')
print()

PROJECT_ROOT = Path('.')
trends_path = PROJECT_ROOT / 'backend/modules/analytics/analyzers/trends.py'

if not trends_path.exists():
    print(f'⚠ Файл не найден: {trends_path}')
    exit(1)

content = trends_path.read_text(encoding='utf-8')
lines = content.split('\n')

# ============================================================================
# Шаг 1: Удаляем неправильный raw_data блок (строки 155-160)
# ============================================================================
new_lines = []
skip_until = -1

for i, line in enumerate(lines):
    if i < skip_until:
        continue
    
    # Пропускаем блок "# Добавляем raw_data для графиков" если он внутри return dict
    if '# Добавляем raw_data для графиков' in line:
        # Проверяем контекст — смотрим что было до
        # Если в предыдущих 5 строках есть "anomaly_rate": — это внутри return
        context = '\n'.join(lines[max(0, i-10):i])
        if '"anomaly_rate":' in context:
            print(f'⊘ Удаляем неправильный raw_data блок на строке {i+1}')
            # Пропускаем следующие строки до пустой строки или закрывающей ]
            j = i + 1
            while j < len(lines):
                if lines[j].strip() == '' and ']' in lines[j-1]:
                    j += 1
                    break
                if lines[j].strip() == ']':
                    j += 1
                    break
                j += 1
            skip_until = j
            continue
    
    new_lines.append(line)

content = '\n'.join(new_lines)
print('✓ Удалён неправильный raw_data блок из return dict')

# ============================================================================
# Шаг 2: Правильно добавляем raw_data ПЕРЕД return statement
# ============================================================================
lines = content.split('\n')
new_lines = []
in_analyze_param_trend = False
raw_data_added = False

for i, line in enumerate(lines):
    # Отслеживаем начало функции analyze_param_trend
    if 'def analyze_param_trend(' in line:
        in_analyze_param_trend = True
    
    # Отслеживаем выход из функции (новая def или class на уровне 0)
    if in_analyze_param_trend and line.startswith('def ') and 'analyze_param_trend' not in line:
        in_analyze_param_trend = False
    
    # Ищем return { внутри analyze_param_trend
    if in_analyze_param_trend and not raw_data_added and line.strip().startswith('return {'):
        # Вставляем raw_data ПЕРЕД этой строкой
        indent = '    '  # отступ внутри функции
        
        raw_data_block = f'''{indent}# Добавляем raw_data для графиков (первые 200 точек)
{indent}raw_data = []
{indent}for p in data_points[:200]:
{indent}    ts = p.get("bucket_start") or p.get("timestamp")
{indent}    val = p.get("avg") if "avg" in p else p.get("value")
{indent}    if ts is not None and val is not None:
{indent}        raw_data.append({{"timestamp": ts, "value": val}})
{indent}
'''
        new_lines.append(raw_data_block)
        raw_data_added = True
        print(f'✓ Вставлен raw_data блок перед return на строке {i+1}')
    
    new_lines.append(line)

content = '\n'.join(new_lines)

if not raw_data_added:
    print('⚠ Не удалось найти return statement для вставки raw_data')

# ============================================================================
# Шаг 3: Добавляем "raw_data": raw_data ВНУТРЬ return dict
# ============================================================================
lines = content.split('\n')
new_lines = []
raw_data_field_added = False

for i, line in enumerate(lines):
    new_lines.append(line)
    
    # Ищем "anomaly_rate": round(...), и добавляем raw_data после него
    if not raw_data_field_added and '"anomaly_rate": round(anomaly_rate' in line:
        # Определяем отступ
        indent = line[:len(line) - len(line.lstrip())]
        new_lines.append(f'{indent}"raw_data": raw_data,')
        raw_data_field_added = True
        print(f'✓ Добавлено "raw_data": raw_data в return dict после строки {i+1}')

content = '\n'.join(new_lines)

# ============================================================================
# Шаг 4: Проверяем синтаксис
# ============================================================================
try:
    compile(content, 'trends.py', 'exec')
    print('✓ Python syntax check passed')
except SyntaxError as e:
    print(f'⚠ Syntax error: {e}')
    print(f'  Line {e.lineno}: {e.text}')
    error_lines = content.split('\n')
    start = max(0, e.lineno - 5)
    end = min(len(error_lines), e.lineno + 5)
    print(f'\nСтроки {start+1}-{end}:')
    for idx in range(start, end):
        marker = '>>>' if idx == e.lineno - 1 else '   '
        print(f'{marker} {idx+1:4d}: {error_lines[idx]}')
    exit(1)

# Записываем файл
trends_path.write_text(content, encoding='utf-8', newline='\n')
print('✓ Файл сохранён')

print()
print('=' * 60)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 60)
print()
print('1. Удалён неправильный raw_data блок из return dict')
print('2. raw_data = [] добавлен ПЕРЕД return statement')
print('3. "raw_data": raw_data добавлен ВНУТРЬ return dict')
print('4. Синтаксис проверен через compile()')
print()
print('Backend перезагрузится автоматически (hot-reload).')
print()
print('Проверка:')
print('  curl "http://localhost:8081/analytics/report?period=7&params=temperature"')
print('  → Должен вернуть JSON с полем "raw_data" в trends.temperature')