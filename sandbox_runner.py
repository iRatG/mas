#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Безопасный сэндбокс для выполнения тестируемого кода.
Выполняет код в отдельном процессе с таймаутом для повышения безопасности.
"""
from __future__ import annotations
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Tuple

PY = sys.executable

def run_tests_sandbox(code: str, bug_id: int, timeout: float = 5.0) -> Tuple[bool, str]:
    """
    Безопасное выполнение тестов в отдельном процессе.
    
    Args:
        code: Код для тестирования
        bug_id: ID бага для определения типа теста
        timeout: Таймаут выполнения в секундах
        
    Returns:
        Tuple[bool, str]: (успех, лог выполнения)
    """
    # Создаём временный файл с кодом
    with tempfile.TemporaryDirectory() as temp_dir:
        code_path = Path(temp_dir) / "code_under_test.py"
        code_path.write_text(code, encoding="utf-8")
        
        # Создаём скрипт-раннер для изолированного выполнения
        runner_script = f"""
import json
import sys
import traceback
from pathlib import Path

# Добавляем путь к основному проекту для импорта patch_utils
sys.path.insert(0, r'{Path(__file__).parent.absolute()}')

try:
    from patch_utils import run_tests
    
    # Читаем код из файла
    code_path = Path(r'{code_path}')
    code = code_path.read_text(encoding='utf-8')
    
    # Выполняем тесты
    passed, output = run_tests(code, {bug_id})
    
    # Возвращаем результат в JSON формате
    result = {{
        'passed': passed,
        'output': output,
        'error': None
    }}
    print(json.dumps(result, ensure_ascii=False))
    
except Exception as e:
    # В случае ошибки возвращаем информацию об исключении
    result = {{
        'passed': False,
        'output': '',
        'error': f'{{type(e).__name__}}: {{str(e)}}',
        'traceback': traceback.format_exc()
    }}
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(1)
"""
        
        # Записываем скрипт-раннер
        runner_path = Path(temp_dir) / "test_runner.py"
        runner_path.write_text(runner_script, encoding="utf-8")
        
        try:
            # Запускаем в отдельном процессе с таймаутом
            process = subprocess.run(
                [PY, str(runner_path)],
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8'
            )
            
            if process.returncode == 0:
                # Парсим JSON результат
                try:
                    result = json.loads(process.stdout.strip())
                    return result['passed'], result['output']
                except (json.JSONDecodeError, KeyError) as e:
                    return False, f"Ошибка парсинга результата: {e}\\nSTDOUT: {process.stdout}\\nSTDERR: {process.stderr}"
            else:
                # Процесс завершился с ошибкой
                try:
                    result = json.loads(process.stdout.strip())
                    error_msg = result.get('error', 'Неизвестная ошибка')
                    return False, f"Ошибка выполнения: {error_msg}"
                except json.JSONDecodeError:
                    return False, f"Процесс завершился с кодом {process.returncode}\\nSTDERR: {process.stderr}"
                    
        except subprocess.TimeoutExpired:
            return False, f"TIMEOUT: Выполнение превысило {timeout} секунд"
        except Exception as e:
            return False, f"Ошибка запуска процесса: {type(e).__name__}: {e}"

def main():
    """Интерфейс командной строки для сэндбокса."""
    if len(sys.argv) != 4:
        print("Использование: python sandbox_runner.py <path_to_code.py> <bug_id> <timeout_sec>")
        sys.exit(1)
    
    try:
        code_path = Path(sys.argv[1])
        bug_id = int(sys.argv[2])
        timeout = float(sys.argv[3])
        
        if not code_path.exists():
            print(f"Файл не найден: {code_path}")
            sys.exit(1)
        
        code = code_path.read_text(encoding="utf-8")
        passed, output = run_tests_sandbox(code, bug_id, timeout)
        
        result = {
            'passed': passed,
            'output': output
        }
        
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(0 if passed else 1)
        
    except ValueError as e:
        print(f"Ошибка в параметрах: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Неожиданная ошибка: {type(e).__name__}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
