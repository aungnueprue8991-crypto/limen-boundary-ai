"""
Boundary tests for Limen.
Every structure must survive these before it can lock.
Tests are cheap, deterministic where possible, and multi-domain.
"""

from __future__ import annotations
import re
import random
from typing import Tuple, Dict, Any, List
from .structures import Structure, InterfaceScore, Level


def test_consistency(structure: Structure, context: Dict[str, Any]) -> Tuple[float, str]:
    base = 0.35 + min(0.5, len(structure.content) / 180.0)
    if any(c in structure.content for c in [":", "-", "."]):
        base += 0.1
    noise = random.uniform(-0.08, 0.08)
    score = max(0.0, min(1.0, base + noise))
    reason = f"consistency_proxy={score:.3f}"
    return score, reason


def test_reversibility(structure: Structure, context: Dict[str, Any]) -> Tuple[float, str]:
    parent_penalty = min(0.6, 0.1 * len(structure.parent_ids))
    strength_penalty = min(0.4, structure.strength * 0.3)
    cost = parent_penalty + strength_penalty
    score = 1.0 - cost
    reason = f"rev_cost={cost:.3f}"
    return score, reason


def test_boundary_sharpness(structure: Structure, context: Dict[str, Any]) -> Tuple[float, str]:
    tags = structure.domain_tags
    if not tags:
        text = structure.content.lower()
        inferred = set()
        if any(w in text for w in ["math", "proof", "equation", "number"]):
            inferred.add("math")
        if any(w in text for w in ["code", "function", "python", "algorithm"]):
            inferred.add("code")
        if any(w in text for w in ["memory", "remember", "store", "archive"]):
            inferred.add("memory")
        if any(w in text for w in ["plan", "goal", "step", "action"]):
            inferred.add("planning")
        if any(w in text for w in ["user", "prefer", "value", "ethic"]):
            inferred.add("values")
        tags = inferred
        structure.domain_tags = tags
    n = len(tags)
    if n <= 1:
        score = 0.9
    elif n == 2:
        score = 0.7
    elif n == 3:
        score = 0.45
    else:
        score = 0.2
    reason = f"domains={list(tags)} sharpness={score:.2f}"
    return score, reason


def test_uncertainty_reduction(structure: Structure, context: Dict[str, Any]) -> Tuple[float, str]:
    text = structure.content.lower()
    signals = 0
    if re.search(r"\b(always|never|invariant|must|cannot)\b", text):
        signals += 1
    if re.search(r"\b(if .* then|when .* fails|boundary|limit)\b", text):
        signals += 1
    if re.search(r"\b(dissolve|reject|fail|invalid)\b", text):
        signals += 1
    if "because" in text or "therefore" in text:
        signals += 0.5
    score = min(1.0, signals / 3.0)
    reason = f"uncertainty_signals={signals:.1f}"
    return score, reason


def test_raw_task(structure: Structure, context: Dict[str, Any]) -> Tuple[float, str]:
    text = structure.content
    lower = text.lower()
    score = 0.2
    if len(text) > 30:
        score += 0.15
    if any(c in text for c in [".", ":", "-"]):
        score += 0.1
    if re.search(r"\b(step|first|then|finally|plan)\b", lower):
        score += 0.15
    if re.search(r"\b(test|verify|check|validate|boundary|dissolve|reversible)\b", lower):
        score += 0.25
    if re.search(r"\b(invariant|must|never|always)\b", lower):
        score += 0.15
    score = min(1.0, score)
    reason = f"task_proxy={score:.2f}"
    return score, reason


BOUNDARY_TESTS = {
    "consistency": test_consistency,
    "reversibility": test_reversibility,
    "boundary_sharpness": test_boundary_sharpness,
    "uncertainty_reduction": test_uncertainty_reduction,
    "raw_task": test_raw_task,
}


def evaluate_structure(structure: Structure, context: Dict[str, Any] | None = None) -> InterfaceScore:
    context = context or {}
    results = {}
    scores = {}
    for name, fn in BOUNDARY_TESTS.items():
        score, reason = fn(structure, context)
        results[name] = {"score": score, "reason": reason}
        scores[name] = score
    structure.test_history.append({
        "time": __import__("time").time(),
        "results": results,
    })
    structure.last_tested = __import__("time").time()
    iface = InterfaceScore(
        reversibility_cost=1.0 - scores["reversibility"],
        boundary_sharpness=scores["boundary_sharpness"],
        uncertainty_reduction=scores["uncertainty_reduction"],
        consistency=scores["consistency"],
        raw_task_score=scores["raw_task"],
    )
    structure.interface = iface
    return iface


def survives(structure: Structure, threshold: float = 0.45) -> bool:
    total = structure.interface.total()
    return total >= threshold
