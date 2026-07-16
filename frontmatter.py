"""Shared YAML frontmatter parsing for user-level scripts.

Narrow YAML subset sufficient for artefact frontmatter. No external deps.

Supports:
  - top-level  key: scalar
  - inline     key: [a, b, c]
  - block list key:\n  - item
  - block dict key:\n  - subkey: val\n    subkey2: val2
  - line-end   # comments

Does NOT support: anchors/aliases, multi-line scalars, flow-style dicts,
nested dicts beyond one level inside a list, quoted strings containing
commas. Artefacts requiring those features should be rewritten.

Public API:
  parse_frontmatter_text(text) -> dict
  extract_frontmatter(md_text)  -> (dict | None, body_text)
  read_frontmatter(path: Path) -> dict | None
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


_KV = re.compile(r"^([\w-]+):\s*(.*)$")
_INDENTED_KV = re.compile(r"^\s+([\w-]+):\s*(.*)$")
_TRAILING_COMMENT = re.compile(r"\s+#.*$")


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if not value:
        return None
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(s) for s in inner.split(",")]
    if value in ("true", "True", "yes"):
        return True
    if value in ("false", "False", "no"):
        return False
    if value in ("null", "None", "~", ""):
        return None
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value


def _parse_dict_block(lines: list[str]) -> dict:
    result: dict = {}
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        line_nc = _TRAILING_COMMENT.sub("", line)
        m = _INDENTED_KV.match(line_nc)
        if m:
            result[m.group(1)] = _parse_scalar(m.group(2))
    return result


def _parse_list_block(lines: list[str]) -> list:
    result: list = []
    current: Any = None
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("-"):
            if isinstance(current, dict):
                result.append(current)
                current = None
            remainder = stripped[1:].strip()
            remainder_nc = _TRAILING_COMMENT.sub("", remainder)
            m = _KV.match(remainder_nc)
            if m and not remainder.startswith(('"', "'")):
                current = {m.group(1): _parse_scalar(m.group(2))}
            else:
                result.append(_parse_scalar(remainder))
        else:
            if isinstance(current, dict):
                line_nc = _TRAILING_COMMENT.sub("", line)
                m = _INDENTED_KV.match(line_nc)
                if m:
                    current[m.group(1)] = _parse_scalar(m.group(2))
    if isinstance(current, dict):
        result.append(current)
    return result


def _parse_block(lines: list[str]) -> Any:
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            if stripped.startswith("-"):
                return _parse_list_block(lines)
            return _parse_dict_block(lines)
    return []


def parse_frontmatter_text(text: str) -> dict:
    lines = text.split("\n")
    result: dict = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        if line != line.lstrip():
            i += 1
            continue
        line_nc = _TRAILING_COMMENT.sub("", line)
        m = _KV.match(line_nc)
        if not m:
            i += 1
            continue
        key, value = m.group(1), m.group(2)
        if value.strip():
            result[key] = _parse_scalar(value)
            i += 1
        else:
            block: list[str] = []
            i += 1
            while i < len(lines):
                nl = lines[i]
                if nl.strip() == "" or nl.strip().startswith("#"):
                    i += 1
                    continue
                if nl == nl.lstrip():
                    break
                block.append(nl)
                i += 1
            result[key] = _parse_block(block)
    return result


def extract_frontmatter(md_text: str) -> tuple[dict | None, str]:
    """Split a markdown file into (frontmatter, body). Returns (None, full_text)
    if no frontmatter fence is found."""
    if not md_text.startswith("---\n"):
        return None, md_text
    end = md_text.find("\n---\n", 4)
    trailing_newline = True
    if end == -1:
        end = md_text.find("\n---", 4)
        trailing_newline = False
        if end == -1:
            return None, md_text
    try:
        fm = parse_frontmatter_text(md_text[4:end]) or {}
    except Exception:
        return None, md_text
    body_start = end + (len("\n---\n") if trailing_newline else len("\n---"))
    return fm, md_text[body_start:]


def read_frontmatter(path: Path) -> dict | None:
    """Read a markdown file's frontmatter, or None if absent/invalid."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    fm, _ = extract_frontmatter(text)
    return fm
