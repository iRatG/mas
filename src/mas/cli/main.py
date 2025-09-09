# -*- coding: utf-8 -*-
"""Unified CLI entrypoint delegating to existing main.py."""
import os
import sys
import runpy

# Ensure project root and src/ on sys.path so imports like `mas.*` and legacy names work
_THIS_DIR = os.path.dirname(__file__)
_PROJECT_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", "..", ".."))
_SRC_ROOT = os.path.join(_PROJECT_ROOT, "src")
for p in (_SRC_ROOT, _PROJECT_ROOT):
	if p not in sys.path:
		sys.path.insert(0, p)

# Shim legacy module names to new package modules so legacy main.py keeps working
try:
	import importlib
	module_map = {
		"test_cases": "mas.evaluation.test_cases",
		"approach1_sync": "mas.approaches.sync",
		"approach2_async": "mas.approaches.async_",
		"patch_utils": "mas.evaluation.patching",
		"llm_utils": "mas.llm.mock_client",
		"real_llm": "mas.llm.real_llm",
	}
	for legacy, modern in module_map.items():
		if legacy not in sys.modules:
			mod = importlib.import_module(modern)
			sys.modules[legacy] = mod
except Exception:
	pass

if __name__ == "__main__":
	main_path = os.path.join(_PROJECT_ROOT, "main.py")
	runpy.run_path(main_path, run_name="__main__")
