# -*- coding: utf-8 -*-
import random
from mas.evaluation.test_cases import BUG_CASES
from mas.llm.mock_client import llm_find_issues, llm_suggest_fixes
from mas.evaluation.patching import apply_patch, run_tests

random.seed(42)

def main():
	ok = 0
	for case in BUG_CASES:
		print(f"\nТест-кейс {case['id']}: {case['description']}")
		report = llm_find_issues(case['code'])
		fixes = llm_suggest_fixes(report)
		chosen = fixes[0] if fixes else ""
		patched = apply_patch(case['code'], chosen)
		passed, log = run_tests(patched, case['id'])
		status = "✅ УСПЕХ" if passed else "❌ ПРОВАЛ"
		print(f"Вердикт: {status}; фикс: {chosen[:80]}")
		if not passed:
			print(f"Лог:\n{log[:300]}")
		ok += 1 if passed else 0
	print(f"\nИТОГО: {ok}/{len(BUG_CASES)} успехов")

if __name__ == "__main__":
	main()
