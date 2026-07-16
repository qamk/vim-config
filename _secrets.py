"""Secret-reference resolution for the /message skill.

A target's ``secret`` field is a *reference*, never a raw token. The dispatcher
resolves it to an actual token (or ``None``) via the schemes below. The adapter
receives only the resolved value and never learns where it came from.

Schemes:
  op://<ref>   -> ``op read op://<ref>`` (1Password CLI)
  env:NAME     -> os.environ[NAME]
  file:PATH    -> contents of PATH (``~`` expanded, trailing whitespace stripped)
  none         -> None (explicit "no secret"; the adapter decides if that is usable)

Anything else -- including an omitted/empty reference or a pasted raw token --
raises ``SecretError``. Rejecting unknown values doubles as a guard against
committing a live credential into a targets file.

Stdlib only (no third-party deps).
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


class SecretError(Exception):
    """A secret reference could not be resolved (or is malformed)."""


def resolve_secret(ref: str | None) -> str | None:
    """Resolve a secret reference to a token, or ``None`` for the ``none`` scheme.

    Raises ``SecretError`` for omitted, empty, malformed, or unknown references.
    The error message never contains a (partial) token value.
    """
    if ref is None or not str(ref).strip():
        raise SecretError(
            "no secret reference set; use a scheme: op://, env:, file:, or none"
        )
    ref = str(ref).strip()

    if ref == "none":
        return None
    if ref.startswith("op://"):
        return _resolve_op(ref)
    if ref.startswith("env:"):
        return _resolve_env(ref[len("env:") :])
    if ref.startswith("file:"):
        return _resolve_file(ref[len("file:") :])

    raise SecretError(
        f"unrecognised secret scheme in {ref!r}; use op://, env:, file:, or none "
        "(a raw token is not allowed in config)"
    )


def _resolve_env(name: str) -> str:
    name = name.strip()
    if not name:
        raise SecretError("env: scheme needs a variable name, e.g. env:SLACK_TOKEN")
    try:
        return os.environ[name]
    except KeyError:
        raise SecretError(f"environment variable {name!r} is not set") from None


def _resolve_file(raw_path: str) -> str:
    path = Path(raw_path.strip()).expanduser()
    try:
        return path.read_text().strip()
    except OSError as exc:
        raise SecretError(f"cannot read secret file {path}: {exc}") from None


def _resolve_op(ref: str) -> str:
    try:
        proc = subprocess.run(
            ["op", "read", ref],
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError:
        raise SecretError(
            "1Password CLI `op` not found on PATH; install it or sign in"
        ) from None
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or "").strip() or f"op exited {exc.returncode}"
        raise SecretError(f"`op read {ref}` failed: {detail}") from None
    value = proc.stdout.strip()
    if not value:
        raise SecretError(f"`op read {ref}` returned an empty value")
    return value
