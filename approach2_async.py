#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Подход 2: Асинхронная шина (2b-стиль) для исправления багов.
Использует агентную архитектуру с асинхронной коммуникацией.
"""

import asyncio
import logging
import random
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from llm_utils import llm_find_issues, llm_suggest_fixes, llm_review_fix
from patch_utils import apply_patch, run_tests

log = logging.getLogger("AsyncApproach")

@dataclass
class AsyncApproachMetrics:
    """Метрики для асинхронного подхода."""
    start_time: float = 0.0
    end_time: float = 0.0
    messages_sent: int = 0
    messages_received: int = 0
    timeouts_occurred: int = 0
    agents_involved: int = 0
    parallel_operations: int = 0
    total_candidates_generated: int = 0
    total_reviews_performed: int = 0
    approved_fixes: int = 0
    successful_patches: int = 0
    failed_patches: int = 0
    retries_used: int = 0
    
    @property
    def execution_time(self) -> float:
        """Возвращает длительность выполнения (секунды)."""
        return self.end_time - self.start_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует метрики в словарь для дальнейшей сериализации/аналитики."""
        return {
            "execution_time_seconds": round(self.execution_time, 3),
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "timeouts_occurred": self.timeouts_occurred,
            "agents_involved": self.agents_involved,
            "parallel_operations": self.parallel_operations,
            "total_candidates_generated": self.total_candidates_generated,
            "total_reviews_performed": self.total_reviews_performed,
            "approved_fixes": self.approved_fixes,
            "successful_patches": self.successful_patches,
            "failed_patches": self.failed_patches,
            "retries_used": self.retries_used,
            "success_rate": round(self.successful_patches / max(1, self.approved_fixes), 2),
            "review_approval_rate": round(self.approved_fixes / max(1, self.total_candidates_generated), 2),
            "message_efficiency": round(self.messages_received / max(1, self.messages_sent), 2)
        }

@dataclass
class Message:
    """Сообщение для асинхронной коммуникации между агентами."""
    type: str
    content: Any
    cid: str
    attempt: int = 0

class AsyncAgent:
    """Базовый агент с входной очередью и счётчиками сообщений.

    Хранит ссылку на общие метрики и предоставляет send/recv интерфейс
    для обмена сообщениями между агентами.
    """
    
    def __init__(self, name: str, metrics: AsyncApproachMetrics):
        self.name = name
        self.inbox: asyncio.Queue[Tuple["AsyncAgent", Message]] = asyncio.Queue()
        self.log = logging.getLogger(f"Agent:{name}")
        self.metrics = metrics

    async def send(self, recipient: "AsyncAgent", msg: Message):
        """Отправляет сообщение в inbox другого агента и инкрементирует счётчик."""
        self.log.debug("-> %s (%s)", recipient.name, msg.type)
        self.metrics.messages_sent += 1
        await recipient.inbox.put((self, msg))

    async def recv(self, timeout: Optional[float] = None) -> Tuple["AsyncAgent", Message]:
        """Получает сообщение из своей очереди, учитывая таймаут (если задан)."""
        try:
            sender, msg = await asyncio.wait_for(self.inbox.get(), timeout=timeout)
            self.metrics.messages_received += 1
            return sender, msg
        except asyncio.TimeoutError:
            self.metrics.timeouts_occurred += 1
            raise

class Analyst(AsyncAgent):
    """Агент-аналитик: принимает код и отвечает отчётом о багах."""
    
    async def run(self):
        """Основной цикл агента-аналитика."""
        while True:
            try:
                sender, msg = await self.recv()
                if msg.type == "analyze_code":
                    report = llm_find_issues(msg.content)
                    await self.send(sender, Message("bug_report", report, msg.cid))
            except asyncio.CancelledError:
                break

class Fixer(AsyncAgent):
    """Агент-исправитель: по отчёту генерирует кандидатов-исправлений."""
    
    async def run(self):
        """Основной цикл агента-исправителя."""
        while True:
            try:
                sender, msg = await self.recv()
                if msg.type == "bug_report":
                    cands = llm_suggest_fixes(msg.content)
                    self.metrics.total_candidates_generated += len(cands)
                    await self.send(sender, Message("fix_candidates", cands, msg.cid, attempt=msg.attempt))
            except asyncio.CancelledError:
                break

class Controller(AsyncAgent):
    """Агент-контролёр: проводит голосование ревьюеров и утверждает фиксы."""
    
    def __init__(self, name: str, n_reviewers: int, rng: random.Random, metrics: AsyncApproachMetrics):
        super().__init__(name, metrics)
        self.n_reviewers = n_reviewers
        self.rng = rng

    async def run(self):
        """Основной цикл агента-контролёра."""
        while True:
            try:
                sender, msg = await self.recv()
                if msg.type == "fix_candidates":
                    approved = []
                    for c in msg.content:
                        votes = []
                        for _ in range(self.n_reviewers):
                            self._seed_next()
                            votes.append(llm_review_fix(c))
                            self.metrics.total_reviews_performed += 1
                        verdict = "approve" if votes.count("approve") >= (len(votes)//2 + 1) else "request_changes"
                        if verdict == "approve":
                            approved.append(c)
                            self.metrics.approved_fixes += 1
                    await self.send(sender, Message("approved_fixes", approved, msg.cid, attempt=msg.attempt))
            except asyncio.CancelledError:
                break

    def _seed_next(self):
        """Обновляет seed для воспроизводимости вердиктов ревью."""
        s = self.rng.random()
        random.seed(int(s * 1e9) % (2**32 - 1))

class Coordinator(AsyncAgent):
    """Координатор: связывает агентов, оркестрирует попытки и тесты."""
    
    def __init__(self, name: str, analyst: Analyst, fixer: Fixer, controller: Controller, 
                 max_retries: int = 2, step_timeout: float = 5.0, metrics: AsyncApproachMetrics = None):
        super().__init__(name, metrics or AsyncApproachMetrics())
        self.analyst = analyst
        self.fixer = fixer
        self.controller = controller
        self.max_retries = max_retries
        self.step_timeout = step_timeout

    async def run_case(self, code: str, bug_id: int, cid: str) -> Dict[str, Any]:
        """Запускает полный цикл обработки одного кейса с данным correlation id."""
        self.metrics.start_time = time.time()
        
        await self.send(self.analyst, Message("analyze_code", code, cid))
        report = await self._await_type("bug_report", cid)
        if report is None:
            self.metrics.end_time = time.time()
            return {
                "status": "timeout", 
                "approach": "async",
                "cid": cid,
                "metrics": self.metrics.to_dict()
            }

        for attempt in range(self.max_retries + 1):
            if attempt > 0:
                self.metrics.retries_used += 1
                
            await self.send(self.fixer, Message("bug_report", report, cid, attempt=attempt))
            candidates = await self._await_type("fix_candidates", cid)
            
            if candidates:
                await self.send(self.controller, Message("fix_candidates", candidates, cid, attempt=attempt))
                approved = await self._await_type("approved_fixes", cid)
                
                if approved:
                    # пробуем применить каждый одобренный фикс
                    for c in approved:
                        patched = apply_patch(code, c)
                        passed, testlog = run_tests(patched, bug_id)
                        
                        if passed:
                            self.metrics.successful_patches += 1
                            self.metrics.end_time = time.time()
                            return {
                                "status": "success",
                                "approach": "async",
                                "cid": cid,
                                "bug_report": report,
                                "chosen_fix": c,
                                "patched_code": patched,
                                "tests_output": testlog,
                                "metrics": self.metrics.to_dict()
                            }
                        else:
                            self.metrics.failed_patches += 1
        
        self.metrics.end_time = time.time()
        return {
            "status": "failed", 
            "approach": "async",
            "cid": cid, 
            "bug_report": report,
            "metrics": self.metrics.to_dict()
        }

    async def _await_type(self, msg_type: str, cid: str):
        """Ожидает сообщение определённого типа/коррелятора от агентов с таймаутом."""
        try:
            while True:
                sender, msg = await asyncio.wait_for(self.inbox.get(), timeout=self.step_timeout)
                self.metrics.messages_received += 1
                if msg.cid == cid and msg.type == msg_type:
                    if msg.type == "approved_fixes":
                        return msg.content  # список строк
                    return msg.content
                else:
                    # Если сообщение не подходит, возвращаем его обратно в очередь
                    # Но так как у нас нет способа вернуть в начало очереди, просто логируем
                    self.log.debug("Получено неожиданное сообщение: %s (ожидали %s для %s)", msg.type, msg_type, cid)
        except asyncio.TimeoutError:
            self.metrics.timeouts_occurred += 1
            self.log.warning("Таймаут при ожидании %s для %s", msg_type, cid)
            return None

def make_cid(i: int) -> str:
    """Генерация correlation ID для сообщений."""
    return f"cid-{i:04d}"

def create_async_system(seed: int = 42, n_reviewers: int = 5, max_retries: int = 2, step_timeout: float = 5.0):
    """Фабричная функция для создания асинхронной системы."""
    metrics = AsyncApproachMetrics()
    rng = random.Random(seed)
    
    analyst = Analyst("Аналитик", metrics)
    fixer = Fixer("Исправитель", metrics)
    controller = Controller("Контролёр", n_reviewers, rng, metrics)
    coordinator = Coordinator("Координатор", analyst, fixer, controller, max_retries, step_timeout, metrics)
    
    metrics.agents_involved = 4  # analyst, fixer, controller, coordinator
    
    return coordinator, [analyst, fixer, controller], metrics
