from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from .models import (
    FEATURES,
    FEATURE_STATUSES,
    Diagnostic,
    Feature,
    Target,
)


def load_target(path: Path) -> tuple[Target | None, list[Diagnostic]]:
    diagnostics: list[Diagnostic] = []
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return None, [
            Diagnostic("error", "invalid-target", f"Cannot load target: {exc}", str(path))
        ]

    target_data = data.get("target", {})
    identifier = target_data.get("id")
    adapter = target_data.get("adapter")
    schema_version = target_data.get("schema_version")
    if not identifier or not adapter or not isinstance(schema_version, int):
        diagnostics.append(
            Diagnostic(
                "error",
                "invalid-target",
                "Target requires target.id, target.adapter, and integer target.schema_version",
                str(path),
            )
        )
        return None, diagnostics

    feature_data = data.get("features", {})
    features: dict[str, Feature] = {}
    for name, raw in feature_data.items():
        if name not in FEATURES:
            diagnostics.append(
                Diagnostic(
                    "warning",
                    "unknown-feature",
                    f"Unknown target feature: {name}",
                    str(path),
                )
            )
            continue
        status = raw.get("status")
        if status not in FEATURE_STATUSES:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "invalid-feature-status",
                    f"{name} has invalid status: {status!r}",
                    str(path),
                )
            )
            continue
        known = {"status", "destination", "policy", "reason"}
        features[name] = Feature(
            name=name,
            status=status,
            destination=raw.get("destination"),
            policy=raw.get("policy", _default_policy(status)),
            reason=raw.get("reason"),
            options={key: value for key, value in raw.items() if key not in known},
        )

    target = Target(
        identifier=identifier,
        adapter=adapter,
        schema_version=schema_version,
        source=path,
        features=features,
        models=data.get("models", {}),
    )
    diagnostics.extend(validate_target(target))
    return target, diagnostics


def validate_target(target: Target) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for feature_name in FEATURES:
        feature = target.features.get(feature_name)
        if feature is None:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "unmapped-feature",
                    f"Target does not classify feature: {feature_name}",
                    str(target.source),
                )
            )
            continue
        if feature.status in {"native", "transformed"} and not feature.destination:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "missing-destination",
                    f"{feature_name} is {feature.status} but has no destination",
                    str(target.source),
                )
            )
        if feature.status in {"unsupported", "disabled", "emulated"} and not feature.reason:
            diagnostics.append(
                Diagnostic(
                    "warning",
                    "missing-feature-reason",
                    f"{feature_name} is {feature.status} without a reason",
                    str(target.source),
                )
            )
    return diagnostics


def load_values(path: Path | None) -> dict[str, dict[str, str]]:
    if path is None or not path.exists():
        return {}
    data: dict[str, Any] = tomllib.loads(path.read_text(encoding="utf-8"))
    result: dict[str, dict[str, str]] = {}
    for namespace, values in data.items():
        if isinstance(values, dict):
            result[namespace] = {
                str(key): str(value) for key, value in values.items()
            }
    return result


def _default_policy(status: str) -> str:
    return {
        "native": "continue",
        "transformed": "continue",
        "emulated": "warn",
        "unsupported": "warn",
        "disabled": "skip",
    }[status]

