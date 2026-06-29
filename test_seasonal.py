#!/usr/bin/env python3
"""
test_seasonal.py — тестируем detect_dominant_periods на реальных данных
"""
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Загружаем переменные окружения из .env
env_path = Path('backend/.env')
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Загружены переменные окружения из {env_path}")
else:
    print(f"⚠️  Файл {env_path} не найден")

# Добавляем backend в путь
sys.path.insert(0, str(Path('backend').absolute()))

from modules.deep_analysis.collectors.data_fetcher import fetch_tag_data
from modules.deep_analysis.analyzers.seasonal import (
    detect_dominant_periods,
    decompose_seasonal,
    get_seasonal_pattern,
)


async def test_on_real_data():
    """Тестируем на реальном теге за 7 дней."""
    
    print('=' * 80)
    print('ТЕСТ: Циклический анализ на реальных данных')
    print('=' * 80)
    print()
    
    # Берём тег с большим количеством данных
    tag_name = "KITCHEN2-CO2"
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    print(f'【1】Загружаем данные для {tag_name}')
    print(f'    Период: {start_date.strftime("%Y-%m-%d")} — {end_date.strftime("%Y-%m-%d")}')
    print('-' * 80)
    
    try:
        data = await fetch_tag_data(
            tag_name=tag_name,
            start_date=start_date,
            end_date=end_date,
            exclude_nulls=False,  # важно для FFT
        )
    except Exception as e:
        print(f'❌ Ошибка загрузки: {e}')
        return
    
    values = data.get('raw_values', [])
    timestamps = data.get('raw_timestamps', [])
    
    print(f'✅ Загружено: {len(values)} точек')
    print(f'   Первая точка: {timestamps[0] if timestamps else "N/A"}')
    print(f'   Последняя точка: {timestamps[-1] if timestamps else "N/A"}')
    print(f'   Значений: min={min(values) if values else 0:.2f}, max={max(values) if values else 0:.2f}')
    print()
    
    if len(values) < 50:
        print('⚠️  Слишком мало данных для анализа')
        return
    
    # Тест 1: Детекция доминирующих периодов
    print('【2】Запускаем detect_dominant_periods')
    print('-' * 80)
    
    result = detect_dominant_periods(values, timestamps)
    
    if 'error' in result:
        print(f'❌ Ошибка: {result["error"]}')
        return
    
    print(f'✅ Анализ завершён')
    print(f'   Sampling rate: {result["sampling_rate"]} точек/час')
    print(f'   Всего точек: {result["n_points"]}')
    print(f'   FFT пиков: {len(result["fft_peaks"])}')
    print(f'   Autocorr пиков: {len(result["autocorr_peaks"])}')
    print()
    
    # Показываем детектированные периоды
    print('【3】Детектированные периоды:')
    print('-' * 80)
    
    detected = result['detected_periods']
    if not detected:
        print('⚠️  Периоды не обнаружены (возможно, данные без сезонности)')
    else:
        print(f'{"Период":<10} {"Частота":<12} {"Power":<10} {"Autocorr":<10} {"Confidence":<12}')
        print('-' * 70)
        
        for p in detected[:5]:  # топ-5
            # Конвертируем период в человекочитаемый формат
            period = p['period']
            sampling_rate = result['sampling_rate']
            
            # Если sampling_rate в точках/час
            if sampling_rate > 0:
                hours = period / sampling_rate
                if hours < 1:
                    human_period = f"{hours * 60:.1f} мин"
                elif hours < 48:
                    human_period = f"{hours:.1f} ч"
                elif hours < 24 * 14:
                    human_period = f"{hours/24:.1f} дн"
                else:
                    human_period = f"{hours/24/7:.1f} нед"
            else:
                human_period = f"{period} pts"
            
            print(f'{period:<10} {p["frequency"]:<12.4f} {p["power"]:<10.3f} '
                  f'{p["autocorrelation"] or 0:<10.3f} {p["confidence"]:<12.3f}  '
                  f'({human_period})')
    
    print()
    
    # Тест 2: Декомпозиция (если нашли основной период)
    if detected:
        main_period = detected[0]['period']
        print(f'【4】Декомпозиция на trend + seasonal + residual')
        print(f'    Основной период: {main_period}')
        print('-' * 80)
        
        decomp = decompose_seasonal(values, period=main_period)
        
        if 'error' in decomp:
            print(f'❌ Ошибка: {decomp["error"]}')
        else:
            trend = decomp['trend']
            seasonal = decomp['seasonal']
            residual = decomp['residual']
            
            import numpy as np
            trend_std = float(np.std(trend))
            seasonal_std = float(np.std(seasonal))
            residual_std = float(np.std(residual))
            
            print(f'✅ Декомпозиция выполнена')
            print(f'   Trend std:    {trend_std:.3f}')
            print(f'   Seasonal std: {seasonal_std:.3f}')
            print(f'   Residual std: {residual_std:.3f}')
            print()
            
            # Соотношение сигнал/шум
            total_var = trend_std**2 + seasonal_std**2 + residual_std**2
            if total_var > 0:
                print('   Распределение дисперсии:')
                print(f'     Trend:    {trend_std**2/total_var*100:5.1f}%')
                print(f'     Seasonal: {seasonal_std**2/total_var*100:5.1f}%')
                print(f'     Residual: {residual_std**2/total_var*100:5.1f}% (шум + аномалии)')
            print()
    
    # Тест 3: Сезонный паттерн
    if detected:
        main_period = detected[0]['period']
        print(f'【5】Типичный сезонный паттерн (период {main_period})')
        print('-' * 80)
        
        pattern = get_seasonal_pattern(values, period=main_period)
        
        print(f'✅ Паттерн построен')
        print(f'   Период: {main_period} точек')
        print(f'   Мин. значение в паттерне: {min(v for v in pattern["pattern"] if v is not None):.2f}')
        print(f'   Макс. значение в паттерне: {max(v for v in pattern["pattern"] if v is not None):.2f}')
        print()
        
        # Показываем первые 10 и последние 10 фаз
        print('   Пример значений (первые 10 фаз):')
        for phase in range(min(10, main_period)):
            val = pattern["pattern"][phase]
            std = pattern["std"][phase]
            n = pattern["n_samples"][phase]
            if val is not None:
                print(f'     Фаза {phase:2d}: {val:7.2f} ± {std:5.2f} (n={n})')
        if main_period > 10:
            print('     ...')
    
    print()
    print('=' * 80)
    print('ИТОГ:')
    print('=' * 80)
    if detected:
        print(f'✅ Обнаружено {len(detected)} периодических паттернов')
        print(f'   Основной период: {detected[0]["period"]} точек')
        print(f'   Можно использовать для улучшения детекции аномалий')
    else:
        print('⚠️  Периоды не обнаружены — возможно, данные шумные или без сезонности')


if __name__ == '__main__':
    asyncio.run(test_on_real_data())