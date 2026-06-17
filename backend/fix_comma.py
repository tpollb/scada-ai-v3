from pathlib import Path

print('=== fix_comma.py ===')
print()

system_path = Path('api/routes/system.py')
content = system_path.read_text(encoding='utf-8')

# Точная замена строки (без regex)
old_line = '        "server_time": datetime.now().isoformat()\n        "capabilities":'
new_line = '        "server_time": datetime.now().isoformat(),\n        "capabilities":'

if old_line in content:
    content = content.replace(old_line, new_line)
    system_path.write_text(content, encoding='utf-8', newline='\n')
    print('✓ Добавлена запятая после server_time')
else:
    print('⚠ Точная строка не найдена, пробуем альтернативный вариант')
    # Альтернатива: может быть другой отступ или пробелы
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if '"server_time": datetime.now().isoformat()' in line and not line.rstrip().endswith(','):
            lines[i] = line.rstrip() + ','
            print(f'✓ Добавлена запятая на строке {i+1}')
            break
    content = '\n'.join(lines)
    system_path.write_text(content, encoding='utf-8', newline='\n')

# Проверяем синтаксис
try:
    compile(content, 'system.py', 'exec')
    print('✓ Python syntax check passed')
except SyntaxError as e:
    print(f'⚠ Syntax error: {e}')
    print(f'  Line {e.lineno}: {e.text}')
    exit(1)

print()
print('Backend перезагрузится автоматически (hot-reload).')
print()
print('Проверка:')
print('  curl http://localhost:8081/system/info | python -m json.tool | grep -A 6 capabilities')