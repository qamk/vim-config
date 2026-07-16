#!/usr/bin/env python3
"""Dispatcher for the /message skill: send an outbound message via a named target.

Universal vocabulary is just ``name`` / ``platform`` / ``secret`` (plus the
message content). Everything else on a target is platform-specific and passed
through verbatim to the adapter, which interprets it. The shared dispatcher core
(config loading, target/secret resolution, adapter invocation) lives in
``_dispatch.py``; this file is the outbound (``op: "send"``) CLI on top of it.

Usage:
  send.py --target <name> --text "..."
  send.py --target <name> --stdin
  send.py --target <name> --file ./shot.png                 # attach one or more files
  send.py --target <name> --text "caption" --file a.png --file b.png
  send.py --target <name> --text "..." --set channel=#other --set thread_ts=123
  send.py --list
  send.py --target <name> --text "..." --dry-run

Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Shared dispatcher core (also re-exported so tests can reach them via ``send``).
from _dispatch import (  # noqa: F401
    ADAPTERS_DIR,
    AdapterError,
    ConfigError,
    SecretError,
    USER_TARGETS,
    apply_overrides,
    encoded_cwd,
    fail as _fail,
    invoke_adapter,
    load_targets,
    note_guidelines,
    print_list,
    project_targets_path,
    resolve_adapter_cmd,
    resolve_secret,
    resolve_target,
    split_target,
)


def build_payload(
    secret: str | None, text: str, blob: dict, files: list[str] | None = None
) -> dict:
    return {
        "secret": secret,
        "op": "send",
        "text": text,
        "files": list(files or []),
        "target": blob,
        "options": {},
    }


def _dry_run(
    core: dict, blob: dict, text: str, files: list[str], cmd: list[str]
) -> None:
    # Resolve the secret only to report status; never print the value.
    try:
        resolve_secret(core.get("secret"))
        secret_status = "resolved ✓ (masked)"
    except SecretError as exc:
        secret_status = f"FAILED: {exc}"
    payload_preview = {"op": "send", "text": text, "files": files, "target": blob}
    print(f"DRY RUN — would send via {cmd[-1]}")
    print(f"  target:  {core.get('name')} (platform: {core.get('platform')})")
    print(f"  secret:  {core.get('secret')}  -> {secret_status}")
    if core.get("guidelines"):
        print(f"  guidelines: {core['guidelines']}")
    print(f"  payload: {json.dumps(payload_preview, ensure_ascii=False)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="send.py", description="Send an outbound message via a named target.")
    parser.add_argument("--target", help="target name from message_targets.md")
    parser.add_argument("--text", help="message content")
    parser.add_argument("--stdin", action="store_true", help="read message content from stdin")
    parser.add_argument("--file", action="append", default=[], metavar="path",
                        help="attach a local file (repeatable); adapter decides how to send it")
    parser.add_argument("--set", action="append", default=[], metavar="key=value",
                        help="override/add a platform-specific field (repeatable)")
    parser.add_argument("--list", action="store_true", help="list resolved targets and exit")
    parser.add_argument("--dry-run", action="store_true", help="show what would be sent without calling the adapter")
    args = parser.parse_args(argv)

    try:
        targets = load_targets(USER_TARGETS, project_targets_path())
    except ConfigError as exc:
        _fail(str(exc))

    if args.list:
        print_list(targets)
        return 0

    if not args.target:
        _fail("--target is required (or use --list)")

    core, blob = resolve_target(targets, args.target, args.set)

    platform = core.get("platform")
    if not platform:
        _fail(f"target {args.target!r} has no 'platform'")

    # Resolve content: text (from --text/--stdin) and/or attached files.
    if args.stdin and args.text is not None:
        _fail("pass either --text or --stdin, not both")
    if args.stdin:
        text = sys.stdin.read()
    elif args.text is not None:
        text = args.text
    else:
        text = ""

    files: list[str] = []
    for raw in args.file:
        path = Path(raw).expanduser()
        if not path.is_file():
            _fail(f"file not found: {raw}")
        files.append(str(path.resolve()))

    if not text and not files:
        _fail("no content: pass --text, --stdin, or --file")

    # Resolve the adapter before secret/send so dry-run can show the path.
    try:
        cmd = resolve_adapter_cmd(ADAPTERS_DIR, platform)
    except AdapterError as exc:
        _fail(str(exc))

    if args.dry_run:
        _dry_run(core, blob, text, files, cmd)
        return 0

    note_guidelines(core)

    try:
        secret = resolve_secret(core.get("secret"))
    except SecretError as exc:
        _fail(str(exc))

    payload = build_payload(secret, text, blob, files)
    try:
        result = invoke_adapter(cmd, payload)
    except AdapterError as exc:
        _fail(str(exc))

    if not result.get("ok"):
        _fail(f"adapter reported failure: {result.get('error', 'unknown error')}")

    bits = [f"sent via {platform}"]
    if result.get("id"):
        bits.append(f"id={result['id']}")
    if result.get("permalink"):
        bits.append(result["permalink"])
    print("  ".join(bits))
    return 0


if __name__ == "__main__":
    sys.exit(main())
