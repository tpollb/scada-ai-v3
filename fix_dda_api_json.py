from pathlib import Path

print('=== fix_dda_api_json.py ===')
print()

panel_path = Path('frontend/src/components/DeepAnalysisPanel.svelte')
content = panel_path.read_text(encoding='utf-8')
original = content

changes = []

# 1. Исправляем onMount — добавляем .json()
old_mount = "const response = await api.get('api/v1/deep_analysis/tags')"
new_mount = "const response = await api.get('api/v1/deep_analysis/tags').json()"

if old_mount in content:
    content = content.replace(old_mount, new_mount)
    changes.append('✓ onMount: добавлен .json() для GET /tags')

# 2. Исправляем runAnalysis — добавляем .json()
old_run = "const response = await api.post('api/v1/deep_analysis/run', {"
new_run = "const response = await api.post('api/v1/deep_analysis/run', {"

# Ищем блок с api.post и добавляем .json() после закрывающей скобки
if old_run in content:
    # Паттерн: api.post(..., { json: {...} })
    # Нужно добавить .json() после закрывающей скобки
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if old_run in line:
            # Ищем закрывающую скобку api.post
            # Считаем скобки чтобы найти правильную
            start_idx = line.find('api.post')
            paren_count = 0
            found_start = False
            for j in range(start_idx, len(line)):
                if line[j] == '(':
                    paren_count += 1
                    found_start = True
                elif line[j] == ')':
                    paren_count -= 1
                    if found_start and paren_count == 0:
                        # Нашли закрывающую скобку
                        # Проверяем что после неё нет .json()
                        if '.json()' not in line[j+1:j+10]:
                            lines[i] = line[:j+1] + '.json()' + line[j+1:]
                            changes.append('✓ runAnalysis: добавлен .json() для POST /run')
                        break
            break
    content = '\n'.join(lines)

if content != original:
    panel_path.write_text(content, encoding='utf-8', newline='\n')
    print('✓ DeepAnalysisPanel.svelte обновлён')
else:
    print('ℹ Файл не изменился')

print()
print('=' * 60)
print('РЕЗУЛЬТАТ:')
print('=' * 60)
for c in changes:
    print(c)

print()
print('=' * 60)
print('ПРОВЕРКА:')
print('=' * 60)
content_check = panel_path.read_text(encoding='utf-8')
lines = content_check.split('\n')
for i, line in enumerate(lines, 1):
    if 'api.get(' in line or 'api.post(' in line:
        if 'deep_analysis' in line:
            print(f'  Строка {i}: {line.strip()}')

print()
print('=' * 60)
print('СЛЕДУЮЩИЙ ШАГ:')
print('=' * 60)
print()
print('Frontend перезагрузится автоматически (Vite HMR).')
print()
print('Проверка:')
print('  1. Открой фронтенд')
print('  2. Клик на кнопку Activity в хедере')
print('  3. В dropdown должен появиться список тегов')
print('  4. Выбери тег → период (30д) → "Запустить анализ"')
print('  5. Увидишь график + статистику + аномалии')