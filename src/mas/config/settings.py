# -*- coding: utf-8 -*-
"""Centralized settings loader: loads .env and exposes env helpers."""
import os
try:
	from dotenv import load_dotenv
	load_dotenv()
except Exception:
	pass

class Settings:
	@staticmethod
	def get(name: str, default: str = "") -> str:
		return os.getenv(name, default)
