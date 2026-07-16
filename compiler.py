from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from .models import BuildEntry, Diagnostic, Target
from .references import render_text


RENDERED_SUFFIXES = {".md", ".txt", ".toml", ".json", ".yaml", ".yml", ".sh"}
RESOURCE_SUFFIXES = {".md", ".txt", ".toml", ".json", ".yaml", ".yml", ".py", ".sh"}


class Builder:
    def __init__(
        self,
        root: Path,
        target: Target,
        values: dict[str, dict[str, str]] | None = None,
    ) -> None:
        self.root = root.resolve()
        self.target = target
        self.values = values or {}
        self.diagnostics: list[Diagnostic] = []
        self.entries: list[BuildEntry] = []
        self._staging_root: Path | None = None

    def build(self, output: Path) -> tuple[dict[str, object], list[Diagnostic]]:
        output = output.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = Path(
            tempfile.mkdtemp(prefix=f".{output.name}.", dir=output.parent)
        )
        self._staging_root = temporary
        try:
            resources = self._resource_destinations()
            values = self._resolved_values()
            self._build_instructions(resources, values)
            self._build_skills(resources, values)
            self._build_subagents(resources, values)
            self._build_hooks(resources, values)
            self._build_resources(resources, values)
            self._build_projects(resources, values)
            self._write_feature_reports()

            manifest = {
                "schema_version": 1,
                "target": self.target.identifier,
                "adapter": self.target.adapter,
                "valid": not any(
                    item.level == "error" for item in self.diagnostics
                ),
                "coverage": self.target.coverage(),
                "files": [
                    entry.to_dict()
                    for entry in sorted(self.entries, key=lambda item: item.destination)
                ],
            }
            self._write_raw(
                temporary / "build-manifest.json",
                (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode(),
            )
            if output.exists():
                shutil.rmtree(output)
            os.replace(temporary, output)
            self._staging_root = output
            return manifest, self.diagnostics
        except Exception:
            shutil.rmtree(temporary, ignore_errors=True)
            raise

    def _build_instructions(
        self,
        resources: dict[str, str],
        values: dict[str, dict[str, str]],
    ) -> None:
        feature = self.target.features["instructions"]
        source = self.root / "core" / "instructions.md"
        if feature.status in {"unsupported", "disabled"}:
            return
        if not source.exists():
            self.diagnostics.append(
                Diagnostic(
                    "warning",
                    "missing-canonical-instructions",
                    "No canonical core/instructions.md exists",
                    str(source),
                )
            )
            return
        data = self._render_file(source, resources, values)
        if data is not None and feature.destination:
            self._stage("instructions", source.name, feature.destination, data)

    def _build_skills(
        self,
        resources: dict[str, str],
        values: dict[str, dict[str, str]],
    ) -> None:
        feature = self.target.features["skills"]
        source_root = self.root / "skills"
        if feature.status in {"unsupported", "disabled"} or not source_root.exists():
            return
        for source in _files(source_root):
            relative = source.relative_to(source_root)
            data = self._render_file(source, resources, values)
            if data is not None and feature.destination:
                self._stage(
                    "skills",
                    str(relative),
                    str(Path(feature.destination).expanduser() / relative),
                    data,
                )

    def _build_subagents(
        self,
        resources: dict[str, str],
        values: dict[str, dict[str, str]],
    ) -> None:
        feature = self.target.features["subagents"]
        source_root = self.root / "agents" / "claude-source"
        if feature.status in {"unsupported", "disabled"} or not source_root.exists():
            return
        if feature.status == "emulated":
            self.diagnostics.append(
                Diagnostic(
                    "warning",
                    "subagents-emulated",
                    feature.reason or "Subagents are emulated for this target",
                )
            )
        for source in _files(source_root):
            if source.suffix != ".md":
                continue
            data = self._render_file(source, resources, values)
            if data is None or not feature.destination:
                continue
            if self.target.adapter == "codex":
                name, description, model, body = _parse_claude_agent(
                    data.decode("utf-8")
                )
                rendered = _codex_agent_toml(
                    name,
                    description,
                    body,
                    _mapped_model(model, self.target.models),
                    self.target.models,
                )
                destination = Path(feature.destination).expanduser() / f"{name}.toml"
                self._stage("subagents", f"{name}.toml", str(destination), rendered)
            else:
                destination = Path(feature.destination).expanduser() / source.name
                self._stage("subagents", source.name, str(destination), data)

    def _build_hooks(
        self,
        resources: dict[str, str],
        values: dict[str, dict[str, str]],
    ) -> None:
        feature = self.target.features["hooks"]
        if feature.status in {"unsupported", "disabled"}:
            return
        source_root = self.root / "hooks" / "source"
        if source_root.exists() and feature.destination:
            for source in _files(source_root):
                relative = source.relative_to(source_root)
                data = self._render_file(source, resources, values)
                if data is not None:
                    destination = Path(feature.destination).expanduser() / relative
                    self._stage("hooks", str(relative), str(destination), data)

        selected_settings = self.root / "imports" / "claude" / "settings-selected.json"
        manifest_destination = feature.options.get("manifest")
        if selected_settings.exists() and manifest_destination:
            data = json.loads(selected_settings.read_text(encoding="utf-8"))
            hooks = {"hooks": data.get("hooks", {})}
            hook_root = str(Path(feature.destination or "").expanduser())
            hooks = _replace_strings(hooks, "~/.claude/hooks", hook_root)
            rendered = (json.dumps(hooks, indent=2, sort_keys=True) + "\n").encode()
            self._stage(
                "hooks",
                "hooks.json",
                str(Path(str(manifest_destination)).expanduser()),
                rendered,
            )
            if self.target.adapter == "codex":
                self.diagnostics.append(
                    Diagnostic(
                        "warning",
                        "hook-matcher-review-required",
                        "Claude hook events were preserved, but tool matchers and payload expectations require Codex review",
                        str(selected_settings),
                    )
                )

    def _build_resources(
        self,
        resources: dict[str, str],
        values: dict[str, dict[str, str]],
    ) -> None:
        feature = self.target.features["resources"]
        source_root = self.root / "resources"
        if feature.status in {"unsupported", "disabled"} or not source_root.exists():
            return
        for source in _files(source_root):
            relative = source.relative_to(source_root)
            data = self._render_file(source, resources, values)
            if data is not None and feature.destination:
                destination = Path(feature.destination).expanduser() / relative
                self._stage("resources", str(relative), str(destination), data)

    def _build_projects(
        self,
        resources: dict[str, str],
        values: dict[str, dict[str, str]],
    ) -> None:
        feature = self.target.features["projects"]
        source_root = self.root / "projects"
        if feature.status in {"unsupported", "disabled"} or not source_root.exists():
            return
        for source in _files(source_root):
            relative = source.relative_to(source_root)
            data = self._render_file(source, resources, values)
            if data is not None and feature.destination:
                destination = Path(feature.destination).expanduser() / relative
                self._stage("projects", str(relative), str(destination), data)

    def _write_feature_reports(self) -> None:
        for name, feature in self.target.features.items():
            if feature.status not in {"emulated", "unsupported", "disabled"}:
                continue
            level = "warning" if feature.policy == "warn" else "info"
            self.diagnostics.append(
                Diagnostic(
                    level,
                    f"feature-{feature.status}",
                    feature.reason or f"{name} is {feature.status}",
                    detail={"feature": name, "status": feature.status},
                )
            )

    def _resource_destinations(self) -> dict[str, str]:
        destinations: dict[str, str] = {}
        instructions = self.target.features["instructions"].destination
        if instructions:
            destinations["core/instructions"] = str(
                Path(instructions).expanduser()
            )
        mappings = (
            (self.root / "resources", "resources"),
            (self.root / "skills", "skills"),
            (self.root / "agents" / "claude-source", "subagents"),
            (self.root / "hooks" / "source", "hooks"),
            (self.root / "projects", "projects"),
        )
        for source_root, feature_name in mappings:
            feature = self.target.features[feature_name]
            if not source_root.exists() or not feature.destination:
                continue
            root_prefix = {
                "resources": "",
                "skills": "skills",
                "subagents": "agents",
                "hooks": "hooks",
                "projects": "projects",
            }[feature_name]
            if root_prefix:
                destinations[root_prefix] = str(
                    Path(feature.destination).expanduser()
                )
            if feature_name == "resources":
                for directory in sorted(
                    path for path in source_root.iterdir() if path.is_dir()
                ):
                    destinations[directory.name] = str(
                        Path(feature.destination).expanduser() / directory.name
                    )
            for source in _files(source_root):
                relative = source.relative_to(source_root)
                identifier_prefix = {
                    "resources": "",
                    "skills": "skills/",
                    "subagents": "agents/",
                    "hooks": "hooks/",
                    "projects": "projects/",
                }[feature_name]
                identifier = f"{identifier_prefix}{relative.as_posix()}"
                physical_relative = relative
                if feature_name == "subagents" and self.target.adapter == "codex":
                    physical_relative = relative.with_suffix(".toml")
                destination = str(
                    Path(feature.destination).expanduser() / physical_relative
                )
                destinations[identifier] = destination
                if source.suffix.lower() in RESOURCE_SUFFIXES:
                    destinations[identifier[: -len(source.suffix)]] = destination
        return destinations

    def _resolved_values(self) -> dict[str, dict[str, str]]:
        values = {
            namespace: dict(entries)
            for namespace, entries in self.values.items()
        }
        target_values = values.setdefault("target", {})
        for name, feature in self.target.features.items():
            if feature.destination:
                target_values[f"{name}_dir"] = str(
                    Path(feature.destination).expanduser()
                )
        return values

    def _render_file(
        self,
        source: Path,
        resources: dict[str, str],
        values: dict[str, dict[str, str]],
    ) -> bytes | None:
        data = source.read_bytes()
        if source.suffix.lower() not in RENDERED_SUFFIXES:
            return data
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            self.diagnostics.append(
                Diagnostic("warning", "non-utf8", "Copied without rendering", str(source))
            )
            return data
        rendered, diagnostics = render_text(
            text,
            resources=resources,
            values=values,
            source=str(source),
        )
        self.diagnostics.extend(diagnostics)
        return rendered.encode("utf-8")

    def _stage(
        self,
        feature: str,
        name: str,
        destination: str,
        data: bytes,
    ) -> None:
        assert self._staging_root is not None
        staged = Path("payload") / feature / name
        path = self._staging_root / staged
        self._write_raw(path, data)
        self.entries.append(
            BuildEntry(
                staged=str(staged),
                destination=str(Path(destination).expanduser()),
                sha256=_sha256_bytes(data),
                feature=feature,
            )
        )

    @staticmethod
    def _write_raw(path: Path, data: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


def diff_build(build_root: Path) -> dict[str, list[dict[str, str]]]:
    manifest = json.loads(
        (build_root / "build-manifest.json").read_text(encoding="utf-8")
    )
    result: dict[str, list[dict[str, str]]] = {
        "new": [],
        "changed": [],
        "unchanged": [],
    }
    for entry in manifest["files"]:
        destination = Path(entry["destination"])
        status = "new"
        if destination.exists():
            status = (
                "unchanged"
                if _sha256_file(destination) == entry["sha256"]
                else "changed"
            )
        result[status].append(entry)
    return result


def install_build(build_root: Path, *, apply: bool) -> tuple[dict[str, int], list[Diagnostic]]:
    manifest = json.loads(
        (build_root / "build-manifest.json").read_text(encoding="utf-8")
    )
    diagnostics: list[Diagnostic] = []
    counts = {
        "new": 0,
        "updated": 0,
        "unchanged": 0,
        "conflict": 0,
        "copied": 0,
    }
    pending_copies: list[tuple[Path, Path]] = []
    if not manifest.get("valid", False):
        return counts, [
            Diagnostic(
                "error",
                "invalid-build",
                "Build contains unresolved errors and cannot be installed",
                str(build_root / "build-manifest.json"),
            )
        ]
    state_path = build_root.parent.parent / "state" / f"{manifest['target']}.json"
    previous = {}
    if state_path.exists():
        previous = json.loads(state_path.read_text(encoding="utf-8"))
    previous_hashes = {
        entry["destination"]: entry["sha256"]
        for entry in previous.get("files", [])
    }

    for entry in manifest["files"]:
        source = build_root / entry["staged"]
        destination = Path(entry["destination"])
        if not destination.exists():
            counts["new"] += 1
            pending_copies.append((source, destination))
            continue
        current_hash = _sha256_file(destination)
        if current_hash == entry["sha256"]:
            counts["unchanged"] += 1
            continue
        if previous_hashes.get(entry["destination"]) != current_hash:
            counts["conflict"] += 1
            diagnostics.append(
                Diagnostic(
                    "error",
                    "destination-conflict",
                    "Refusing to overwrite an unowned or manually modified target file",
                    str(destination),
                )
            )
            continue
        counts["updated"] += 1
        pending_copies.append((source, destination))

    if any(item.level == "error" for item in diagnostics):
        return counts, diagnostics

    if apply:
        for source, destination in pending_copies:
            _copy_file(source, destination)
            counts["copied"] += 1
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return counts, diagnostics


def _parse_claude_agent(text: str) -> tuple[str, str, str | None, str]:
    if not text.startswith("---\n"):
        raise ValueError("Claude agent is missing YAML-style frontmatter")
    marker = text.find("\n---\n", 4)
    if marker == -1:
        raise ValueError("Claude agent frontmatter is not terminated")
    frontmatter = text[4:marker]
    body = text[marker + 5 :].lstrip()
    fields: dict[str, str] = {}
    current: str | None = None
    for line in frontmatter.splitlines():
        if line.startswith((" ", "\t")) and current:
            fields[current] += " " + line.strip()
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        current = key.strip()
        fields[current] = value.strip()
    name = fields.get("name")
    description = fields.get("description")
    if not name or not description:
        raise ValueError("Claude agent requires name and description")
    return name, description, fields.get("model"), body


def _mapped_model(
    source_model: str | None,
    target_models: dict[str, str],
) -> str | None:
    if not source_model:
        return target_models.get("default")
    return target_models.get(
        {"haiku": "fast", "opus": "deep", "sonnet": "default"}.get(
            source_model.lower(), "default"
        )
    )


def _codex_agent_toml(
    name: str,
    description: str,
    body: str,
    model: str | None,
    target_models: dict[str, str],
) -> bytes:
    lines = [
        f"name = {json.dumps(name)}",
        f"description = {json.dumps(description)}",
        f"developer_instructions = {json.dumps(body)}",
    ]
    if model:
        lines.append(f"model = {json.dumps(model)}")
    if model == target_models.get("fast"):
        lines.append('model_reasoning_effort = "low"')
    elif model == target_models.get("deep"):
        lines.append('model_reasoning_effort = "high"')
    return ("\n".join(lines) + "\n").encode()


def _replace_strings(value: Any, old: str, new: str) -> Any:
    if isinstance(value, str):
        return value.replace(old, new)
    if isinstance(value, list):
        return [_replace_strings(item, old, new) for item in value]
    if isinstance(value, dict):
        return {
            key: _replace_strings(item, old, new)
            for key, item in value.items()
        }
    return value


def _files(root: Path):
    return sorted(path for path in root.rglob("*") if path.is_file())


def _copy_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        dir=destination.parent,
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        shutil.copy2(source, temporary)
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
