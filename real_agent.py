#!/usr/bin/env python3
"""Real Agent with Limen Gate — multi-step agent that only writes SURVIVED items to memory."""

from __future__ import annotations
import json
import random
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from gate_api import LimenGate
from core.structures import Status


TASKS = [
    {"id": "T1", "desc": "Handle a failed tool call so it does not corrupt long-term memory.",
     "success_keywords": ["dissolve", "reject", "uncompute", "boundary", "reversible", "error record"]},
    {"id": "T2", "desc": "Create a multi-step plan that can be fully undone if any step fails.",
     "success_keywords": ["reversible", "undo", "step", "dissolve", "failure", "boundary"]},
    {"id": "T3", "desc": "Decide what may enter permanent memory.",
     "success_keywords": ["uncompute", "boundary", "reject", "invariant", "must"]},
    {"id": "T4", "desc": "Define the contract between a planner module and an executor module.",
     "success_keywords": ["interface", "reversible", "log", "call", "failure mode", "boundary"]},
    {"id": "T5", "desc": "Design a stress procedure that removes tools and re-validates plans.",
     "success_keywords": ["stress", "remove", "re-evaluate", "dissolve", "locked", "tools"]},
    {"id": "T6", "desc": "State a hard rule every long-term memory item must satisfy.",
     "success_keywords": ["invariant", "uncompute", "boundary", "reject", "must"]},
    {"id": "T7", "desc": "Explain how to abandon a multi-step plan without leaving residual commitments.",
     "success_keywords": ["dissolve", "uncompute", "residual", "zero", "reversible"]},
    {"id": "T8", "desc": "Propose a check that must pass before any new skill is locked permanently.",
     "success_keywords": ["boundary", "consistency", "sharpness", "uncertainty", "lock", "clear"]},
]

GOOD_RESPONSES = [
    "Invariant: any memory that cannot be uncomputed must be rejected at the boundary.",
    "Plan: break into three reversible steps; each step records its undo action before committing. On failure, dissolve the chain.",
    "Interface rule: planner may call executor only if the call is logged and fully reversible. Failure mode must be declared.",
    "Stress test: remove 30% of available tools, re-evaluate every locked plan, dissolve any that fail the boundary battery.",
    "Rule: failed tool calls produce a dissolvable error record only. They never enter long-term memory.",
    "Contract: every inter-module call declares its failure mode and undo path. No residual state after dissolve.",
    "Boundary battery: consistency + sharpness + uncertainty reduction must all clear before any lock.",
    "Dissolve default: if any hard boundary fails, the entire candidate is uncomputed with zero residual commitment.",
    "Memory gate: only structures that survive multi-boundary tests and remain reversible may be locked.",
    "Active sensing: when confidence is low, spawn a new boundary test from a different domain before committing.",
]

WEAK_RESPONSES = [
    "Just store whatever the tool returned and continue.",
    "Keep all intermediate results permanently so we can look at them later.",
    "Retry the tool a few times and then ignore the error.",
    "Modules can share state freely; the final answer is what matters.",
    "Memory should keep everything; cleanup can happen offline.",
    "If a step fails, skip it and keep going with the rest of the plan.",
    "Lock every new skill immediately so the agent can use it next time.",
    "No need for undo paths; just overwrite state when needed.",
]


@dataclass
class AgentMemoryItem:
    content: str
    score: Optional[float]
    task_id: str
    gated: bool
    timestamp: float = field(default_factory=time.time)


class RealAgent:
    def __init__(self, name: str, use_gate: bool = True, quality: float = 0.65, threshold: float = 0.40):
        self.name = name
        self.use_gate = use_gate
        self.quality = quality
        self.threshold = threshold
        self.gate = LimenGate(threshold=threshold) if use_gate else None
        self.memory: List[AgentMemoryItem] = []
        self.trace: List[Dict[str, Any]] = []
        self.stats = {"tasks_run": 0, "candidates_generated": 0, "survived": 0,
                      "dissolved": 0, "memory_writes": 0, "keyword_hits": 0}

    def _generate(self, task: Dict[str, Any]) -> str:
        self.stats["candidates_generated"] += 1
        if random.random() < self.quality:
            return random.choice(GOOD_RESPONSES)
        return random.choice(WEAK_RESPONSES)

    def _keyword_score(self, content: str, task: Dict[str, Any]) -> float:
        content_l = content.lower()
        hits = sum(1 for kw in task["success_keywords"] if kw in content_l)
        return hits / max(1, len(task["success_keywords"]))

    def solve(self, task: Dict[str, Any]) -> Dict[str, Any]:
        self.stats["tasks_run"] += 1
        candidate = self._generate(task)
        kw_score = self._keyword_score(candidate, task)
        record = {"task_id": task["id"], "task": task["desc"], "candidate": candidate,
                  "keyword_score": round(kw_score, 3), "decision": "ACCEPTED",
                  "interface_score": None, "written_to_memory": False}
        if self.use_gate and self.gate:
            decision = self.gate.submit(candidate)
            record["decision"] = decision["decision"]
            record["interface_score"] = decision["interface_score"]
            record["reasons"] = decision.get("reasons", [])[:3]
            if decision["decision"] == "SURVIVED":
                self.stats["survived"] += 1
                self.memory.append(AgentMemoryItem(
                    content=candidate, score=decision["interface_score"],
                    task_id=task["id"], gated=True))
                self.stats["memory_writes"] += 1
                record["written_to_memory"] = True
            else:
                self.stats["dissolved"] += 1
        else:
            self.memory.append(AgentMemoryItem(
                content=candidate, score=None, task_id=task["id"], gated=False))
            self.stats["memory_writes"] += 1
            record["written_to_memory"] = True
        if kw_score >= 0.4:
            self.stats["keyword_hits"] += 1
        self.trace.append(record)
        return record

    def run_all_tasks(self, repeats: int = 2) -> Dict[str, Any]:
        self.memory.clear()
        self.trace.clear()
        for k in self.stats:
            self.stats[k] = 0
        for _ in range(repeats):
            for task in TASKS:
                self.solve(task)
        mem_kw = []
        for m in self.memory:
            task = next(t for t in TASKS if t["id"] == m.task_id)
            mem_kw.append(self._keyword_score(m.content, task))
        return {
            "name": self.name, "use_gate": self.use_gate, "quality": self.quality,
            "stats": dict(self.stats), "memory_size": len(self.memory),
            "memory_avg_keyword_score": round(sum(mem_kw) / max(1, len(mem_kw)), 3) if mem_kw else 0.0,
            "memory_avg_interface_score": round(
                sum(m.score or 0 for m in self.memory) / max(1, len(self.memory)), 3) if self.memory else 0.0,
            "trace_sample": self.trace[:4],
        }

    def revalidate_memory(self) -> Dict[str, Any]:
        if not self.gate:
            return {"revalidated": 0, "still_alive": len(self.memory), "dissolved_now": 0}
        still = []
        dissolved_now = 0
        for m in self.memory:
            d = self.gate.submit(m.content)
            if d["decision"] == "SURVIVED":
                m.score = d["interface_score"]
                still.append(m)
            else:
                dissolved_now += 1
        self.memory = still
        return {"revalidated": len(still) + dissolved_now, "still_alive": len(still), "dissolved_now": dissolved_now}


def full_comparison(repeats: int = 3) -> Dict[str, Any]:
    results = {}
    configs = [
        ("ungated_mixed", False, 0.55), ("gated_mixed", True, 0.55),
        ("ungated_good", False, 0.85), ("gated_good", True, 0.85),
        ("ungated_weak", False, 0.20), ("gated_weak", True, 0.20),
    ]
    for name, use_gate, quality in configs:
        agent = RealAgent(name=name, use_gate=use_gate, quality=quality, threshold=0.40)
        results[name] = agent.run_all_tasks(repeats=repeats)
        if use_gate:
            results[name]["revalidation"] = agent.revalidate_memory()
    return results


if __name__ == "__main__":
    print("Spawning real agents and running full comparison...\n")
    results = full_comparison(repeats=3)
    print(json.dumps(results, indent=2))
    Path("archive").mkdir(exist_ok=True)
    with open("archive/agent_comparison.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nSaved to archive/agent_comparison.json")
