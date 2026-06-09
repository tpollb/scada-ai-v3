from pathlib import Path

print('=== fix_render_async.py ===')
print()

# ============================================================================
# 1. Делаем render_all async в renderers.py
# ============================================================================
renderers_path = Path('modules/health/renderers.py')
content = renderers_path.read_text(encoding='utf-8')

# 1.1. Меняем def render_all на async def render_all
if 'async def render_all' in content:
    print('ℹ render_all уже async')
elif 'def render_all(report: HealthReport)' in content:
    content = content.replace(
        'def render_all(report: HealthReport)',
        'async def render_all(report: HealthReport)'
    )
    print('✓ render_all сделан async')
else:
    print('⚠ Не нашёл render_all')

# 1.2. Добавляем await перед render_visual
if 'await render_visual' in content:
    print('ℹ await перед render_visual уже есть')
elif '"visual": render_visual(report)' in content:
    content = content.replace(
        '"visual": render_visual(report)',
        '"visual": await render_visual(report)'
    )
    print('✓ Добавлен await перед render_visual')
else:
    print('⚠ Не нашёл вызов render_visual')

renderers_path.write_text(content, encoding='utf-8', newline='\n')

# ============================================================================
# 2. Добавляем await в chat.py
# ============================================================================
chat_path = Path('api/routes/chat.py')
content = chat_path.read_text(encoding='utf-8')

# 2.1. Основной вызов render_all
if 'await render_all(report)' in content:
    print('ℹ await render_all уже есть в chat.py')
elif 'rendered = render_all(report)' in content:
    content = content.replace(
        'rendered = render_all(report)',
        'rendered = await render_all(report)'
    )
    print('✓ Добавлен await перед render_all в chat.py')
else:
    print('⚠ Не нашёл render_all в chat.py')

# 2.2. В fallback блоке (когда LLM не вернул JSON)
if 'rendered = render_all(report)\n        return ChatResponse(' in content:
    # Если ещё не заменён
    pass
# Проверим все вхождения
count = content.count('render_all(report)')
count_await = content.count('await render_all(report)')
if count > count_await:
    # Заменяем все оставшиеся
    content = content.replace(
        'rendered = render_all(report)',
        'rendered = await render_all(report)'
    )
    print(f'✓ Все вызовы render_all теперь с await')

chat_path.write_text(content, encoding='utf-8', newline='\n')

print()
print('=' * 60)
print('ЧТО ИСПРАВЛЕНО:')
print('=' * 60)
print('1. render_all → async def render_all')
print('2. render_all внутри делает await render_visual(report)')
print('3. chat.py делает rendered = await render_all(report)')
print()
print('Перезапусти backend и попробуй снова: "покажи здоровье здания"')