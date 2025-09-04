#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Демонстрация работы с реальным OpenAI API.
"""

import os
from real_llm import is_openai_available, RealLLMClient, LLMConfig
from test_cases import BUG_CASES

def test_openai_connection():
    """Тестирование подключения к OpenAI API."""
    print("🔍 ПРОВЕРКА ПОДКЛЮЧЕНИЯ К OPENAI API")
    print("="*50)
    
    if not is_openai_available():
        print("❌ OpenAI API недоступен:")
        print("   1. Установите зависимости: pip install -r requirements.txt")
        print("   2. Создайте файл .env с OPENAI_API_KEY")
        return False
    
    try:
        # Создаём тестовый клиент
        client = RealLLMClient()
        print(f"✅ Подключение успешно!")
        print(f"   Модель: {client.config.model}")
        print(f"   Max tokens: {client.config.max_tokens}")
        print(f"   Temperature: {client.config.temperature}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

def demo_real_analysis():
    """Демонстрация реального анализа кода через OpenAI."""
    if not test_openai_connection():
        return
    
    print(f"\n🤖 ДЕМОНСТРАЦИЯ АНАЛИЗА КОДА ЧЕРЕЗ OPENAI")
    print("="*60)
    
    # Выберем один кейс для демонстрации
    case = BUG_CASES[2]  # Деление на ноль
    print(f"📋 Кейс: {case['description']}")
    print(f"Код:\n{case['code']}")
    
    try:
        client = RealLLMClient()
        
        print(f"\n🔍 Анализ через OpenAI...")
        from real_llm import llm_find_issues_real
        analysis = llm_find_issues_real(case['code'], client)
        print(f"Результат анализа:")
        print(f"{analysis}")
        
        print(f"\n💡 Генерация исправлений...")
        from real_llm import llm_suggest_fixes_real
        fixes = llm_suggest_fixes_real(analysis, case['code'], client)
        print(f"Предложенные исправления:")
        for i, fix in enumerate(fixes, 1):
            print(f"{i}. {fix}")
        
        if fixes:
            print(f"\n👥 Ревью первого исправления...")
            from real_llm import llm_review_fix_real
            review = llm_review_fix_real(fixes[0], client)
            print(f"Результат ревью: {review}")
            
    except Exception as e:
        print(f"❌ Ошибка при работе с OpenAI: {e}")

def demo_cost_estimation():
    """Демонстрация оценки стоимости."""
    print(f"\n💰 ОЦЕНКА СТОИМОСТИ ИСПОЛЬЗОВАНИЯ OPENAI API")
    print("="*60)
    
    # Примерные расценки для GPT-4 (актуальные на момент создания)
    costs = {
        "gpt-4": {"input": 0.03, "output": 0.06},  # $ за 1K токенов
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015}
    }
    
    print("Примерная стоимость обработки одного кейса:")
    print("(включает анализ + генерацию исправлений + ревью)")
    print()
    
    for model, price in costs.items():
        # Примерная оценка: ~500 токенов на вход, ~300 на выход за запрос
        # 3 запроса на кейс (анализ, исправления, ревью)
        input_tokens = 500 * 3  # 1500 токенов
        output_tokens = 300 * 3  # 900 токенов
        
        cost_per_case = (input_tokens/1000 * price["input"] + 
                        output_tokens/1000 * price["output"])
        
        print(f"{model:15s}: ~${cost_per_case:.4f} за кейс")
    
    print(f"\nДля всех {len(BUG_CASES)} кейсов:")
    for model, price in costs.items():
        cost_all = (1500/1000 * price["input"] + 900/1000 * price["output"]) * len(BUG_CASES)
        print(f"{model:15s}: ~${cost_all:.3f} за полный тест")
    
    print("\n⚠️ Это приблизительные оценки. Реальная стоимость может отличаться.")

def main():
    """Главная функция демонстрации."""
    print("🎯 ДЕМОНСТРАЦИЯ ИНТЕГРАЦИИ С OPENAI API")
    print("="*60)
    
    print("""
📋 ЧТО БУДЕТ ПРОДЕМОНСТРИРОВАНО:
1. Проверка подключения к OpenAI API
2. Реальный анализ кода через GPT
3. Генерация исправлений через AI  
4. Ревью исправлений через AI
5. Оценка стоимости использования

⚠️ ТРЕБОВАНИЯ:
- Файл .env с OPENAI_API_KEY
- Установленные зависимости (pip install -r requirements.txt)
- Средства на балансе OpenAI аккаунта
    """)
    
    # Проверка готовности
    if not is_openai_available():
        print("❌ Система не готова к работе с OpenAI API")
        print("\n📝 ИНСТРУКЦИЯ ПО НАСТРОЙКЕ:")
        print("1. Установите зависимости:")
        print("   pip install -r requirements.txt")
        print("2. Создайте файл .env в корне проекта:")
        print("   OPENAI_API_KEY=your_api_key_here")
        print("3. Получите API ключ на https://platform.openai.com/api-keys")
        return
    
    # Демонстрация
    demo_real_analysis()
    demo_cost_estimation()
    
    print(f"\n🚀 ЗАПУСК MAS СИСТЕМЫ С OPENAI API:")
    print("python main.py --use-openai --approach both")
    print("python main.py --use-openai --openai-model gpt-3.5-turbo --cases 1 2")
    
    print(f"\n✅ Демонстрация завершена!")

if __name__ == "__main__":
    main()
