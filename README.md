# agentic://scripts/python/

Home for **shared** Python utilities — modules imported by multiple skills, or scripts invoked by multiple callers.

## What lives here vs inside a skill

- **Here**: genuinely shared code. Example: `frontmatter.py` is imported by multiple skill-local scripts; `build_artefact_index.py` is invoked by more than one skill.
- **Inside a skill** (`agentic://skills/<name>/`): scripts whose only caller is that skill. Colocating keeps the skill self-contained and makes removal painless.

Skill-local scripts that import from shared modules do so via a one-line `sys.path` shim:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path.home() / ".claude" / "scripts" / "python"))
from frontmatter import extract_frontmatter  # noqa: E402
```

## Convention

- **Zero-dep scripts**: run directly with system `python3`.
- **Scripts with external deps**: share a single venv at `agentic://scripts/python/.venv/` and a pinned `requirements.txt` in this directory. Invoke via `agentic://scripts/python/.venv/bin/python <script>` or source the venv first.
- Keep scripts project-agnostic — callers pass paths/config via CLI args.
- One responsibility per script. If it grows, split.

## Setup (once, when a dep is first needed)

```sh
cd agentic://scripts/python
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Re-run `pip install -r requirements.txt` after editing `requirements.txt`.

## Current contents

- `frontmatter.py` — shared YAML-subset parser for artefact frontmatter. Imported by skill-local scripts.
- `build_artefact_index.py` — scans a single artefact directory, parses frontmatter, applies taxonomy, writes `index.json`. Called by `/lookup`'s query script and (future) by other skills. Zero deps.
