# -*- coding: utf-8 -*-
"""
Безопасный сэндбокс для выполнения тестируемого кода (перенос из sandbox_runner.py).
"""

from __future__ import annotations
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Tuple

PY = sys.executable

_THIS_FILE = Path(__file__).resolve()
_SRC_ROOT = _THIS_FILE.parents[2]  # .../src
_PROJECT_ROOT = _THIS_FILE.parents[3]

def run_tests_sandbox(code: str, bug_id: int, timeout: float = 5.0) -> Tuple[bool, str]:
	"""
	Безопасное выполнение тестов в отдельном процессе.
	"""
	with tempfile.TemporaryDirectory() as temp_dir:
		code_path = Path(temp_dir) / "code_under_test.py"
		code_path.write_text(code, encoding="utf-8")

		runner_script = f"""
import json
import sys
import traceback
from pathlib import Path

# Добавляем пути проекта для импорта mas.evaluation.patching
sys.path.insert(0, r'{_SRC_ROOT.as_posix()}')
sys.path.insert(0, r'{_PROJECT_ROOT.as_posix()}')

try:
    from mas.evaluation.patching import run_tests

    code_path = Path(r'{code_path.as_posix()}')
    code = code_path.read_text(encoding='utf-8')

    passed, output = run_tests(code, {bug_id})

    result = {{
        'passed': passed,
        'output': output,
        'error': None
    }}
    print(json.dumps(result, ensure_ascii=False))

except Exception as e:
    result = {{
        'passed': False,
        'output': '',
        'error': f'{{type(e).__name__}}: {{str(e)}}',
        'traceback': traceback.format_exc()
    }}
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(1)
"""

		runner_path = Path(temp_dir) / "test_runner.py"
		runner_path.write_text(runner_script, encoding="utf-8")

		try:
			process = subprocess.run(
				[PY, str(runner_path)],
				capture_output=True,
				text=True,
				timeout=timeout,
				encoding='utf-8'
			)

			if process.returncode == 0:
				try:
					result = json.loads(process.stdout.strip())
					return result['passed'], result['output']
				except (json.JSONDecodeError, KeyError) as e:
					return False, f"Ошибка парсинга результата: {e}\nSTDOUT: {process.stdout}\nSTDERR: {process.stderr}"
			else:
				try:
					result = json.loads(process.stdout.strip())
					error_msg = result.get('error', 'Неизвестная ошибка')
					return False, f"Ошибка выполнения: {error_msg}"
				except json.JSONDecodeError:
					return False, f"Процесс завершился с кодом {process.returncode}\nSTDERR: {process.stderr}"

		except subprocess.TimeoutExpired:
			return False, f"TIMEOUT: Выполнение превысило {timeout} секунд"
		except Exception as e:
			return False, f"Ошибка запуска процесса: {type(e).__name__}: {e}"

__all__ = ["run_tests_sandbox"]
