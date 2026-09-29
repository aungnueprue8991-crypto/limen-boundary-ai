#!/usr/bin/env python3
"""Simple CLI for Limen — inspect, run generations, stress, show top."""
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from core.engine import LimenEngine
from core.structures import Status

def main():
    engine = LimenEngine()
    args = sys.argv[1:]
    if not args or args[0] in ("status", "summary"):
        print(json.dumps(engine.summary(), indent=2))
        return
    if args[0] == "top":
        n = int(args[1]) if len(args) > 1 else 10
        for s in engine.top_structures(n):
            flag = "LOCKED" if s.status == Status.LOCKED else s.status.value
            print(f"[{flag:8}] {s.strength:.3f} {s.level.value:8} | {s.content[:100]}")
        return
    if args[0] == "run":
        n = int(args[1]) if len(args) > 1 else 5
        for _ in range(n):
            r = engine.run_generation(7)
            print(f"Gen {r['generation']}: surv={r['survived']} mod={r['modules_formed']} "
                  f"org={r['organisms_formed']} prom={r['promoted']} locked={r['locked']}")
        print(json.dumps(engine.summary(), indent=2))
        return
    if args[0] == "stress":
        s = engine.stress_cycle()
        print(s)
        return
    print("Usage: limen_cli.py [status|top [N]|run [N]|stress]")

if __name__ == "__main__":
    main()
