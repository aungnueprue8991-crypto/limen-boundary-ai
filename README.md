# Limen — Reversible Boundary AI

Multi-level evolutionary system with **interface-first selection** and **dissolution-by-default**.

## Core idea

Structures form weakly → multi-boundary tests → dissolve (default) or survive → assemble into modules/organisms → lock high-strength survivors.

Selection pressure acts at **interfaces** (reversibility, boundary sharpness, uncertainty reduction), not only task performance.

## Quick start

```bash
python limen_cli.py status
python limen_cli.py top 15
python limen_cli.py run 20
python limen_cli.py stress
```

## Gate API (for any outer agent)

```python
from gate_api import LimenGate
gate = LimenGate(threshold=0.40)
result = gate.submit("your plan or memory candidate")
# → decision: SURVIVED | DISSOLVED, interface_score, reasons
```

Only write SURVIVED candidates into long-term memory.

## Real agent test

```bash
python real_agent.py
```

Compares gated vs ungated agents: gate dissolves ~96% of weak irreversible content while keeping reversible-boundary structures.

## Architecture

- `core/structures.py` — Micro / Module / Organism units + Archive
- `core/boundaries.py` — Consistency, reversibility, sharpness, uncertainty, task tests
- `core/engine.py` — Evolutionary loop
- `gate_api.py` — Thin submit → SURVIVED/DISSOLVED API
- `real_agent.py` — Multi-step agent that uses the gate
- `limen_cli.py` — CLI

## Constitution (discovered by evolution)

Top locked principle: *Any memory that cannot be uncomputed must be rejected at the boundary.*

## License

MIT
