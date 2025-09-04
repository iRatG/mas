#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Грид-эксперименты поверх твоего main.py.
Пробегаем по (кандидаты, ревьюеры, ретраи) и собираем сводную таблицу.
Зависимости: только стандартная библиотека. Python 3.10+.
"""

from __future__ import annotations
import csv
import json
import subprocess
import sys
from itertools import product
from pathlib import Path
from datetime import datetime

PY = sys.executable  # текущая интерпретация Python
ROOT = Path(__file__).resolve().parent

def run_case(approach: str, seed: int, extra_args: list[str]) -> dict:
    """Запуск твоего main.py и возврат сводки по результатам из stdout."""
    cmd = [PY, str(ROOT / "main.py"), "--approach", approach, "--seed", str(seed), "--verbose"]
    cmd += extra_args
    out = subprocess.run(cmd, capture_output=True, text=True, check=False)
    # Функция ниже вытаскивает из вывода ключевые метрики (успех/время/сообщения и т.п.).
    return parse_stdout(out.stdout)

def parse_stdout(stdout: str) -> dict:
    # Очень простой парсер: ищем ключевые строки из твоего README-образца.
    # Для прод-версии можно сделать JSON-лог в самом main.py.
    summary = {"success_cases": 0, "failed_cases": 0, "avg_time": None}
    lines = [l.strip() for l in stdout.splitlines()]
    success = failed = 0
    times = []
    for i, line in enumerate(lines):
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
    grid_candidates = [1, 2, 3, 5]
    grid_reviewers = [1, 3, 5]
    grid_retries = [0, 1, 2]
    seed = 42

    rows = []
    for approach in ["sync", "async"]:
        for n_cand, n_rev, n_ret in product(grid_candidates, grid_reviewers, grid_retries):
            extra = [
                "--cases", "1", "2", "3", "4", "5",
                "--save-results", "tmp.json",
                # ниже — флаги, которые ты можешь обработать в main.py
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

    # Сохраняем результаты
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_csv = ROOT / f"sweep_results_{ts}.csv"
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    out_json = ROOT / f"sweep_results_{ts}.json"
    out_json.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nГотово: {out_csv}\nИ JSON: {out_json}")

if __name__ == "__main__":
    main()
