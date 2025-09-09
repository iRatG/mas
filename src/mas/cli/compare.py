# -*- coding: utf-8 -*-
"""
Сравнительный раннер: запускает 4 подхода и сохраняет метрики в analytics/results.
"""
from __future__ import annotations
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from mas.evaluation.test_cases import BUG_CASES
from mas.llm.mock_client import llm_find_issues, llm_suggest_fixes
from mas.evaluation.patching import apply_patch, run_tests
from mas.approaches.iterative.runner import IterativeLLMClient

PY = sys.executable
HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[2]
RESULTS_DIR = PROJECT_ROOT / "src" / "mas" / "analytics" / "results"


def run_sync_async(approach: str, cases: List[int]) -> Dict[str, Any]:
	"""Запускает main.py для sync/async и возвращает JSON-результат (из файла)."""
	assert approach in ("sync", "async")
	tmp = PROJECT_ROOT / "tmp_compare_{}_{}.json".format(approach, datetime.now().strftime("%H%M%S"))
	cmd = [
		PY, "-X", "utf8",
		str(PROJECT_ROOT / "src" / "mas" / "cli" / "main.py"),
		"--approach", approach,
		"--cases", *[str(i) for i in cases],
		"--save-results", str(tmp),
	]
	subprocess.run(cmd, check=False, text=True)
	if tmp.exists():
		data = json.loads(tmp.read_text(encoding="utf-8"))
		tmp.unlink(missing_ok=True)
		return data
	return {"error": "no_result"}


def run_baseline(cases: List[int]) -> Dict[str, Any]:
	"""Однопроходный бейслайн на мок-LLM: собираем простые метрики."""
	results: List[Dict[str, Any]] = []
	ok = 0
	for case in BUG_CASES:
		if case["id"] not in cases:
			continue
		report = llm_find_issues(case["code"])
		fixes = llm_suggest_fixes(report)
		chosen = fixes[0] if fixes else ""
		patched = apply_patch(case["code"], chosen)
		passed, log = run_tests(patched, case["id"])
		ok += 1 if passed else 0
		results.append({
			"id": case["id"],
			"description": case["description"],
			"fix": chosen,
			"passed": passed,
			"log": log[:500],
		})
	return {
		"approach": "baseline",
		"cases": cases,
		"success": ok,
		"total": len(cases),
		"results": results,
	}


def run_iterative(cases: List[int]) -> Dict[str, Any]:
	client = IterativeLLMClient()
	results: List[Dict[str, Any]] = []
	ok = 0
	for case in BUG_CASES:
		if case["id"] not in cases:
			continue
		m = client.iterate_process(code=case['code'], bug_id=case['id'], task_description=case['description'])
		ok += 1 if m.get("success") else 0
		results.append({"id": case["id"], "description": case["description"], **m})
	return {
		"approach": "iterative",
		"cases": cases,
		"success": ok,
		"total": len(cases),
		"results": results,
	}


def main():
	RESULTS_DIR.mkdir(parents=True, exist_ok=True)
	cases = [c["id"] for c in BUG_CASES]

	print("\n▶ Запуск sync...")
	sync_json = run_sync_async("sync", cases)
	print("Готово")

	print("\n▶ Запуск async...")
	async_json = run_sync_async("async", cases)
	print("Готово")

	print("\n▶ Запуск baseline...")
	baseline_json = run_baseline(cases)
	print(f"Готово: {baseline_json['success']}/{baseline_json['total']}")

	print("\n▶ Запуск iterative...")
	iter_json = run_iterative(cases)
	print(f"Готово: {iter_json['success']}/{iter_json['total']}")

	ts = datetime.now().strftime("%Y%m%d_%H%M%S")
	out_path = RESULTS_DIR / f"compare_{ts}.json"
	summary = {
		"timestamp": ts,
		"cases": cases,
		"sync": sync_json,
		"async": async_json,
		"baseline": baseline_json,
		"iterative": iter_json,
	}
	out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
	print(f"\n💾 Метрики сохранены: {out_path}")

	# Краткий свод
	def _succ(d: Dict[str, Any]) -> str:
		if "results" in d and "success" in d and "total" in d:
			return f"{d['success']}/{d['total']}"
		if isinstance(d, dict) and d.get("comparison") or d.get("sync_approach"):
			# свод из main.py
			s = d.get("sync_approach", {})
			a = d.get("async_approach", {})
			return f"sync:{s.get('cases_processed',0)} async:{a.get('cases_processed',0)}"
		return "n/a"
	print("\nСвод: baseline=", _succ(baseline_json), " iterative=", _succ(iter_json))

if __name__ == "__main__":
	main()
