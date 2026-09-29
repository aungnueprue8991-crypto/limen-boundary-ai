"""
Limen Core Structures
Micro-structures, Modules, Organisms, and Interface metrics.
Default fate of every structure is dissolution.
"""

from __future__ import annotations
import uuid
import time
import json
import hashlib
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Set
from enum import Enum


class Level(Enum):
    MICRO = "micro"
    MODULE = "module"
    ORGANISM = "organism"
    ECOLOGY = "ecology"


class Status(Enum):
    WEAK = "weak"
    TESTING = "testing"
    SURVIVED = "survived"
    LOCKED = "locked"
    DISSOLVED = "dissolved"


@dataclass
class InterfaceScore:
    """The decisive fitness: quality of the boundary this structure creates."""
    reversibility_cost: float = 1.0
    boundary_sharpness: float = 0.0
    uncertainty_reduction: float = 0.0
    consistency: float = 0.0
    raw_task_score: float = 0.0

    def total(self, weights: Optional[Dict[str, float]] = None) -> float:
        w = weights or {
            "reversibility_cost": -0.3,
            "boundary_sharpness": 0.35,
            "uncertainty_reduction": 0.25,
            "consistency": 0.25,
            "raw_task_score": 0.15,
        }
        rev = 1.0 - self.reversibility_cost
        return (
            w["reversibility_cost"] * rev +
            w["boundary_sharpness"] * self.boundary_sharpness +
            w["uncertainty_reduction"] * self.uncertainty_reduction +
            w["consistency"] * self.consistency +
            w["raw_task_score"] * self.raw_task_score
        )


@dataclass
class Structure:
    """Universal unit that can exist at any level."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    level: Level = Level.MICRO
    content: str = ""
    parent_ids: List[str] = field(default_factory=list)
    child_ids: List[str] = field(default_factory=list)
    status: Status = Status.WEAK
    interface: InterfaceScore = field(default_factory=InterfaceScore)
    birth_time: float = field(default_factory=time.time)
    last_tested: float = 0.0
    test_history: List[Dict[str, Any]] = field(default_factory=list)
    strength: float = 0.0
    decay_rate: float = 0.05
    domain_tags: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def age(self) -> float:
        return time.time() - self.birth_time

    def decay(self) -> None:
        self.strength = max(0.0, self.strength * (1.0 - self.decay_rate))

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["level"] = self.level.value
        d["status"] = self.status.value
        d["domain_tags"] = list(self.domain_tags)
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Structure":
        d = d.copy()
        d["level"] = Level(d["level"])
        d["status"] = Status(d["status"])
        d["domain_tags"] = set(d.get("domain_tags", []))
        iface = d.pop("interface", {})
        obj = cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})
        obj.interface = InterfaceScore(**iface)
        return obj

    def content_hash(self) -> str:
        return hashlib.sha256(self.content.encode()).hexdigest()[:12]


@dataclass
class BoundaryTest:
    name: str
    description: str
    weight: float = 1.0


@dataclass
class Archive:
    structures: Dict[str, Structure] = field(default_factory=dict)
    dissolved_log: List[str] = field(default_factory=list)

    def add(self, s: Structure) -> None:
        self.structures[s.id] = s

    def dissolve(self, sid: str, reason: str = "") -> None:
        if sid in self.structures:
            s = self.structures.pop(sid)
            s.status = Status.DISSOLVED
            self.dissolved_log.append(f"{sid}:{reason}:{time.time()}")

    def get_by_level(self, level: Level) -> List[Structure]:
        return [s for s in self.structures.values() if s.level == level]

    def save(self, path: str) -> None:
        data = {
            "structures": {k: v.to_dict() for k, v in self.structures.items()},
            "dissolved_log": self.dissolved_log[-500:],
        }
        import time as _t
        import os
        tmp = path + ".tmp"
        for attempt in range(5):
            try:
                with open(tmp, "w") as f:
                    json.dump(data, f, indent=2)
                os.replace(tmp, path)
                return
            except OSError:
                _t.sleep(0.2 * (attempt + 1))
        try:
            alt = path + f".bak_{int(_t.time())}"
            with open(alt, "w") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def load(self, path: str) -> None:
        try:
            with open(path) as f:
                data = json.load(f)
            self.structures = {
                k: Structure.from_dict(v) for k, v in data.get("structures", {}).items()
            }
            self.dissolved_log = data.get("dissolved_log", [])
        except FileNotFoundError:
            pass
