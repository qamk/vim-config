#!/usr/bin/env python3
"""Build an index of artefact frontmatter under a single directory.

Scans *.md files recursively, parses YAML frontmatter, applies taxonomy
aliases/implies, checks scope against known_components, and writes index.json.

The script is lenient: malformed or schema-violating entries are skipped with
a warning; the script still exits 0 so callers can index partial state during
migration. A separate validator (not this script) is responsible for strict
enforcement and DAG invariants.

Example:
    python build_artefact_index.py \\
        --dir /path/to/working_notes \\
        --output /path/to/working_notes/index.json \\
        --taxonomy /path/to/working_notes/taxonomy.json \\
        --architecture ~/.claude/projects/<project>/architecture.md
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from datetime import date as date_type
from datetime import datetime, timezone
from pathlib import Path

from frontmatter import extract_frontmatter


KNOWN_RELATIONSHIPS = {
    "similar-pattern",
    "context-for",
    "follows-up",
    "extracted-from",
    "supersedes",
}


@dataclass
class Entry:
    path: str
    id: str
    type: str
    date: str
    subtype: str | None = None
    tags: list[str] = field(default_factory=list)
    scope: list[str] = field(default_factory=list)
    tickets: list[str] = field(default_factory=list)
    audience: list[str] = field(default_factory=list)
    impact: str | None = None
    related: list[dict] = field(default_factory=list)
    part: str | None = None
    focus: str | None = None
    scenarios: list[str] = field(default_factory=list)
    environments: list[str] = field(default_factory=list)
    last_verified: str | None = None
    normalised: dict[str, list[str]] = field(default_factory=dict)


def derive_id(path: Path) -> str:
    """Filename stem minus leading YYYY-MM-DD_ prefix if present."""
    stem = path.stem
    if (
        len(stem) > 11
        and stem[4] == "-"
        and stem[7] == "-"
        and stem[10] == "_"
    ):
        try:
            datetime.strptime(stem[:10], "%Y-%m-%d")
            return stem[11:]
        except ValueError:
            pass
    return stem


def parse_frontmatter(md_path: Path) -> dict | None:
    text = md_path.read_text(encoding="utf-8", errors="replace")
    fm, _ = extract_frontmatter(text)
    return fm


def normalise_with_aliases(values: list[str], section: dict) -> list[str]:
    canonical = {}
    for name, meta in section.items():
        canonical[name] = name
        for alias in meta.get("aliases", []) or []:
            canonical[alias] = name
    return [canonical.get(v, v) for v in values]


def expand_implies(values: list[str], section: dict) -> list[str]:
    result = list(values)
    seen = set(result)
    stack = list(values)
    while stack:
        v = stack.pop()
        for implied in section.get(v, {}).get("implies", []) or []:
            if implied not in seen:
                seen.add(implied)
                result.append(implied)
                stack.append(implied)
    return result


def expand_scope_hierarchy(values: list[str]) -> list[str]:
    result = list(values)
    seen = set(result)
    for v in values:
        parts = v.split("/")
        for i in range(1, len(parts)):
            prefix = "/".join(parts[:i])
            if prefix not in seen:
                seen.add(prefix)
                result.append(prefix)
    return result


def load_json(path: Path | None) -> dict:
    if path is None or not path.exists():
        return {}
    with path.open() as f:
        return json.load(f)


def load_known_components(architecture_path: Path | None) -> set[str] | None:
    if architecture_path is None or not architecture_path.exists():
        return None
    text = architecture_path.read_text(encoding="utf-8")
    fm, _ = extract_frontmatter(text)
    if not fm:
        return None
    components = fm.get("known_components")
    return set(components) if components else None


def coerce_date(value: object) -> str | None:
    if isinstance(value, date_type):
        return value.isoformat()
    if isinstance(value, str):
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return value
        except ValueError:
            return None
    return None


def build_entry(
    md_path: Path,
    dir_root: Path,
    fm: dict,
    taxonomy: dict,
    known_components: set[str] | None,
    warnings: list[str],
) -> Entry | None:
    rel_path = str(md_path.relative_to(dir_root))
    enums = taxonomy.get("enums", {})

    artefact_type = fm.get("type")
    if not artefact_type:
        warnings.append(f"{rel_path}: missing `type`")
        return None
    if enums.get("type") and artefact_type not in enums["type"]:
        warnings.append(f"{rel_path}: unknown type `{artefact_type}`")
        return None

    date_str = coerce_date(fm.get("date"))
    if not date_str:
        warnings.append(f"{rel_path}: missing or invalid `date`")
        return None

    subtype_raw = fm.get("subtype")
    subtype = (
        normalise_with_aliases([subtype_raw], taxonomy.get("subtype", {}))[0]
        if subtype_raw
        else None
    )

    tags = list(fm.get("tags") or [])
    scope = list(fm.get("scope") or [])

    tickets_raw = fm.get("tickets") or []
    if not isinstance(tickets_raw, list):
        warnings.append(
            f"{rel_path}: tickets is {type(tickets_raw).__name__}, "
            f"expected list[str] — ignoring"
        )
        tickets: list[str] = []
    else:
        bad_tickets = [t for t in tickets_raw if not isinstance(t, str)]
        if bad_tickets:
            warnings.append(
                f"{rel_path}: tickets contains non-strings {bad_tickets!r} — "
                f"dropping (schema requires list[str] in <source>:<id> form)"
            )
        tickets = [t for t in tickets_raw if isinstance(t, str)]

    audience = list(fm.get("audience") or [])
    impact = fm.get("impact")
    related = list(fm.get("related") or [])

    if impact and enums.get("impact") and impact not in enums["impact"]:
        warnings.append(f"{rel_path}: invalid impact `{impact}`")
    for a in audience:
        if enums.get("audience") and a not in enums["audience"]:
            warnings.append(f"{rel_path}: invalid audience `{a}`")
    for rel in related:
        if isinstance(rel, dict):
            relationship = rel.get("relationship")
            if relationship and relationship not in KNOWN_RELATIONSHIPS:
                warnings.append(
                    f"{rel_path}: unknown relationship `{relationship}`"
                )
    if known_components is not None:
        for s in scope:
            top = s.split("/", 1)[0]
            if top not in known_components:
                warnings.append(
                    f"{rel_path}: scope `{s}` top-level `{top}` not in known_components"
                )

    tags_norm = expand_implies(
        normalise_with_aliases(tags, taxonomy.get("tags", {})),
        taxonomy.get("tags", {}),
    )
    scope_norm = expand_implies(
        expand_scope_hierarchy(
            normalise_with_aliases(scope, taxonomy.get("scope", {}))
        ),
        taxonomy.get("scope", {}),
    )

    part_raw = fm.get("part")
    part_str = part_raw if isinstance(part_raw, str) else None
    focus_raw = fm.get("focus")
    focus_str = focus_raw if isinstance(focus_raw, str) else None

    return Entry(
        path=rel_path,
        id=derive_id(md_path),
        type=artefact_type,
        date=date_str,
        subtype=subtype,
        tags=tags,
        scope=scope,
        tickets=tickets,
        audience=audience,
        impact=impact,
        related=related,
        part=part_str,
        focus=focus_str,
        scenarios=list(fm.get("scenarios") or []),
        environments=list(fm.get("environments") or []),
        last_verified=coerce_date(fm.get("last_verified")),
        normalised={"tags": tags_norm, "scope": scope_norm},
    )


def strip_empty(d: dict) -> dict:
    return {k: v for k, v in d.items() if v not in (None, [], {}, "")}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--taxonomy", type=Path)
    parser.add_argument("--architecture", type=Path)
    args = parser.parse_args()

    if not args.dir.is_dir():
        print(f"error: --dir {args.dir} is not a directory", file=sys.stderr)
        return 2

    taxonomy = load_json(args.taxonomy)
    known_components = load_known_components(args.architecture)

    warnings: list[str] = []
    entries: list[Entry] = []

    for md_path in sorted(args.dir.rglob("*.md")):
        rel = md_path.relative_to(args.dir)
        if any(part.startswith(".") for part in rel.parts):
            continue
        fm = parse_frontmatter(md_path)
        if fm is None:
            warnings.append(f"{rel}: no frontmatter or unparseable")
            continue
        entry = build_entry(
            md_path, args.dir, fm, taxonomy, known_components, warnings
        )
        if entry:
            entries.append(entry)

    index = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dir": str(args.dir),
        "entry_count": len(entries),
        "warning_count": len(warnings),
        "warnings": warnings,
        "entries": [strip_empty(asdict(e)) for e in entries],
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(index, indent=2, default=str), encoding="utf-8"
    )
    print(
        f"Wrote {len(entries)} entries to {args.output} "
        f"({len(warnings)} warning(s))",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
