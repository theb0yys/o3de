#!/usr/bin/env python3
#
# Copyright (c) Contributors to the Open 3D Engine Project.
# For complete copyright and license terms please see the LICENSE at the root of this distribution.
#
# SPDX-License-Identifier: Apache-2.0 OR MIT
#
"""Shared deterministic Actor/Troop population-fixture contract helpers."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

FIXTURE_SCHEMA_VERSION = 1
FIXTURE_ID = "preview.population-authoring-0"
MANIFEST_NAME = "population-preview-fixture.manifest.json"

WORKSPACE_PATH = "preview-population.tgworkspace.json"
PACK_PATH = "Packs/preview.population.tgpack.json"
SOURCE_INPUT_PATH = "Input/preview-population-source.json"
SOURCE_DOCUMENT_PATH = "Sources/preview.population.source/source.tgsource.json"
EVIDENCE_DOCUMENT_PATH = (
    "Sources/preview.population.source/evidence.tgevidence.json"
)
CATALOG_PATH = "Catalog/catalog.tgcatalog.json"
EXPECTED_FILE_PATHS = (
    WORKSPACE_PATH,
    PACK_PATH,
    SOURCE_INPUT_PATH,
    SOURCE_DOCUMENT_PATH,
    EVIDENCE_DOCUMENT_PATH,
    CATALOG_PATH,
)

WORKSPACE_ID = "preview.population.workspace"
PROFILE_ID = "preview.population.profile.windows-x64"
PACK_ID = "preview.population.pack"
GAME_VERSION = "preview-population-build-0"
BRANCH = "preview-population"
RUNTIME_TARGET = "Mono"
SOURCE_ID = "preview.population.source"

ACTOR_LEADER_ID = "preview.population.actor.leader"
ACTOR_SCOUT_ID = "preview.population.actor.scout"
TEMPLATE_GUARD_ID = "preview.population.template.guard"
TROOP_PATROL_ID = "preview.population.troop.patrol"
MEMBER_LEADER_ID = "preview.population.member.patrol-leader"
MEMBER_SCOUT_ID = "preview.population.member.patrol-scout"
RELATIONSHIP_LEADER_TEMPLATE_ID = (
    "preview.population.relationship.leader-template"
)
UNRESOLVED_TEMPLATE_SUBJECT = (
    "subject:preview:population:template:scout-unresolved"
)

EXPECTED_STATE = {
    "actor_profile_count": 2,
    "allowed_spawn_candidate_record_ids": [
        ACTOR_LEADER_ID,
        TROOP_PATROL_ID,
    ],
    "evidence_count": 8,
    "forbidden_spawn_candidate_record_ids": [ACTOR_SCOUT_ID],
    "record_count": 4,
    "relationship_count": 1,
    "troop_member_count": 2,
    "troop_profile_count": 1,
    "unresolved_template_subjects": [UNRESOLVED_TEMPLATE_SUBJECT],
}

PRIVATE_PATH_PATTERN = re.compile(
    r"^(?:[A-Za-z]:[\\/]|/|\\\\)|(?:^|[\\/])(?:Users|home)[\\/]",
    re.IGNORECASE,
)
SECRET_PATTERN = re.compile(
    r"(?:-----BEGIN [A-Z ]*PRIVATE KEY-----|"
    r"gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,})"
)
STABLE_ID_PATTERN = re.compile(
    r"[a-z0-9][a-z0-9._-]*\.[a-z0-9][a-z0-9._-]*"
)


class PopulationFixtureError(RuntimeError):
    """Raised when population fixture generation or verification fails closed."""


def template_root_from_script() -> Path:
    return (
        Path(__file__).resolve().parents[1]
        / "Preview"
        / "PopulationTemplate"
    )


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise PopulationFixtureError(message)


def require_string(value: Any, field: str) -> str:
    require(
        isinstance(value, str) and bool(value),
        f"{field} must be a non-empty string",
    )
    return value


def require_list(value: Any, field: str) -> list[Any]:
    require(isinstance(value, list), f"{field} must be an array")
    return value


def require_sorted_unique(values: Any, field: str) -> list[Any]:
    result = require_list(values, field)
    require(result == sorted(result), f"{field} must be sorted")
    require(len(result) == len(set(result)), f"{field} must be unique")
    return result


def require_stable_id(value: Any, field: str) -> str:
    result = require_string(value, field)
    require(
        STABLE_ID_PATTERN.fullmatch(result) is not None,
        f"{field} must be a lowercase stable namespaced identity",
    )
    return result


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PopulationFixtureError(
            f"Unable to read valid UTF-8 JSON from {path}: {exc}"
        ) from exc
    require(isinstance(value, dict), f"Expected a JSON object in {path}")
    return value


def normalize_relative_path(value: Any) -> str:
    require(
        isinstance(value, str) and bool(value),
        "Manifest paths must be non-empty strings",
    )
    require("\\" not in value, f"Manifest path must use forward slashes: {value}")
    path = PurePosixPath(value)
    require(not path.is_absolute(), f"Manifest path must be relative: {value}")
    require(".." not in path.parts, f"Manifest path traversal is prohibited: {value}")
    require(path.as_posix() == value, f"Manifest path is not canonical: {value}")
    return value


def ensure_no_symlinks(root: Path) -> None:
    if root.is_symlink():
        raise PopulationFixtureError(
            f"Population fixture directory must not be a symbolic link: {root}"
        )
    if not root.exists():
        return
    for path in root.rglob("*"):
        if path.is_symlink():
            raise PopulationFixtureError(
                f"Population fixture contains a symbolic link: {path}"
            )


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        dir=str(path.parent),
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def iter_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from iter_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_strings(child)


def assert_public_synthetic_content(value: Any, *, label: str) -> None:
    for text in iter_strings(value):
        require(
            not PRIVATE_PATH_PATTERN.search(text),
            f"{label} contains an absolute or private path: {text}",
        )
        require(
            not SECRET_PATTERN.search(text),
            f"{label} contains secret-like material",
        )
        require("\x00" not in text, f"{label} contains a NUL character")


def is_reserved_population_subject(value: str) -> bool:
    return value.startswith(
        (
            "subject:preview:population:",
            "population-troop-member:preview.population.member.",
            "relationship:preview.population.relationship.",
        )
    )


