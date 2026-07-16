from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

from .compiler import Builder, diff_build, install_build
from .importer import execute_import, plan_claude_import
from .models import Diagnostic
from .references import scan_paths
from .targets import load_target, load_values


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    root = Path(
        args.root
        or os.environ.get("AGENTIC_CONFIG_HOME")
        or Path(__file__).resolve().parents[2]
    ).expanduser().resolve()

    try:
        return args.handler(args, root)
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        return 130
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agentic-config",
        description="Compile canonical agent configuration into copy-only targets.",
    )
    parser.add_argument("--root", help="Canonical root (default: script checkout)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    import_parser = subparsers.add_parser("import", help="Import a source configuration")
    import_parser.add_argument("adapter", choices=["claude"])
    import_parser.add_argument("--source", default="~/.claude")
    _add_apply_mode(import_parser)
    _add_format(import_parser)
    import_parser.set_defaults(handler=_import_command)

    validate_parser = subparsers.add_parser("validate", help="Validate canonical configuration")
    _add_format(validate_parser)
    validate_parser.set_defaults(handler=_validate_command)

    build_parser = subparsers.add_parser("build", help="Compile a target into build/")
    build_parser.add_argument("target")
    build_parser.add_argument("--values")
    _add_format(build_parser)
    build_parser.set_defaults(handler=_build_command)

    status_parser = subparsers.add_parser("status", help="Show target feature coverage")
    status_parser.add_argument("target")
    _add_format(status_parser)
    status_parser.set_defaults(handler=_status_command)

    diff_parser = subparsers.add_parser("diff", help="Compare a build with live destinations")
    diff_parser.add_argument("target")
    _add_format(diff_parser)
    diff_parser.set_defaults(handler=_diff_command)

    install_parser = subparsers.add_parser("install", help="Copy a completed build into a target")
    install_parser.add_argument("target")
    _add_apply_mode(install_parser)
    _add_format(install_parser)
    install_parser.set_defaults(handler=_install_command)

    sync_parser = subparsers.add_parser("sync", help="Build and copy a target")
    sync_parser.add_argument("target")
    sync_parser.add_argument("--values")
    _add_apply_mode(sync_parser)
    _add_format(sync_parser)
    sync_parser.set_defaults(handler=_sync_command)

    doctor_parser = subparsers.add_parser("doctor", help="Report portability issues")
    doctor_parser.add_argument("target", nargs="?")
    _add_format(doctor_parser)
    doctor_parser.set_defaults(handler=_doctor_command)
    return parser


def _add_format(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--format", choices=["text", "json"], default="text")


def _add_apply_mode(parser: argparse.ArgumentParser) -> None:
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--dry-run", action="store_false", dest="apply")
    parser.set_defaults(apply=False)


def _import_command(args: argparse.Namespace, root: Path) -> int:
    source = Path(args.source).expanduser()
    entries, diagnostics = plan_claude_import(source, root)
    report, execution_diagnostics = execute_import(
        entries,
        root=root,
        source=source,
        apply=args.apply,
    )
    diagnostics.extend(execution_diagnostics)
    _emit(
        {
            "operation": "import",
            "mode": "apply" if args.apply else "dry-run",
            "counts": report["counts"],
            "report": report,
        },
        diagnostics,
        args.format,
    )
    return _exit_code(diagnostics)


def _validate_command(args: argparse.Namespace, root: Path) -> int:
    diagnostics: list[Diagnostic] = []
    targets: dict[str, Any] = {}
    for path in sorted((root / "targets").glob("*.toml")):
        target, target_diagnostics = load_target(path)
        diagnostics.extend(target_diagnostics)
        if target:
            targets[target.identifier] = target.coverage()

    resources = _canonical_resource_ids(root)
    paths = [
        path
        for source_root in (
            root / "core",
            root / "skills",
            root / "agents",
            root / "hooks",
            root / "resources",
            root / "projects",
        )
        if source_root.exists()
        for path in source_root.rglob("*")
    ]
    diagnostics.extend(scan_paths(paths, resources))
    _emit(
        {
            "operation": "validate",
            "targets": targets,
            "resource_count": len(resources),
            "file_count": sum(path.is_file() for path in paths),
        },
        diagnostics,
        args.format,
    )
    return _exit_code(diagnostics)


def _build_command(args: argparse.Namespace, root: Path) -> int:
    target, diagnostics = _target(root, args.target)
    if target is None or any(item.level == "error" for item in diagnostics):
        _emit({"operation": "build", "target": args.target}, diagnostics, args.format)
        return _exit_code(diagnostics)
    values_path = Path(args.values).expanduser() if args.values else root / "values" / "user.toml"
    values = load_values(values_path if values_path.exists() else None)
    output = root / "build" / target.identifier
    manifest, build_diagnostics = Builder(root, target, values).build(output)
    diagnostics.extend(build_diagnostics)
    _emit(
        {
            "operation": "build",
            "target": target.identifier,
            "output": str(output),
            "coverage": manifest["coverage"],
            "file_count": len(manifest["files"]),
        },
        diagnostics,
        args.format,
    )
    return _exit_code(diagnostics)


def _status_command(args: argparse.Namespace, root: Path) -> int:
    target, diagnostics = _target(root, args.target)
    data: dict[str, Any] = {"operation": "status", "target": args.target}
    if target:
        data["coverage"] = target.coverage()
        data["features"] = {
            name: feature.to_dict() for name, feature in target.features.items()
        }
        build_manifest = root / "build" / target.identifier / "build-manifest.json"
        data["build_exists"] = build_manifest.exists()
        if build_manifest.exists():
            data["build_file_count"] = len(
                json.loads(build_manifest.read_text(encoding="utf-8"))["files"]
            )
    _emit(data, diagnostics, args.format)
    return _exit_code(diagnostics)


def _diff_command(args: argparse.Namespace, root: Path) -> int:
    build = root / "build" / args.target
    diagnostics: list[Diagnostic] = []
    if not (build / "build-manifest.json").exists():
        diagnostics.append(
            Diagnostic(
                "error",
                "missing-build",
                f"Build does not exist; run: agentic-config build {args.target}",
                str(build),
            )
        )
        data: dict[str, Any] = {"operation": "diff", "target": args.target}
    else:
        differences = diff_build(build)
        data = {
            "operation": "diff",
            "target": args.target,
            "counts": {key: len(value) for key, value in differences.items()},
            "files": differences,
        }
    _emit(data, diagnostics, args.format)
    return _exit_code(diagnostics)


def _install_command(args: argparse.Namespace, root: Path) -> int:
    build = root / "build" / args.target
    diagnostics: list[Diagnostic] = []
    if not (build / "build-manifest.json").exists():
        diagnostics.append(
            Diagnostic(
                "error",
                "missing-build",
                f"Build does not exist; run: agentic-config build {args.target}",
                str(build),
            )
        )
        counts = {}
    else:
        counts, install_diagnostics = install_build(build, apply=args.apply)
        diagnostics.extend(install_diagnostics)
    _emit(
        {
            "operation": "install",
            "target": args.target,
            "mode": "apply" if args.apply else "dry-run",
            "counts": counts,
        },
        diagnostics,
        args.format,
    )
    return _exit_code(diagnostics)


def _sync_command(args: argparse.Namespace, root: Path) -> int:
    target, diagnostics = _target(root, args.target)
    counts: dict[str, int] = {}
    output = root / "build" / args.target
    if target is not None and not any(item.level == "error" for item in diagnostics):
        values_path = (
            Path(args.values).expanduser()
            if args.values
            else root / "values" / "user.toml"
        )
        values = load_values(values_path if values_path.exists() else None)
        output = root / "build" / target.identifier
        _, build_diagnostics = Builder(root, target, values).build(output)
        diagnostics.extend(build_diagnostics)
        if not any(item.level == "error" for item in diagnostics):
            counts, install_diagnostics = install_build(output, apply=args.apply)
            diagnostics.extend(install_diagnostics)
    _emit(
        {
            "operation": "sync",
            "target": args.target,
            "mode": "apply" if args.apply else "dry-run",
            "output": str(output),
            "counts": counts,
        },
        diagnostics,
        args.format,
    )
    return _exit_code(diagnostics)


def _doctor_command(args: argparse.Namespace, root: Path) -> int:
    diagnostics: list[Diagnostic] = []
    paths = [
        path
        for source_root in (
            root / "core",
            root / "skills",
            root / "agents",
            root / "hooks",
            root / "resources",
            root / "projects",
        )
        if source_root.exists()
        for path in source_root.rglob("*")
        if path.is_file()
    ]
    legacy_pattern = re.compile(r"(?:~|/Users/[^/]+)/\.claude")
    vendor_pattern = re.compile(
        r"\b(?:CLAUDE\.md|WebFetch|WebSearch|TodoWrite|subagent_type|haiku|opus)\b"
    )
    for path in paths:
        if path.suffix.lower() not in {".md", ".txt", ".py", ".sh", ".js", ".ts"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for line_number, line in enumerate(text.splitlines(), 1):
            if legacy_pattern.search(line):
                diagnostics.append(
                    Diagnostic(
                        "warning",
                        "legacy-claude-path",
                        "Claude-specific filesystem path remains",
                        str(path),
                        line_number,
                    )
                )
            if args.target == "codex" and vendor_pattern.search(line):
                diagnostics.append(
                    Diagnostic(
                        "warning",
                        "target-specific-language",
                        "Claude-specific terminology may require Codex adaptation",
                        str(path),
                        line_number,
                    )
                )
    _emit(
        {
            "operation": "doctor",
            "target": args.target,
            "file_count": len(paths),
        },
        diagnostics,
        args.format,
    )
    return _exit_code(diagnostics)


def _target(root: Path, name: str):
    path = root / "targets" / f"{name}.toml"
    return load_target(path)


def _canonical_resource_ids(root: Path) -> set[str]:
    identifiers: set[str] = {"core/instructions"}
    mappings = (
        (root / "resources", ""),
        (root / "skills", "skills/"),
        (root / "agents" / "claude-source", "agents/"),
        (root / "hooks" / "source", "hooks/"),
        (root / "projects", "projects/"),
    )
    for source_root, prefix in mappings:
        if not source_root.exists():
            continue
        root_identifier = prefix.rstrip("/")
        if root_identifier:
            identifiers.add(root_identifier)
        if source_root == root / "resources":
            identifiers.update(
                path.name for path in source_root.iterdir() if path.is_dir()
            )
        for path in source_root.rglob("*"):
            if not path.is_file():
                continue
            identifier = prefix + path.relative_to(source_root).as_posix()
            identifiers.add(identifier)
            if path.suffix:
                identifiers.add(identifier[: -len(path.suffix)])
    return identifiers


def _emit(data: dict[str, Any], diagnostics: list[Diagnostic], output_format: str) -> None:
    if output_format == "json":
        payload = dict(data)
        payload["diagnostics"] = [item.to_dict() for item in diagnostics]
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    operation = str(data.get("operation", "operation")).upper()
    target = f" {data['target']}" if data.get("target") else ""
    print(f"{operation}{target}")
    for key in ("mode", "output", "resource_count", "file_count", "build_file_count"):
        if key in data:
            print(f"  {key.replace('_', ' ')}: {data[key]}")
    if "counts" in data:
        for key, value in data["counts"].items():
            print(f"  {key}: {value}")
    if "coverage" in data:
        print("  coverage:")
        for status, features in data["coverage"].items():
            print(f"    {status}: {', '.join(features) if features else 'none'}")
    _emit_diagnostics(diagnostics)


def _emit_diagnostics(diagnostics: list[Diagnostic]) -> None:
    for item in diagnostics:
        location = ""
        if item.path:
            location = f" {item.path}"
            if item.line:
                location += f":{item.line}"
        print(
            f"{item.level.upper()} {item.code}:{location} {item.message}",
            file=sys.stderr,
        )


def _exit_code(diagnostics: list[Diagnostic]) -> int:
    error_codes = {item.code for item in diagnostics if item.level == "error"}
    if "unresolved-value" in error_codes:
        return 2
    if error_codes & {"unmapped-feature", "invalid-feature-status", "missing-destination"}:
        return 3
    if "destination-conflict" in error_codes:
        return 4
    return 1 if error_codes else 0
