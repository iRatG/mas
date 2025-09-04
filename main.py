#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MAS Demo: главный модуль для запуска и сравнения подходов.
Поддерживает синхронный оркестратор и асинхронную шину для авто-исправления багов.
"""

import argparse
import asyncio
import json
import logging
import time
from typing import Any, Dict, List

from test_cases import BUG_CASES
from approach1_sync import create_sync_orchestrator
from approach2_async import create_async_system, make_cid
from real_llm import is_openai_available

# ----------------------------- ЛОГИ ---------------------------------

def setup_logging(verbose: bool):
    """Настройка системы логирования."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )

log = logging.getLogger("MAS")

# ------------------------- АНАЛИТИКА --------------------------------

class OverallAnalytics:
    """Система общей аналитики для сравнения подходов."""
    
    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        self.start_time = time.time()
        self.llm_mode = "simulation"  # "simulation" или "openai"
        self.openai_model = None
    
    def add_result(self, result: Dict[str, Any]):
        """Добавление результата выполнения."""
        self.results.append(result)
    
    def generate_summary(self) -> Dict[str, Any]:
        """Генерация сводного отчёта."""
        total_time = time.time() - self.start_time
        
        sync_results = [r for r in self.results if r.get("approach") == "sync"]
        async_results = [r for r in self.results if r.get("approach") == "async"]
        
        summary = {
            "total_execution_time": round(total_time, 3),
            "total_cases": len(self.results),
            "llm_mode": self.llm_mode,
            "openai_model": self.openai_model,
            "sync_approach": self._analyze_approach(sync_results, "sync"),
            "async_approach": self._analyze_approach(async_results, "async"),
            "comparison": self._compare_approaches(sync_results, async_results)
        }
        
        return summary
    
    def _analyze_approach(self, results: List[Dict[str, Any]], approach_name: str) -> Dict[str, Any]:
        """Анализ результатов для конкретного подхода."""
        if not results:
            return {"cases_processed": 0, "success_rate": 0, "average_time": 0}
        
        successful = [r for r in results if r.get("status") == "success"]
        failed = [r for r in results if r.get("status") == "failed"]
        timeouts = [r for r in results if r.get("status") == "timeout"]
        
        metrics = [r.get("metrics", {}) for r in results if "metrics" in r]
        
        analysis = {
            "cases_processed": len(results),
            "successful": len(successful),
            "failed": len(failed),
            "timeouts": len(timeouts),
            "success_rate": round(len(successful) / len(results), 2) if results else 0,
            "average_execution_time": round(
                sum(m.get("execution_time_seconds", 0) for m in metrics) / len(metrics), 3
            ) if metrics else 0,
        }
        
        # Специфичные метрики для каждого подхода
        if approach_name == "sync":
            analysis.update({
                "total_retries": sum(m.get("retries_used", 0) for m in metrics),
                "average_candidates_per_case": round(
                    sum(m.get("total_candidates_generated", 0) for m in metrics) / len(metrics), 1
                ) if metrics else 0,
                "average_reviews_per_case": round(
                    sum(m.get("total_reviews_performed", 0) for m in metrics) / len(metrics), 1
                ) if metrics else 0,
            })
        elif approach_name == "async":
            analysis.update({
                "total_messages": sum(m.get("messages_sent", 0) for m in metrics),
                "total_timeouts": sum(m.get("timeouts_occurred", 0) for m in metrics),
                "average_message_efficiency": round(
                    sum(m.get("message_efficiency", 0) for m in metrics) / len(metrics), 2
                ) if metrics else 0,
            })
        
        return analysis
    
    def _compare_approaches(self, sync_results: List[Dict], async_results: List[Dict]) -> Dict[str, Any]:
        """Сравнение подходов."""
        if not sync_results or not async_results:
            return {"comparison_available": False}
        
        sync_metrics = [r.get("metrics", {}) for r in sync_results if "metrics" in r]
        async_metrics = [r.get("metrics", {}) for r in async_results if "metrics" in r]
        
        sync_avg_time = sum(m.get("execution_time_seconds", 0) for m in sync_metrics) / len(sync_metrics)
        async_avg_time = sum(m.get("execution_time_seconds", 0) for m in async_metrics) / len(async_metrics)
        
        sync_success = len([r for r in sync_results if r.get("status") == "success"])
        async_success = len([r for r in async_results if r.get("status") == "success"])
        
        return {
            "comparison_available": True,
            "faster_approach": "sync" if sync_avg_time < async_avg_time else "async",
            "time_difference_seconds": round(abs(sync_avg_time - async_avg_time), 3),
            "more_successful": "sync" if sync_success > async_success else "async" if async_success > sync_success else "equal",
            "success_difference": abs(sync_success - async_success),
        }
    
    def print_summary(self):
        """Вывод сводного отчёта в консоль."""
        summary = self.generate_summary()
        
        print("\n" + "="*80)
        print("СВОДНЫЙ ОТЧЁТ ПО АНАЛИЗУ ПОДХОДОВ")
        print("="*80)
        
        print(f"Общее время выполнения: {summary['total_execution_time']} сек")
        print(f"Всего обработано кейсов: {summary['total_cases']}")
        
        print(f"\n📊 СИНХРОННЫЙ ПОДХОД:")
        sync = summary['sync_approach']
        if sync['cases_processed'] > 0:
            print(f"  • Обработано кейсов: {sync['cases_processed']}")
            print(f"  • Успешных: {sync['successful']}, Неудачных: {sync['failed']}")
            print(f"  • Процент успеха: {sync['success_rate']*100}%")
            print(f"  • Среднее время: {sync['average_execution_time']} сек")
            print(f"  • Всего ретраев: {sync.get('total_retries', 0)}")
            print(f"  • Среднее кандидатов на кейс: {sync.get('average_candidates_per_case', 0)}")
        else:
            print("  • Не запускался")
        
        print(f"\n🚀 АСИНХРОННЫЙ ПОДХОД:")
        async_data = summary['async_approach']
        if async_data['cases_processed'] > 0:
            print(f"  • Обработано кейсов: {async_data['cases_processed']}")
            print(f"  • Успешных: {async_data['successful']}, Неудачных: {async_data['failed']}, Таймаутов: {async_data['timeouts']}")
            print(f"  • Процент успеха: {async_data['success_rate']*100}%")
            print(f"  • Среднее время: {async_data['average_execution_time']} сек")
            print(f"  • Всего сообщений: {async_data.get('total_messages', 0)}")
            print(f"  • Эффективность сообщений: {async_data.get('average_message_efficiency', 0)}")
        else:
            print("  • Не запускался")
        
        comparison = summary['comparison']
        if comparison['comparison_available']:
            print(f"\n⚡ СРАВНЕНИЕ:")
            print(f"  • Быстрее: {comparison['faster_approach']} подход")
            print(f"  • Разница во времени: {comparison['time_difference_seconds']} сек")
            print(f"  • Больше успешных: {comparison['more_successful']}")
            print(f"  • Разница в успешности: {comparison['success_difference']} кейсов")
        
        print("="*80)

# ------------------------ ЗАПУСК ПОДХОДОВ ---------------------------

async def run_sync_approach(cases: List[Dict[str, Any]], seed: int, analytics: OverallAnalytics, args):
    """Запуск синхронного подхода."""
    print(f"\n🔄 Запуск СИНХРОННОГО подхода (seed={seed})")
    print("-" * 50)
    
    # Применяем параметры из командной строки если указаны
    kwargs = {'seed': seed}
    if args.n_candidates:
        kwargs['n_candidates'] = args.n_candidates
    if args.n_reviewers:
        kwargs['n_reviewers'] = args.n_reviewers  
    if args.max_retries:
        kwargs['max_retries'] = args.max_retries
        
    orchestrator = create_sync_orchestrator(**kwargs)
    
    for bug in cases:
        print(f"\n--- SYNC кейс {bug['id']}: {bug['description']} ---")
        correlation_id = f"sync-case{bug['id']}-{int(time.time()*1000) % 10000}"
        result = orchestrator.run(bug["code"], bug["id"], correlation_id)
        analytics.add_result(result)
        
        # Краткий вывод результата
        status_emoji = "✅" if result["status"] == "success" else "❌"
        print(f"{status_emoji} Статус: {result['status']}")
        if "metrics" in result:
            metrics = result["metrics"]
            print(f"   Время: {metrics['execution_time_seconds']} сек")
            print(f"   Кандидатов: {metrics['total_candidates_generated']}")
            print(f"   Ретраев: {metrics['retries_used']}")

async def run_async_approach(cases: List[Dict[str, Any]], seed: int, parallel: bool, analytics: OverallAnalytics, args):
    """Запуск асинхронного подхода."""
    mode_text = "ПАРАЛЛЕЛЬНОМ" if parallel else "ПОСЛЕДОВАТЕЛЬНОМ"
    print(f"\n🚀 Запуск АСИНХРОННОГО подхода в {mode_text} режиме (seed={seed})")
    print("-" * 50)
    
    # Применяем параметры из командной строки если указаны
    kwargs = {'seed': seed}
    if args.n_reviewers:
        kwargs['n_reviewers'] = args.n_reviewers
    if args.max_retries:
        kwargs['max_retries'] = args.max_retries
        
    coordinator, agents, metrics = create_async_system(**kwargs)
    
    # Запускаем агентов
    agent_tasks = [asyncio.create_task(agent.run()) for agent in agents]
    
    try:
        if parallel:
            # Параллельная обработка с семафором
            semaphore = asyncio.Semaphore(3)
            
            async def process_case_parallel(idx: int, bug: Dict[str, Any]):
                async with semaphore:
                    print(f"\n>>> [START] async кейс {bug['id']}: {bug['description']}")
                    correlation_id = make_cid(idx) 
                    result = await coordinator.run_case(bug["code"], bug["id"], correlation_id)
                    analytics.add_result(result)
                    
                    status_emoji = "✅" if result["status"] == "success" else "❌" if result["status"] == "failed" else "⏰"
                    print(f"{status_emoji} [DONE] async кейс {bug['id']}: {result['status']}")
                    
                    if "metrics" in result:
                        m = result["metrics"]
                        print(f"    Время: {m['execution_time_seconds']} сек, Сообщений: {m['messages_sent']}")
            
            await asyncio.gather(*[process_case_parallel(i, bug) for i, bug in enumerate(cases, 1)])
        else:
            # Последовательная обработка
            for i, bug in enumerate(cases, 1):
                print(f"\n--- ASYNC кейс {bug['id']}: {bug['description']} ---")
                correlation_id = make_cid(i)
                result = await coordinator.run_case(bug["code"], bug["id"], correlation_id)
                analytics.add_result(result)
                
                status_emoji = "✅" if result["status"] == "success" else "❌" if result["status"] == "failed" else "⏰"
                print(f"{status_emoji} Статус: {result['status']}")
                if "metrics" in result:
                    m = result["metrics"]
                    print(f"   Время: {m['execution_time_seconds']} сек")
                    print(f"   Сообщений: {m['messages_sent']}/{m['messages_received']}")
                    print(f"   Таймауты: {m['timeouts_occurred']}")
    finally:
        # Остановка агентов
        for task in agent_tasks:
            task.cancel()
        await asyncio.gather(*agent_tasks, return_exceptions=True)

# ----------------------------- MAIN ---------------------------------

def parse_args():
    """Парсинг аргументов командной строки."""
    parser = argparse.ArgumentParser(description="MAS Demo: сравнение синхронного и асинхронного подходов")
    parser.add_argument("--approach", choices=["sync", "async", "both"], default="both", 
                       help="Какой подход запустить: sync, async или both")
    parser.add_argument("--parallel", action="store_true", 
                       help="Для async: обрабатывать кейсы параллельно")
    parser.add_argument("--seed", type=int, default=42, 
                       help="Seed для воспроизводимости результатов")
    parser.add_argument("--verbose", action="store_true", 
                       help="Подробные логи")
    parser.add_argument("--cases", type=int, nargs='+', 
                       help="Номера конкретных кейсов для обработки (например: --cases 1 3 5)")
    parser.add_argument("--save-results", type=str, 
                       help="Сохранить подробные результаты в JSON файл")
    parser.add_argument("--use-openai", action="store_true", 
                       help="Использовать реальный OpenAI API вместо имитации")
    parser.add_argument("--openai-model", type=str, default="gpt-4", 
                       help="Модель OpenAI для использования (по умолчанию: gpt-4)")
    # Параметры для инференс-скейлинга
    parser.add_argument("--n-candidates", type=int, 
                       help="Количество кандидатов для генерации (переопределяет настройки по умолчанию)")
    parser.add_argument("--n-reviewers", type=int, 
                       help="Количество ревьюеров (переопределяет настройки по умолчанию)")
    parser.add_argument("--max-retries", type=int, 
                       help="Максимальное количество ретраев (переопределяет настройки по умолчанию)")
    return parser.parse_args()

async def main():
    """Главная функция."""
    args = parse_args()
    setup_logging(args.verbose)
    
    # Проверяем и настраиваем режим работы с LLM
    if args.use_openai:
        if not is_openai_available():
            print("❌ OpenAI API недоступен. Убедитесь, что:")
            print("   1. Установлены зависимости: pip install -r requirements.txt")
            print("   2. Создан файл .env с OPENAI_API_KEY")
            print("   3. API ключ корректный")
            print("\n🔄 Переключаемся на режим имитации...")
            args.use_openai = False
        else:
            print(f"🤖 Используем реальный OpenAI API (модель: {args.openai_model})")
            # Устанавливаем переменную окружения для модели
            import os
            os.environ['OPENAI_MODEL'] = args.openai_model
            
            # Заменяем импорты LLM функций на реальные
            import approach1_sync
            import approach2_async
            from real_llm import llm_find_issues_wrapper, llm_suggest_fixes_wrapper, llm_review_fix_wrapper
            
            # Monkey patching для использования реального API
            approach1_sync.llm_find_issues = llm_find_issues_wrapper
            approach1_sync.llm_suggest_fixes = llm_suggest_fixes_wrapper  
            approach1_sync.llm_review_fix = llm_review_fix_wrapper
            approach2_async.llm_find_issues = llm_find_issues_wrapper
            approach2_async.llm_suggest_fixes = llm_suggest_fixes_wrapper
            approach2_async.llm_review_fix = llm_review_fix_wrapper
    else:
        print("🎭 Используем режим имитации LLM")
    
    # Выбираем кейсы для обработки
    if args.cases:
        cases = [case for case in BUG_CASES if case["id"] in args.cases]
        print(f"Выбраны кейсы: {[c['id'] for c in cases]}")
    else:
        cases = BUG_CASES
        print(f"Обрабатываем все {len(cases)} кейсов")
    
    # Предупреждение о стоимости при использовании OpenAI
    if args.use_openai:
        print(f"\n⚠️  ВНИМАНИЕ: Используется реальный OpenAI API!")
        print(f"   Модель: {args.openai_model}")
        print(f"   Кейсов для обработки: {len(cases)}")
        print(f"   Примерная стоимость: ~${len(cases) * 0.01:.3f}")
        
        if len(cases) > 3:
            response = input("\n❓ Продолжить? (y/N): ")
            if response.lower() not in ['y', 'yes', 'да']:
                print("❌ Отменено пользователем")
                return
    
    analytics = OverallAnalytics()
    
    # Добавляем информацию о режиме работы в аналитику
    analytics.llm_mode = "openai" if args.use_openai else "simulation"
    analytics.openai_model = args.openai_model if args.use_openai else None
    
    # Запуск подходов
    if args.approach in ["sync", "both"]:
        await run_sync_approach(cases, args.seed, analytics, args)
    
    if args.approach in ["async", "both"]:
        await run_async_approach(cases, args.seed, args.parallel, analytics, args)
    
    # Вывод аналитики
    analytics.print_summary()
    
    # Сохранение результатов
    if args.save_results:
        summary = analytics.generate_summary()
        summary["detailed_results"] = analytics.results
        summary["configuration"] = {
            "use_openai": args.use_openai,
            "openai_model": args.openai_model if args.use_openai else None,
            "seed": args.seed,
            "approach": args.approach,
            "parallel": args.parallel
        }
        
        with open(args.save_results, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Результаты сохранены в {args.save_results}")

if __name__ == "__main__":
    asyncio.run(main())
