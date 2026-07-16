#!/usr/bin/env python3
"""Shared dispatcher core for the /message skill.

The skill's universal vocabulary is just ``name`` / ``platform`` / ``secret``;
everything else on a target is platform-specific and passed through verbatim to
the adapter, which interprets it. The adapter is any OS-executable file under
``scripts/adapters/<platform>`` that reads a JSON payload on stdin and writes a
JSON result on stdout.

This module holds the pieces both operations share — layered config loading,
target shaping, secret-reference wiring, and adapter resolution/invocation. The
thin CLIs build on top of it:

  * ``send.py`` — outbound (``op: "send"``): post text and/or files.
  * ``read.py`` — inbound  (``op: "read"``): read a channel/thread the bot is in.

Stdlib only. Reads the shared frontmatter parser from
``~/.claude/scripts/python/frontmatter.py``.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ADAPTERS_DIR = SCRIPT_DIR / "adapters"
SHARED_PY = Path.home() / ".claude" / "scripts" / "python"

# Make sibling modules and the shared parser importable.
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(SHARED_PY))

from _secrets import SecretError, resolve_secret  # noqa: E402,F401 (re-exported)

try:
    from frontmatter import extract_frontmatter  # noqa: E402
except ImportError as exc:  # pragma: no cover - environment guard
    print(
        json.dumps(
            {
                "ok": False,
                "error": f"shared frontmatter parser not found at {SHARED_PY}: {exc}",
            }
        ),
        file=sys.stderr,
    )
    sys.exit(2)

CORE_KEYS = ("name", "platform", "secret")
# Agent-facing metadata: surfaced to the model in --list/--dry-run, and NEVER
# forwarded to the adapter. Guidelines describe how the model should compose and
# deliver a message to this target (e.g. "start a new thread per test run"); they
# are soft guidance the model follows unless the user directs otherwise, not
# platform delivery fields.
META_KEYS = ("guidelines",)
EXT_INTERP = {".py": [sys.executable], ".sh": ["bash"], ".js": ["node"]}

USER_TARGETS = Path.home() / ".claude" / "message_targets.md"


class ConfigError(Exception):
    """A targets file is missing or malformed."""


class AdapterError(Exception):
    """No usable adapter for a platform."""


# --------------------------------------------------------------------------- #
# Config loading (layered: user base, then project override)
# --------------------------------------------------------------------------- #
def encoded_cwd() -> str:
    """Encode the cwd the way per-project config dirs are named."""
    return os.getcwd().replace("/", "-")


def project_targets_path() -> Path:
    return Path.home() / ".claude" / "projects" / encoded_cwd() / "message_targets.md"


def _read_targets_file(path: Path) -> list[dict]:
    if not path.exists():
        return []
    fm, _ = extract_frontmatter(path.read_text())
    if not fm:
        return []
    targets = fm.get("targets") or []
    if not isinstance(targets, list):
        raise ConfigError(f"{path}: 'targets' must be a list of entries")
    return targets


def load_targets(user_path: Path, project_path: Path) -> dict[str, dict]:
    """Merge user-level then project-level targets; project wins on name clash."""
    merged: dict[str, dict] = {}
    for path in (user_path, project_path):
        for entry in _read_targets_file(path):
            name = entry.get("name")
            if not name:
                raise ConfigError(f"{path}: a target entry is missing 'name'")
            merged[name] = entry
    return merged


# --------------------------------------------------------------------------- #
# Target shaping
# --------------------------------------------------------------------------- #
def split_target(target: dict) -> tuple[dict, dict]:
    """Split a target into the agent-facing core and the platform-specific blob.

    ``core`` carries the universal fields (name/platform/secret) plus any
    agent-facing metadata (``guidelines``) — everything the model reads but the
    adapter never sees. ``blob`` is the platform pass-through handed to the
    adapter, with the metadata keys stripped out.
    """
    core = {k: target.get(k) for k in CORE_KEYS}
    core.update({k: target[k] for k in META_KEYS if target.get(k) is not None})
    blob = {
        k: v for k, v in target.items() if k not in CORE_KEYS and k not in META_KEYS
    }
    return core, blob


def apply_overrides(blob: dict, sets: list[str] | None) -> dict:
    """Merge ``--set key=value`` overrides into the pass-through blob."""
    out = dict(blob)
    for item in sets or []:
        if "=" not in item:
            raise ValueError(f"--set expects key=value, got {item!r}")
        key, value = item.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"--set expects a non-empty key, got {item!r}")
        if key in CORE_KEYS or key in META_KEYS:
            raise ValueError(
                f"--set cannot override {key!r} "
                f"(name/platform/secret/guidelines); edit the target instead"
            )
        out[key] = value
    return out


# --------------------------------------------------------------------------- #
# Adapter resolution + execution
# --------------------------------------------------------------------------- #
def resolve_adapter_cmd(adapters_dir: Path, platform: str) -> list[str]:
    """Return the argv to run the adapter for ``platform``.

    Prefers an executable file (run directly; shebang/binary decides interpreter).
    Falls back to a known extension map for non-executable .py/.sh/.js scripts.
    """
    candidates: list[Path] = []
    extensionless = adapters_dir / platform
    if extensionless.is_file():
        candidates.append(extensionless)
    candidates += sorted(p for p in adapters_dir.glob(f"{platform}.*") if p.is_file())

    if not candidates:
        raise AdapterError(
            f"no adapter for platform {platform!r}: expected "
            f"{adapters_dir}/{platform} or {adapters_dir}/{platform}.<ext>"
        )

    path = candidates[0]
    if os.access(path, os.X_OK):
        return [str(path)]
    interp = EXT_INTERP.get(path.suffix)
    if interp:
        return interp + [str(path)]
    raise AdapterError(
        f"adapter {path} is not executable and has an unknown type; "
        "`chmod +x` it (with a shebang) or write it as .py/.sh/.js"
    )


def invoke_adapter(cmd: list[str], payload: dict) -> dict:
    """Run the adapter, feed the payload on stdin, parse its JSON result."""
    try:
        proc = subprocess.run(
            cmd, input=json.dumps(payload), capture_output=True, text=True
        )
    except OSError as exc:
        raise AdapterError(f"could not run adapter {cmd[0]}: {exc}") from None

    out = proc.stdout.strip()
    if not out:
        tail = (proc.stderr or "").strip()[-500:]
        raise AdapterError(
            f"adapter {cmd[-1]} exited {proc.returncode} with no output"
            + (f"; stderr: {tail}" if tail else "")
        )
    try:
        result = json.loads(out)
    except json.JSONDecodeError:
        tail = (proc.stderr or "").strip()[-500:]
        raise AdapterError(
            f"adapter {cmd[-1]} returned malformed output: {out[:200]!r}"
            + (f"; stderr: {tail}" if tail else "")
        ) from None

    if not isinstance(result, dict) or "ok" not in result:
        raise AdapterError(f"adapter {cmd[-1]} result missing 'ok': {result!r}")
    return result


# --------------------------------------------------------------------------- #
# Shared CLI helpers
# --------------------------------------------------------------------------- #
def print_list(targets: dict[str, dict]) -> None:
    if not targets:
        print("No targets configured.")
        print(f"  user:    {USER_TARGETS}")
        print(f"  project: {project_targets_path()}")
        return
    width = max(len(n) for n in targets)
    for name, t in targets.items():
        platform = t.get("platform", "?")
        dest = t.get("channel") or t.get("chat") or t.get("to") or ""
        dest = f"  ->  {dest}" if dest else ""
        print(f"  {name.ljust(width)}  [{platform}]{dest}")
        guidelines = t.get("guidelines")
        if guidelines:
            print(f"  {' ' * width}  guidelines: {guidelines}")


def fail(message: str, code: int = 1) -> None:
    print(f"error: {message}", file=sys.stderr)
    sys.exit(code)


def note_guidelines(core: dict) -> None:
    """Echo a target's agent-facing guidelines to stderr on a live op.

    The agent never reads ``message_targets.md`` itself — the dispatcher parses
    it — so a guideline is invisible unless a script prints it. ``--list`` and
    ``--dry-run`` show it, but both are optional; this fires on the always-run
    send/read path so a bare invocation can't silently bypass the guidance.
    Advisory only: written to stderr, never the payload, never stdout (which
    carries the parseable result), and never blocking.
    """
    guidelines = core.get("guidelines")
    if guidelines:
        print(f"guidelines for {core.get('name')}: {guidelines}", file=sys.stderr)


def resolve_target(targets: dict[str, dict], name: str, sets: list[str]) -> tuple[dict, dict]:
    """Look up a target by name and return its (core, override-applied blob).

    Exits via ``fail`` on an unknown target name or a bad ``--set``.
    """
    target = targets.get(name)
    if target is None:
        available = ", ".join(sorted(targets)) or "(none configured)"
        fail(f"no target named {name!r}; available: {available}")
    core, blob = split_target(target)
    try:
        blob = apply_overrides(blob, sets)
    except ValueError as exc:
        fail(str(exc))
    return core, blob
