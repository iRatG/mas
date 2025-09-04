#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Демонстрация реальных багов и их исправления через MAS систему.
"""

from test_cases import BUG_CASES
import traceback

def demonstrate_real_bugs():
    """Демонстрация того, что баги действительно существуют."""
    print("🐛 ДЕМОНСТРАЦИЯ РЕАЛЬНЫХ БАГОВ")
    print("="*60)
    
    for case in BUG_CASES:
        print(f"\n📋 Кейс {case['id']}: {case['description']}")
        print("-" * 40)
        print("Код:")
        print(case['code'])
        print("\n🚨 Попытка выполнения:")
        
        try:
            # Выполняем код в изолированном окружении
            env = {}
            exec(case['code'], env, env)
            
            # Пытаемся вызвать функции с проблемными параметрами
            if case['id'] == 1:  # Выход за границы
                result = env['calculate_sum']([1, 2, 3])
                print(f"❌ НЕОЖИДАННО: код выполнился! Результат: {result}")
                
            elif case['id'] == 2:  # None обращение
                result = env['process_data'](None)
                print(f"❌ НЕОЖИДАННО: код выполнился! Результат: {result}")
                
            elif case['id'] == 3:  # Деление на ноль
                result = env['divide'](10, 0)
                print(f"❌ НЕОЖИДАННО: код выполнился! Результат: {result}")
                
            elif case['id'] == 4:  # Несоответствие типов
                result = env['add_numbers']('hello', 5)
                print(f"❌ НЕОЖИДАННО: код выполнился! Результат: {result}")
                
            elif case['id'] == 5:  # Неинициализированная переменная
                env['count_down'](2)
                print("❌ НЕОЖИДАННО: код выполнился без ошибок!")
                
        except Exception as e:
            print(f"✅ ОШИБКА ОБНАРУЖЕНА: {type(e).__name__}: {e}")
            print(f"   Это именно та проблема, которую должна решить MAS система!")

def demonstrate_working_fixes():
    """Демонстрация рабочих исправлений."""
    print(f"\n{'='*60}")
    print("🔧 ДЕМОНСТРАЦИЯ ИСПРАВЛЕННОГО КОДА")
    print("="*60)
    
    # Исправленные версии
    fixed_codes = {
        1: """def calculate_sum(arr):
    s = 0
    for i in range(len(arr)):  # Исправлено: убрали +1
        s += arr[i]
    return s""",
        
        2: """def process_data(data):
    if data is None:  # Исправлено: добавили проверку
        return None
    result = data.get('value')
    return result * 2 if result is not None else None""",
        
        3: """def divide(a, b):
    if b == 0:  # Исправлено: проверка деления на ноль
        return None
    return a / b""",
        
        4: """def add_numbers(a, b):
    # Исправлено: приведение типов
    def _to_num(x):
        if isinstance(x, str):
            try:
                return int(x)
            except ValueError:
                try:
                    return float(x)
                except ValueError:
                    raise TypeError("неконвертируемый тип")
        return x
    a2, b2 = _to_num(a), _to_num(b)
    return a2 + b2""",
        
        5: """def count_down(n):
    while n >= 0:
        print(n)  # Исправлено: печатаем n, а не i
        n -= 1"""
    }
    
    test_cases = {
        1: lambda env: env['calculate_sum']([1, 2, 3]),
        2: lambda env: (env['process_data'](None), env['process_data']({'value': 3})),
        3: lambda env: (env['divide'](10, 2), env['divide'](10, 0)),
        4: lambda env: env['add_numbers']('5', 3),
        5: lambda env: env['count_down'](2)
    }
    
    for case_id, fixed_code in fixed_codes.items():
        case = BUG_CASES[case_id - 1]
        print(f"\n📋 Кейс {case_id}: {case['description']}")
        print("-" * 40)
        print("Исправленный код:")
        print(fixed_code)
        print("\n✅ Результат выполнения:")
        
        try:
            env = {}
            exec(fixed_code, env, env)
            result = test_cases[case_id](env)
            print(f"✅ УСПЕХ: {result}")
        except Exception as e:
            print(f"❌ Ошибка в исправлении: {e}")

if __name__ == "__main__":
    demonstrate_real_bugs()
    demonstrate_working_fixes()
    
    print(f"\n{'='*60}")
    print("🎯 ЗАКЛЮЧЕНИЕ")
    print("="*60)
    print("1. Мы показали реальные баги в коде")
    print("2. Мы показали, как их можно исправить")
    print("3. Теперь MAS система должна автоматически найти и применить эти исправления!")
    print("\nЗапустите: python main.py --approach both")
    print("="*60)
