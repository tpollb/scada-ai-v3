from pathlib import Path

print('=== fix_trends_syntax.py ===')
print()

PROJECT_ROOT = Path('.')
trends_path = PROJECT_ROOT / 'backend/modules/analytics/analyzers/trends.py'

if not trends_path.exists():
    print(f'⚠ Файл не найден: {trends_path}')
    exit(1)

content = trends_path.read_text(encoding='utf-8')

# Удаляем все неправильные вставки raw_data (могут быть несколько)
import re

# Удаляем блоки raw_data которые могли вставиться в неправильные места
content = re.sub(
    r'\n\s*# Добавляем raw_data для графиков.*?raw_data = \[\n.*?\]\n\s*\n',
    '\n',
    content,
    flags=re.DOTALL
)

# Удаляем "raw_data": raw_data из неправильных мест
content = re.sub(
    r'\n\s*"raw_data":\s*raw_data,',
    '',
    content
)

# Проверяем что мы очистили
if 'raw_data' in content:
    print('⚠ После очистки raw_data всё ещё есть в файле, показываю строки:')
    for i, line in enumerate(content.split('\n'), 1):
        if 'raw_data' in line:
            print(f'  {i}: {line}')

# Теперь правильно добавляем raw_data ПЕРЕД return statement
# Ищем функцию analyze_param_trend и её return
lines = content.split('\n')
new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    
    # Ищем строку с "anomaly_rate": round(anomaly_rate, 4),
    if '"anomaly_rate":' in line and 'round(anomaly_rate' in line:
        # Добавляем эту строку
        new_lines.append(line)
        
        # Теперь добавляем raw_data ПЕРЕД закрывающей }
        # Находим следующую строку с закрывающей }
        j = i + 1
        while j < len(lines) and lines[j].strip() not in ('}', '    }', '        }'):
            j += 1
        
        if j < len(lines):
            # Вставляем raw_data перед строкой j
            indent = '    '  # отступ для кода внутри функции
            raw_data_block = f'''
{indent}# Добавляем raw_data для графиков (первые 200 точек)
{indent}raw_data = [
{indent}    {{"timestamp": p.get("bucket_start") or p.get("timestamp"), "value": p.get("avg") if "avg" in p else p.get("value")}}
{indent}    for p in data_points[:200]
{indent}    if (p.get("bucket_start") or p.get("timestamp")) and (p.get("avg") is not None if "avg" in p else p.get("value") is not None)
{indent}]
{indent}
'''
            new_lines.append(raw_data_block)
            print(f'✓ Вставлен raw_data блок после строки {i+1}')
            break
    
    new_lines.append(line)
    i += 1

# Добавляем остальные строки
new_lines.extend(lines[i+1:])

# Теперь добавляем "raw_data": raw_data в return dict
content_new = '\n'.join(new_lines)

# Ищем return { ... "anomaly_rate": ..., } и добавляем "raw_data": raw_data
# Находим последнюю строку с "anomaly_rate" перед закрывающей }
lines_new = content_new.split('\n')
for i in range(len(lines_new) - 1, -1, -1):
    if '"anomaly_rate":' in lines_new[i]:
        # Находим следующую закрывающую }
        for j in range(i + 1, min(i + 5, len(lines_new))):
            if lines_new[j].strip() == '}':
                # Вставляем "raw_data": raw_data перед этой строкой
                indent = lines_new[j][:len(lines_new[j]) - len(lines_new[j].lstrip())]
                lines_new.insert(j, f'{indent}    "raw_data": raw_data,')
                print(f'✓ Добавлено "raw_data": raw_data в return dict')
                break
        break

content_final = '\n'.join(lines_new)

# Проверяем синтаксис
try:
    compile(content_final, 'trends.py', 'exec')
    print('✓ Python syntax check passed')
except SyntaxError as e:
    print(f'⚠ Syntax error: {e}')
    print(f'  Line {e.lineno}: {e.text}')
    # Показываем строки вокруг ошибки
    error_lines = content_final.split('\n')
    start = max(0, e.lineno - 5)
    end = min(len(error_lines), e.lineno + 5)
    print(f'\nСтроки {start+1}-{end}:')
    for idx in range(start, end):
        marker = '>>>' if idx == e.lineno - 1 else '   '
        print(f'{marker} {idx+1:4d}: {error_lines[idx]}')
    exit(1)

# Записываем исправленный файл
trends_path.write_text(content_final, encoding='utf-8', newline='\n')
print('✓ Файл сохранён')

print()
print('=' * 60)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 60)
print()
print('1. Удалены все неправильные вставки raw_data')
print('2. raw_data правильно добавлен перед return statement')
print('3. "raw_data": raw_data добавлен в return dict')
print('4. Синтаксис проверен через compile()')
print()
print('Backend перезагрузится автоматически (hot-reload).')
print()
print('Проверка:')
print('  curl "http://localhost:8081/analytics/report?period=7&params=temperature"')
print('  → Должен вернуть JSON с полем "raw_data" в trends.temperature')