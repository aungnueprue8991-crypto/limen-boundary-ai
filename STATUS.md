# Limen Live Status

**Repo:** https://github.com/aungnueprue8991-crypto/limen-boundary-ai

## Last full system run

- Archive size: ~996 structures
- Locked: 546
- Modules: 132 | Organisms: 40
- Gate: GOOD candidates SURVIVED, BAD candidates DISSOLVED
- Real agent (gated): tasks written to memory only after SURVIVED

## Constitution (top locked principle)

> Any memory that cannot be uncomputed must be rejected at the boundary.

## How to run

```bash
python limen_cli.py status
python limen_cli.py run 20
python real_agent.py
```

## Gate for any agent

```python
from gate_api import LimenGate
print(LimenGate(threshold=0.40).submit("candidate text"))
```
