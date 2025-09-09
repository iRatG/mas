# -*- coding: utf-8 -*-
"""
Тест-кейсы с багами (перенесено из test_cases.py).
"""

BUG_CASES = [
	{
		"id": 1,
		"description": "Выход за границы массива",
		"code": "def calculate_sum(arr):\n    s = 0\n    for i in range(len(arr)+1):  # Ошибка: выход за границы индекса\n        s += arr[i]\n    return s"
	},
	{
		"id": 2,
		"description": "None-обращение (эквивалент NPE)",
		"code": "def process_data(data):\n    result = data.get('value')\n    return result * 2  # Ошибка: data может быть None"
	},
	{
		"id": 3,
		"description": "Деление на ноль",
		"code": "def divide(a, b):\n    return a / b  # Ошибка: не проверяется деление на ноль"
	},
	{
		"id": 4,
		"description": "Несоответствие типов (строка + число)",
		"code": "def add_numbers(a, b):\n    return a + b\n\nx = add_numbers('2', 3)  # Ошибка: сложение строки и числа"
	},
	{
		"id": 5,
		"description": "Неинициализированная переменная",
		"code": "def count_down(n):\n    while n >= 0:\n        print(i)  # Ошибка: переменная i не инициализирована\n        n -= 1"
	}
]
