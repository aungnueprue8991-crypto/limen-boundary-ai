"""
Limen Gate API
Thin interface: submit a candidate → get SURVIVED / DISSOLVED + score + reasons.
Any outer agent can call this before committing to memory or skills.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from core.structures import Structure, Level, Status
from core.boundaries import evaluate_structure, survives, BOUNDARY_TESTS
from core.engine import LimenEngine


class LimenGate:
    def __init__(
        self,
        archive_path: str = "archive/limen_archive.json",
        threshold: float = 0.36,
        constitution_path: str = "archive/constitution.json",
    ):
        self.engine = LimenEngine(archive_path=archive_path, threshold=threshold)
        self.threshold = threshold
        self.constitution: List[Dict[str, Any]] = []
        try:
            with open(constitution_path) as f:
                self.constitution = json.load(f)
        except FileNotFoundError:
            pass

    def submit(
        self,
        content: str,
        level: str = "micro",
        domain_tags: Optional[List[str]] = None,
        force_evaluate: bool = True,
    ) -> Dict[str, Any]:
        """
        Submit a candidate structure.
        Returns a decision dict that any outer agent can act on.
        """
        try:
            lvl = Level(level)
        except ValueError:
            lvl = Level.MICRO

        s = Structure(
            level=lvl,
            content=content,
            domain_tags=set(domain_tags or []),
        )
        evaluate_structure(s)
        total = s.interface.total()
        passed = survives(s, self.threshold)

        decision = "SURVIVED" if passed else "DISSOLVED"
        if passed:
            s.status = Status.SURVIVED
            s.strength = total
            self.engine.archive.add(s)
            self.engine.archive.save(str(self.engine.archive_path))

        reasons = []
        if s.test_history:
            last = s.test_history[-1].get("results", {})
            for name, info in last.items():
                reasons.append(f"{name}: {info.get('reason', '')} (score={info.get('score', 0):.2f})")

        constitution_hits = []
        content_lower = content.lower()
        for c in self.constitution[:10]:
            key_words = set(c["content"].lower().split()) & set(content_lower.split())
            if len(key_words) >= 3:
                constitution_hits.append(c["rank"])

        return {
            "decision": decision,
            "id": s.id,
            "interface_score": round(total, 4),
            "threshold": self.threshold,
            "level": lvl.value,
            "reasons": reasons,
            "constitution_alignment": constitution_hits,
            "interface": {
                "reversibility_cost": round(s.interface.reversibility_cost, 3),
                "boundary_sharpness": round(s.interface.boundary_sharpness, 3),
                "uncertainty_reduction": round(s.interface.uncertainty_reduction, 3),
                "consistency": round(s.interface.consistency, 3),
                "raw_task_score": round(s.interface.raw_task_score, 3),
            },
            "content_preview": content[:120],
        }

    def get_constitution(self, n: int = 20) -> List[Dict[str, Any]]:
        return self.constitution[:n]

    def archive_summary(self) -> Dict[str, Any]:
        return self.engine.summary()


def gate_candidate(content: str, **kwargs) -> Dict[str, Any]:
    gate = LimenGate()
    return gate.submit(content, **kwargs)
