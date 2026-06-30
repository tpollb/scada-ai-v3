"""Промпты для LLM-интерпретации результатов глубокого анализа"""

DDA_SYSTEM_PROMPT = """Ты — старший инженер-аналитик SCADA-системы промышленного здания.

Твоя задача — дать ДЕТАЛЬНУЮ техническую интерпретацию на основе предоставленных данных.

СТРОГИЕ ЗАПРЕТЫ:
- ЗАПРЕЩЕНО использовать любые эмодзи
- ЗАПРЕЩЕНО использовать символ решётки (#)
- ЗАПРЕЩЕНО использовать markdown заголовки
- ЗАПРЕЩЕНЫ общие фразы без конкретики ("проблемы с датчиками", "возможные проблемы")

ТРЕБОВАНИЯ К КОНКРЕТИКЕ:
- В КАЖДОМ утверждении используй КОНКРЕТНЫЕ ЦИФРЫ из входных данных
- Указывай ТОЧНЫЕ НАЗВАНИЯ ТЕГОВ (например "KITCHEN2-CO2", а не "зона 1")
- Указывай ТОЧНЫЕ ПЕРИОДЫ (например "288 точек = 24 часа", а не "сутки")
- Указывай ТОЧНЫЕ ЗНАЧЕНИЯ (r = 0.62, p-value = 0.001, 1469 аномалий)
- Приводи ВЫЧИСЛЕННЫЕ МЕТРИКИ (процент от нормы, отклонение в единицах измерения)
- Для каждого тега указывай ЕДИНИЦЫ ИЗМЕРЕНИЯ (ppm, °C, %, кВт·ч)

ФОРМАТ ОТВЕТА (СТРОГО СЛЕДУЙ):

РЕЗЮМЕ
[2-3 предложения с упоминанием конкретных тегов и ключевых метрик. Пример: "В тегах KITCHEN2-CO2 (среднее 850 ppm) и R201-CO2 (среднее 920 ppm) обнаружено 1469 аномалий за период 30 дней."]

КЛЮЧЕВЫЕ НАХОДКИ
- [Конкретный факт с цифрами. Пример: "Тег KITCHEN2-CO2: 529 аномалий типа spike (отклонения >3σ от среднего 850 ppm),主要集中在 рабочие часы 8:00-18:00."]
- [Конкретный факт. Пример: "Корреляция KITCHEN2-CO2 ↔ R201-CO2: r = 0.62 (p < 0.001), что указывает на общий источник выбросов."]
- [Конкретный факт. Пример: "Сезонность KITCHEN2-CO2: доминирующий период 288 точек (24 часа) с мощностью 0.73 и уверенностью 82%."]

ВОЗМОЖНЫЕ ПРИЧИНЫ
- [Техническая причина с объяснением механизма. Пример: "Синхронные пики CO2 в обеих зонах в 12:00-14:00 (обеденное время) указывают на работу кухонного оборудования или вентиляционной системы."]
- [Причина. Пример: "Отсутствие суточной цикличности в R201-CO2 (мощность сезонности 0.12) может указывать на неисправность датчика или постоянный источник выбросов."]

РЕКОМЕНДАЦИИ
- Приоритет: высокий. [Конкретное действие с указанием оборудования]. Ожидаемый эффект: [измеримый результат в цифрах].
- Приоритет: средний. [Действие]. Ожидаемый эффект: [результат].
- Приоритет: низкий. [Действие]. Ожидаемый эффект: [результат].

ПРОГНОЗ
[Что произойдёт через 7/30 дней если ничего не менять, с оценкой в цифрах]

ВАЖНО:
- НЕ выдумывай данные которых нет в input
- Используй ТОЛЬКО предоставленные числа и теги
- Отвечай на русском языке
- Каждый пункт должен содержать МИНИМУМ 2 конкретные цифры
- ПИШИ ПРОСТОЙ ТЕКСТ БЕЗ СПЕЦСИМВОЛОВ
"""


def _safe_format(value, fmt=".2f", default="N/A"):
    if value is None: return default
    try:
        return f"{float(value):{fmt}}"
    except (ValueError, TypeError):
        return str(value) if value is not None else default


def build_dda_prompt(analysis_result: dict) -> str:
    """Компактный промпт для LLM — только ключевые метрики, без сырых массивов"""
    
    lines = [
        "Проанализируй результаты глубокого анализа данных SCADA-системы.",
        "",
        "=== ОСНОВНАЯ ИНФОРМАЦИЯ ===",
        f"Период анализа: {analysis_result.get('period', 'N/A')}",
        f"Теги: {', '.join(analysis_result.get('tags', []))}",
    ]
    
    # Summary (если есть — это самое важное!)
    summary = analysis_result.get('summary')
    if summary:
        lines.append("")
        lines.append(f"Краткое резюме: {summary}")
    
    # === СТАТИСТИКА (может быть None для multi-tag) ===
    stats = analysis_result.get('statistics')
    if stats and isinstance(stats, dict):
        lines.append("")
        lines.append("=== СТАТИСТИКА ===")
        for tag_name, tag_stats in stats.items():
            if isinstance(tag_stats, dict):
                mean = tag_stats.get('mean')
                std = tag_stats.get('std')
                mn = tag_stats.get('min')
                mx = tag_stats.get('max')
                lines.append(f"• {tag_name}: mean={_safe_format(mean)}, std={_safe_format(std)}, range=[{_safe_format(mn)}..{_safe_format(mx)}]")
    
    # === АНОМАЛИИ (только количество, не индексы!) ===
    anomalies = analysis_result.get('anomalies')
    if anomalies and isinstance(anomalies, dict):
        lines.append("")
        lines.append("=== АНОМАЛИИ ===")
        
        # Проверяем структуру: может быть per_tag или сразу по тегам
        per_tag = anomalies.get('per_tag', anomalies)
        
        if isinstance(per_tag, dict):
            for tag_name, anom_data in per_tag.items():
                if isinstance(anom_data, dict):
                    count = len(anom_data.get('anomaly_indices', []))
                    anom_type = anom_data.get('anomaly_type', 'unknown')
                    lines.append(f"• {tag_name}: {count} аномалий (тип: {anom_type})")
                elif isinstance(anom_data, int):
                    lines.append(f"• {tag_name}: {anom_data} аномалий")
        
        # Общая статистика
        total = anomalies.get('total_anomalies')
        if total:
            lines.append(f"Всего аномалий: {total}")
    
    # === СЕЗОННОСТЬ (только доминирующие периоды) ===
    seasonality = analysis_result.get('seasonality')
    if seasonality and isinstance(seasonality, dict):
        lines.append("")
        lines.append("=== СЕЗОННОСТЬ ===")
        for tag_name, season_data in seasonality.items():
            if not isinstance(season_data, dict):
                continue
            
            lines.append(f"• {tag_name}:")
            periods = season_data.get('periods', {})
            
            if isinstance(periods, dict):
                detected = periods.get('detected_periods', [])
                if isinstance(detected, list) and detected:
                    # Берём топ-3 периода
                    top_periods = detected[:3]
                    for p in top_periods:
                        if isinstance(p, dict):
                            period = p.get('period', 'N/A')
                            power = p.get('power', 0)
                            conf = p.get('confidence', 0)
                            # Форматируем период в дни/часы
                            hours = period / 12 if isinstance(period, (int, float)) else 0
                            days = hours / 24
                            if days >= 1:
                                period_str = f"~{days:.1f} дней"
                            elif hours >= 1:
                                period_str = f"~{hours:.1f}ч"
                            else:
                                period_str = f"{period} точек"
                            lines.append(f"    Период: {period_str} (power={_safe_format(power)}, conf={_safe_format(conf, '.1%')})")
                
                dominant = periods.get('dominant_period', {})
                if isinstance(dominant, dict) and dominant:
                    period = dominant.get('period')
                    conf = dominant.get('confidence', 0)
                    lines.append(f"    Доминирующий: период={period}, уверенность={_safe_format(conf, '.1%')}")
            
            # Паттерн (только статистика)
            pattern = season_data.get('pattern')
            if isinstance(pattern, dict):
                amplitude = pattern.get('amplitude')
                if amplitude is not None:
                    lines.append(f"    Амплитуда: {_safe_format(amplitude)}")
    
    # === КОРРЕЛЯЦИИ (только сильные пары) ===
    correlations = analysis_result.get('correlations')
    if correlations and isinstance(correlations, dict):
        lines.append("")
        lines.append("=== КОРРЕЛЯЦИИ ===")
        
        tags = correlations.get('tags', [])
        matrix = correlations.get('matrix', [])
        method = correlations.get('method', 'pearson')
        valid_points = correlations.get('valid_points', 'N/A')
        
        lines.append(f"Метод: {method}, валидных точек: {valid_points}")
        
        if isinstance(tags, list) and isinstance(matrix, list):
            # Извлекаем сильные корреляции (|r| > 0.5)
            strong_pairs = []
            for i in range(len(tags)):
                for j in range(i+1, len(tags)):
                    if i < len(matrix) and j < len(matrix[i]):
                        coef = matrix[i][j]
                        try:
                            coef_val = float(coef)
                            if abs(coef_val) > 0.5:
                                strong_pairs.append((tags[i], tags[j], coef_val))
                        except (ValueError, TypeError):
                            pass
            
            if strong_pairs:
                strong_pairs.sort(key=lambda x: abs(x[2]), reverse=True)
                lines.append("Сильные корреляции (|r| > 0.5):")
                for tag1, tag2, coef in strong_pairs[:5]:
                    lines.append(f"  • {tag1} ↔ {tag2}: r={coef:+.3f}")
            else:
                lines.append("Сильных корреляций не обнаружено (все |r| < 0.5)")
    
    # === A/B СРАВНЕНИЕ (если есть) ===
    ab = analysis_result.get('ab_comparison')
    if ab and isinstance(ab, dict):
        lines.append("")
        lines.append("=== A/B СРАВНЕНИЕ ===")
        
        lines.append(f"Режим: {ab.get('mode', 'N/A')}")
        
        stats = ab.get('statistics', {})
        if isinstance(stats, dict):
            delta = stats.get('delta', {})
            if isinstance(delta, dict):
                lines.append(f"Изменение среднего: {_safe_format(delta.get('mean'), '+.2%')}")
        
        sig = ab.get('significance', {})
        if isinstance(sig, dict):
            pval = sig.get('p_value')
            interp = sig.get('interpretation', '')
            if pval is not None:
                lines.append(f"p-value: {pval} ({interp})")
        
        verdict = ab.get('verdict', {})
        if isinstance(verdict, dict):
            severity = verdict.get('severity')
            summary_ab = verdict.get('summary')
            if severity:
                lines.append(f"Вердикт: {severity}")
            if summary_ab:
                lines.append(f"  {summary_ab}")
    
    lines.append("")
    lines.append("=== ТВОЯ ЗАДАЧА ===")
    lines.append("Дай экспертную интерпретацию этих данных.")
    lines.append("Объясни что происходит в системе и почему.")
    lines.append("Дай конкретные рекомендации инженеру.")
    lines.append("Используй markdown для структурирования ответа.")

    result = "\n".join(lines)
    
    # Логируем размер
    from structlog import get_logger
    log = get_logger()
    log.info("DDA prompt built", chars=len(result), 
             estimated_tokens=len(result) // 4)
    
    return result
