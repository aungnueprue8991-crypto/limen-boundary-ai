# Codespaces setup for Limen

## Open Codespace (from browser)

1. Go to: https://github.com/aungnueprue8991-crypto/limen-boundary-ai
2. Click **Code** → **Codespaces** → **Create codespace on main**
3. Wait for the environment to build
4. In the terminal:

```bash
python limen_cli.py status
python limen_cli.py run 10
python real_agent.py
```

## Create Codespace from CLI (on your machine)

Requires [GitHub CLI](https://cli.github.com/) authenticated with `codespace` scope:

```bash
gh auth login
gh codespace create -r aungnueprue8991-crypto/limen-boundary-ai -b main
gh codespace ssh   # optional: SSH into it
```

## Why Grok cannot create Codespaces from here

The connected GitHub integration supports repos, files, PRs, and search, but **not** the Codespaces API (`codespace` scope). Creating a Codespace requires either:

- Browser UI on github.com
- `gh codespace create` on a machine with a PAT that has `codespace` scope
- Direct REST: `POST /repos/{owner}/{repo}/codespaces` with a token that has Codespaces write

## After Codespace is open

```bash
mkdir -p archive
python limen_cli.py status
python limen_cli.py run 20
```
