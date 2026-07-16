#!/usr/bin/env python3
"""Lint a report against its per-type YAML schema.

Loads _base.yml + <subtype>.yml from ~/.claude/reports/schemas/,
merges their field definitions, and validates the report's frontmatter.

Supported field types in schema YAML:
  - string
  - numerical
  - date          (ISO YYYY-MM-DD)
  - datetime      (ISO YYYY-MM-DDTHH:MM:SSZ or similar)
  - path          (file path — warns if not found on disk)
  - enum          (exact match against `values` list)
  - list[string]
  - list[enum]    (each item checked against `values`)
  - list[object]  (list of dicts — structural check only)
  - object        (dict with optional `children` sub-schema)

Exit codes (same convention as lint_note.py):
  0 — clean (warnings printed to stderr if any)
  1 — warnings in --strict mode
  2 — errors
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".claude" / "scripts" / "python"))
from frontmatter import extract_frontmatter  # noqa: E402

SCHEMAS_DIR = Path.home() / ".claude" / "reports" / "schemas"

SUBTYPE_TO_SCHEMA: dict[str, str] = {
    "problem-solution": "problem_solution",
    "analysis": "analysis",
    "outline": "outline",
    "feature-release": "feature_release",
    "handoff": "handoff",
    "post-mortem": "post_mortem",
    "roundup": "roundup",
}

_KV_RE = re.compile(r"^([\w-]+):\s*(.*)$")


def _parse_scalar(val: str) -> object:
    """Parse a YAML scalar value (string, bool, int, list)."""
    val = val.strip()
    if not val:
        return None
    if (val.startswith('"') and val.endswith('"')) or (
        val.startswith("'") and val.endswith("'")
    ):
        return val[1:-1]
    if val.startswith("[") and val.endswith("]"):
        inner = val[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(s) for s in inner.split(",")]
    if val in ("true", "True", "yes"):
        return True
    if val in ("false", "False", "no"):
        return False
    if val in ("null", "None", "~"):
        return None
    return val


def _parse_indented_block(lines: list[str], base_indent: int) -> dict:
    """Recursively parse indented key-value blocks into nested dicts.

    Given lines at `base_indent`, groups each key with any deeper-indented
    lines beneath it. If a key has no inline value and has deeper children,
    recurse. Otherwise store the parsed scalar.
    """
    result: dict = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        indent = len(line) - len(line.lstrip())
        if indent != base_indent:
            i += 1
            continue

        m = _KV_RE.match(line.strip())
        if not m:
            i += 1
            continue

        key, val_str = m.group(1), m.group(2).strip()
        i += 1

        # Collect any deeper-indented lines belonging to this key.
        children_lines: list[str] = []
        while i < len(lines):
            next_indent = len(lines[i]) - len(lines[i].lstrip())
            if lines[i].strip() == "" or lines[i].strip().startswith("#"):
                i += 1
                continue
            if next_indent <= base_indent:
                break
            children_lines.append(lines[i])
            i += 1

        if val_str:
            result[key] = _parse_scalar(val_str)
        elif children_lines:
            child_indent = len(children_lines[0]) - len(children_lines[0].lstrip())
            result[key] = _parse_indented_block(children_lines, child_indent)
        else:
            result[key] = None

    return result


def _load_schema_yaml(path: Path) -> dict:
    """Load a schema YAML file and return the field definitions.

    Parses the `fields:` block into a dict of {field_name: {prop: value}}.
    """
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")
    top = _parse_indented_block(lines, 0)
    fields = top.get("fields", {})
    return fields if isinstance(fields, dict) else {}


def load_schema(subtype: str) -> dict[str, dict] | None:
    """Load base + per-type schema, merged. Returns field definitions."""
    schema_name = SUBTYPE_TO_SCHEMA.get(subtype)
    if not schema_name:
        return None

    fields: dict[str, dict] = {}

    base_path = SCHEMAS_DIR / "_base.yml"
    if base_path.exists():
        base = _load_schema_yaml(base_path)
        fields.update(base)

    type_path = SCHEMAS_DIR / f"{schema_name}.yml"
    if type_path.exists():
        type_fields = _load_schema_yaml(type_path)
        fields.update(type_fields)

    return fields


def _validate_field(
    field_name: str,
    value: object,
    spec: dict,
    errors: list[str],
    warnings: list[str],
) -> None:
    field_type = spec.get("type", "string")

    if field_type == "string":
        if not isinstance(value, str):
            errors.append(f"{field_name}: expected string, got {type(value).__name__}")

    elif field_type == "numerical":
        if not isinstance(value, int | float):
            errors.append(f"{field_name}: expected number, got {type(value).__name__}")

    elif field_type == "date":
        if isinstance(value, str):
            try:
                datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                errors.append(f"{field_name}: not ISO YYYY-MM-DD: {value!r}")
        else:
            errors.append(f"{field_name}: expected date string, got {type(value).__name__}")

    elif field_type == "datetime":
        if isinstance(value, str):
            if not re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", value):
                errors.append(f"{field_name}: not ISO datetime: {value!r}")
        else:
            errors.append(f"{field_name}: expected datetime string, got {type(value).__name__}")

    elif field_type == "path":
        if isinstance(value, str):
            p = Path(value).expanduser()
            if not p.exists():
                warnings.append(f"{field_name}: path not found: {value}")
        else:
            errors.append(f"{field_name}: expected path string, got {type(value).__name__}")

    elif field_type == "enum":
        allowed = spec.get("values", [])
        if isinstance(allowed, list):
            str_allowed = [str(v) for v in allowed]
            if str(value) not in str_allowed:
                errors.append(
                    f"{field_name}: {value!r} not in allowed values: {str_allowed}"
                )
        else:
            errors.append(f"{field_name}: schema error — values is not a list")

    elif field_type == "list[string]":
        if not isinstance(value, list):
            errors.append(f"{field_name}: expected list, got {type(value).__name__}")
        else:
            bad = [v for v in value if not isinstance(v, str)]
            if bad:
                sample = ", ".join(repr(v) for v in bad[:3])
                errors.append(f"{field_name}: non-string items in list: {sample}")

    elif field_type == "list[enum]":
        allowed = spec.get("values", [])
        str_allowed = [str(v) for v in allowed] if isinstance(allowed, list) else []
        if not isinstance(value, list):
            errors.append(f"{field_name}: expected list, got {type(value).__name__}")
        else:
            for item in value:
                if str(item) not in str_allowed:
                    errors.append(
                        f"{field_name}: {item!r} not in allowed values: {str_allowed}"
                    )

    elif field_type == "list[object]":
        if not isinstance(value, list):
            errors.append(f"{field_name}: expected list of objects, got {type(value).__name__}")
        else:
            for i, item in enumerate(value):
                if not isinstance(item, dict):
                    errors.append(f"{field_name}[{i}]: expected object, got {type(item).__name__}")

    elif field_type == "object":
        if not isinstance(value, dict):
            errors.append(f"{field_name}: expected object, got {type(value).__name__}")
        else:
            children = spec.get("children", {})
            if isinstance(children, dict):
                for child_name, child_spec in children.items():
                    child_val = value.get(child_name)
                    child_required = child_spec.get("required", False)
                    if child_required and child_val in (None, "", []):
                        errors.append(f"{field_name}.{child_name}: required but missing")
                    elif child_val is not None:
                        _validate_field(
                            f"{field_name}.{child_name}",
                            child_val,
                            child_spec,
                            errors,
                            warnings,
                        )


def lint(path: Path) -> tuple[list[str], list[str]]:
    """Validate a report file against its schema. Returns (errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []

    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return [f"cannot read file: {exc}"], []

    fm, _ = extract_frontmatter(text)
    if fm is None:
        errors.append("no frontmatter fence, or frontmatter unparseable")
        return errors, warnings

    subtype = fm.get("subtype")
    if not subtype:
        errors.append("missing required field: subtype (needed to select schema)")
        return errors, warnings

    schema = load_schema(str(subtype))
    if schema is None:
        warnings.append(f"no schema found for subtype: {subtype!r}")
        return errors, warnings

    for field_name, spec in schema.items():
        required = spec.get("required", False)
        value = fm.get(field_name)

        if required and value in (None, "", []):
            errors.append(f"missing required field: {field_name}")
            continue

        if value is not None and value != "" and value != []:
            _validate_field(field_name, value, spec, errors, warnings)

    unknown = set(fm.keys()) - set(schema.keys())
    if unknown:
        for field in sorted(unknown):
            warnings.append(f"unknown field not in schema: {field!r}")

    return errors, warnings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("path", type=Path, nargs="+", help="Report file(s) to lint")
    ap.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as exit-1 failures",
    )
    args = ap.parse_args()

    total_errors = 0
    total_warnings = 0

    for path in args.path:
        errs, warns = lint(path)
        if errs or warns:
            print(f"{path}:", file=sys.stderr)
        for e in errs:
            print(f"  error: {e}", file=sys.stderr)
        for w in warns:
            print(f"  warning: {w}", file=sys.stderr)
        total_errors += len(errs)
        total_warnings += len(warns)

    if total_errors:
        return 2
    if total_warnings and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
