#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестирование системы патчинга.
"""

from patch_utils import apply_patch, run_tests
from test_cases import BUG_CASES

def test_individual_patches():
    """Тестирование отдельных патчей."""
    print("🔧 ТЕСТИРОВАНИЕ СИСТЕМЫ ПАТЧИНГА")
    print("="*50)
    
    for case in BUG_CASES:
        print(f"\n📋 Кейс {case['id']}: {case['description']}")
        print("-" * 30)
        
        # Применяем разные фиксы для каждого кейса
        if case['id'] == 1:
            fix_text = "Заменить range(len(arr)+1) на range(len(arr))"
        elif case['id'] == 2:
            fix_text = "Добавить проверку if data is None: return None"
        elif case['id'] == 3:
            fix_text = "Добавить проверку if b == 0: return None"
        elif case['id'] == 4:
            fix_text = "Попробовать преобразовать строковые числа в int"
        elif case['id'] == 5:
            fix_text = "Заменить print(i) на print(n)"
        else:
            continue
            
        print(f"Применяем фикс: {fix_text}")
        
        # Применяем патч
        patched_code = apply_patch(case['code'], fix_text)
        
        print("Исходный код:")
        print(case['code'])
        print("\nПосле патча:")
        print(patched_code)
        
        # Тестируем
        passed, test_output = run_tests(patched_code, case['id'])
        status = "✅ ПРОШЕЛ" if passed else "❌ НЕ ПРОШЕЛ"
        print(f"\nТест: {status}")
        if not passed:
            print(f"Ошибка: {test_output}")

if __name__ == "__main__":
    test_individual_patches()
