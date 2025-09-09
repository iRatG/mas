# -*- coding: utf-8 -*-
"""Thin adapter to RealLLMClient now located under mas.llm.real_llm."""
from typing import List

try:
	from .real_llm import RealLLMClient, get_llm_client  # reuse implementation now moved
except Exception as _e:  # pragma: no cover
	RealLLMClient = None
	get_llm_client = None
	__import_error__ = _e

__all__ = ["RealLLMClient", "get_llm_client"]
