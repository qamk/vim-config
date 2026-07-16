from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .models import Diagnostic


PROJECT_FILES = {
    "architecture.md",
    "message_targets.md",
    "path_variables.md",
    "project_terms.txt",
    "publishing_targets.md",
    "taxonomy.json",
}

EXCLUDED_PARTS = {
    "__pycache__",
    ".DS_Store",
    ".git",
    ".venv",
    "node_modules",
}

SELECTED_SETTINGS_KEYS = {
    "enabledPlugins",
    "extraKnownMarketplaces",
    "hooks",
    "permissions",
    "showThinkingSummaries",
    "skipAutoPermissionPrompt",
    "statusLine",
}

EXECUTABLE_SUFFIXES = {".py", ".sh", ".js", ".ts"}


@dataclass(frozen=True)
class ImportEntry:
    source: Path
    destination: Path
    transform: Callable[[bytes], bytes] | None = None
    category: str = "resource"


def plan_claude_import(source: Path, root: Path) -> tuple[list[ImportEntry], list[Diagnostic]]:
    source = source.expanduser().resolve()
    root = root.expanduser().resolve()
    diagnostics: list[Diagnostic] = []
    entries: list[ImportEntry] = []

    if not source.is_dir():
        return [], [
            Diagnostic("error", "missing-source", "Claude source directory does not exist", str(source))
        ]

    instructions = source / "CLAUDE.md"
    if instructions.is_file():
        entries.append(
            ImportEntry(
                instructions,
                root / "core" / "instructions.md",
                _normalize_markdown_bytes,
                "instructions",
            )
        )

    for path in sorted(source.glob("*.md")):
        if path.name == "CLAUDE.md" or ".bak" in path.name:
            continue
        entries.append(
            ImportEntry(
                path,
                root / "resources" / "references" / path.name,
                _normalize_markdown_bytes,
                "reference",
            )
        )

    directory_mappings = {
        "skills": root / "skills",
        "agents": root / "agents" / "claude-source",
        "hooks": root / "hooks" / "source",
        "scripts": root / "resources" / "scripts",
        "reports": root / "resources" / "reports",
        "schemas": root / "resources" / "schemas",
        "adapters": root / "resources" / "adapters",
    }
    for name, destination in directory_mappings.items():
        directory = source / name
        if not directory.is_dir():
            continue
        for path in _iter_authored_files(directory):
            relative = path.relative_to(directory)
            transform = _normalize_markdown_bytes if path.suffix.lower() == ".md" else None
            entries.append(
                ImportEntry(path, destination / relative, transform, name)
            )
            if path.suffix.lower() in EXECUTABLE_SUFFIXES:
                diagnostics.extend(_hardcoded_path_diagnostics(path))

    projects = source / "projects"
    if projects.is_dir():
        for path in sorted(projects.glob("*/*")):
            if path.is_file() and path.name in PROJECT_FILES:
                project_name = path.parent.name
                transform = (
                    _normalize_markdown_bytes if path.suffix.lower() == ".md" else None
                )
                entries.append(
                    ImportEntry(
                        path,
                        root / "projects" / project_name / path.name,
                        transform,
                        "project",
                    )
                )

    settings = source / "settings.json"
    if settings.is_file():
        try:
            selected = _selected_settings(settings)
        except (OSError, json.JSONDecodeError) as exc:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "invalid-settings",
                    f"Could not parse Claude settings: {exc}",
                    str(settings),
                )
            )
        else:
            generated = root / "imports" / "claude" / "settings-selected.json"
            entries.append(
                ImportEntry(
                    settings,
                    generated,
                    lambda _data, value=selected: (
                        json.dumps(value, indent=2, sort_keys=True) + "\n"
                    ).encode(),
                    "settings",
                )
            )

    if (source / "plugins").exists():
        diagnostics.append(
            Diagnostic(
                "warning",
                "plugins-deferred",
                "Claude plugin caches and marketplaces are not imported; port custom plugins separately",
                str(source / "plugins"),
            )
        )
    diagnostics.append(
        Diagnostic(
            "info",
            "runtime-state-excluded",
            "Sessions, tasks, histories, caches, authentication, backups, telemetry, and daemon state are excluded",
            str(source),
        )
    )
    return entries, diagnostics


def execute_import(
    entries: list[ImportEntry],
    *,
    root: Path,
    source: Path,
    apply: bool,
) -> tuple[dict[str, object], list[Diagnostic]]:
    root = root.expanduser().resolve()
    source = source.expanduser().resolve()
    diagnostics: list[Diagnostic] = []
    previous = _load_previous_manifest(root)
    previous_hashes = {
        item["destination"]: item["sha256"]
        for item in previous.get("files", [])
        if isinstance(item, dict) and "destination" in item and "sha256" in item
    }
    planned_files: list[dict[str, str]] = []
    pending_writes: list[tuple[bytes, Path]] = []
    counts = {"new": 0, "updated": 0, "unchanged": 0, "conflict": 0}

    for entry in entries:
        source_before = _sha256_file(entry.source)
        data = entry.source.read_bytes()
        if entry.transform:
            data = entry.transform(data)
        source_after = _sha256_file(entry.source)
        if source_before != source_after:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "source-mutated",
                    "Source changed while it was being imported",
                    str(entry.source),
                )
            )
            continue

        destination_key = str(entry.destination.relative_to(root))
        rendered_hash = _sha256_bytes(data)
        status = "new"
        if entry.destination.exists():
            current_hash = _sha256_file(entry.destination)
            if current_hash == rendered_hash:
                status = "unchanged"
            elif previous_hashes.get(destination_key) == current_hash:
                status = "updated"
            else:
                status = "conflict"
                diagnostics.append(
                    Diagnostic(
                        "error",
                        "destination-conflict",
                        "Destination differs from both the source and the previous imported copy",
                        str(entry.destination),
                        detail={"source": str(entry.source)},
                    )
                )
        counts[status] += 1
        planned_files.append(
            {
                "source": str(entry.source),
                "destination": destination_key,
                "sha256": rendered_hash,
                "category": entry.category,
                "status": status,
            }
        )
        if status in {"new", "updated"}:
            pending_writes.append((data, entry.destination))

    manifest_files = [
        {
            key: value
            for key, value in item.items()
            if key in {"source", "destination", "sha256", "category"}
        }
        for item in planned_files
        if item["status"] != "conflict"
    ]
    report: dict[str, object] = {
        "adapter": "claude",
        "source": str(source),
        "destination": str(root),
        "apply": apply,
        "counts": counts,
        "files": planned_files,
    }
    if apply and not any(d.level == "error" for d in diagnostics):
        for data, destination in pending_writes:
            _atomic_copy_bytes(data, destination)
        manifest = {
            "schema_version": 1,
            "adapter": "claude",
            "source": str(source),
            "files": manifest_files,
        }
        _atomic_copy_bytes(
            (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode(),
            root / "imports" / "claude" / "manifest.json",
        )
    return report, diagnostics


def _iter_authored_files(directory: Path):
    for path in sorted(directory.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(directory)
        if any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        yield path


def _normalize_markdown_bytes(data: bytes) -> bytes:
    text = data.decode("utf-8")
    text = re.sub(
        r"@?~/\.claude/CLAUDE\.md",
        "agentic://core/instructions",
        text,
    )
    top_level = re.compile(r"@?~/\.claude/(?P<name>[a-zA-Z0-9_-]+\.md)")

    def top_replacement(match: re.Match[str]) -> str:
        return f"agentic://references/{Path(match.group('name')).stem}"

    text = top_level.sub(top_replacement, text)
    prefix_mappings = {
        "reports": "reports",
        "schemas": "schemas",
        "scripts": "scripts",
        "adapters": "adapters",
        "hooks": "hooks",
        "skills": "skills",
        "agents": "agents",
        "projects": "projects",
    }
    for old, new in prefix_mappings.items():
        text = re.sub(
            rf"@?~/\.claude/{re.escape(old)}/",
            f"agentic://{new}/",
            text,
        )
    return text.encode("utf-8")


def _selected_settings(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        key: data[key]
        for key in sorted(SELECTED_SETTINGS_KEYS)
        if key in data
    }


def _hardcoded_path_diagnostics(path: Path) -> list[Diagnostic]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []
    diagnostics: list[Diagnostic] = []
    for line_number, line in enumerate(text.splitlines(), 1):
        if "~/.claude" in line or re.search(r"/Users/[^/]+/\.claude", line):
            diagnostics.append(
                Diagnostic(
                    "warning",
                    "hardcoded-claude-path",
                    "Executable source contains a Claude-specific path and was copied unchanged",
                    str(path),
                    line_number,
                )
            )
    return diagnostics


def _load_previous_manifest(root: Path) -> dict[str, object]:
    path = root / "imports" / "claude" / "manifest.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _atomic_copy_bytes(data: bytes, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        dir=destination.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
