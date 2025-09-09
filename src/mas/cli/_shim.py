# -*- coding: utf-8 -*-
"""Helper to run legacy scripts with new module layout."""
import os
import sys
import runpy
import importlib

_THIS_DIR = os.path.dirname(__file__)
_PROJECT_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", "..", ".."))
_SRC_ROOT = os.path.join(_PROJECT_ROOT, "src")
for p in (_SRC_ROOT, _PROJECT_ROOT):
	if p not in sys.path:
		sys.path.insert(0, p)

MODULE_MAP = {
	"test_cases": "mas.evaluation.test_cases",
	"approach1_sync": "mas.approaches.sync",
	"approach2_async": "mas.approaches.async_",
	"patch_utils": "mas.evaluation.patching",
	"llm_utils": "mas.llm.mock_client",
}

def shim_legacy_imports() -> None:
	for legacy, modern in MODULE_MAP.items():
		if legacy not in sys.modules:
			mod = importlib.import_module(modern)
			sys.modules[legacy] = mod


def run_legacy_script(script_name: str) -> None:
	shim_legacy_imports()
	candidate_paths = [
		os.path.join(_PROJECT_ROOT, script_name),
		os.path.join(_PROJECT_ROOT, "examples", script_name),
	]
	for script_path in candidate_paths:
		if os.path.exists(script_path):
			runpy.run_path(script_path, run_name="__main__")
			return
	raise FileNotFoundError(f"Cannot locate {script_name} in {candidate_paths}")
