# -*- coding: utf-8 -*-
import os
import sys
from mas.approaches.iterative.runner import IterativeLLMClient
from mas.evaluation.test_cases import BUG_CASES

# ensure UTF-8 stdout on Windows
try:
	import ctypes
	ctypes.windll.kernel32.SetConsoleOutputCP(65001)
except Exception:
	pass

def main():
	client = IterativeLLMClient()
	ok = 0
	for case in BUG_CASES:
		print(f"\nТест-кейс {case['id']}: {case['description']}")
		m = client.iterate_process(code=case['code'], bug_id=case['id'], task_description=case['description'])
		status = "✅ УСПЕХ" if m["success"] else "❌ ПРОВАЛ"
		print(f"Статус: {status}; попыток: {m['attempts']}; время: {m['total_time_sec']:.2f}с")
		ok += 1 if m["success"] else 0
	print(f"\nИТОГО: {ok}/{len(BUG_CASES)} успехов")

if __name__ == "__main__":
	main()
