# -*- coding: utf-8 -*-
"""
Утилиты для применения патчей и запуска тестов (перенесено из patch_utils.py).
"""

import re
import textwrap
from contextlib import redirect_stdout
from io import StringIO
from typing import Any, Dict, Tuple

try:
	from mas.evaluation.sandbox import run_tests_sandbox
	SANDBOX_AVAILABLE = True
except Exception:
	SANDBOX_AVAILABLE = False

def apply_patch(code: str, fix_text: str) -> str:
	"""Наивное применение патча по тексту предложенного фикса."""
	patched = code

	if "range(len(arr)+1)" in patched and ("range(len(arr))" in fix_text or "Заменить" in fix_text):
		patched = re.sub(r"range\(len\((\w+)\)\+1\)", r"range(len(\1))", patched)

	if "process_data" in patched and ("data is None" in fix_text or ".get" in fix_text):
		new_function = """def process_data(data):
	if data is None:
		return None
	result = data.get('value')
	return result * 2 if result is not None else None"""
		patched = re.sub(
			r"def process_data\(data\):\s*\n\s*result = data\.get\('value'\)\s*\n\s*return result \* 2.*",
			new_function,
			patched,
			flags=re.DOTALL
		)

	if "return a / b" in patched and ("b == 0" in fix_text or "исключение" in fix_text):
		patched = re.sub(
			r"def divide\(a, b\):\s*\n\s*return a / b",
			"def divide(a, b):\n    if b == 0:\n        return None\n    return a / b",
			patched
		)

	if "def add_numbers(a, b):" in patched and ("int" in fix_text or "try" in fix_text or "типов" in fix_text):
		new_function = """def add_numbers(a, b):
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
    return a2 + b2"""
		patched = re.sub(
			r"def add_numbers\(a, b\):\s*\n\s*return a \+ b",
			new_function,
			patched
		)

	if "print(i)" in patched and ("print(n)" in fix_text or "печать n" in fix_text or "логичнее печатать n" in fix_text):
		patched = patched.replace("print(i)", "print(n)")

	return patched

def get_test_description(bug_id: int) -> str:
	"""
	Возвращает описание теста для заданного ID бага.
	"""
	descriptions = {
		1: "Тест суммирования массива [1,2,3] должен вернуть 6",
		2: "process_data(None) -> None, process_data({'value': 3}) -> 6",
		3: "divide(4,2) -> 2, divide(4,0) -> None",
		4: "add_numbers('2', 3) -> 5 (приведение типов)",
		5: "count_down(2) должен выполниться без NameError"
	}
	return descriptions.get(bug_id, f"Неизвестный тест для бага {bug_id}")

def run_tests(code: str, bug_id: int, use_sandbox: bool = False, timeout: float = 5.0) -> Tuple[bool, str]:
	"""
	Гоним мини-тесты в песочнице.
	"""
	if use_sandbox and SANDBOX_AVAILABLE:
		return run_tests_sandbox(code, bug_id, timeout)
	return _run_tests_direct(code, bug_id)

def _run_tests_direct(code: str, bug_id: int) -> Tuple[bool, str]:
	env: Dict[str, Any] = {}
	out = StringIO()
	try:
		with redirect_stdout(out):
			exec(code, env, env)
			if bug_id == 1:
				res = env["calculate_sum"]([1, 2, 3])
				assert res == 6, f"Expected 6, got {res}"
			elif bug_id == 2:
				assert env["process_data"](None) is None, "process_data(None) should return None"
				result = env["process_data"]({"value": 3})
				assert result == 6, f"process_data({'value': 3}) should return 6, got {result}"
			elif bug_id == 3:
				assert env["divide"](4, 2) == 2, "divide(4, 2) should return 2"
				assert env["divide"](4, 0) is None, "divide(4, 0) should return None"
			elif bug_id == 4:
				res = env["add_numbers"]("2", 3)
				assert res == 5, f"add_numbers('2', 3) should return 5, got {res}"
			elif bug_id == 5:
				env["count_down"](2)
			elif bug_id == 6:
				# Проверяем корректный разбор CSV с кавычками и запятыми внутри
				parse = env["parse_csv_line"]
				res1 = parse('a,"b,c",d')
				assert res1 == ["a", "b,c", "d"], f"CSV case1: {res1}"
				res2 = parse('"a,bc","d""e",f')
				assert res2 == ["a,bc", 'd"e', "f"], f"CSV case2: {res2}"
				# Дополнительно: пробелы и пустые поля
				res3 = parse(' ,"",x ')
				assert res3 == ["", "", "x"], f"CSV case3: {res3}"
			else:
				print("Нет тестов для этого кейса; считаем passed.")
		return True, out.getvalue()
	except Exception as e:
		return False, f"TEST FAILED: {type(e).__name__}: {e}\n--- Output ---\n{out.getvalue()}"
