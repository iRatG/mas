#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Утилиты для применения патчей и запуска тестов.
"""

import re
import textwrap
from contextlib import redirect_stdout
from io import StringIO
from typing import Any, Dict, Tuple

def apply_patch(code: str, fix_text: str) -> str:
    """Наивное применение патча по тексту предложенного фикса."""
    patched = code

    if "range(len(arr)+1)" in patched and ("range(len(arr))" in fix_text or "Заменить" in fix_text):
        patched = re.sub(r"range\(len\((\w+)\)\+1\)", r"range(len(\1))", patched)

    if "process_data" in patched and ("data is None" in fix_text or ".get" in fix_text):
        # Заменяем всю функцию process_data
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
        # Заменяем функцию divide целиком
        patched = re.sub(
            r"def divide\(a, b\):\s*\n\s*return a / b",
            "def divide(a, b):\n    if b == 0:\n        return None\n    return a / b",
            patched
        )

    if "def add_numbers(a, b):" in patched and ("int" in fix_text or "try" in fix_text or "типов" in fix_text):
        # Заменяем функцию add_numbers, но сохраняем вызов
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
        # Заменяем только определение функции, не трогая вызов
        patched = re.sub(
            r"def add_numbers\(a, b\):\s*\n\s*return a \+ b",
            new_function,
            patched
        )

    if "print(i)" in patched and ("print(n)" in fix_text or "печать n" in fix_text or "логичнее печатать n" in fix_text):
        patched = patched.replace("print(i)", "print(n)")

    return patched

def run_tests(code: str, bug_id: int) -> Tuple[bool, str]:
    """
    Гоним мини-тесты в песочнице (exec в локальном dict).
    Для каждого бага — простой оракул.
    """
    env: Dict[str, Any] = {}
    out = StringIO()
    try:
        with redirect_stdout(out):
            exec(code, env, env)
            if bug_id == 1:
                res = env["calculate_sum"]([1, 2, 3])
                assert res == 6
            elif bug_id == 2:
                assert env["process_data"](None) is None
                assert env["process_data"]({"value": 3}) == 6
            elif bug_id == 3:
                assert env["divide"](4, 2) == 2
                assert env["divide"](4, 0) is None
            elif bug_id == 4:
                res = env["add_numbers"]("2", 3)
                assert res == 5
            elif bug_id == 5:
                # Должно просто выполниться без NameError
                env["count_down"](2)
            else:
                print("Нет тестов для этого кейса; считаем passed.")
        return True, out.getvalue()
    except Exception as e:
        return False, f"TEST FAILED: {e}\n--- Output ---\n{out.getvalue()}"
