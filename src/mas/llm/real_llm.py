#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Реальная интеграция с OpenAI API для MAS системы.
"""

import os
import time
import logging
from typing import List, Optional
from dataclasses import dataclass

# Попытка импорта OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ OpenAI не установлен. Установите: pip install openai")

# Попытка импорта python-dotenv
try:
    from dotenv import load_dotenv
    load_dotenv()
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    print("⚠️ python-dotenv не установлен. Установите: pip install python-dotenv")

log = logging.getLogger("RealLLM")

@dataclass
class LLMConfig:
    """Конфигурация для OpenAI API."""
    api_key: str
    model: str = "gpt-4"
    max_tokens: int = 1000
    temperature: float = 0.1
    max_requests_per_minute: int = 20

class RealLLMClient:
    """Клиент для работы с реальным OpenAI API."""
    
    def __init__(self, config: Optional[LLMConfig] = None):
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library not installed. Run: pip install openai")
        
        if config is None:
            config = self._load_config_from_env()
        
        self.config = config
        self.client = OpenAI(api_key=config.api_key)
        self.request_times = []  # Для rate limiting
        
        log.info(f"Инициализирован OpenAI клиент с моделью {config.model}")
    
    def _load_config_from_env(self) -> LLMConfig:
        """Загрузка конфигурации из переменных окружения."""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY не найден в переменных окружения. "
                "Создайте файл .env с вашим API ключом или установите переменную окружения."
            )
        
        return LLMConfig(
            api_key=api_key,
            model=os.getenv('OPENAI_MODEL', 'gpt-4'),
            max_tokens=int(os.getenv('OPENAI_MAX_TOKENS', '1000')),
            temperature=float(os.getenv('OPENAI_TEMPERATURE', '0.1')),
            max_requests_per_minute=int(os.getenv('OPENAI_MAX_REQUESTS_PER_MINUTE', '20'))
        )
    
    def _rate_limit(self):
        """Простая реализация rate limiting."""
        now = time.time()
        # Удаляем запросы старше минуты
        self.request_times = [t for t in self.request_times if now - t < 60]
        
        if len(self.request_times) >= self.config.max_requests_per_minute:
            sleep_time = 60 - (now - self.request_times[0])
            if sleep_time > 0:
                log.warning(f"Rate limit достигнут. Ожидание {sleep_time:.1f} секунд...")
                time.sleep(sleep_time)
        
        self.request_times.append(now)
    
    def _make_request(self, messages: List[dict]) -> str:
        """Выполнение запроса к OpenAI API."""
        self._rate_limit()
        
        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature
            )
            
            content = response.choices[0].message.content
            log.debug(f"Получен ответ от OpenAI: {content[:100]}...")
            return content
            
        except Exception as e:
            log.error(f"Ошибка при обращении к OpenAI API: {e}")
            raise

def llm_find_issues_real(code: str, client: RealLLMClient) -> str:
    """Реальный анализ кода через OpenAI API."""
    messages = [
        {
            "role": "system",
            "content": """Ты - эксперт по анализу кода Python. Твоя задача - найти потенциальные баги и проблемы в коде.
            
Анализируй код на предмет:
- Выходов за границы массивов
- Обращений к None объектам
- Деления на ноль
- Несоответствия типов
- Неинициализированных переменных
- Других потенциальных ошибок

Отвечай кратко и конкретно, указывая найденные проблемы."""
        },
        {
            "role": "user",
            "content": f"Проанализируй этот код на наличие багов:\n\n```python\n{code}\n```"
        }
    ]
    
    return client._make_request(messages)

def llm_suggest_fixes_real(report: str, code: str, client: RealLLMClient) -> List[str]:
    """Реальная генерация исправлений через OpenAI API."""
    messages = [
        {
            "role": "system", 
            "content": """Ты - эксперт по исправлению багов в Python коде. 
            
Твоя задача - предложить конкретные исправления для найденных проблем.
Каждое исправление должно быть:
- Конкретным и применимым
- Кратким (1-2 предложения)
- Направленным на решение конкретной проблемы

Верни список из 2-5 различных вариантов исправления в формате:
1. Первое исправление
2. Второе исправление
и т.д."""
        },
        {
            "role": "user",
            "content": f"""Код с проблемой:
```python
{code}
```

Найденные проблемы:
{report}

Предложи конкретные исправления:"""
        }
    ]
    
    response = client._make_request(messages)
    
    # Парсим ответ на отдельные предложения
    fixes = []
    for line in response.split('\n'):
        line = line.strip()
        if line and (line[0].isdigit() or line.startswith('-') or line.startswith('*')):
            # Убираем нумерацию
            clean_fix = line
            for prefix in ['1.', '2.', '3.', '4.', '5.', '-', '*']:
                if clean_fix.startswith(prefix):
                    clean_fix = clean_fix[len(prefix):].strip()
                    break
            if clean_fix:
                fixes.append(clean_fix)
    
    return fixes[:5]  # Максимум 5 исправлений

def llm_review_fix_real(fix_text: str, client: RealLLMClient) -> str:
    """Реальное ревью исправления через OpenAI API."""
    messages = [
        {
            "role": "system",
            "content": """Ты - опытный код-ревьюер. Твоя задача - оценить предложенное исправление кода.
            
Критерии оценки:
- Корректность решения
- Полнота исправления
- Отсутствие новых проблем
- Читаемость кода

Ответь только одним словом:
- "approve" - если исправление хорошее
- "request_changes" - если нужны доработки"""
        },
        {
            "role": "user", 
            "content": f"Оцени это исправление: {fix_text}"
        }
    ]
    
    response = client._make_request(messages).lower().strip()
    
    # Извлекаем решение из ответа
    if "approve" in response:
        return "approve"
    else:
        return "request_changes"

# Глобальный клиент для использования в системе
_global_client: Optional[RealLLMClient] = None

def get_llm_client() -> RealLLMClient:
    """Получение глобального клиента LLM."""
    global _global_client
    if _global_client is None:
        _global_client = RealLLMClient()
    return _global_client

def is_openai_available() -> bool:
    """Проверка доступности OpenAI API."""
    return OPENAI_AVAILABLE and DOTENV_AVAILABLE

# Обёртки для совместимости с существующим кодом
def llm_find_issues_wrapper(code: str) -> str:
    """Обёртка для совместимости."""
    if not is_openai_available():
        # Fallback к имитации
        from llm_utils import llm_find_issues
        return llm_find_issues(code)
    
    try:
        client = get_llm_client()
        return llm_find_issues_real(code, client)
    except Exception as e:
        log.error(f"Ошибка при использовании OpenAI API: {e}")
        # Fallback к имитации
        from llm_utils import llm_find_issues
        return llm_find_issues(code)

def llm_suggest_fixes_wrapper(report: str, code: str = "") -> List[str]:
    """Обёртка для совместимости."""
    if not is_openai_available():
        from llm_utils import llm_suggest_fixes
        return llm_suggest_fixes(report)
    
    try:
        client = get_llm_client()
        return llm_suggest_fixes_real(report, code, client)
    except Exception as e:
        log.error(f"Ошибка при использовании OpenAI API: {e}")
        from llm_utils import llm_suggest_fixes
        return llm_suggest_fixes(report)

def llm_review_fix_wrapper(fix_text: str) -> str:
    """Обёртка для совместимости."""
    if not is_openai_available():
        from llm_utils import llm_review_fix
        return llm_review_fix(fix_text)
    
    try:
        client = get_llm_client()
        return llm_review_fix_real(fix_text, client)
    except Exception as e:
        log.error(f"Ошибка при использовании OpenAI API: {e}")
        from llm_utils import llm_review_fix
        return llm_review_fix(fix_text)
