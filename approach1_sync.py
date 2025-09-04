#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Подход 1: Синхронный оркестратор для исправления багов.
Использует линейную обработку с ретраями.
"""

import logging
import random
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List

from llm_utils import llm_find_issues, llm_suggest_fixes, llm_review_fix
from patch_utils import apply_patch, run_tests

log = logging.getLogger("SyncApproach")

@dataclass
class SyncApproachMetrics:
    """Метрики для синхронного подхода."""
    start_time: float = 0.0
    end_time: float = 0.0
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
        """Преобразует метрики в словарь для сериализации/логирования."""
        return {
            "execution_time_seconds": round(self.execution_time, 3),
            "total_candidates_generated": self.total_candidates_generated,
            "total_reviews_performed": self.total_reviews_performed,
            "approved_fixes": self.approved_fixes,
            "successful_patches": self.successful_patches,
            "failed_patches": self.failed_patches,
            "retries_used": self.retries_used,
            "success_rate": round(self.successful_patches / max(1, self.approved_fixes), 2),
            "review_approval_rate": round(self.approved_fixes / max(1, self.total_candidates_generated), 2)
        }

@dataclass
class SyncOrchestrator:
    """Синхронный оркестратор для исправления багов."""
    n_candidates: int = 5
    n_reviewers: int = 5
    max_retries: int = 2
    rng: random.Random = field(default_factory=lambda: random.Random(42))
    
    def run(self, code: str, bug_id: int, correlation_id: str = None) -> Dict[str, Any]:
        """Линейный цикл: найти → сгенерировать N фиксов → ревью (голосование) → тесты → успех/ретрай."""
        metrics = SyncApproachMetrics()
        metrics.start_time = time.time()
        
        log.info("SYNC | Старт обработки кейса %d", bug_id)
        report = llm_find_issues(code)
        log.debug("SYNC | Отчёт: %s", report)

        for attempt in range(self.max_retries + 1):
            if attempt > 0:
                metrics.retries_used += 1
                
            # генерируем кандидатов
            cands = llm_suggest_fixes(report)
            self.rng.shuffle(cands)
            cands = cands[: self.n_candidates]
            metrics.total_candidates_generated += len(cands)
            log.debug("SYNC | Кандидаты (%d): %s", len(cands), cands)

            # ревью каждого кандидата несколькими «ревьюерами»
            approved: List[str] = []
            for c in cands:
                votes = []
                for _ in range(self.n_reviewers):
                    # управляем случайностью через общий seed
                    self._seed_next()
                    votes.append(llm_review_fix(c))
                    metrics.total_reviews_performed += 1
                    
                verdict = "approve" if votes.count("approve") >= (len(votes) // 2 + 1) else "request_changes"
                log.debug("SYNC | Вердикт '%s' для '%s' по голосам %s", verdict, c, votes)
                if verdict == "approve":
                    approved.append(c)
                    metrics.approved_fixes += 1

            # применяем и тестируем одобренные
            for c in approved:
                patched = apply_patch(code, c)
                passed, testlog = run_tests(patched, bug_id)
                log.debug("SYNC | Тесты: %s", "OK" if passed else "FAIL")
                
                if passed:
                    metrics.successful_patches += 1
                    metrics.end_time = time.time()
                    return {
                        "status": "success",
                        "approach": "sync",
                        "bug_report": report,
                        "chosen_fix": c,
                        "patched_code": patched,
                        "tests_output": testlog,
                        "metrics": metrics.to_dict()
                    }
                else:
                    metrics.failed_patches += 1

            log.info("SYNC | Не прошли — ретрай %d/%d", attempt + 1, self.max_retries)

        metrics.end_time = time.time()
        return {
            "status": "failed", 
            "approach": "sync",
            "bug_report": report,
            "metrics": metrics.to_dict()
        }

    def _seed_next(self):
        """Обновляет глобальный seed случайности для воспроизводимых голосований."""
        # Эмуляция «случайности» ревью, завязанной на rng
        s = self.rng.random()
        random.seed(int(s * 1e9) % (2**32 - 1))

def create_sync_orchestrator(seed: int = 42, **kwargs) -> SyncOrchestrator:
    """Фабричная функция для создания синхронного оркестратора."""
    return SyncOrchestrator(rng=random.Random(seed), **kwargs)
