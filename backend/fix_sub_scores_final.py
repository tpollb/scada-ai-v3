from pathlib import Path

print('=== fix_sub_scores_final.py ===')
print()

chat_path = Path('api/routes/chat.py')
content = chat_path.read_text(encoding='utf-8')

# Проверка — применён ли уже фикс
if 'deterministic_report' in content:
    print('ℹ Фикс уже применён в chat.py')
    print('Проверяю что именно используется для sub_scores...')
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        if 'sub_scores=' in line and 'deterministic_report' in line:
            print(f'✓ Строка {i}: {line.strip()}')
    exit(0)

# Ищем точную строку с sub_scores=parsed.get("sub_scores", {})
target_line = '            sub_scores=parsed.get("sub_scores", {}),'
target_line_idx = None
lines = content.split('\n')

for i, line in enumerate(lines):
    if target_line in line or 'sub_scores=parsed.get("sub_scores", {})' in line:
        target_line_idx = i
        print(f'✓ Нашёл целевую строку {i+1}: {line.strip()}')
        break

if target_line_idx is None:
    print('⚠ Целевая строка не найдена!')
    print('Показываю все строки с sub_scores:')
    for i, line in enumerate(lines, 1):
        if 'sub_scores' in line:
            print(f'  {i}: {line}')
    exit(1)

# Ищем начало report = HealthReport(
health_report_start = None
for i in range(target_line_idx, max(-1, target_line_idx - 20), -1):
    if 'report = HealthReport(' in lines[i]:
        health_report_start = i
        print(f'✓ Нашёл HealthReport на строке {i+1}')
        break

if health_report_start is None:
    print('⚠ Не нашёл начало HealthReport')
    exit(1)

# Вставляем код ПЕРЕД HealthReport
insert_code = [
    '        # sub_scores вычисляем ДЕТЕРМИНИРОВАННО из реальных данных (не из LLM)',
    '        from modules.health.analysis import compute_health_report',
    '        deterministic_report = compute_health_report(data)',
    '        log.info("Using deterministic sub_scores", sub_scores=deterministic_report.sub_scores)',
    '',
]

lines = lines[:health_report_start] + insert_code + lines[health_report_start:]

# Заменяем sub_scores (с учётом сдвига на количество вставленных строк)
new_target_idx = target_line_idx + len(insert_code)
old_line = lines[new_target_idx]
lines[new_target_idx] = old_line.replace(
    'sub_scores=parsed.get("sub_scores", {})',
    'sub_scores=deterministic_report.sub_scores'
)
print(f'✓ Замена на строке {new_target_idx+1}:')
print(f'  Было: {old_line.strip()}')
print(f'  Стало: {lines[new_target_idx].strip()}')

# Сохраняем
content = '\n'.join(lines)
chat_path.write_text(content, encoding='utf-8', newline='\n')

print()
print('=' * 60)
print('✓ ФИКС ПРИМЕНЁН')
print('=' * 60)
print()
print('Что изменилось:')
print('  1. Перед HealthReport вставлено:')
print('     deterministic_report = compute_health_report(data)')
print('  2. sub_scores теперь берётся из deterministic_report')
print('  3. Добавлено логирование sub_scores при запросе')
print()
print('Backend перезагрузится автоматически (hot-reload).')
print()
print('ПРОВЕРКА:')
print('  1. Напиши "покажи здоровье здания"')
print('  2. В логах backend появится:')
print('     [info] Using deterministic sub_scores')
print('     sub_scores={... alarms, environmental, equipment, energy ...}')
print('  3. В UI под статусом HealthScoreCard появится:')
print('     "55 = Аварии 19 + Среда 22 + Оборудование 12 + Энергия 3"')
print()
print('Когда появится — скажи "детализация работает" и коммитим v3.1.0')