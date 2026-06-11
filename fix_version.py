from pathlib import Path

print('=== fix_version.py ===')
print()

files = [
    'frontend/src/routes/Home.svelte',
    'frontend/src/routes/Config.svelte',
]

for file_path in files:
    path = Path(file_path)
    if not path.exists():
        print(f'⚠ Файл не найден: {file_path}')
        continue
    
    content = path.read_text(encoding='utf-8')
    new_content = content.replace('v3.0.2', 'v3.1.0')
    
    if new_content != content:
        path.write_text(new_content, encoding='utf-8', newline='\n')
        count = content.count('v3.0.2')
        print(f'✓ {file_path}: заменено {count} вхождений v3.0.2 → v3.1.0')
    else:
        print(f'ℹ {file_path}: v3.0.2 не найдено')

print()
print('Vite подхватит через HMR.')
print('Версия в хидере Home.svelte и футере Config.svelte теперь 3.1.0')