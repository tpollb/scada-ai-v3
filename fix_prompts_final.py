#!/usr/bin/env python3
"""
fix_prompts_final.py - перезаписывает build_dda_prompt с safe форматированием
"""
from pathlib import Path

prompts_path = Path('backend/modules/deep_analysis/prompts.py')
content = prompts_path.read_text(encoding='utf-8')

print('Перезаписываю функцию build_dda_prompt...')
print()

# Находим начало и конец функции build_dda_prompt
lines = content.split('\n')

# Ищем def build_dda_prompt
start_idx = None
for i, line in enumerate(lines):
    if line.startswith('def build_dda_prompt('):
        start_idx = i
        break

if start_idx is None:
    print('❌ Функция build_dda_prompt не найдена')
    exit(1)

# Ищем конец функции (следующая функция или конец файла)
end_idx = len(lines)
for i in range(start_idx + 1, len(lines)):
    if lines[i].startswith('def ') or lines[i].startswith('class '):
        end_idx = i
        break

print(f'Найдена функция на строках {start_idx+1}-{end_idx}')

# Новая функция с safe форматированием
new_function = '''def _safe_format(value, fmt: str = ".2f", default: str = "N/A") -> str:
    """Безопасное форматирование чисел с fallback на 'N/A'"""
    if value is None:
        return default
    try:
        num = float(value)
        return f"{num:{fmt}}"
    except (ValueError, TypeError):
        return str(value) if value else default


def _safe_pct(value, default: str = "N/A") -> str:
    """Безопасное форматирование процентов"""
    if value is None:
        return default
    try:
        num = float(value)
        # Если число уже в процентах (больше 1.5), форматируем как есть
        if abs(num) > 1.5:
            return f"{num:.1f}%"
        else:
            return f"{num:.1%}"
    except (ValueError, TypeError):
        return str(value) if value else default


def build_dda_prompt(analysis_result: dict) -> str:
    """
    Строит user prompt с результатами глубокого анализа.
    
    Args:
        analysis_result: полный результат анализа из /deep_analysis/run
        
    Returns:
        Строка с отформатированными данными для LLM
    """
    lines = [
        "Проанализируй результаты глубокого анализа данных SCADA-системы.",
        "",
        "=== ОСНОВНАЯ ИНФОРМАЦИЯ ===",
        f"Период анализа: {analysis_result.get('period', 'N/A')}",
        f"Количество тегов: {len(analysis_result.get('tags', []))}",
        "",
    ]

    # Статистика
    if 'statistics' in analysis_result:
        lines.append("=== СТАТИСТИКА ===")
        for tag_name, stats in analysis_result['statistics'].items():
            lines.append(f"• {tag_name}:")
            lines.append(f"    Среднее: {_safe_format(stats.get('mean'))}")
            lines.append(f"    Медиана: {_safe_format(stats.get('median'))}")
            lines.append(f"    Std: {_safe_format(stats.get('std'))}")
            lines.append(f"    Мин-Макс: {_safe_format(stats.get('min'))} - {_safe_format(stats.get('max'))}")
            lines.append(f"    Диапазон: {_safe_format(stats.get('range'))}")
            lines.append("")

    # Аномалии
    if 'anomalies' in analysis_result:
        lines.append("=== АНОМАЛИИ ===")
        for tag_name, anomaly_data in analysis_result['anomalies'].items():
            total = anomaly_data.get('total_anomalies', 0)
            anomaly_type = anomaly_data.get('anomaly_type', 'N/A')
            lines.append(f"• {tag_name}: {total} аномалий (тип: {anomaly_type})")
            if 'anomaly_indices' in anomaly_data:
                indices = anomaly_data['anomaly_indices'][:5]
                lines.append(f"    Индексы: {indices}...")
            if 'anomaly_values' in anomaly_data:
                values = anomaly_data['anomaly_values'][:5]
                lines.append(f"    Значения: {values}...")
        lines.append("")

    # Сезонность
    if 'seasonality' in analysis_result:
        lines.append("=== СЕЗОННОСТЬ ===")
        for tag_name, season_data in analysis_result['seasonality'].items():
            lines.append(f"• {tag_name}:")
            
            # Периоды
            periods = season_data.get('periods', {})
            if periods:
                dominant = periods.get('dominant_period', {})
                if dominant:
                    lines.append(f"    Доминирующий период: {dominant.get('period', 'N/A')} точек")
                    lines.append(f"    Уверенность: {_safe_pct(dominant.get('confidence'))}")
                    lines.append(f"    Мощность: {_safe_format(dominant.get('power'))}")
                
                # Декомпозиция
                decomp = periods.get('decomposition', {})
                if decomp:
                    lines.append(f"    Декомпозиция:")
                    lines.append(f"      Тренд: {_safe_pct(decomp.get('trend'))}")
                    lines.append(f"      Сезонность: {_safe_pct(decomp.get('seasonal'))}")
                    lines.append(f"      Остаток: {_safe_pct(decomp.get('residual'))}")
            
            # Паттерн
            pattern = season_data.get('pattern', {})
            if pattern:
                lines.append(f"    Типичный паттерн:")
                lines.append(f"      Период: {pattern.get('period', 'N/A')} точек")
                lines.append(f"      Мин: {_safe_format(pattern.get('min'))}")
                lines.append(f"      Макс: {_safe_format(pattern.get('max'))}")
                lines.append(f"      Амплитуда: {_safe_format(pattern.get('amplitude'))}")
            lines.append("")

    # Корреляции
    if 'correlations' in analysis_result:
        lines.append("=== КОРРЕЛЯЦИИ ===")
        corr_data = analysis_result['correlations']
        if 'matrix' in corr_data:
            matrix = corr_data['matrix']
            tags = corr_data.get('tags', [])
            
            # Показываем сильные корреляции
            strong_corr = []
            for i in range(len(tags)):
                for j in range(i+1, len(tags)):
                    coef = matrix[i][j]
                    try:
                        if abs(float(coef)) > 0.5:
                            strong_corr.append((tags[i], tags[j], coef))
                    except (ValueError, TypeError):
                        pass
            
            if strong_corr:
                strong_corr.sort(key=lambda x: abs(float(x[2])), reverse=True)
                for tag1, tag2, coef in strong_corr[:5]:
                    lines.append(f"• {tag1} ↔ {tag2}: r={_safe_format(coef, '+.3f')}")
            else:
                lines.append("• Сильных корреляций не обнаружено (|r| < 0.5)")
        lines.append("")

    # A/B анализ (если есть)
    if 'ab_comparison' in analysis_result:
        lines.append("=== A/B СРАВНЕНИЕ ===")
        ab = analysis_result['ab_comparison']
        
        lines.append(f"Режим: {ab.get('mode', 'N/A')}")
        lines.append(f"Период A: {ab.get('snapshot_a', {}).get('period', 'N/A')}")
        lines.append(f"Период B: {ab.get('snapshot_b', {}).get('period', 'N/A')}")
        lines.append("")
        
        # Статистика
        stats = ab.get('statistics', {})
        delta = stats.get('delta', {})
        if delta:
            lines.append("Изменения:")
            lines.append(f"  Среднее: {_safe_pct(delta.get('mean'))}")
            lines.append(f"  Std: {_safe_pct(delta.get('std'))}")
            lines.append(f"  Мин: {_safe_pct(delta.get('min'))}")
            lines.append(f"  Макс: {_safe_pct(delta.get('max'))}")
            lines.append("")
        
        # Значимость
        sig = ab.get('significance', {})
        if sig:
            lines.append("Статистическая значимость:")
            lines.append(f"  t-stat: {_safe_format(sig.get('t_stat'), '.3f')}")
            lines.append(f"  p-value: {_safe_format(sig.get('p_value'), '.6f')}")
            lines.append(f"  Интерпретация: {sig.get('interpretation', 'N/A')}")
            lines.append("")
        
        # Паттерны
        patterns = ab.get('pattern_comparison', {})
        if patterns:
            lines.append("Сравнение паттернов:")
            lines.append(f"  Периоды совпадают: {patterns.get('period_match', 'N/A')}")
            lines.append(f"  Изменение амплитуды: {_safe_pct(patterns.get('delta_amplitude_pct', 0) / 100)}")
            if patterns.get('pattern_correlation') is not None:
                lines.append(f"  Корреляция паттернов: {_safe_format(patterns['pattern_correlation'], '.3f')}")
            lines.append("")
        
        # Вердикт
        verdict = ab.get('verdict', {})
        if verdict:
            lines.append(f"Автоматический вердикт: {verdict.get('severity', 'N/A')}")
            if verdict.get('summary'):
                lines.append(f"  {verdict['summary']}")
            lines.append("")

    lines.append("=== ТВОЯ ЗАДАЧА ===")
    lines.append("Дай экспертную интерпретацию этих данных.")
    lines.append("Объясни что происходит в системе и почему.")
    lines.append("Дай конкретные рекомендации инженеру.")
    lines.append("Используй markdown для структурирования ответа.")

    return "\\n".join(lines)
'''

# Удаляем старую функцию и вставляем новую
new_lines = lines[:start_idx] + new_function.split('\n') + lines[end_idx:]
new_content = '\n'.join(new_lines)

# Сохраняем
prompts_path.write_text(new_content, encoding='utf-8', newline='\n')

print()
print('✅ Функция build_dda_prompt перезаписана')
print()

# Проверяем синтаксис
import ast
try:
    ast.parse(new_content)
    print('✅ Файл синтаксически корректен')
except SyntaxError as e:
    print(f'❌ Синтаксическая ошибка: {e}')