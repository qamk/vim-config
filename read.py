#!/usr/bin/env python3
"""Reader for the /message skill: read recent messages from a named target.

The inbound counterpart to ``send.py``. It resolves the same named targets and
secrets, then hands the adapter an ``op: "read"`` payload and prints the
messages the adapter returns. A platform can only read where its bot has been
added (Slack: `/invite @bot`, plus the relevant `*:history` read scopes).

Usage:
  read.py --target <name>                       # latest messages in the channel
  read.py --target <name> --limit 50
  read.py --target <name> --set thread_ts=1720000000.001  # read a thread's replies
  read.py --target <name> --json                # raw message JSON instead of text
  read.py --list
  read.py --target <name> --dry-run

Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import sys

from _dispatch import (
    ADAPTERS_DIR,
    AdapterError,
    ConfigError,
    SecretError,
    USER_TARGETS,
    fail as _fail,
    invoke_adapter,
    load_targets,
    note_guidelines,
    print_list,
    project_targets_path,
    resolve_adapter_cmd,
    resolve_secret,
    resolve_target,
)

DEFAULT_LIMIT = 20


def build_payload(secret: str | None, blob: dict, limit: int) -> dict:
    return {
        "secret": secret,
        "op": "read",
        "text": "",
        "files": [],
        "target": blob,
        "options": {"limit": limit},
    }


def _dry_run(core: dict, blob: dict, limit: int, cmd: list[str]) -> None:
    try:
        resolve_secret(core.get("secret"))
        secret_status = "resolved ✓ (masked)"
    except SecretError as exc:
        secret_status = f"FAILED: {exc}"
    payload_preview = {"op": "read", "target": blob, "options": {"limit": limit}}
    print(f"DRY RUN — would read via {cmd[-1]}")
    print(f"  target:  {core.get('name')} (platform: {core.get('platform')})")
    print(f"  secret:  {core.get('secret')}  -> {secret_status}")
    if core.get("guidelines"):
        print(f"  guidelines: {core['guidelines']}")
    print(f"  payload: {json.dumps(payload_preview, ensure_ascii=False)}")


def _print_messages(messages: list[dict]) -> None:
    if not messages:
        print("(no messages)")
        return
    for m in messages:
        who = m.get("user") or m.get("username") or m.get("bot_id") or "?"
        ts = m.get("ts", "")
        text = (m.get("text") or "").replace("\n", "\n    ")
        print(f"[{ts}] {who}: {text}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="read.py", description="Read recent messages from a named target.")
    parser.add_argument("--target", help="target name from message_targets.md")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT,
                        help=f"max messages to fetch (default {DEFAULT_LIMIT})")
    parser.add_argument("--set", action="append", default=[], metavar="key=value",
                        help="override/add a platform-specific field, e.g. thread_ts (repeatable)")
    parser.add_argument("--json", action="store_true", help="print raw message JSON instead of formatted lines")
    parser.add_argument("--list", action="store_true", help="list resolved targets and exit")
    parser.add_argument("--dry-run", action="store_true", help="show what would be read without calling the adapter")
    args = parser.parse_args(argv)

    if args.limit < 1:
        _fail("--limit must be a positive integer")

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

    try:
        cmd = resolve_adapter_cmd(ADAPTERS_DIR, platform)
    except AdapterError as exc:
        _fail(str(exc))

    if args.dry_run:
        _dry_run(core, blob, args.limit, cmd)
        return 0

    note_guidelines(core)

    try:
        secret = resolve_secret(core.get("secret"))
    except SecretError as exc:
        _fail(str(exc))

    payload = build_payload(secret, blob, args.limit)
    try:
        result = invoke_adapter(cmd, payload)
    except AdapterError as exc:
        _fail(str(exc))

    if not result.get("ok"):
        _fail(f"adapter reported failure: {result.get('error', 'unknown error')}")

    messages = result.get("messages") or []
    if args.json:
        print(json.dumps(messages, ensure_ascii=False, indent=2))
    else:
        _print_messages(messages)
    return 0


if __name__ == "__main__":
    sys.exit(main())
