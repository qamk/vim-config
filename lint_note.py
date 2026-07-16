#!/usr/bin/env python3
"""Lint a note against the unified artefact frontmatter schema.

Checks the easy-to-break invariants that the /note skill wants caught quickly:
  - frontmatter parses
  - required fields present for declared type
  - no duplicated top-level `##` headings in body
  - task-list items are well-formed (`- [ ]` or `- [x]` only)
  - if the note splits into parts (`part: N of M`), part numbers are consistent
  - date strings are ISO YYYY-MM-DD

Exits 0 with warnings on stderr when non-strict; exits 1 on warnings in --strict
mode; exits 2 on errors regardless of mode.

Intended to be cheap — a single read + regex sweep. No taxonomy or index
traversal.
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".claude" / "scripts" / "python"))
from frontmatter import extract_frontmatter  # noqa: E402


REQUIRED_PER_TYPE = {
    "note": {"type", "date", "subtype"},
    "report": {"type", "date", "subtype", "audience"},
    "playbook": {"type", "date", "subtype", "audience", "impact", "scenarios", "last_verified"},
    "ground-audit": {"type", "date", "subtype", "verifications"},
}

TASK_LINE = re.compile(r"^\s*- \[( |x|X)\] ")
MALFORMED_TASK = re.compile(r"^\s*- \[[^ xX]\] | - \[\] ")
H2_LINE = re.compile(r"^##\s+(.+?)\s*$")
PART_FM_KEY = "part"
LIST_STR_FIELDS = ("tickets", "tags", "scope")


def check_list_of_strings(fm: dict, field_name: str) -> list[str]:
    """Return errors if the field exists and isn't a clean list[str]."""
    errors: list[str] = []
    value = fm.get(field_name)
    if value is None:
        return errors
    if not isinstance(value, list):
        errors.append(
            f"{field_name} must be a list (got {type(value).__name__})"
        )
        return errors
    bad = [v for v in value if not isinstance(v, str)]
    if bad:
        sample = ", ".join(repr(v) for v in bad[:3])
        hint = ""
        if any(isinstance(v, dict) for v in bad):
            hint = (
                " — YAML parses unquoted `key:value` list items as mappings. "
                'Quote each item, e.g. `tickets: ["pylon:339"]` '
                'or `- "pylon:339"`.'
            )
        errors.append(
            f"{field_name} must be list[str]; non-string items: {sample}{hint}"
        )
    return errors


DATE_DIR_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def check_related_dag(fm: dict, path: Path) -> list[str]:
    """Error when any related.path points to a note with date > source date.

    The notes corpus is a DAG: edges point backward in time. If a later note
    extends an earlier one, the edge lives on the later note (e.g. builds-upon,
    supersedes). Same-date edges are allowed (split siblings, breakdowns).
    """
    errors: list[str] = []
    related = fm.get("related") or []
    if not isinstance(related, list):
        return errors
    source_date = fm.get("date")
    if not isinstance(source_date, str):
        return errors

    # Resolve the notes root: parent of the date dir.
    if not path.parent or not DATE_DIR_RE.match(path.parent.name):
        return errors
    notes_root = path.parent.parent

    for rel in related:
        if not isinstance(rel, dict):
            continue
        tgt_rel = rel.get("path")
        if not isinstance(tgt_rel, str):
            continue
        tgt_path = notes_root / tgt_rel
        if not tgt_path.exists():
            continue
        try:
            tgt_text = tgt_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        tgt_fm, _ = extract_frontmatter(tgt_text)
        if not tgt_fm:
            continue
        tgt_date = tgt_fm.get("date")
        if not isinstance(tgt_date, str):
            continue
        if tgt_date > source_date:
            errors.append(
                f"related points forward in time: {tgt_rel} "
                f"(date {tgt_date}) > source date {source_date}. "
                "Invert the edge onto the newer note using a backward "
                "relationship (e.g. builds-upon, supersedes, context-for)."
            )
    return errors


def lint(path: Path) -> tuple[list[str], list[str]]:
    """Return (errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []

    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return [f"cannot read file: {exc}"], []

    fm, body = extract_frontmatter(text)
    if fm is None:
        errors.append("no frontmatter fence, or frontmatter unparseable")
        return errors, warnings

    artefact_type = fm.get("type")
    if not artefact_type:
        errors.append("missing required field: type")
    elif artefact_type in REQUIRED_PER_TYPE:
        for required in REQUIRED_PER_TYPE[artefact_type]:
            if fm.get(required) in (None, "", []):
                errors.append(f"missing required field for type={artefact_type}: {required}")
    else:
        warnings.append(f"unknown type: {artefact_type}")

    date_str = fm.get("date")
    if isinstance(date_str, str):
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            errors.append(f"date is not ISO YYYY-MM-DD: {date_str!r}")

    last_verified = fm.get("last_verified")
    if isinstance(last_verified, str):
        try:
            datetime.strptime(last_verified, "%Y-%m-%d")
        except ValueError:
            errors.append(f"last_verified is not ISO YYYY-MM-DD: {last_verified!r}")

    part = fm.get(PART_FM_KEY)
    if part is not None:
        if not isinstance(part, str) or not re.match(r"^\d+\s+of\s+\d+$", part):
            errors.append(f"part field must be 'N of M' (got {part!r})")
        elif not fm.get("focus"):
            warnings.append("part is set but focus is missing — add a short label describing this part's semantic focus")

    for field in LIST_STR_FIELDS:
        errors.extend(check_list_of_strings(fm, field))

    errors.extend(check_related_dag(fm, path))

    headings_seen: dict[str, int] = {}
    for line in body.splitlines():
        m = H2_LINE.match(line)
        if m:
            key = m.group(1).strip().lower()
            headings_seen[key] = headings_seen.get(key, 0) + 1
    for heading, count in headings_seen.items():
        if count > 1:
            warnings.append(f"duplicate ## heading: '{heading}' appears {count} times")

    for lineno, line in enumerate(body.splitlines(), start=1):
        if MALFORMED_TASK.search(line):
            warnings.append(f"line {lineno}: malformed task list item: {line.strip()!r}")

    return errors, warnings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("path", type=Path, nargs="+", help="Note file(s) to lint")
    ap.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as exit-1 failures",
    )
    args = ap.parse_args()

    total_errors = 0
    total_warnings = 0

    for path in args.path:
        errors, warnings = lint(path)
        if errors or warnings:
            print(f"{path}:", file=sys.stderr)
        for e in errors:
            print(f"  error: {e}", file=sys.stderr)
        for w in warnings:
            print(f"  warning: {w}", file=sys.stderr)
        total_errors += len(errors)
        total_warnings += len(warnings)

    if total_errors:
        return 2
    if total_warnings and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
