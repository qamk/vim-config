from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from .models import Diagnostic, Reference


RESOURCE_RE = re.compile(
    r"(?<!\\)agentic://"
    r"(?P<key>[a-zA-Z0-9](?:[a-zA-Z0-9._/-]*[a-zA-Z0-9])?)"
)
VALUE_RE = re.compile(
    r"(?<!\\)\{\{\s*"
    r"(?P<kind>target|user|project|runtime|secret)\."
    r"(?P<key>[a-zA-Z0-9][a-zA-Z0-9_.-]*)"
    r"\s*\}\}"
)
ESCAPED_RESOURCE_RE = re.compile(r"\\(agentic://)")
ESCAPED_VALUE_RE = re.compile(r"\\(\{\{)")

TEXT_SUFFIXES = {
    ".md",
    ".txt",
    ".toml",
    ".json",
    ".yaml",
    ".yml",
    ".sh",
    ".py",
    ".js",
    ".ts",
    ".html",
}


def find_references(text: str) -> list[Reference]:
    references: list[Reference] = []
    for match in RESOURCE_RE.finditer(text):
        references.append(
            Reference("resource", match.group("key"), match.group(0), *match.span())
        )
    for match in VALUE_RE.finditer(text):
        references.append(
            Reference(
                match.group("kind"),
                match.group("key"),
                match.group(0),
                *match.span(),
            )
        )
    return sorted(references, key=lambda reference: reference.start)


def unescape_literals(text: str) -> str:
    return ESCAPED_RESOURCE_RE.sub(r"\1", ESCAPED_VALUE_RE.sub(r"\1", text))


def render_text(
    text: str,
    *,
    resources: dict[str, str],
    values: dict[str, dict[str, str]],
    source: str,
) -> tuple[str, list[Diagnostic]]:
    diagnostics: list[Diagnostic] = []

    def resource_replacement(match: re.Match[str]) -> str:
        key = match.group("key")
        value = resources.get(key)
        if value is None:
            prefix = _longest_resource_prefix(key, resources)
            if prefix is not None:
                return resources[prefix].rstrip("/") + key[len(prefix) :]
            diagnostics.append(
                Diagnostic(
                    "error",
                    "unresolved-resource",
                    f"Resource is not registered: {key}",
                    source,
                    _line_for_offset(text, match.start()),
                )
            )
            return match.group(0)
        return value

    rendered = RESOURCE_RE.sub(resource_replacement, text)

    def value_replacement(match: re.Match[str]) -> str:
        kind = match.group("kind")
        key = match.group("key")
        value = values.get(kind, {}).get(key)
        if value is not None:
            return value
        level = "info" if kind in {"runtime", "secret"} else "error"
        diagnostics.append(
            Diagnostic(
                level,
                "late-bound-value" if level == "info" else "unresolved-value",
                f"{kind}.{key} was not resolved",
                source,
                _line_for_offset(text, match.start()),
                {"namespace": kind, "key": key},
            )
        )
        return match.group(0)

    rendered = VALUE_RE.sub(value_replacement, rendered)
    return unescape_literals(rendered), diagnostics


def scan_paths(paths: Iterable[Path], known_resources: set[str]) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for path in paths:
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            diagnostics.append(
                Diagnostic("warning", "non-utf8", "Skipped non-UTF-8 file", str(path))
            )
            continue
        for reference in find_references(text):
            if (
                reference.kind == "resource"
                and reference.key not in known_resources
                and _longest_resource_prefix(reference.key, known_resources) is None
            ):
                diagnostics.append(
                    Diagnostic(
                        "error",
                        "unresolved-resource",
                        f"Resource is not registered: {reference.key}",
                        str(path),
                        _line_for_offset(text, reference.start),
                    )
                )
            elif reference.kind in {"user", "project"}:
                diagnostics.append(
                    Diagnostic(
                        "info",
                        "value-requires-binding",
                        f"{reference.kind}.{reference.key} requires a resolver",
                        str(path),
                        _line_for_offset(text, reference.start),
                    )
                )
    return diagnostics


def _line_for_offset(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _longest_resource_prefix(
    key: str,
    resources: dict[str, str] | set[str],
) -> str | None:
    candidates = [
        candidate
        for candidate in resources
        if key.startswith(candidate + "/")
    ]
    return max(candidates, key=len) if candidates else None
