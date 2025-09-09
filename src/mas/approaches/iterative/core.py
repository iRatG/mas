# -*- coding: utf-8 -*-
"""
Итеративный процесс взаимодействия с LLM API (перенос из iterative_process.py).
"""

import os
import time
import logging
import re
from typing import Optional, List, Tuple
from dataclasses import dataclass

try:
	from openai import OpenAI
	OPENAI_AVAILABLE = True
except ImportError:
	OPENAI_AVAILABLE = False
	print("⚠️ OpenAI не установлен. Установите: pip install openai")

try:
	from dotenv import load_dotenv
	load_dotenv()
	DOTENV_AVAILABLE = True
except ImportError:
	DOTENV_AVAILABLE = False
	print("⚠️ python-dotenv не установлен. Установите: pip install python-dotenv")

log = logging.getLogger("IterativeProcess")

@dataclass
class LLMConfig:
	"""Конфигурация для OpenAI API."""
	api_key: str
	model: str
	max_tokens: int
	temperature: float
	max_requests_per_minute: int

class IterativeLLMClient:
	"""Клиент для итеративного процесса с OpenAI API."""
	
	def __init__(self, config: Optional[LLMConfig] = None):
		if not OPENAI_AVAILABLE:
			raise ImportError("OpenAI library not installed. Run: pip install openai")
		if config is None:
			config = self._load_config_from_env()
		self.config = config
		self.client = OpenAI(api_key=config.api_key)
		self.request_times = []
		log.info(f"Инициализирован OpenAI клиент с моделью {config.model}")
	
	def _load_config_from_env(self) -> LLMConfig:
		api_key = os.getenv('OPENAI_API_KEY')
		if not api_key:
			raise ValueError("OPENAI_API_KEY не найден в окружении")
		return LLMConfig(
			api_key=api_key,
			model=os.getenv('OPENAI_MODEL'),
			max_tokens=int(os.getenv('OPENAI_MAX_TOKENS')),
			temperature=float(os.getenv('OPENAI_TEMPERATURE')),
			max_requests_per_minute=int(os.getenv('OPENAI_MAX_REQUESTS_PER_MINUTE'))
		)
	
	def _make_messages(self, task_description: str, code: str, history: str) -> List[dict]:
		system_prompt = (
			"Ты помощник-разработчик. Исправь баги в переданном Python-коде. "
			"Верни только целиком исправленный код в одном блоке ```python ...```. "
			"Не добавляй пояснений, текста вне блока кода или форматирования."
		)
		user_prompt = (
			f"Задача: {task_description}.\n\n"
			f"История неуспешных попыток (если есть):\n{history}\n\n"
			"Исправь следующий код так, чтобы он проходил простые тесты. "
			"Верни только полностью исправленный код целиком:\n\n"
			f"```python\n{code}\n```"
		)
		return [
			{"role": "system", "content": system_prompt},
			{"role": "user", "content": user_prompt},
		]
	
	def send_request(self, messages: List[dict]) -> str:
		if not self.client:
			raise RuntimeError("OpenAI client is not initialized.")
		response = self.client.chat.completions.create(
			model=self.config.model,
			messages=messages,
			max_tokens=self.config.max_tokens,
			temperature=self.config.temperature,
		)
		return response.choices[0].message.content or ""
	
	def _extract_code(self, text: str) -> Optional[str]:
		pattern = r"```python\n([\s\S]*?)```|```\n([\s\S]*?)```"
		m = re.search(pattern, text, re.IGNORECASE)
		if not m:
			return None
		code_block = m.group(1) if m.group(1) is not None else m.group(2)
		return code_block.strip()
	
	def check_code(self, code: str, bug_id: int) -> Tuple[bool, float, str]:
		from mas.evaluation.patching import run_tests
		start_time = time.time()
		success, log_text = run_tests(code, bug_id, use_sandbox=False, timeout=5.0)
		elapsed = time.time() - start_time
		return success, elapsed, log_text
	
	def iterate_process(self, code: str, bug_id: int, task_description: str, max_attempts: int = 3) -> dict:
		attempt = 0
		history = ""
		metrics = {
			"bug_id": bug_id,
			"attempts": 0,
			"success": False,
			"total_time_sec": 0.0,
			"attempt_details": [],
		}
		while attempt < max_attempts:
			attempt += 1
			t0 = time.time()
			messages = self._make_messages(task_description, code, history)
			raw_response = self.send_request(messages)
			llm_time = time.time() - t0
			fixed_code = self._extract_code(raw_response)
			if not fixed_code:
				metrics["attempt_details"].append({
					"attempt": attempt,
					"llm_time_sec": llm_time,
					"test_time_sec": 0.0,
					"result": "no_code_block",
					"log": raw_response[:500],
				})
				history += f"\nПопытка {attempt}: Модель не вернула код в блоке. Верни только код."
				continue
			ok, test_time, test_log = self.check_code(fixed_code, bug_id)
			metrics["attempt_details"].append({
				"attempt": attempt,
				"llm_time_sec": llm_time,
				"test_time_sec": test_time,
				"result": "success" if ok else "fail",
				"log": test_log[:1000],
			})
			if ok:
				metrics["success"] = True
				metrics["attempts"] = attempt
				metrics["total_time_sec"] = sum(d["llm_time_sec"] + d["test_time_sec"] for d in metrics["attempt_details"])
				return metrics
			history += (
				f"\nПопытка {attempt} не прошла тесты. Ошибки/лог:\n{test_log[:500]}\n"
				"Не повторяй прежнее решение. Предложи другой подход."
			)
		metrics["attempts"] = attempt
		metrics["total_time_sec"] = sum(d["llm_time_sec"] + d["test_time_sec"] for d in metrics["attempt_details"])
		return metrics
