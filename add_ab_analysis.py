#!/usr/bin/env python3
"""
add_ab_analysis.py - добавляет модуль A/B анализа и endpoint
"""
from pathlib import Path

print('=' * 80)
print('ДОБАВЛЕНИЕ: Модуль A/B анализа')
print('=' * 80)
print()

# 1. Создаём ab.py
print('【1】Создаём backend/modules/deep_analysis/analyzers/ab.py')
print('-' * 80)

ab_path = Path('backend/modules/deep_analysis/analyzers/ab.py')
ab_content = '''"""A/B анализ: сравнение двух временных периодов или двух тегов

Модуль для сравнительного анализа:
- Before/After: один тег в разные периоды
- Equipment Comparison: два тега в один период
"""
from typing import Optional
from datetime import datetime
import numpy as np
from scipy import stats
from structlog import get_logger

from .stats import compute_basic_stats
from .seasonal import detect_dominant_periods, get_seasonal_pattern

log = get_logger()


def compare_snapshots(data_a: list[float], data_b: list[float]) -> dict:
    """
    Сравнивает два набора данных (snapshot A vs snapshot B).

    Args:
        data_a: значения первого периода/тега
        data_b: значения второго периода/тега

    Returns:
        {
            "statistics": {
                "a": {...},  # базовая статистика для A
                "b": {...},  # базовая статистика для B
                "delta": {...}  # разница в процентах
            },
            "significance": {
                "t_stat": float,
                "p_value": float,
                "cohens_d": float,
                "interpretation": str
            }
        }
    """
    # Базовая статистика
    stats_a = compute_basic_stats(data_a)
    stats_b = compute_basic_stats(data_b)

    # Разница в процентах
    delta = {}
    for key in ['mean', 'median', 'std', 'min', 'max', 'range']:
        val_a = stats_a.get(key, 0)
        val_b = stats_b.get(key, 0)
        
        if val_a != 0:
            delta[key] = ((val_b - val_a) / abs(val_a)) * 100
        else:
            delta[key] = 0 if val_b == 0 else float('inf')

    # Статистическая значимость (Welch's t-test)
    t_stat, p_value = stats.ttest_ind(data_a, data_b, equal_var=False)

    # Effect size (Cohen's d)
    mean_diff = stats_b['mean'] - stats_a['mean']
    pooled_std = np.sqrt((stats_a['variance'] + stats_b['variance']) / 2)
    cohens_d = mean_diff / pooled_std if pooled_std > 0 else 0

    # Интерпретация
    if p_value < 0.001:
        significance_interp = "highly_significant"
    elif p_value < 0.05:
        significance_interp = "significant"
    else:
        significance_interp = "not_significant"

    return {
        "statistics": {
            "a": stats_a,
            "b": stats_b,
            "delta": delta
        },
        "significance": {
            "t_stat": float(t_stat),
            "p_value": float(p_value),
            "cohens_d": float(cohens_d),
            "interpretation": significance_interp
        }
    }


def compare_patterns(
    values_a: list[float],
    values_b: list[float],
    period_a: Optional[int] = None,
    period_b: Optional[int] = None
) -> dict:
    """
    Сравнивает сезонные паттерны двух наборов данных.

    Args:
        values_a: значения первого периода/тега
        values_b: значения второго периода/тега
        period_a: доминирующий период для A (если None - автодетект)
        period_b: доминирующий период для B (если None - автодетект)

    Returns:
        {
            "a": {"period": int, "pattern": [...], "amplitude": float},
            "b": {"period": int, "pattern": [...], "amplitude": float},
            "comparison": {
                "period_match": bool,
                "delta_amplitude_pct": float,
                "pattern_correlation": float
            }
        }
    """
    # Автодетект периодов если не указаны
    if period_a is None:
        periods_a = detect_dominant_periods(values_a)
        period_a = periods_a['dominant_period'] if periods_a['dominant_period'] else 288  # fallback: 24h

    if period_b is None:
        periods_b = detect_dominant_periods(values_b)
        period_b = periods_b['dominant_period'] if periods_b['dominant_period'] else 288

    # Вычисляем паттерны
    pattern_a = get_seasonal_pattern(values_a, period_a)
    pattern_b = get_seasonal_pattern(values_b, period_b)

    # Амплитуды
    amp_a = max(pattern_a) - min(pattern_a)
    amp_b = max(pattern_b) - min(pattern_b)

    # Разница амплитуд в процентах
    delta_amp = ((amp_b - amp_a) / amp_a * 100) if amp_a > 0 else 0

    # Корреляция паттернов (если периоды совпадают)
    pattern_corr = None
    if period_a == period_b and len(pattern_a) == len(pattern_b):
        pattern_corr = float(np.corrcoef(pattern_a, pattern_b)[0, 1])

    return {
        "a": {
            "period": period_a,
            "pattern": pattern_a,
            "amplitude": amp_a
        },
        "b": {
            "period": period_b,
            "pattern": pattern_b,
            "amplitude": amp_b
        },
        "comparison": {
            "period_match": period_a == period_b,
            "delta_amplitude_pct": float(delta_amp),
            "pattern_correlation": pattern_corr
        }
    }


def generate_verdict(
    comparison_result: dict,
    pattern_result: Optional[dict] = None,
    mode: str = "before_after"
) -> dict:
    """
    Генерирует автоматический вердикт на основе результатов анализа.

    Args:
        comparison_result: результат compare_snapshots
        pattern_result: результат compare_patterns (опционально)
        mode: "before_after" или "equipment_comparison"

    Returns:
        {
            "summary": str,
            "key_findings": list[str],
            "recommendations": list[str],
            "severity": str  # "low" | "medium" | "high"
        }
    """
    stats = comparison_result['statistics']
    sig = comparison_result['significance']
    
    delta_mean = stats['delta']['mean']
    delta_std = stats['delta']['std']
    
    findings = []
    recommendations = []
    severity = "low"

    # 1. Анализ разницы средних
    if abs(delta_mean) > 20:
        direction = "увеличилось" if delta_mean > 0 else "уменьшилось"
        findings.append(f"Среднее значение {direction} на {abs(delta_mean):.1f}%")
        severity = "high" if abs(delta_mean) > 50 else "medium"
    elif abs(delta_mean) > 5:
        direction = "увеличилось" if delta_mean > 0 else "уменьшилось"
        findings.append(f"Среднее значение {direction} на {abs(delta_mean):.1f}%")

    # 2. Анализ изменчивости
    if abs(delta_std) > 50:
        direction = "увеличилась" if delta_std > 0 else "уменьшилась"
        findings.append(f"Изменчивость (std) {direction} на {abs(delta_std):.1f}%")
        severity = "high" if abs(delta_std) > 100 else max(severity, "medium")

    # 3. Статистическая значимость
    if sig['interpretation'] == "highly_significant":
        findings.append("Различие статистически высоко значимо (p < 0.001)")
    elif sig['interpretation'] == "significant":
        findings.append("Различие статистически значимо (p < 0.05)")
    else:
        findings.append("Различие статистически не значимо")

    # 4. Анализ сезонных паттернов
    if pattern_result:
        comp = pattern_result['comparison']
        
        if not comp['period_match']:
            findings.append(f"Доминирующие периоды различаются: {pattern_result['a']['period']} vs {pattern_result['b']['period']}")
            severity = "medium"
        
        delta_amp = comp['delta_amplitude_pct']
        if abs(delta_amp) > 30:
            direction = "увеличилась" if delta_amp > 0 else "уменьшилась"
            findings.append(f"Сезонная амплитуда {direction} на {abs(delta_amp):.1f}%")
            severity = max(severity, "medium")

    # 5. Рекомендации
    if mode == "before_after":
        if severity == "high":
            recommendations.append("⚠️ Обнаружены значительные изменения. Требуется детальный анализ причин.")
            recommendations.append("Проверить условия эксплуатации и внешние факторы.")
        elif severity == "medium":
            recommendations.append("Заметные изменения. Рекомендуется мониторинг.")
        else:
            recommendations.append("Существенных изменений не обнаружено.")
    else:  # equipment_comparison
        if severity == "high":
            recommendations.append("⚠️ Оборудование работает по-разному. Проверить настройки и состояние.")
        elif severity == "medium":
            recommendations.append("Есть различия в работе. Стоит обратить внимание.")
        else:
            recommendations.append("Оборудование работает схожим образом.")

    # Формируем summary
    if severity == "high":
        summary = "Обнаружены критические различия"
    elif severity == "medium":
        summary = "Обнаружены заметные различия"
    else:
        summary = "Существенных различий не обнаружено"

    return {
        "summary": summary,
        "key_findings": findings,
        "recommendations": recommendations,
        "severity": severity
    }
'''

ab_path.write_text(ab_content, encoding='utf-8')
print('✅ Модуль ab.py создан')

# 2. Добавляем endpoint в api.py
print()
print('【2】Добавляем endpoint в backend/modules/deep_analysis/api.py')
print('-' * 80)

api_path = Path('backend/modules/deep_analysis/api.py')
api_content = api_path.read_text(encoding='utf-8')

# Проверяем что endpoint ещё не добавлен
if '@app.post("/deep-analysis/ab"' in api_content:
    print('ℹ️  Endpoint уже существует, пропускаем')
else:
    # Добавляем импорт в начало файла (после других импортов)
    import_marker = 'from modules.deep_analysis.collectors.data_fetcher import fetch_multiple_tags'
    if import_marker in api_content:
        # Импорты уже есть, добавляем endpoint в конец
        ab_endpoint = '''

@app.post("/deep-analysis/ab", response_model=None)
async def ab_analysis(request: Request):
    """
    A/B анализ: сравнение двух временных периодов или двух тегов.
    
    Modes:
    - before_after: один тег в разные периоды (snapshot_a.tag == snapshot_b.tag)
    - equipment_comparison: два тега в один период (snapshot_a.tag != snapshot_b.tag)
    """
    from modules.deep_analysis.analyzers.ab import (
        compare_snapshots,
        compare_patterns,
        generate_verdict
    )
    
    body = await request.json()
    
    snapshot_a = body.get('snapshot_a', {})
    snapshot_b = body.get('snapshot_b', {})
    
    tag_a = snapshot_a.get('tag')
    tag_b = snapshot_b.get('tag')
    start_a = datetime.fromisoformat(snapshot_a.get('start'))
    end_a = datetime.fromisoformat(snapshot_a.get('end'))
    start_b = datetime.fromisoformat(snapshot_b.get('start'))
    end_b = datetime.fromisoformat(snapshot_b.get('end'))
    
    log.info(
        "A/B analysis request",
        tag_a=tag_a,
        tag_b=tag_b,
        period_a=f"{start_a} - {end_a}",
        period_b=f"{start_b} - {end_b}"
    )
    
    # Определяем режим
    mode = "before_after" if tag_a == tag_b else "equipment_comparison"
    
    # Получаем данные
    if mode == "before_after":
        # Один тег, два периода
        data_a = await fetch_multiple_tags([tag_a], start_a, end_a)
        data_b = await fetch_multiple_tags([tag_b], start_b, end_b)
        
        values_a = data_a['tags'][tag_a]['values']
        values_b = data_b['tags'][tag_b]['values']
    else:
        # Два тега, два периода (могут быть одинаковыми или разными)
        data_a = await fetch_multiple_tags([tag_a], start_a, end_a)
        data_b = await fetch_multiple_tags([tag_b], start_b, end_b)
        
        values_a = data_a['tags'][tag_a]['values']
        values_b = data_b['tags'][tag_b]['values']
    
    # Базовое сравнение
    comparison = compare_snapshots(values_a, values_b)
    
    # Сравнение паттернов (опционально, если достаточно данных)
    pattern_comparison = None
    if len(values_a) >= 288 and len(values_b) >= 288:  # минимум 24 часа данных
        pattern_comparison = compare_patterns(values_a, values_b)
    
    # Генерируем вердикт
    verdict = generate_verdict(comparison, pattern_comparison, mode)
    
    # Формируем ответ
    result = {
        "mode": mode,
        "snapshot_a": {
            "tag": tag_a,
            "period": f"{start_a.isoformat()} - {end_a.isoformat()}",
            "data_points": len(values_a)
        },
        "snapshot_b": {
            "tag": tag_b,
            "period": f"{start_b.isoformat()} - {end_b.isoformat()}",
            "data_points": len(values_b)
        },
        "comparison": comparison,
        "verdict": verdict
    }
    
    if pattern_comparison:
        result["pattern_comparison"] = pattern_comparison
    
    return result
'''
        
        api_content = api_content + ab_endpoint
        api_path.write_text(api_content, encoding='utf-8')
        print('✅ Endpoint добавлен в api.py')

print()
print('=' * 80)
print('ГОТОВО! Что добавлено:')
print('=' * 80)
print()
print('1. backend/modules/deep_analysis/analyzers/ab.py')
print('   • compare_snapshots() - базовое сравнение статистик')
print('   • compare_patterns() - сравнение сезонных паттернов')
print('   • generate_verdict() - автоматический вердикт')
print()
print('2. Endpoint POST /api/v1/deep-analysis/ab')
print('   • Режим before_after: один тег, два периода')
print('   • Режим equipment_comparison: два тега, два периода')
print('   • Использует существующие анализаторы')
print()
print('=' * 80)
print('ТЕСТИРОВАНИЕ:')
print('=' * 80)
print()
print('1. Запусти backend:')
print('   cd backend')
print('   python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8081')
print()
print('2. Тестовый запрос (curl):')
print('''
curl -X POST http://localhost:8081/api/v1/deep-analysis/ab \\
  -H "Content-Type: application/json" \\
  -d '{
    "snapshot_a": {
      "tag": "KITCHEN2-CO2",
      "start": "2026-01-01T00:00:00",
      "end": "2026-01-31T23:59:59"
    },
    "snapshot_b": {
      "tag": "KITCHEN2-CO2",
      "start": "2026-02-01T00:00:00",
      "end": "2026-02-28T23:59:59"
    }
  }' | python -m json.tool
''')
print()
print('Ожидаемый ответ:')
print('  • mode: "before_after"')
print('  • comparison.statistics.delta.mean_pct: разница средних')
print('  • comparison.significance.p_value: статистическая значимость')
print('  • verdict.severity: "low" | "medium" | "high"')