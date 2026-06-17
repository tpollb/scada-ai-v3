from pathlib import Path

print('=== fix_widget_rendering.py ===')
print()

PROJECT_ROOT = Path('.')

# ============================================================================
# 1. Добавляем console.log в Home.svelte для дебага
# ============================================================================
home_path = PROJECT_ROOT / 'frontend/src/routes/Home.svelte'
if home_path.exists():
    content = home_path.read_text(encoding='utf-8')
    
    # Ищем блок где обрабатывается resp.visual
    old_block = '''      if (resp.visual?.widgets && resp.visual.widgets.length > 0) {
        currentWidgets = resp.visual.widgets
      }'''
    
    new_block = '''      // DEBUG: логируем что пришло с backend
      console.log('Chat response:', {
        status: resp.status,
        has_visual: !!resp.visual,
        visual_widgets: resp.visual?.widgets,
        widgets_count: resp.visual?.widgets?.length || 0
      })
      
      if (resp.visual?.widgets && resp.visual.widgets.length > 0) {
        console.log('Setting widgets:', resp.visual.widgets)
        currentWidgets = resp.visual.widgets
      } else {
        console.log('No widgets to render')
      }'''
    
    if old_block in content:
        content = content.replace(old_block, new_block)
        home_path.write_text(content, encoding='utf-8', newline='\n')
        print('✓ Home.svelte: добавлен console.log для дебага')
    else:
        print('⚠ Не найден точный блок в Home.svelte')

# ============================================================================
# 2. Добавляем лог в backend что возвращает visual.widgets
# ============================================================================
chat_path = PROJECT_ROOT / 'backend/api/routes/chat.py'
if chat_path.exists():
    content = chat_path.read_text(encoding='utf-8')
    
    # Ищем return ChatResponse в handle_analytics_query
    # Добавляем лог перед return
    old_return = '''        return ChatResponse(
            response=summary,
            status="success",
            visual={'''
    
    new_return = '''        log.info("handle_analytics_query returning",
                 summary_len=len(summary),
                 has_trends="trends" in trends,
                 trends_count=len(trends.get("trends", {})),
                 correlations_count=len(correlations),
                 top_issues_count=len(top_issues),
                 has_llm="summary" in llm_result)
        
        return ChatResponse(
            response=summary,
            status="success",
            visual={'''
    
    if old_return in content:
        content = content.replace(old_return, new_return)
        chat_path.write_text(content, encoding='utf-8', newline='\n')
        print('✓ chat.py: добавлен лог перед return ChatResponse')
    else:
        print('⚠ Не найден точный return в chat.py')
    
    # Также добавляем лог после формирования widget
    old_widget = '''                    {
                        "type": "analytics_panel",
                        "data": {
                            "period_days": 30,
                            "trends": trends["trends"],
                            "correlations": correlations,
                            "top_issues": top_issues,
                            "summary": llm_result.get("summary", ""),
                            "insights": llm_result.get("insights", []),
                            "recommendations": llm_result.get("recommendations", []),
                            "forecast": llm_result.get("forecast", {})
                        },
                        "size": "wide"
                    }'''
    
    new_widget = '''                    {
                        "type": "analytics_panel",
                        "data": {
                            "period_days": 30,
                            "trends": trends["trends"],
                            "correlations": correlations,
                            "top_issues": top_issues,
                            "summary": llm_result.get("summary", ""),
                            "insights": llm_result.get("insights", []),
                            "recommendations": llm_result.get("recommendations", []),
                            "forecast": llm_result.get("forecast", {})
                        },
                        "size": "wide"
                    }
                ]
            }
        )
    
    except Exception as e:
        log.error("handle_analytics_query failed", error=str(e), exc_info=True)'''
    
    if old_widget in content:
        # Проверяем что после widget идёт правильный except
        if 'except Exception as e:' in content.split(old_widget)[1][:200]:
            print('✓ chat.py: структура try/except уже правильная')
        else:
            print('⚠ chat.py: нужно проверить структуру try/except')

print()
print('=' * 60)
print('ЧТО ДОБАВЛЕНО:')
print('=' * 60)
print()
print('1. frontend/src/routes/Home.svelte:')
print('   • console.log для дебага — показывает что пришло с backend')
print('   • Логирует: has_visual, visual_widgets, widgets_count')
print()
print('2. backend/api/routes/chat.py:')
print('   • Лог перед return ChatResponse')
print('   • Показывает: summary_len, trends_count, correlations_count, etc.')
print()
print('Backend перезагрузится автоматически (hot-reload).')
print('Frontend перезагрузится автоматически (Vite HMR).')
print()
print('ПРОВЕРКА:')
print('1. Открой DevTools → Console (F12)')
print('2. В чате напиши: "покажи аналитику"')
print('3. Смотри в консоль браузера:')
print('   - Должно появиться: "Chat response: { has_visual: true, ... }"')
print('   - Должно появиться: "Setting widgets: [...]"')
print()
print('4. Смотри в backend логи:')
print('   - Должно появиться: "handle_analytics_query returning"')
print('   - Должно показать: trends_count=5, correlations_count=1, etc.')
print()
print('5. Скинь вывод из обеих консолей — дам точечный фикс')