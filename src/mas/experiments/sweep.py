# -*- coding: utf-8 -*-
"""
Адаптированная версия sweep: запускает новый CLI `src/mas/cli/main.py`.
"""

from __future__ import annotations
import csv
import json
import subprocess
import sys
from itertools import product
from pathlib import Path
from datetime import datetime

PY = sys.executable
HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[2]
RESULTS_DIR = PROJECT_ROOT / "src" / "mas" / "analytics" / "results"

def run_case(approach: str, seed: int, extra_args: list[str]) -> dict:
	cmd = [PY, "-X", "utf8", str(PROJECT_ROOT / "src" / "mas" / "cli" / "main.py"), "--approach", approach, "--seed", str(seed), "--verbose"]
	cmd += extra_args
	out = subprocess.run(cmd, capture_output=True, text=True, check=False)
	return parse_stdout(out.stdout)

def parse_stdout(stdout: str) -> dict:
	summary = {"success_cases": 0, "failed_cases": 0, "avg_time": None}
	lines = [l.strip() for l in stdout.splitlines()]
	success = failed = 0
	times = []
	for line in lines:
		if line.startswith("✅ Статус: success"):
			success += 1
		if line.startswith("❌ Статус: failed") or "Статус: failed" in line:
			failed += 1
		if line.startswith("Время:"):
			try:
				val = float(line.split()[1])
				times.append(val)
			except Exception:
				pass
	summary["success_cases"] = success
	summary["failed_cases"] = failed
	summary["avg_time"] = round(sum(times)/len(times), 6) if times else None
	return summary

def main():
	grid_candidates = [1, 2]
	grid_reviewers = [1, 3]
	grid_retries = [0, 1]
	seed = 42

	rows = []
	for approach in ["sync", "async"]:
		for n_cand, n_rev, n_ret in product(grid_candidates, grid_reviewers, grid_retries):
			extra = [
				"--cases", "1", "2", "3",
				"--save-results", "tmp.json",
				"--n-candidates", str(n_cand),
				"--n-reviewers", str(n_rev),
				"--max-retries", str(n_ret),
			]
			res = run_case(approach, seed, extra)
			rows.append({
				"approach": approach,
				"n_candidates": n_cand,
				"n_reviewers": n_rev,
				"max_retries": n_ret,
				**res,
			})
			print(f"{approach} | cand={n_cand} rev={n_rev} ret={n_ret} -> {res}")

	ts = datetime.now().strftime("%Y%m%d_%H%M%S")
	RESULTS_DIR.mkdir(parents=True, exist_ok=True)
	out_csv = RESULTS_DIR / f"sweep_results_{ts}.csv"
	with out_csv.open("w", newline="", encoding="utf-8") as f:
		w = csv.DictWriter(f, fieldnames=rows[0].keys())
		w.writeheader()
		w.writerows(rows)
	out_json = RESULTS_DIR / f"sweep_results_{ts}.json"
	out_json.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
	print(f"\nГотово: {out_csv}\nИ JSON: {out_json}")

if __name__ == "__main__":
	main()
