from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


FEATURES = (
    "instructions",
    "skills",
    "subagents",
    "hooks",
    "rules",
    "plugins",
    "resources",
    "projects",
    "content",
)

FEATURE_STATUSES = {
    "native",
    "transformed",
    "emulated",
    "unsupported",
    "disabled",
}


@dataclass(frozen=True)
class Diagnostic:
    level: str
    code: str
    message: str
    path: str | None = None
    line: int | None = None
    detail: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Reference:
    kind: str
    key: str
    raw: str
    start: int
    end: int


@dataclass
class Feature:
    name: str
    status: str
    destination: str | None = None
    policy: str = "continue"
    reason: str | None = None
    options: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Target:
    identifier: str
    adapter: str
    schema_version: int
    source: Path
    features: dict[str, Feature]
    models: dict[str, str]

    def coverage(self) -> dict[str, list[str]]:
        result = {
            "native": [],
            "transformed": [],
            "emulated": [],
            "unsupported": [],
            "disabled": [],
            "unmapped": [],
        }
        for name in FEATURES:
            feature = self.features.get(name)
            if feature is None:
                result["unmapped"].append(name)
            else:
                result[feature.status].append(name)
        return result


@dataclass(frozen=True)
class BuildEntry:
    staged: str
    destination: str
    sha256: str
    feature: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)

