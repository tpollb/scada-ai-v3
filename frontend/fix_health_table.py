from pathlib import Path

print('=== fix_health_table.py ===')
print()

path = Path('src/components/health/HealthScoreCard.svelte')
content = path.read_text(encoding='utf-8')

# Замены в таблице штрафов
replacements = [
    # Аварии
    ('>Авария High (крит.)<', '>Авария высокого приоритета (крит.)<'),
    ('>Авария Medium<', '>Авария среднего приоритета<'),
    ('>Авария Low<', '>Авария низкого приоритета<'),
    
    # Параметры
    ('>CRITICAL параметр<', '>Критичный параметр<'),
    ('>WARNING параметр<', '>Параметр с отклонением<'),
]

count = 0
for old, new in replacements:
    if old in content:
        content = content.replace(old, new)
        count += 1
        print(f'  ✓ {old[1:-1]} → {new[1:-1]}')
    else:
        print(f'  ⚠ Не нашёл: {old}')

path.write_text(content, encoding='utf-8', newline='\n')
print()
print(f'✓ Обновлено {count} из {len(replacements)} записей в таблице штрафов')
print(f'✓ Файл: {path}')
print()
print('Таблица теперь:')
print('  • Авария высокого приоритета (крит.)    -15 (макс -50)')
print('  • Авария среднего приоритета            -4 (макс -25)')
print('  • Авария низкого приоритета             -0.5 (макс -10)')
print('  • Битый датчик                          до -40')
print('  • Офлайн тег                            до -30')
print('  • Критичный параметр                    score=15')
print('  • Параметр с отклонением                score=55')
print()
print('Vite подхватит через HMR. Обнови страницу.')