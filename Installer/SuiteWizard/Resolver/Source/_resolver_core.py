#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Strict internal implementation for deterministic installer suite resolution.

This module is import-only. The supported command-line entry point is
``suite_package_resolver.py``; direct execution fails closed.
"""

from __future__ import annotations

import argparse
import hashlib
import heapq
import json
import os
import re
import stat
import sys
import tempfile
from dataclasses import dataclass
from functools import total_ordering
from pathlib import Path, PurePosixPath
from typing import Iterable, Sequence
from urllib.parse import urlparse

SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)
ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:[.-][a-z0-9]+)+$")
DIR_RE = re.compile(r"^[A-Za-z][A-Za-z0-9._-]{0,127}$")
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
CAPABILITY_RE = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
RANGE_RE = re.compile(r"^(<=|>=|==|=|<|>)?(.+)$")
WINDOWS_BAD = frozenset('<>:"|?*')
WINDOWS_RESERVED = {
    "con",
    "prn",
    "aux",
    "nul",
    *(f"com{i}" for i in range(1, 10)),
    *(f"lpt{i}" for i in range(1, 10)),
}
AUTHORITY = (
    "game_launch",
    "runtime_execution",
    "deployment",
    "save_mutation",
    "signing",
    "publication",
    "catalog_mutation",
    "evidence_promotion",
)
PACKAGE_KINDS = {
    "core-foundation",
    "editor-project",
    "plugin",
    "integration",
    "runtime-adapter",
    "external-tool-provider",
    "documentation",
    "sample",
}
PACKAGE_STATUSES = {
    "planned",
    "experimental",
    "preview",
    "supported",
    "deprecated",
    "blocked",
}
SOURCE_KINDS = {"product", "plugin", "reviewed-external", "generated"}
RUNTIME_TARGETS = {"editor-only", "mono", "il2cpp", "runtime-neutral"}
INSTALL_SCOPES = {"per-user", "per-machine", "portable"}
REDISTRIBUTION_STATES = {"project-owned", "approved", "notice-required", "blocked"}
REVIEW_STATES = {"required", "approved", "blocked", "not-applicable"}
SUITE_CHANNELS = {"development", "alpha", "beta", "release-candidate", "stable"}
SELECTION_STATES = {"required", "default", "optional"}


class ResolverError(RuntimeError):
    """Raised when a manifest or resolution request fails closed."""


@total_ordering
@dataclass(frozen=True)
class SemVer:
    major: int
    minor: int
    patch: int
    pre: tuple[str, ...] = ()

    @classmethod
    def parse(cls, value: str, label: str = "version") -> "SemVer":
        match = SEMVER_RE.fullmatch(value)
        if not match:
            raise ResolverError(f"{label} is not valid SemVer: {value!r}")
        pre = tuple(match.group(4).split(".")) if match.group(4) else ()
        if any(part.isdigit() and len(part) > 1 and part.startswith("0") for part in pre):
            raise ResolverError(
                f"{label} has a numeric prerelease identifier with a leading zero."
            )
        return cls(
            int(match.group(1)),
            int(match.group(2)),
            int(match.group(3)),
            pre,
        )

    def __eq__(self, other: object) -> bool:
        return isinstance(other, SemVer) and (
            self.major,
            self.minor,
            self.patch,
            self.pre,
        ) == (
            other.major,
            other.minor,
            other.patch,
            other.pre,
        )

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, SemVer):
            return NotImplemented
        left = (self.major, self.minor, self.patch)
        right = (other.major, other.minor, other.patch)
        if left != right:
            return left < right
        if not self.pre:
            return False
        if not other.pre:
            return True
        for a, b in zip(self.pre, other.pre):
            if a == b:
                continue
            a_numeric, b_numeric = a.isdigit(), b.isdigit()
            if a_numeric and b_numeric:
                return int(a) < int(b)
            if a_numeric != b_numeric:
                return a_numeric
            return a < b
        return len(self.pre) < len(other.pre)


@dataclass(frozen=True)
class VersionRange:
    source: str
    clauses: tuple[tuple[str, SemVer], ...]

    @classmethod
    def parse(cls, value: str, label: str) -> "VersionRange":
        value = value.strip()
        if value == "*":
            return cls(value, ())
        if not value or any(mark in value for mark in ("||", "^", "~")):
            raise ResolverError(
                f"{label} uses unsupported version-range syntax {value!r}; "
                "use '*', exact SemVer, or space-separated comparators."
            )
        clauses: list[tuple[str, SemVer]] = []
        for token in value.replace(",", " ").split():
            match = RANGE_RE.fullmatch(token)
            if not match:
                raise ResolverError(f"{label} contains invalid range token {token!r}.")
            clauses.append(
                (
                    match.group(1) or "==",
                    SemVer.parse(match.group(2), label),
                )
            )
        return cls(value, tuple(clauses))

    def matches(self, version: SemVer) -> bool:
        for operator, expected in self.clauses:
            if operator in ("=", "==") and version != expected:
                return False
            if operator == ">" and not version > expected:
                return False
            if operator == ">=" and not version >= expected:
                return False
            if operator == "<" and not version < expected:
                return False
            if operator == "<=" and not version <= expected:
                return False
        return True


@dataclass(frozen=True)
class Context:
    platform: str
    architecture: str
    runtime_target: str
    game_version: str = ""
    branch: str = ""


ResolutionContext = Context


def canonical_json(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode()


canonical_json_bytes = canonical_json


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def is_reparse(path: Path) -> bool:
    try:
        return bool(path.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)
    except AttributeError:
        return False
    except OSError as exc:
        raise ResolverError(f"Unable to inspect {path}: {exc}") from exc


def directory(path: Path, label: str) -> Path:
    if path.is_symlink() or is_reparse(path) or not path.is_dir():
        raise ResolverError(f"{label} is missing, not a directory, or unsafe: {path}")
    return path.resolve(strict=True)


def regular(path: Path, label: str) -> Path:
    if path.is_symlink() or is_reparse(path) or not path.is_file():
        raise ResolverError(f"{label} is missing, not a regular file, or unsafe: {path}")
    return path


def load_json(path: Path, label: str) -> tuple[dict[str, object], str]:
    raw = regular(path, label).read_bytes()

    def no_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ResolverError(f"Duplicate JSON key {key!r} in {label}.")
            result[key] = value
        return result

    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=no_duplicates)
    except ResolverError:
        raise
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ResolverError(f"Unable to parse {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise ResolverError(f"{label} must be a JSON object.")
    return value, sha256(raw)


def text(value: object, label: str, empty: bool = False) -> str:
    if not isinstance(value, str):
        raise ResolverError(f"{label} must be a string.")
    value = value.strip()
    if (not empty and not value) or CONTROL_RE.search(value):
        raise ResolverError(f"{label} is empty or contains control characters.")
    return value


def boolean(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise ResolverError(f"{label} must be a boolean.")
    return value


def integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ResolverError(f"{label} must be an integer.")
    return value


def array(value: object, label: str) -> list[object]:
    if not isinstance(value, list):
        raise ResolverError(f"{label} must be an array.")
    return value


def obj(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ResolverError(f"{label} must be an object.")
    return value


def identity(value: object, label: str) -> str:
    value = text(value, label)
    if not ID_RE.fullmatch(value):
        raise ResolverError(f"{label} is not a namespaced ID: {value!r}")
    return value


def strings(value: object, label: str) -> tuple[str, ...]:
    result = tuple(
        text(item, f"{label}[{index}]")
        for index, item in enumerate(array(value, label))
    )
    if len(set(result)) != len(result):
        raise ResolverError(f"{label} contains duplicates.")
    return result


def relative_path(value: object, label: str) -> str:
    value = text(value, label)
    if "\\" in value:
        raise ResolverError(f"{label} must use forward slashes.")
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or any(
        part in ("", ".", "..") for part in path.parts
    ):
        raise ResolverError(f"{label} is not a canonical relative path: {value!r}")
    for part in path.parts:
        if any(character in WINDOWS_BAD for character in part) or part.endswith((" ", ".")):
            raise ResolverError(
                f"{label} contains a Windows-unsafe component: {value!r}"
            )
        if part.split(".", 1)[0].casefold() in WINDOWS_RESERVED:
            raise ResolverError(
                f"{label} uses a reserved Windows device name: {value!r}"
            )
    return path.as_posix()


def path_key(value: str) -> str:
    return "/".join(
        part.rstrip(" .").casefold() for part in PurePosixPath(value).parts
    )


def enum(value: object, label: str, allowed: set[str]) -> str:
    result = text(value, label)
    if result not in allowed:
        raise ResolverError(
            f"{label} must be one of: {', '.join(sorted(allowed))}; got {result!r}."
        )
    return result


def uri(value: object, label: str) -> str:
    result = text(value, label)
    parsed = urlparse(result)
    if parsed.scheme not in {"https", "http"} or not parsed.netloc:
        raise ResolverError(f"{label} must be an absolute HTTP(S) URI.")
    return result


def utc(value: object, label: str) -> str:
    result = text(value, label)
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", result):
        raise ResolverError(f"{label} must be a whole-second UTC timestamp.")
    return result


def compat(document: dict[str, object], label: str) -> dict[str, tuple[str, ...]]:
    return {
        key: strings(document.get(key), f"{label}.{key}")
        for key in (
            "platforms",
            "architectures",
            "game_versions",
            "branches",
            "runtime_targets",
        )
    }


def match_context(
    label: str,
    allowed: dict[str, tuple[str, ...]],
    context: Context,
) -> None:
    actual = {
        "platforms": context.platform,
        "architectures": context.architecture,
        "game_versions": context.game_version,
        "branches": context.branch,
        "runtime_targets": context.runtime_target,
    }
    for key, values in allowed.items():
        if not values:
            continue
        selected = actual[key]
        if not selected:
            readable = key[:-1].replace("_", " ")
            raise ResolverError(
                f"{label} requires explicit {readable} context; allowed: {', '.join(values)}."
            )
        if selected not in values:
            readable = key[:-1].replace("_", " ")
            raise ResolverError(
                f"{label} rejects {readable} {selected!r}; allowed: {', '.join(values)}."
            )


def validate_schema_version(document: dict[str, object], label: str) -> None:
    version = integer(document.get("schema_version"), f"{label}.schema_version")
    if version != 1:
        raise ResolverError(f"{label}.schema_version must be exactly 1; got {version}.")


def load_packages(installer: Path) -> dict[str, dict[str, object]]:
    root = directory(installer / "Packages", "Installer Packages root")
    result: dict[str, dict[str, object]] = {}
    for child in sorted(root.iterdir(), key=lambda item: item.name.casefold()):
        if child.name == "README.md":
            regular(child, "Installer Packages README")
            continue
        folder = directory(child, f"Package directory {child.name}")
        if not DIR_RE.fullmatch(folder.name):
            raise ResolverError(f"Invalid package directory name: {folder.name!r}")
        document, fingerprint = load_json(
            folder / "package.json", f"package {folder.name}"
        )
        validate_schema_version(document, f"package {folder.name}")
        package_id = identity(
            document.get("package_id"), f"{folder.name}.package_id"
        )
        if package_id in result:
            raise ResolverError(f"Duplicate package_id {package_id!r}.")
        version_text = text(document.get("version"), f"{package_id}.version")
        version = SemVer.parse(version_text, f"{package_id}.version")
        kind = enum(document.get("kind"), f"{package_id}.kind", PACKAGE_KINDS)
        status = enum(
            document.get("status"), f"{package_id}.status", PACKAGE_STATUSES
        )

        source = obj(document.get("source"), f"{package_id}.source")
        source_kind = enum(
            source.get("kind"), f"{package_id}.source.kind", SOURCE_KINDS
        )
        source_repository = uri(
            source.get("repository"), f"{package_id}.source.repository"
        )
        commit = text(source.get("commit"), f"{package_id}.source.commit")
        if not GIT_SHA_RE.fullmatch(commit):
            raise ResolverError(
                f"{package_id}.source.commit must be an exact lowercase Git SHA."
            )
        source_path = relative_path(
            source.get("path"), f"{package_id}.source.path"
        )
        source_hash = source.get("fingerprint_sha256")
        if source_hash is not None:
            source_hash = text(
                source_hash, f"{package_id}.source.fingerprint_sha256"
            )
            if not SHA_RE.fullmatch(source_hash):
                raise ResolverError(
                    f"{package_id}.source.fingerprint_sha256 must be lowercase SHA-256."
                )

        compatibility = compat(
            obj(document.get("compatibility"), f"{package_id}.compatibility"),
            f"{package_id}.compatibility",
        )
        if any(value != "windows" for value in compatibility["platforms"]):
            raise ResolverError(
                f"{package_id} currently supports only the Windows host platform."
            )
        if any(value != "x86_64" for value in compatibility["architectures"]):
            raise ResolverError(
                f"{package_id} currently supports only the x86_64 host architecture."
            )
        unknown_runtime_targets = sorted(
            set(compatibility["runtime_targets"]) - RUNTIME_TARGETS
        )
        if unknown_runtime_targets:
            raise ResolverError(
                f"{package_id} contains unknown runtime targets: "
                + ", ".join(unknown_runtime_targets)
            )

        dependencies: list[dict[str, object]] = []
        dependency_ids: set[str] = set()
        for index, raw in enumerate(
            array(document.get("dependencies"), f"{package_id}.dependencies")
        ):
            dependency = obj(raw, f"{package_id}.dependencies[{index}]")
            dependency_id = identity(
                dependency.get("package_id"),
                f"{package_id}.dependencies[{index}].package_id",
            )
            if dependency_id == package_id or dependency_id in dependency_ids:
                raise ResolverError(
                    f"Package {package_id} has a self or duplicate dependency {dependency_id}."
                )
            dependency_ids.add(dependency_id)
            dependencies.append(
                {
                    "package_id": dependency_id,
                    "range": VersionRange.parse(
                        text(
                            dependency.get("version_range"),
                            f"{package_id}.{dependency_id}.range",
                        ),
                        f"{package_id} dependency {dependency_id}",
                    ),
                    "required": boolean(
                        dependency.get("required"),
                        f"{package_id}.{dependency_id}.required",
                    ),
                }
            )

        conflicts = tuple(
            identity(value, f"{package_id}.conflict")
            for value in array(
                document.get("conflicts", []), f"{package_id}.conflicts"
            )
        )
        if package_id in conflicts or len(set(conflicts)) != len(conflicts):
            raise ResolverError(
                f"{package_id}.conflicts contains a self or duplicate conflict."
            )

        capabilities = strings(
            document.get("capabilities", []), f"{package_id}.capabilities"
        )
        invalid_capabilities = sorted(
            value for value in capabilities if not CAPABILITY_RE.fullmatch(value)
        )
        if invalid_capabilities:
            raise ResolverError(
                f"{package_id} contains invalid capabilities: "
                + ", ".join(invalid_capabilities)
            )

        payload: list[dict[str, object]] = []
        destinations: set[str] = set()
        for index, raw in enumerate(
            array(document.get("payload"), f"{package_id}.payload")
        ):
            item = obj(raw, f"{package_id}.payload[{index}]")
            destination = relative_path(
                item.get("destination"),
                f"{package_id}.payload[{index}].destination",
            )
            destination_key = path_key(destination)
            if destination_key in destinations:
                raise ResolverError(
                    f"Package {package_id} duplicates destination {destination!r}."
                )
            destinations.add(destination_key)
            checksum = text(
                item.get("sha256"), f"{package_id}.payload[{index}].sha256"
            )
            if not SHA_RE.fullmatch(checksum):
                raise ResolverError(
                    f"{package_id}.payload[{index}].sha256 must be lowercase SHA-256."
                )
            redistribution = enum(
                item.get("redistribution"),
                f"{package_id}.payload[{index}].redistribution",
                REDISTRIBUTION_STATES,
            )
            if redistribution == "blocked":
                raise ResolverError(
                    f"Package {package_id} contains redistribution-blocked payload."
                )
            size = integer(
                item.get("size_bytes"),
                f"{package_id}.payload[{index}].size_bytes",
            )
            if size < 0:
                raise ResolverError(
                    f"{package_id}.payload[{index}].size_bytes must be non-negative."
                )
            payload.append(
                {
                    "source": relative_path(
                        item.get("source"),
                        f"{package_id}.payload[{index}].source",
                    ),
                    "destination": destination,
                    "sha256": checksum,
                    "size_bytes": size,
                    "redistribution": redistribution,
                }
            )

        lifecycle = obj(document.get("lifecycle"), f"{package_id}.lifecycle")
        install_scope = enum(
            lifecycle.get("install_scope"),
            f"{package_id}.lifecycle.install_scope",
            INSTALL_SCOPES,
        )
        lifecycle_values: dict[str, object] = {"install_scope": install_scope}
        for field in (
            "elevation_required",
            "repair_supported",
            "upgrade_supported",
            "uninstall_supported",
            "rollback_required",
            "preserve_external_workspaces",
        ):
            lifecycle_values[field] = boolean(
                lifecycle.get(field), f"{package_id}.lifecycle.{field}"
            )
        if lifecycle_values["preserve_external_workspaces"] is not True:
            raise ResolverError(f"Package {package_id} must preserve external workspaces.")

        legal = obj(document.get("legal"), f"{package_id}.legal")
        license_expression = text(
            legal.get("license_expression"), f"{package_id}.legal.license_expression"
        )
        review = enum(
            legal.get("redistribution_review"),
            f"{package_id}.legal.redistribution_review",
            REVIEW_STATES,
        )
        notices = tuple(
            relative_path(value, f"{package_id}.legal.notice_files[{index}]")
            for index, value in enumerate(
                array(legal.get("notice_files"), f"{package_id}.legal.notice_files")
            )
        )
        if len(set(notices)) != len(notices):
            raise ResolverError(f"{package_id}.legal.notice_files contains duplicates.")

        authority = obj(document.get("authority"), f"{package_id}.authority")
        for field in AUTHORITY:
            if boolean(authority.get(field), f"{package_id}.authority.{field}"):
                raise ResolverError(
                    f"Package {package_id} illegally grants authority {field}."
                )

        result[package_id] = {
            "id": package_id,
            "display": text(document.get("display_name"), f"{package_id}.display_name"),
            "version_text": version_text,
            "version": version,
            "kind": kind,
            "status": status,
            "manifest_sha256": fingerprint,
            "source": {
                "kind": source_kind,
                "repository": source_repository,
                "commit": commit,
                "path": source_path,
                **(
                    {"fingerprint_sha256": source_hash}
                    if source_hash is not None
                    else {}
                ),
            },
            "compatibility": compatibility,
            "dependencies": tuple(
                sorted(dependencies, key=lambda item: str(item["package_id"]))
            ),
            "conflicts": tuple(sorted(conflicts)),
            "capabilities": tuple(sorted(capabilities)),
            "payload": tuple(
                sorted(payload, key=lambda item: path_key(str(item["destination"])))
            ),
            "lifecycle": lifecycle_values,
            "legal": {
                "license_expression": license_expression,
                "redistribution_review": review,
                "notice_files": sorted(notices),
            },
        }
    return result


def load_suite(installer: Path, name: str) -> dict[str, object]:
    if not DIR_RE.fullmatch(name):
        raise ResolverError(f"Invalid suite directory name: {name!r}")
    document, fingerprint = load_json(
        directory(installer / "Suites" / name, f"Suite {name}") / "suite.json",
        f"suite {name}",
    )
    validate_schema_version(document, f"suite {name}")
    suite_id = identity(document.get("suite_id"), f"{name}.suite_id")
    version = text(document.get("version"), f"{suite_id}.version")
    SemVer.parse(version, f"{suite_id}.version")
    channel = enum(document.get("channel"), f"{suite_id}.channel", SUITE_CHANNELS)

    entries: list[dict[str, object]] = []
    package_ids: set[str] = set()
    orders: set[int] = set()
    entry_features: dict[str, tuple[str, ...]] = {}
    for index, raw in enumerate(
        array(document.get("packages"), f"{suite_id}.packages")
    ):
        entry = obj(raw, f"{suite_id}.packages[{index}]")
        package_id = identity(
            entry.get("package_id"), f"{suite_id}.packages[{index}].package_id"
        )
        selection = enum(
            entry.get("selection"),
            f"{suite_id}.{package_id}.selection",
            SELECTION_STATES,
        )
        order = integer(entry.get("order"), f"{suite_id}.{package_id}.order")
        if order < 0 or package_id in package_ids or order in orders:
            raise ResolverError(
                f"Suite {suite_id} has duplicate ID/order or invalid order for {package_id}."
            )
        package_ids.add(package_id)
        orders.add(order)
        feature_ids = tuple(
            identity(value, f"{suite_id}.{package_id}.feature_id")
            for value in array(
                entry.get("feature_ids", []), f"{suite_id}.{package_id}.feature_ids"
            )
        )
        if len(set(feature_ids)) != len(feature_ids):
            raise ResolverError(
                f"{suite_id}.{package_id}.feature_ids contains duplicates."
            )
        entry_features[package_id] = feature_ids
        entries.append(
            {
                "package_id": package_id,
                "selection": selection,
                "order": order,
            }
        )
    if not entries:
        raise ResolverError(f"{suite_id}.packages must contain at least one package entry.")

    features: dict[str, tuple[str, ...]] = {}
    for index, raw in enumerate(
        array(document.get("features", []), f"{suite_id}.features")
    ):
        feature = obj(raw, f"{suite_id}.features[{index}]")
        feature_id = identity(
            feature.get("feature_id"), f"{suite_id}.features[{index}].feature_id"
        )
        referenced = tuple(
            sorted(
                identity(value, f"{feature_id}.package_id")
                for value in array(
                    feature.get("package_ids"), f"{feature_id}.package_ids"
                )
            )
        )
        if feature_id in features or not referenced or len(set(referenced)) != len(referenced):
            raise ResolverError(
                f"Suite {suite_id} has duplicate or empty feature {feature_id}."
            )
        unknown = sorted(set(referenced) - package_ids)
        if unknown:
            raise ResolverError(
                f"Feature {feature_id} references packages outside the suite: "
                + ", ".join(unknown)
            )
        text(feature.get("display_name"), f"{feature_id}.display_name")
        features[feature_id] = referenced

    for package_id, declared_features in sorted(entry_features.items()):
        unknown = sorted(set(declared_features) - features.keys())
        if unknown:
            raise ResolverError(
                f"Suite package {package_id} references unknown features: "
                + ", ".join(unknown)
            )
        for feature_id in declared_features:
            if package_id not in features[feature_id]:
                raise ResolverError(
                    f"Suite package {package_id} declares feature {feature_id}, "
                    "but the feature does not include it."
                )

    compatibility_document = obj(
        document.get("compatibility"), f"{suite_id}.compatibility"
    )
    platforms = strings(
        compatibility_document.get("platforms"),
        f"{suite_id}.compatibility.platforms",
    )
    architectures = strings(
        compatibility_document.get("architectures"),
        f"{suite_id}.compatibility.architectures",
    )
    if not platforms or any(value != "windows" for value in platforms):
        raise ResolverError(f"{suite_id} currently supports only the Windows host platform.")
    if not architectures or any(value != "x86_64" for value in architectures):
        raise ResolverError(f"{suite_id} currently supports only the x86_64 host architecture.")

    policies_document = obj(document.get("policies"), f"{suite_id}.policies")
    policies = {
        field: boolean(
            policies_document.get(field), f"{suite_id}.policies.{field}"
        )
        for field in (
            "network_allowed",
            "elevation_allowed",
            "unreviewed_packages_allowed",
            "silent_install_allowed",
        )
    }
    if policies["unreviewed_packages_allowed"]:
        raise ResolverError(f"Suite {suite_id} may not allow unreviewed packages.")

    provenance = obj(document.get("provenance"), f"{suite_id}.provenance")
    uri(provenance.get("source_repository"), f"{suite_id}.provenance.source_repository")
    source_commit = text(
        provenance.get("source_commit"), f"{suite_id}.provenance.source_commit"
    )
    if not GIT_SHA_RE.fullmatch(source_commit):
        raise ResolverError(
            f"{suite_id}.provenance.source_commit must be an exact lowercase Git SHA."
        )
    text(provenance.get("reviewed_by"), f"{suite_id}.provenance.reviewed_by")
    utc(provenance.get("reviewed_at_utc"), f"{suite_id}.provenance.reviewed_at_utc")

    return {
        "id": suite_id,
        "display": text(document.get("display_name"), f"{suite_id}.display_name"),
        "version": version,
        "channel": channel,
        "manifest_sha256": fingerprint,
        "entries": tuple(
            sorted(entries, key=lambda item: (int(item["order"]), str(item["package_id"])))
        ),
        "features": features,
        "policies": policies,
        "compatibility": {
            "platforms": platforms,
            "architectures": architectures,
        },
    }


def cycle(
    selected: set[str], packages: dict[str, dict[str, object]]
) -> tuple[str, ...]:
    state: dict[str, int] = {}
    stack: list[str] = []
    positions: dict[str, int] = {}

    def visit(package_id: str) -> tuple[str, ...] | None:
        state[package_id] = 1
        positions[package_id] = len(stack)
        stack.append(package_id)
        dependencies = packages[package_id]["dependencies"]
        assert isinstance(dependencies, tuple)
        for dependency_id in sorted(
            str(dependency["package_id"])
            for dependency in dependencies
            if str(dependency["package_id"]) in selected
        ):
            if state.get(dependency_id, 0) == 0:
                found = visit(dependency_id)
                if found:
                    return found
            elif state.get(dependency_id) == 1:
                body = stack[positions[dependency_id] :]
                start = min(range(len(body)), key=lambda index: body[index])
                body = body[start:] + body[:start]
                return tuple(body + [body[0]])
        stack.pop()
        positions.pop(package_id)
        state[package_id] = 2
        return None

    for package_id in sorted(selected):
        if state.get(package_id, 0) == 0:
            found = visit(package_id)
            if found:
                return found
    return ()


def resolve(
    installer: Path,
    suite_name: str,
    context: Context,
    *,
    selected: Iterable[str] = (),
    excluded: Iterable[str] = (),
    features: Iterable[str] = (),
) -> dict[str, object]:
    selected_values = tuple(selected)
    excluded_values = tuple(excluded)
    feature_values = tuple(features)
    installer = directory(installer, "Installer root")
    suite = load_suite(installer, suite_name)
    packages = load_packages(installer)
    match_context(f"Suite {suite['id']}", suite["compatibility"], context)

    entries = {
        str(entry["package_id"]): entry
        for entry in suite["entries"]
    }
    missing_manifests = sorted(set(entries) - packages)
    if missing_manifests:
        raise ResolverError(
            "Suite references package entries without package.json: "
            + ", ".join(missing_manifests)
        )

    user_selected = {
        identity(value, "selected package") for value in selected_values
    }
    user_excluded = {
        identity(value, "excluded package") for value in excluded_values
    }
    chosen_features = {
        identity(value, "selected feature") for value in feature_values
    }
    if user_selected & user_excluded:
        raise ResolverError("A package cannot be selected and excluded.")
    unknown = sorted((user_selected | user_excluded) - entries.keys())
    if unknown:
        raise ResolverError(
            "User selection references packages outside the suite: "
            + ", ".join(unknown)
        )
    suite_features = suite["features"]
    assert isinstance(suite_features, dict)
    unknown_features = sorted(chosen_features - suite_features.keys())
    if unknown_features:
        raise ResolverError(
            "Unknown suite features: " + ", ".join(unknown_features)
        )

    chosen: set[str] = set()
    reasons: dict[str, set[str]] = {}
    for entry in suite["entries"]:
        package_id = str(entry["package_id"])
        selection = str(entry["selection"])
        if selection == "required" and package_id in user_excluded:
            raise ResolverError(f"Required package {package_id} cannot be excluded.")
        if (
            selection == "required"
            or (selection == "default" and package_id not in user_excluded)
            or package_id in user_selected
        ):
            chosen.add(package_id)
            reasons.setdefault(package_id, set()).add(f"suite:{selection}")
    for feature_id in sorted(chosen_features):
        for package_id in suite_features[feature_id]:
            if package_id in user_excluded:
                raise ResolverError(
                    f"Feature {feature_id} requires excluded package {package_id}."
                )
            chosen.add(package_id)
            reasons.setdefault(package_id, set()).add(f"feature:{feature_id}")
    for package_id in user_selected:
        reasons.setdefault(package_id, set()).add("user:selected")

    pending = list(chosen)
    heapq.heapify(pending)
    validated: set[str] = set()
    warnings: set[str] = set()
    while pending:
        package_id = heapq.heappop(pending)
        if package_id in validated:
            continue
        package = packages.get(package_id)
        if package is None:
            raise ResolverError(f"Selected package {package_id} has no package.json.")
        if package["status"] in {"planned", "blocked"}:
            raise ResolverError(
                f"Package {package_id} is not installable while status is {package['status']!r}."
            )
        legal = package["legal"]
        assert isinstance(legal, dict)
        if legal["redistribution_review"] not in {"approved", "not-applicable"}:
            raise ResolverError(
                f"Package {package_id} lacks approved redistribution review."
            )
        compatibility = package["compatibility"]
        assert isinstance(compatibility, dict)
        match_context(f"Package {package_id}", compatibility, context)
        if package["status"] in {"experimental", "deprecated"}:
            warnings.add(
                f"Package {package_id} has lifecycle status {package['status']}."
            )
        validated.add(package_id)
        dependencies = package["dependencies"]
        assert isinstance(dependencies, tuple)
        for dependency in dependencies:
            dependency_id = str(dependency["package_id"])
            if bool(dependency["required"]) and dependency_id not in packages:
                raise ResolverError(
                    f"Package {package_id} requires missing package {dependency_id}."
                )
            if bool(dependency["required"]):
                if dependency_id in user_excluded:
                    raise ResolverError(
                        f"Package {package_id} requires excluded package {dependency_id}."
                    )
                reasons.setdefault(dependency_id, set()).add(
                    f"dependency:{package_id}"
                )
                if dependency_id not in chosen:
                    chosen.add(dependency_id)
                    heapq.heappush(pending, dependency_id)

    for package_id in sorted(chosen):
        dependencies = packages[package_id]["dependencies"]
        assert isinstance(dependencies, tuple)
        for dependency in dependencies:
            dependency_id = str(dependency["package_id"])
            constraint = dependency["range"]
            assert isinstance(constraint, VersionRange)
            if dependency_id in chosen and not constraint.matches(
                packages[dependency_id]["version"]
            ):
                raise ResolverError(
                    f"Package {package_id} requires {dependency_id} {constraint.source}, "
                    f"but selected version is {packages[dependency_id]['version_text']}."
                )

    pairs = {
        tuple(sorted((package_id, conflict)))
        for package_id in chosen
        for conflict in packages[package_id]["conflicts"]
        if conflict in chosen
    }
    if pairs:
        raise ResolverError(
            "Selected packages conflict: "
            + ", ".join(f"{left} <-> {right}" for left, right in sorted(pairs))
        )

    elevated = sorted(
        package_id
        for package_id in chosen
        if bool(packages[package_id]["lifecycle"]["elevation_required"])
    )
    if elevated and not bool(suite["policies"]["elevation_allowed"]):
        raise ResolverError(
            "suite forbids elevation required by: " + ", ".join(elevated)
        )

    dependents = {package_id: set() for package_id in chosen}
    indegree = {package_id: 0 for package_id in chosen}
    for package_id in chosen:
        dependencies = packages[package_id]["dependencies"]
        assert isinstance(dependencies, tuple)
        for dependency in dependencies:
            dependency_id = str(dependency["package_id"])
            if dependency_id in chosen and package_id not in dependents[dependency_id]:
                dependents[dependency_id].add(package_id)
                indegree[package_id] += 1
    ready = [
        package_id for package_id, degree in indegree.items() if degree == 0
    ]
    heapq.heapify(ready)
    order: list[str] = []
    while ready:
        package_id = heapq.heappop(ready)
        order.append(package_id)
        for child in sorted(dependents[package_id]):
            indegree[child] -= 1
            if indegree[child] == 0:
                heapq.heappush(ready, child)
    if len(order) != len(chosen):
        found = cycle(chosen, packages)
        raise ResolverError("Dependency cycle detected: " + " -> ".join(found))

    destinations: dict[str, str] = {}
    rows: list[dict[str, object]] = []
    file_count = 0
    total_size = 0
    for package_id in order:
        package = packages[package_id]
        output_payload: list[dict[str, object]] = []
        payload = package["payload"]
        assert isinstance(payload, tuple)
        for raw_item in payload:
            item = dict(raw_item)
            destination = str(item["destination"])
            key = path_key(destination)
            if key in destinations:
                raise ResolverError(
                    f"destination collision at {destination!r}: "
                    f"{destinations[key]} and {package_id}."
                )
            destinations[key] = package_id
            output_payload.append(item)
            file_count += 1
            total_size += int(item["size_bytes"])
        dependencies = package["dependencies"]
        assert isinstance(dependencies, tuple)
        rows.append(
            {
                "package_id": package_id,
                "display_name": package["display"],
                "version": package["version_text"],
                "kind": package["kind"],
                "status": package["status"],
                "selection_reasons": sorted(
                    reasons.get(package_id, {"dependency:implicit"})
                ),
                "dependency_ids": sorted(
                    str(dependency["package_id"])
                    for dependency in dependencies
                    if str(dependency["package_id"]) in chosen
                ),
                "capabilities": list(package["capabilities"]),
                "manifest_sha256": package["manifest_sha256"],
                "source": package["source"],
                "lifecycle": dict(package["lifecycle"]),
                "legal": package["legal"],
                "payload": output_payload,
            }
        )

    base: dict[str, object] = {
        "schema_version": 1,
        "suite": {
            "suite_id": suite["id"],
            "display_name": suite["display"],
            "version": suite["version"],
            "channel": suite["channel"],
            "manifest_sha256": suite["manifest_sha256"],
        },
        "context": {
            "platform": context.platform,
            "architecture": context.architecture,
            "runtime_target": context.runtime_target,
            "game_version": context.game_version,
            "branch": context.branch,
        },
        "selection": {
            "selected_package_ids": sorted(user_selected),
            "excluded_package_ids": sorted(user_excluded),
            "selected_feature_ids": sorted(chosen_features),
        },
        "policies": dict(sorted(suite["policies"].items())),
        "requires_elevation": bool(elevated),
        "package_order": order,
        "packages": rows,
        "summary": {
            "package_count": len(rows),
            "payload_file_count": file_count,
            "payload_size_bytes": total_size,
        },
        "warnings": sorted(warnings),
    }
    return {**base, "plan_sha256": sha256(canonical_json(base))}


def resolve_suite(
    installer_root: Path,
    suite_name: str,
    context: Context,
    *,
    selected_package_ids: Iterable[str] = (),
    excluded_package_ids: Iterable[str] = (),
    selected_feature_ids: Iterable[str] = (),
) -> dict[str, object]:
    return resolve(
        installer_root,
        suite_name,
        context,
        selected=selected_package_ids,
        excluded=excluded_package_ids,
        features=selected_feature_ids,
    )


def atomic_write(path: Path, data: bytes) -> None:
    path = path.resolve(strict=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and (path.is_symlink() or is_reparse(path)):
        raise ResolverError(f"Output is an unsafe link: {path}")
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "wb",
            dir=path.parent,
            prefix=f".{path.name}.",
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except OSError as exc:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        raise ResolverError(f"Unable to publish {path}: {exc}") from exc


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Resolve a reviewed installer suite into a canonical plan."
    )
    parser.add_argument("--installer-root", type=Path, required=True)
    parser.add_argument("--suite", required=True)
    parser.add_argument("--platform", default="windows")
    parser.add_argument("--architecture", default="x86_64")
    parser.add_argument("--runtime-target", default="editor-only")
    parser.add_argument("--game-version", default="")
    parser.add_argument("--branch", default="")
    parser.add_argument("--select", action="append", default=[])
    parser.add_argument("--exclude", action="append", default=[])
    parser.add_argument("--feature", action="append", default=[])
    parser.add_argument("--output", type=Path)
    return parser.parse_args(argv)


if __name__ == "__main__":
    print(
        "_resolver_core.py is an internal import-only module; "
        "use suite_package_resolver.py.",
        file=sys.stderr,
    )
    raise SystemExit(2)
