# -*- coding: utf-8 -*-
"""Adapter to reuse inference_scaling_lab functions (now moved)."""
try:
	from .inference_scaling_lab import run_scaling_experiment, parse_output  # noqa: F401
except Exception as _e:  # pragma: no cover
	run_scaling_experiment = None
	parse_output = None
	__import_error__ = _e
