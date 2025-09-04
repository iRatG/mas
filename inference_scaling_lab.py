#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Лаборатория инференс-скейлинга для MAS системы.
Исследование влияния параметров (кандидаты, ревьюеры, ретраи) на качество результатов.
"""

from __future__ import annotations
import csv
import json
import subprocess
import sys
import time
from itertools import product
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple
import statistics

PY = sys.executable
ROOT = Path(__file__).resolve().parent

def run_experiment(approach: str, seed: int, n_candidates: int, n_reviewers: int, max_retries: int, cases: List[int] = None) -> Dict[str, Any]:
    """Запускает один эксперимент и возвращает агрегированные метрики.

    Параметры задают конфигурацию синхронного/асинхронного подхода.
    При необходимости сохраняет детальные результаты в временный JSON.
    """
    if cases is None:
        cases = [1, 2, 3, 4, 5]
    
    # Формируем команду
    cmd = [
        PY, str(ROOT / "main.py"),
        "--approach", approach,
        "--seed", str(seed),
        "--n-candidates", str(n_candidates),
        "--n-reviewers", str(n_reviewers), 
        "--max-retries", str(max_retries),
        "--cases"
    ] + [str(c) for c in cases]
    
    # Временный файл для результатов
    temp_results = ROOT / f"temp_results_{approach}_{int(time.time()*1000)}.json"
    cmd.extend(["--save-results", str(temp_results)])
    
    try:
        # Запускаем эксперимент
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        execution_time = time.time() - start_time
        
        # Читаем детальные результаты если есть
        detailed_results = {}
        if temp_results.exists():
            try:
                detailed_results = json.loads(temp_results.read_text(encoding='utf-8'))
                temp_results.unlink()  # Удаляем временный файл
            except Exception:
                pass
        
        # Парсим основные метрики из вывода
        metrics = parse_output(result.stdout)
        
        # Объединяем результаты
        experiment_result = {
            'approach': approach,
            'n_candidates': n_candidates,
            'n_reviewers': n_reviewers,
            'max_retries': max_retries,
            'seed': seed,
            'cases_tested': cases,
            'execution_time': round(execution_time, 3),
            'return_code': result.returncode,
            **metrics
        }
        
        # Добавляем детальную информацию если доступна
        if detailed_results:
            experiment_result['detailed_metrics'] = detailed_results
            
        return experiment_result
        
    except subprocess.TimeoutExpired:
        return {
            'approach': approach,
            'n_candidates': n_candidates,
            'n_reviewers': n_reviewers,
            'max_retries': max_retries,
            'seed': seed,
            'cases_tested': cases,
            'execution_time': 60.0,
            'return_code': -1,
            'error': 'TIMEOUT',
            'success_count': 0,
            'fail_count': len(cases)
        }
    except Exception as e:
        return {
            'approach': approach,
            'n_candidates': n_candidates,
            'n_reviewers': n_reviewers,
            'max_retries': max_retries,
            'seed': seed,
            'cases_tested': cases,
            'execution_time': 0.0,
            'return_code': -2,
            'error': str(e),
            'success_count': 0,
            'fail_count': len(cases)
        }
    finally:
        # Очищаем временные файлы
        if temp_results.exists():
            temp_results.unlink()

def parse_output(stdout: str) -> Dict[str, Any]:
    """Парсит stdout main.py и извлекает базовые метрики (успех/время)."""
    lines = stdout.splitlines()
    metrics = {
        'success_count': 0,
        'fail_count': 0,
        'timeout_count': 0,
        'avg_execution_time': None,
        'total_candidates': None,
        'total_reviews': None,
        'success_rate': None
    }
    
    execution_times = []
    
    for line in lines:
        line = line.strip()
        
        # Подсчёт успешных/неуспешных кейсов
        if "✅ Статус: success" in line:
            metrics['success_count'] += 1
        elif "❌ Статус: failed" in line:
            metrics['fail_count'] += 1
        elif "⏰ Статус: timeout" in line:
            metrics['timeout_count'] += 1
        
        # Извлечение времени выполнения
        if "Время:" in line:
            try:
                time_str = line.split("Время:")[1].split("сек")[0].strip()
                execution_times.append(float(time_str))
            except (ValueError, IndexError):
                pass
        
        # Извлечение метрик из итогового отчёта
        if "Среднее время:" in line:
            try:
                time_str = line.split("Среднее время:")[1].split("сек")[0].strip()
                metrics['avg_execution_time'] = float(time_str)
            except (ValueError, IndexError):
                pass
        
        if "Среднее кандидатов на кейс:" in line:
            try:
                candidates_str = line.split("Среднее кандидатов на кейс:")[1].strip()
                metrics['total_candidates'] = float(candidates_str)
            except (ValueError, IndexError):
                pass
    
    # Вычисляем дополнительные метрики
    if execution_times:
        metrics['avg_execution_time'] = round(statistics.mean(execution_times), 4)
        metrics['min_execution_time'] = round(min(execution_times), 4)
        metrics['max_execution_time'] = round(max(execution_times), 4)
    
    total_cases = metrics['success_count'] + metrics['fail_count'] + metrics['timeout_count']
    if total_cases > 0:
        metrics['success_rate'] = round(metrics['success_count'] / total_cases, 3)
    
    return metrics

def run_scaling_experiment() -> List[Dict[str, Any]]:
    """Гоняет сетку параметров и собирает результаты во множество экспериментов."""
    print("🔬 Запуск лаборатории инференс-скейлинга...")
    print("="*60)
    
    # Параметры эксперимента
    approaches = ["sync", "async"]
    candidates_grid = [1, 2, 3, 5]
    reviewers_grid = [1, 3, 5]
    retries_grid = [0, 1, 2]
    seed = 42
    
    # Для быстрого тестирования используем подмножество кейсов
    test_cases = [1, 2, 3]  # Можно расширить до [1, 2, 3, 4, 5] для полного теста
    
    results = []
    total_experiments = len(approaches) * len(candidates_grid) * len(reviewers_grid) * len(retries_grid)
    
    print(f"Всего экспериментов: {total_experiments}")
    print(f"Тестируемые кейсы: {test_cases}")
    print(f"Подходы: {approaches}")
    print(f"Кандидаты: {candidates_grid}")
    print(f"Ревьюеры: {reviewers_grid}")
    print(f"Ретраи: {retries_grid}")
    print()
    
    experiment_num = 0
    
    for approach in approaches:
        for n_cand, n_rev, n_ret in product(candidates_grid, reviewers_grid, retries_grid):
            experiment_num += 1
            
            print(f"[{experiment_num}/{total_experiments}] {approach} | "
                  f"кандидатов={n_cand}, ревьюеров={n_rev}, ретраев={n_ret}")
            
            result = run_experiment(approach, seed, n_cand, n_rev, n_ret, test_cases)
            results.append(result)
            
            # Краткий вывод результата
            status = "✅" if result.get('success_count', 0) == len(test_cases) else "❌"
            exec_time = result.get('execution_time', 0)
            success_rate = result.get('success_rate', 0) or 0
            
            print(f"   {status} Успешность: {success_rate:.1%}, Время: {exec_time:.3f}с")
    
    return results

def analyze_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Анализирует массив результатов и вычисляет сводную статистику по подходам."""
    analysis = {
        'total_experiments': len(results),
        'by_approach': {},
        'best_configurations': {},
        'parameter_impact': {}
    }
    
    # Группировка по подходам
    sync_results = [r for r in results if r['approach'] == 'sync']
    async_results = [r for r in results if r['approach'] == 'async']
    
    for approach_name, approach_results in [('sync', sync_results), ('async', async_results)]:
        if not approach_results:
            continue
        
        success_rates = [(r.get('success_rate') or 0) for r in approach_results]
        exec_times = [float(r.get('execution_time', 0) or 0) for r in approach_results]
        sr_clean = [float(x) for x in success_rates if isinstance(x, (int, float))]
        et_clean = [float(x) for x in exec_times if isinstance(x, (int, float))]
        
        analysis['by_approach'][approach_name] = {
            'experiments_count': len(approach_results),
            'avg_success_rate': round(statistics.mean(sr_clean), 3) if sr_clean else 0.0,
            'best_success_rate': max(sr_clean) if sr_clean else 0.0,
            'avg_execution_time': round(statistics.mean(et_clean), 3) if et_clean else 0.0,
            'fastest_time': min(et_clean) if et_clean else 0.0
        }
    
    # Поиск лучших конфигураций
    best_overall = max(results, key=lambda r: ((r.get('success_rate') or 0), -(r.get('execution_time') or float('inf'))))
    fastest_successful = min([r for r in results if r.get('success_rate', 0) == 1.0], 
                           key=lambda r: r.get('execution_time', float('inf')), default=None)
    
    analysis['best_configurations'] = {
        'overall_best': {
            'approach': best_overall['approach'],
            'n_candidates': best_overall['n_candidates'],
            'n_reviewers': best_overall['n_reviewers'],
            'max_retries': best_overall['max_retries'],
            'success_rate': best_overall.get('success_rate', 0),
            'execution_time': best_overall.get('execution_time', 0)
        }
    }
    
    if fastest_successful:
        analysis['best_configurations']['fastest_perfect'] = {
            'approach': fastest_successful['approach'],
            'n_candidates': fastest_successful['n_candidates'],
            'n_reviewers': fastest_successful['n_reviewers'],
            'max_retries': fastest_successful['max_retries'],
            'execution_time': fastest_successful.get('execution_time', 0)
        }
    
    return analysis

def save_results(results: List[Dict[str, Any]], analysis: Dict[str, Any]):
    """Сохраняет результаты экспериментов и анализ в CSV и JSON файлы."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # CSV файл для табличного анализа
    csv_file = ROOT / f"inference_scaling_results_{timestamp}.csv"
    if results:
        with csv_file.open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
    
    # JSON файл с полными данными и анализом
    json_file = ROOT / f"inference_scaling_analysis_{timestamp}.json"
    full_data = {
        'metadata': {
            'timestamp': timestamp,
            'total_experiments': len(results),
            'description': 'Инференс-скейлинг эксперименты для MAS системы'
        },
        'results': results,
        'analysis': analysis
    }
    
    json_file.write_text(json.dumps(full_data, ensure_ascii=False, indent=2), encoding='utf-8')
    
    return csv_file, json_file

def print_summary(analysis: Dict[str, Any]):
    """Красиво печатает сводные метрики инференс-скейлинга в консоль."""
    print("\n" + "="*60)
    print("📊 СВОДКА РЕЗУЛЬТАТОВ ИНФЕРЕНС-СКЕЙЛИНГА")
    print("="*60)
    
    print(f"Всего экспериментов: {analysis['total_experiments']}")
    
    for approach, data in analysis['by_approach'].items():
        print(f"\n🔧 {approach.upper()} подход:")
        print(f"  • Экспериментов: {data['experiments_count']}")
        print(f"  • Средняя успешность: {data['avg_success_rate']:.1%}")
        print(f"  • Лучшая успешность: {data['best_success_rate']:.1%}")
        print(f"  • Среднее время: {data['avg_execution_time']:.3f}с")
        print(f"  • Лучшее время: {data['fastest_time']:.3f}с")
    
    print(f"\n🏆 ЛУЧШИЕ КОНФИГУРАЦИИ:")
    
    best = analysis['best_configurations']['overall_best']
    best_sr = float(best.get('success_rate') or 0.0)
    best_time = float(best.get('execution_time') or 0.0)
    print(f"  • Лучшая общая: {best['approach']} "
          f"(кандидатов={best['n_candidates']}, ревьюеров={best['n_reviewers']}, ретраев={best['max_retries']})")
    print(f"    Успешность: {best_sr:.1%}, Время: {best_time:.3f}с")
    
    if 'fastest_perfect' in analysis['best_configurations']:
        fastest = analysis['best_configurations']['fastest_perfect']
        print(f"  • Самая быстрая (100%): {fastest['approach']} "
              f"(кандидатов={fastest['n_candidates']}, ревьюеров={fastest['n_reviewers']}, ретраев={fastest['max_retries']})")
        fastest_time = float(fastest.get('execution_time') or 0.0)
        print(f"    Время: {fastest_time:.3f}с")

def main():
    """
    Главная функция лаборатории инференс-скейлинга.
    """
    print("🧪 ЛАБОРАТОРИЯ ИНФЕРЕНС-СКЕЙЛИНГА MAS СИСТЕМЫ")
    print("Исследование влияния параметров на качество результатов")
    print()
    
    # Запуск экспериментов
    results = run_scaling_experiment()
    
    # Анализ результатов
    analysis = analyze_results(results)
    
    # Сохранение результатов
    csv_file, json_file = save_results(results, analysis)
    
    # Вывод сводки
    print_summary(analysis)
    
    print(f"\n📁 РЕЗУЛЬТАТЫ СОХРАНЕНЫ:")
    print(f"  • CSV таблица: {csv_file}")
    print(f"  • JSON анализ: {json_file}")
    print("\n✅ Лаборатория инференс-скейлинга завершена!")

if __name__ == "__main__":
    main()
