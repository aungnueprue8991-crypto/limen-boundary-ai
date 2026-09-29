"""
Limen Evolutionary Engine v2
Generate → Multi-boundary test → Dissolve or Survive → Form modules → Form organisms
→ Promote strong survivors to LOCKED → Decay → Stress cycles
"""

from __future__ import annotations
import random
import time
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from .structures import Structure, Level, Status, Archive, InterfaceScore
from .boundaries import evaluate_structure, survives, BOUNDARY_TESTS


SEED_TEMPLATES = [
    "Plan: break the problem into three reversible steps that can each be dissolved independently.",
    "Invariant: any memory that cannot be uncomputed must be rejected at the boundary.",
    "Module idea: a consistency checker that re-runs the last action under light perturbation.",
    "Cross-domain: treat failed plans like virus capsids — weak bonds, cheap failure.",
    "Active sensing: when confidence < 0.4, spawn a new boundary test from a different domain.",
    "Decay rule: strength halves every 48 hours unless re-validated against current boundaries.",
    "Interface rule: a module may only call another module if the call is logged and reversible.",
    "Stress test: remove 30% of available tools and re-evaluate every locked plan.",
    "Cumulative advantage: prefer structures that have survived >3 distinct boundary sets.",
    "Self-model: ask 'what would break if this boundary shifted by 20%?' before locking.",
    "Organism rule: an assembly of modules survives only if every interface between them is reversible.",
    "Boundary battery: every candidate must clear consistency + sharpness + uncertainty reduction before lock.",
    "Dissolve default: any structure that fails a single hard boundary is uncomputed with zero residual.",
    "Multi-level gate: micro → module requires shared domain; module → organism requires interface score > 0.55.",
]


def _mutate(content: str) -> str:
    ops = [
        lambda c: c + " [re-validated]",
        lambda c: c.replace("must", "should") if "must" in c else c + " with explicit failure mode.",
        lambda c: "Refined: " + c[:90],
        lambda c: c + " | sharper boundary enforced.",
        lambda c: c + " | tested under resource stress.",
        lambda c: "Strengthened: " + c if not c.startswith("Strengthened") else c,
        lambda c: c.replace("boundary", "strict boundary") if "boundary" in c else c,
    ]
    return random.choice(ops)(content)


def generate_micro(population_size: int = 8, archive: Optional[Archive] = None) -> List[Structure]:
    micros = []
    for _ in range(population_size):
        if archive and archive.structures and random.random() < 0.55:
            candidates = list(archive.structures.values())
            weights = [max(0.05, s.strength) for s in candidates]
            parent = random.choices(candidates, weights=weights, k=1)[0]
            content = _mutate(parent.content)
            s = Structure(
                level=Level.MICRO,
                content=content,
                parent_ids=[parent.id],
                domain_tags=set(parent.domain_tags),
            )
        else:
            content = random.choice(SEED_TEMPLATES)
            if random.random() < 0.35:
                content = _mutate(content)
            s = Structure(level=Level.MICRO, content=content)
        micros.append(s)
    return micros


def try_form_module(survivors: List[Structure], archive: Archive) -> Optional[Structure]:
    if len(survivors) < 2:
        return None
    by_tag: Dict[str, List[Structure]] = {}
    for s in survivors:
        tags = s.domain_tags or {"general"}
        for t in tags:
            by_tag.setdefault(t, []).append(s)
    if not by_tag:
        return None
    best_tag, group = max(by_tag.items(), key=lambda x: len(x[1]))
    if len(group) < 2:
        return None
    members = random.sample(group, min(3, len(group)))
    content = (
        f"Module[{best_tag}]: combines {' + '.join(m.id for m in members)} "
        f"| purpose: enforce {best_tag} boundary; all calls reversible."
    )
    mod = Structure(
        level=Level.MODULE,
        content=content,
        parent_ids=[m.id for m in members],
        domain_tags={best_tag},
    )
    return mod


def try_form_organism(archive: Archive) -> Optional[Structure]:
    modules = [s for s in archive.structures.values()
               if s.level == Level.MODULE and s.status in (Status.SURVIVED, Status.LOCKED)
               and s.strength >= 0.40]
    if len(modules) < 2:
        return None
    members = random.sample(modules, min(4, len(modules)))
    ids = " + ".join(m.id for m in members)
    content = (
        f"Organism: assembly of modules [{ids}] | "
        f"contract: every inter-module call is logged, reversible, and boundary-checked; "
        f"failure of any interface dissolves the dependent micro-structures only."
    )
    org = Structure(
        level=Level.ORGANISM,
        content=content,
        parent_ids=[m.id for m in members],
        domain_tags={"organism", "multi-module"},
    )
    return org


def promote_to_locked(archive: Archive, min_strength: float = 0.52, min_tests: int = 2) -> int:
    count = 0
    for s in archive.structures.values():
        if s.status == Status.SURVIVED and s.strength >= min_strength and len(s.test_history) >= min_tests:
            s.status = Status.LOCKED
            s.decay_rate = 0.01
            count += 1
    return count


class LimenEngine:
    def __init__(self, archive_path: str = "archive/limen_archive.json", threshold: float = 0.36):
        self.archive = Archive()
        self.archive_path = Path(archive_path)
        self.archive_path.parent.mkdir(parents=True, exist_ok=True)
        self.archive.load(str(self.archive_path))
        self.threshold = threshold
        self.generation = 0
        self.log: List[Dict[str, Any]] = []

    def run_generation(self, n_micro: int = 8) -> Dict[str, Any]:
        self.generation += 1
        report: Dict[str, Any] = {
            "generation": self.generation, "generated": 0, "survived": 0, "locked": 0,
            "dissolved": 0, "modules_formed": 0, "organisms_formed": 0, "promoted": 0, "details": [],
        }
        micros = generate_micro(n_micro, self.archive)
        report["generated"] = len(micros)
        survivors: List[Structure] = []
        for s in micros:
            evaluate_structure(s)
            total = s.interface.total()
            detail = {"id": s.id, "level": s.level.value, "total": round(total, 3),
                      "content_preview": s.content[:65] + ("..." if len(s.content) > 65 else "")}
            if survives(s, self.threshold):
                s.status = Status.SURVIVED
                s.strength = total
                survivors.append(s)
                self.archive.add(s)
                report["survived"] += 1
                detail["fate"] = "SURVIVED"
            else:
                s.status = Status.DISSOLVED
                report["dissolved"] += 1
                detail["fate"] = "DISSOLVED"
            report["details"].append(detail)
        mod = try_form_module(survivors, self.archive)
        if mod:
            evaluate_structure(mod)
            if survives(mod, self.threshold + 0.04):
                mod.status = Status.SURVIVED
                mod.strength = mod.interface.total()
                self.archive.add(mod)
                report["modules_formed"] = 1
                report["details"].append({"id": mod.id, "level": "module",
                    "total": round(mod.interface.total(), 3), "content_preview": mod.content[:65],
                    "fate": "MODULE_SURVIVED"})
            else:
                report["details"].append({"id": mod.id, "level": "module",
                    "total": round(mod.interface.total(), 3), "fate": "MODULE_DISSOLVED"})
        if self.generation % 3 == 0 or random.random() < 0.25:
            org = try_form_organism(self.archive)
            if org:
                evaluate_structure(org)
                if survives(org, self.threshold + 0.12):
                    org.status = Status.SURVIVED
                    org.strength = org.interface.total()
                    self.archive.add(org)
                    report["organisms_formed"] = 1
                    report["details"].append({"id": org.id, "level": "organism",
                        "total": round(org.interface.total(), 3), "content_preview": org.content[:65],
                        "fate": "ORGANISM_SURVIVED"})
                else:
                    report["details"].append({"id": org.id, "level": "organism",
                        "total": round(org.interface.total(), 3), "fate": "ORGANISM_DISSOLVED"})
        promoted = promote_to_locked(self.archive, min_strength=0.50, min_tests=2)
        report["promoted"] = promoted
        report["locked"] = sum(1 for s in self.archive.structures.values() if s.status == Status.LOCKED)
        to_dissolve = []
        for s in list(self.archive.structures.values()):
            if s.status != Status.LOCKED:
                s.decay()
                if s.strength < 0.07:
                    to_dissolve.append(s.id)
        for sid in to_dissolve:
            self.archive.dissolve(sid, reason="decay")
            report["dissolved"] += 1
        self.archive.save(str(self.archive_path))
        self.log.append(report)
        return report

    def stress_cycle(self, harshness: float = 0.08) -> Dict[str, Any]:
        report = {"retested": 0, "newly_dissolved": 0, "still_alive": 0, "locked_protected": 0}
        harsh = self.threshold + harshness
        for s in list(self.archive.structures.values()):
            if s.status == Status.LOCKED:
                report["locked_protected"] += 1
                evaluate_structure(s)
                s.strength = max(s.strength, s.interface.total() * 0.95)
                continue
            evaluate_structure(s)
            report["retested"] += 1
            if not survives(s, harsh):
                self.archive.dissolve(s.id, reason="stress_cycle")
                report["newly_dissolved"] += 1
            else:
                s.strength = s.interface.total()
                report["still_alive"] += 1
        self.archive.save(str(self.archive_path))
        return report

    def summary(self) -> Dict[str, Any]:
        by_level: Dict[str, int] = {}
        by_status: Dict[str, int] = {}
        for s in self.archive.structures.values():
            by_level[s.level.value] = by_level.get(s.level.value, 0) + 1
            by_status[s.status.value] = by_status.get(s.status.value, 0) + 1
        return {"generation": self.generation, "archive_size": len(self.archive.structures),
                "by_level": by_level, "by_status": by_status,
                "dissolved_total": len(self.archive.dissolved_log)}

    def top_structures(self, n: int = 8) -> List[Structure]:
        return sorted(
            self.archive.structures.values(),
            key=lambda s: (s.status == Status.LOCKED, s.strength),
            reverse=True,
        )[:n]
