# -*- coding: utf-8 -*-
"""
Имитация LLM функциональности (перенос из llm_utils.py).
"""

import random
from typing import List

def llm_find_issues(code: str) -> str:
	"""Наивная «диагностика» по ключевым паттернам."""
	if "len(arr)+1" in code:
		return "Обнаружен выход за границы индекса в цикле range(len(arr)+1)."
	if "data.get" in code and "process_data" in code:
		return "Возможен None во входе: data может быть None перед обращением .get."
	if "return a / b" in code:
		return "Не обрабатывается деление на ноль: b может быть 0."
	if "add_numbers" in code and "return a + b" in code:
		return "Сложение строки и числа вызывает TypeError: необходимо приведение типов."
	if "print(i)" in code and "count_down" in code:
		return "Используется неинициализированная переменная i: вероятно, хотели печатать n."
	return "Проблемы не распознаны. Проверьте граничные случаи и типы."

def llm_suggest_fixes(report: str) -> List[str]:
	"""Формируем несколько текстовых предложений фиксов (кандидатов)."""
	suggestions = []
	if "границы" in report or "range(len(arr)+1)" in report:
		suggestions += [
			"Заменить range(len(arr)+1) на range(len(arr)).",
			"Итерироваться по элементам: for x in arr: s += x."
		]
	if "None" in report:
		suggestions += [
			"Добавить проверку if data is None: return None перед .get.",
			"Безопасная логика: if data and 'value' in data: ... else: return None."
		]
	if "деление на ноль" in report or "b может быть 0" in report:
		suggestions += [
			"Добавить проверку if b == 0: return None.",
			"Поднять исключение при b == 0."
		]
	if "TypeError" in report:
		suggestions += [
			"Попробовать преобразовать строковые числа в int перед сложением.",
			"Обработать типы через try/except и привести к числам."
		]
	if "неинициализированная" in report:
		suggestions += [
			"Заменить print(i) на print(n) внутри цикла.",
			"Ввести локальную i = n, но логичнее печатать n."
		]
	if not suggestions:
		suggestions = ["Добавить проверки входных данных и тесты на крайние случаи."]
	return suggestions[:5]

def llm_review_fix(fix_text: str) -> str:
	"""Имитируем вердикт ревьюера по тексту фикса."""
	score = 0
	for kw in ("Заменить", "Добавить", "проверку", "try", "исключение", "int", "range", "print(n)"):
		if kw.lower() in fix_text.lower():
			score += 1
	return "approve" if score + random.random() > 1.2 else "request_changes"

__all__ = ["llm_find_issues", "llm_suggest_fixes", "llm_review_fix"]
