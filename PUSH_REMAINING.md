# Remaining source + Codespaces

## Already on GitHub

- README.md, STATUS.md, CODESPACES.md
- core/__init__.py
- limen_cli.py, run_limen.py, gate_api.py
- .devcontainer/devcontainer.json, requirements.txt

## Still in the Grok sandbox (full working system)

- core/structures.py
- core/boundaries.py
- core/engine.py
- real_agent.py
- archive/ (live evolutionary state)

The full system runs in the sandbox. To get the remaining modules into the repo, either:

1. Clone the repo, copy those files from a local export, and push, or
2. Ask Grok to continue uploading file-by-file via the GitHub API.

## Open a Codespace (you do this in the browser)

1. https://github.com/aungnueprue8991-crypto/limen-boundary-ai
2. **Code** → **Codespaces** → **Create codespace on main**
3. Devcontainer uses Python 3.12

## Create Codespace from your machine (CLI)

```bash
gh auth login   # need codespace scope
gh codespace create -r aungnueprue8991-crypto/limen-boundary-ai -b main
```

Grok cannot call the Codespaces API from this connection (no `codespace` scope tool).
