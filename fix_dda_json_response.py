from pathlib import Path

print('=== fix_dda_json_response.py ===')
print()

panel_path = Path('frontend/src/components/DeepAnalysisPanel.svelte')
content = panel_path.read_text(encoding='utf-8')

# Ищем блок runAnalysis
lines = content.split('\n')
run_analysis_start = None
for i, line in enumerate(lines):
    if 'async function runAnalysis' in line:
        run_analysis_start = i
        print(f'✓ Найдена функция runAnalysis на строке {i+1}')
        break

if run_analysis_start is None:
    print('❌ Функция runAnalysis не найдена')
    exit(1)

# Печатаем текущий код runAnalysis для диагностики
print()
print('Текущий код runAnalysis:')
print('=' * 60)
for j in range(run_analysis_start, min(run_analysis_start + 25, len(lines))):
    print(f'{j+1:4d}: {lines[j]}')
print('=' * 60)
print()

# Проверяем есть ли .json() после api.post
has_json = False
for i in range(run_analysis_start, min(run_analysis_start + 25, len(lines))):
    if 'api.post' in lines[i] and '.json()' in lines[i]:
        has_json = True
        print(f'✓ .json() уже есть на строке {i+1}')
        break
    if 'const response = await api.post' in lines[i]:
        # Проверяем следующие строки на наличие .json()
        for j in range(i, min(i+5, len(lines))):
            if '.json()' in lines[j]:
                has_json = True
                print(f'✓ .json() найден на строке {j+1}')
                break

if not has_json:
    print('❌ .json() отсутствует после api.post!')
    print()
    print('Исправляю...')
    
    # Ищем строку с const response = await api.post
    for i in range(run_analysis_start, min(run_analysis_start + 25, len(lines))):
        if 'const response = await api.post' in lines[i]:
            # Находим закрывающую скобку api.post
            # Ищем строку где заканчивается объект { json: {...} }
            paren_count = 0
            found_post = False
            for j in range(i, len(lines)):
                line = lines[j]
                for char in line:
                    if char == '(':
                        paren_count += 1
                        found_post = True
                    elif char == ')':
                        paren_count -= 1
                        if found_post and paren_count == 0:
                            # Нашли закрывающую скобку
                            # Проверяем что после неё нет .json()
                            rest_of_line = line[line.rfind(')')+1:]
                            if '.json()' not in rest_of_line:
                                # Добавляем .json()
                                lines[j] = line.rstrip() + '.json()'
                                print(f'✓ Добавлен .json() на строке {j+1}')
                                print(f'   Было: {line.strip()}')
                                print(f'   Стало: {lines[j].strip()}')
                            break
                if found_post and paren_count == 0:
                    break
            break
    
    # Сохраняем
    new_content = '\n'.join(lines)
    panel_path.write_text(new_content, encoding='utf-8', newline='\n')
    print()
    print('✓ Файл обновлён')
else:
    print('ℹ .json() уже присутствует')

# Также добавим более детальное логирование Response
print()
print('Добавляю детальное логирование Response...')

content_new = panel_path.read_text(encoding='utf-8')

old_log = "console.log('🔍 Analysis response:', response)"
new_log = """console.log('🔍 Analysis response:', response)
      console.log('🔍 Response type:', typeof response)
      console.log('🔍 Response keys:', Object.keys(response || {}))
      console.log('🔍 Has visualizations?', !!response?.visualizations)"""

if old_log in content_new:
    content_new = content_new.replace(old_log, new_log)
    panel_path.write_text(content_new, encoding='utf-8', newline='\n')
    print('✓ Добавлено детальное логирование Response')

print()
print('=' * 60)
print('СЛЕДУЮЩИЙ ШАГ:')
print('=' * 60)
print()
print('Frontend перезагрузится автоматически (Vite HMR).')
print()
print('Проверка:')
print('  1. Открой фронтенд')
print('  2. Открой DevTools → Console (F12)')
print('  3. Клик Activity → выбери R203-Temperature → "Запустить анализ"')
print('  4. Смотри в консоль — должны появиться:')
print('     🔍 Analysis response: {analysis_id: "...", visualizations: {...}, ...}')
print('     🔍 Response type: object')
print('     🔍 Response keys: ["analysis_id", "status", "visualizations", ...]')
print('     🔍 Has visualizations? true')
print('     📈 Visualization data: {has_visualizations: true, labels_count: 720, ...}')
print()
print('Если response всё ещё Response объект — скинь вывод консоли!')