import urllib.request
import json

print('Отправляю запрос к API (это займёт ~60 сек)...')

req = urllib.request.Request(
    'http://localhost:8081/chat',
    data=json.dumps({'message': 'покажи здоровье здания'}).encode('utf-8'),
    headers={'Content-Type': 'application/json'},
    method='POST'
)

try:
    with urllib.request.urlopen(req, timeout=120) as response:
        body = response.read().decode('utf-8')
        data = json.loads(body)
except Exception as e:
    print(f'⚠ Ошибка: {e}')
    exit(1)

# Сохраняем полный ответ
with open('chat_response.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f'✓ Status: {response.status}')
print('✓ Ответ сохранён в chat_response.json')
print()

# Извлекаем health_score виджет
if 'visual' in data and 'widgets' in data['visual']:
    health_score = [w for w in data['visual']['widgets'] if w['type'] == 'health_score']
    if health_score:
        print('=== health_score виджет ===')
        print(json.dumps(health_score[0], ensure_ascii=False, indent=2))
        
        # Показываем sub_scores отдельно
        if 'data' in health_score[0] and 'sub_scores' in health_score[0]['data']:
            print()
            print('=== sub_scores ===')
            print(json.dumps(health_score[0]['data']['sub_scores'], ensure_ascii=False, indent=2))
    else:
        print('⚠ health_score виджет не найден')
else:
    print('⚠ В ответе нет visual.widgets')
    print('Ключи ответа:', list(data.keys()))
    print('Preview:', json.dumps(data, ensure_ascii=False)[:500])