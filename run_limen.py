#!/usr/bin/env python3
"""
Limen runner — continuous evolutionary loop with multi-level assembly and locking.
"""

import sys
import json
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.engine import LimenEngine
from core.structures import Status


def print_report(r: dict) -> None:
    print(f"\n=== Gen {r['generation']} === "
          f"gen={r['generated']} surv={r['survived']} "
          f"mod={r['modules_formed']} org={r['organisms_formed']} "
          f"promoted={r['promoted']} diss={r['dissolved']} locked_now={r['locked']}")
    for d in r.get("details", [])[:8]:
        fate = d.get("fate", "?")
        lvl = d.get("level", "")
        total = d.get("total", 0)
        preview = d.get("content_preview", "")[:55]
        print(f"  [{fate:18}] {lvl:8} {total:.3f} | {preview}")


def main(generations: int = 30, stress_every: int = 5):
    engine = LimenEngine(threshold=0.36)
    print("Limen v2 started.")
    print("Initial:", engine.summary())

    for g in range(generations):
        report = engine.run_generation(n_micro=8)
        print_report(report)

        if (g + 1) % stress_every == 0:
            print("--- Stress cycle ---")
            stress = engine.stress_cycle(harshness=0.07)
            print(f"  retested={stress['retested']} new_diss={stress['newly_dissolved']} "
                  f"alive={stress['still_alive']} locked_protected={stress['locked_protected']}")

        time.sleep(0.02)

    print("\n========== FINAL STATE ==========")
    summary = engine.summary()
    print(json.dumps(summary, indent=2))

    print("\nTop structures (locked preferred):")
    for s in engine.top_structures(10):
        flag = "LOCKED" if s.status == Status.LOCKED else s.status.value
        print(f"  [{flag:8}] str={s.strength:.3f} lvl={s.level.value:8} | {s.content[:90]}")

    print(f"\nArchive: {engine.archive_path}")
    print(f"Dissolved log entries: {len(engine.archive.dissolved_log)}")
    return engine


if __name__ == "__main__":
    gens = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    main(generations=gens)
