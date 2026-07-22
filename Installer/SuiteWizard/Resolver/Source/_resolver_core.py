#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Resolve one reviewed installer suite into a canonical, non-executable plan."""

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

SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)
ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:[.-][a-z0-9]+)+$")
DIR_RE = re.compile(r"^[A-Za-z][A-Za-z0-9._-]{0,127}$")
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
RANGE_RE = re.compile(r"^(<=|>=|==|=|<|>)?(.+)$")
WINDOWS_BAD = frozenset('<>:"|?*')
WINDOWS_RESERVED = {
    "con", "prn", "aux", "nul",
    *(f"com{i}" for i in range(1, 10)),
    *(f"lpt{i}" for i in range(1, 10)),
}
AUTHORITY = (
    "game_launch", "runtime_execution", "deployment", "save_mutation",
    "signing", "publication", "catalog_mutation", "evidence_promotion",
)


class ResolverError(RuntimeError):
    pass


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
            raise ResolverError(f"{label} has a numeric prerelease identifier with a leading zero.")
        return cls(int(match.group(1)), int(match.group(2)), int(match.group(3)), pre)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, SemVer) and (
            self.major, self.minor, self.patch, self.pre
        ) == (other.major, other.minor, other.patch, other.pre)

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
            an, bn = a.isdigit(), b.isdigit()
            if an and bn:
                return int(a) < int(b)
            if an != bn:
                return an
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
        clauses = []
        for token in value.replace(",", " ").split():
            match = RANGE_RE.fullmatch(token)
            if not match:
                raise ResolverError(f"{label} contains invalid range token {token!r}.")
            clauses.append((match.group(1) or "==", SemVer.parse(match.group(2), label)))
        return cls(value, tuple(clauses))

    def matches(self, version: SemVer) -> bool:
        for op, expected in self.clauses:
            if op in ("=", "==") and version != expected:
                return False
            if op == ">" and not version > expected:
                return False
            if op == ">=" and not version >= expected:
                return False
            if op == "<" and not version < expected:
                return False
            if op == "<=" and not version <= expected:
                return False
        return True


@dataclass(frozen=True)
class Context:
    platform: str
    architecture: str
    runtime_target: str
    game_version: str = ""
    branch: str = ""


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


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
        result = {}
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
    result = tuple(text(item, f"{label}[{i}]") for i, item in enumerate(array(value, label)))
    if len(set(result)) != len(result):
        raise ResolverError(f"{label} contains duplicates.")
    return result


def relative_path(value: object, label: str) -> str:
    value = text(value, label)
    if "\\" in value:
        raise ResolverError(f"{label} must use forward slashes.")
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or any(part in ("", ".", "..") for part in path.parts):
        raise ResolverError(f"{label} is not a canonical relative path: {value!r}")
    for part in path.parts:
        if any(ch in WINDOWS_BAD for ch in part) or part.endswith((" ", ".")):
            raise ResolverError(f"{label} contains a Windows-unsafe component: {value!r}")
        if part.split(".", 1)[0].casefold() in WINDOWS_RESERVED:
            raise ResolverError(f"{label} uses a reserved Windows device name: {value!r}")
    return path.as_posix()


def path_key(value: str) -> str:
    return "/".join(part.rstrip(" .").casefold() for part in PurePosixPath(value).parts)


def compat(document: dict[str, object], label: str) -> dict[str, tuple[str, ...]]:
    return {
        key: strings(document.get(key), f"{label}.{key}")
        for key in ("platforms", "architectures", "game_versions", "branches", "runtime_targets")
    }


def match_context(label: str, allowed: dict[str, tuple[str, ...]], context: Context) -> None:
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
            raise ResolverError(f"{label} requires explicit {readable} context; allowed: {', '.join(values)}.")
        if selected not in values:
            readable = key[:-1].replace("_", " ")
            raise ResolverError(f"{label} rejects {readable} {selected!r}; allowed: {', '.join(values)}.")


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
        doc, fingerprint = load_json(folder / "package.json", f"package {folder.name}")
        pid = identity(doc.get("package_id"), f"{folder.name}.package_id")
        if pid in result:
            raise ResolverError(f"Duplicate package_id {pid!r}.")
        version_text = text(doc.get("version"), f"{pid}.version")
        version = SemVer.parse(version_text, f"{pid}.version")
        source = obj(doc.get("source"), f"{pid}.source")
        commit = text(source.get("commit"), f"{pid}.source.commit")
        if not re.fullmatch(r"[0-9a-f]{40}", commit):
            raise ResolverError(f"{pid}.source.commit must be an exact lowercase Git SHA.")
        source_path = relative_path(source.get("path"), f"{pid}.source.path")
        source_hash = source.get("fingerprint_sha256")
        if source_hash is not None and not SHA_RE.fullmatch(text(source_hash, f"{pid}.source.fingerprint")):
            raise ResolverError(f"{pid}.source.fingerprint_sha256 must be lowercase SHA-256.")

        dependencies = []
        seen = set()
        for i, raw in enumerate(array(doc.get("dependencies"), f"{pid}.dependencies")):
            dep = obj(raw, f"{pid}.dependencies[{i}]")
            did = identity(dep.get("package_id"), f"{pid}.dependencies[{i}].package_id")
            if did == pid or did in seen:
                raise ResolverError(f"Package {pid} has a self or duplicate dependency {did}.")
            seen.add(did)
            dependencies.append({
                "package_id": did,
                "range": VersionRange.parse(text(dep.get("version_range"), f"{pid}.{did}.range"), f"{pid} dependency {did}"),
                "required": boolean(dep.get("required"), f"{pid}.{did}.required"),
            })

        payload, destinations = [], set()
        for i, raw in enumerate(array(doc.get("payload"), f"{pid}.payload")):
            item = obj(raw, f"{pid}.payload[{i}]")
            destination = relative_path(item.get("destination"), f"{pid}.payload[{i}].destination")
            key = path_key(destination)
            if key in destinations:
                raise ResolverError(f"Package {pid} duplicates destination {destination!r}.")
            destinations.add(key)
            checksum = text(item.get("sha256"), f"{pid}.payload[{i}].sha256")
            if not SHA_RE.fullmatch(checksum):
                raise ResolverError(f"{pid}.payload[{i}].sha256 must be lowercase SHA-256.")
            redistribution = text(item.get("redistribution"), f"{pid}.payload[{i}].redistribution")
            if redistribution == "blocked":
                raise ResolverError(f"Package {pid} contains redistribution-blocked payload.")
            size = integer(item.get("size_bytes"), f"{pid}.payload[{i}].size_bytes")
            if size < 0:
                raise ResolverError(f"{pid}.payload[{i}].size_bytes must be non-negative.")
            payload.append({
                "source": relative_path(item.get("source"), f"{pid}.payload[{i}].source"),
                "destination": destination,
                "sha256": checksum,
                "size_bytes": size,
                "redistribution": redistribution,
            })

        lifecycle = obj(doc.get("lifecycle"), f"{pid}.lifecycle")
        for key in (
            "elevation_required", "repair_supported", "upgrade_supported",
            "uninstall_supported", "rollback_required", "preserve_external_workspaces",
        ):
            boolean(lifecycle.get(key), f"{pid}.lifecycle.{key}")
        if lifecycle.get("preserve_external_workspaces") is not True:
            raise ResolverError(f"Package {pid} must preserve external workspaces.")

        legal = obj(doc.get("legal"), f"{pid}.legal")
        review = text(legal.get("redistribution_review"), f"{pid}.legal.redistribution_review")
        authority = obj(doc.get("authority"), f"{pid}.authority")
        for field in AUTHORITY:
            if boolean(authority.get(field), f"{pid}.authority.{field}"):
                raise ResolverError(f"Package {pid} illegally grants authority {field}.")

        result[pid] = {
            "id": pid,
            "display": text(doc.get("display_name"), f"{pid}.display_name"),
            "version_text": version_text,
            "version": version,
            "kind": text(doc.get("kind"), f"{pid}.kind"),
            "status": text(doc.get("status"), f"{pid}.status"),
            "manifest_sha256": fingerprint,
            "source": {
                "kind": text(source.get("kind"), f"{pid}.source.kind"),
                "repository": text(source.get("repository"), f"{pid}.source.repository"),
                "commit": commit,
                "path": source_path,
                **({"fingerprint_sha256": source_hash} if source_hash is not None else {}),
            },
            "compatibility": compat(obj(doc.get("compatibility"), f"{pid}.compatibility"), f"{pid}.compatibility"),
            "dependencies": tuple(sorted(dependencies, key=lambda item: item["package_id"])),
            "conflicts": tuple(sorted(identity(item, f"{pid}.conflict") for item in array(doc.get("conflicts", []), f"{pid}.conflicts"))),
            "capabilities": tuple(sorted(strings(doc.get("capabilities", []), f"{pid}.capabilities"))),
            "payload": tuple(sorted(payload, key=lambda item: path_key(item["destination"]))),
            "lifecycle": lifecycle,
            "legal": {
                "license_expression": text(legal.get("license_expression"), f"{pid}.license"),
                "redistribution_review": review,
                "notice_files": sorted(relative_path(item, f"{pid}.notice") for item in array(legal.get("notice_files"), f"{pid}.notices")),
            },
        }
    return result


def load_suite(installer: Path, name: str) -> dict[str, object]:
    if not DIR_RE.fullmatch(name):
        raise ResolverError(f"Invalid suite directory name: {name!r}")
    doc, fingerprint = load_json(
        directory(installer / "Suites" / name, f"Suite {name}") / "suite.json",
        f"suite {name}",
    )
    sid = identity(doc.get("suite_id"), f"{name}.suite_id")
    version = text(doc.get("version"), f"{sid}.version")
    SemVer.parse(version, f"{sid}.version")
    entries, ids, orders = [], set(), set()
    for i, raw in enumerate(array(doc.get("packages"), f"{sid}.packages")):
        item = obj(raw, f"{sid}.packages[{i}]")
        pid = identity(item.get("package_id"), f"{sid}.packages[{i}].package_id")
        selection = text(item.get("selection"), f"{sid}.{pid}.selection")
        order = integer(item.get("order"), f"{sid}.{pid}.order")
        if pid in ids or order in orders or selection not in {"required", "default", "optional"}:
            raise ResolverError(f"Suite {sid} has duplicate ID/order or invalid selection for {pid}.")
        ids.add(pid)
        orders.add(order)
        entries.append({"package_id": pid, "selection": selection, "order": order})

    features, feature_ids = {}, set()
    for i, raw in enumerate(array(doc.get("features", []), f"{sid}.features")):
        item = obj(raw, f"{sid}.features[{i}]")
        fid = identity(item.get("feature_id"), f"{sid}.features[{i}].feature_id")
        pids = tuple(sorted(identity(value, f"{fid}.package") for value in array(item.get("package_ids"), f"{fid}.packages")))
        if fid in feature_ids or not pids or any(pid not in ids for pid in pids):
            raise ResolverError(f"Suite {sid} has duplicate/empty/unknown feature {fid}.")
        feature_ids.add(fid)
        features[fid] = pids

    policies_doc = obj(doc.get("policies"), f"{sid}.policies")
    policies = {
        key: boolean(policies_doc.get(key), f"{sid}.policies.{key}")
        for key in ("network_allowed", "elevation_allowed", "unreviewed_packages_allowed", "silent_install_allowed")
    }
    if policies["unreviewed_packages_allowed"]:
        raise ResolverError(f"Suite {sid} may not allow unreviewed packages.")
    compatibility = obj(doc.get("compatibility"), f"{sid}.compatibility")
    return {
        "id": sid,
        "display": text(doc.get("display_name"), f"{sid}.display_name"),
        "version": version,
        "channel": text(doc.get("channel"), f"{sid}.channel"),
        "manifest_sha256": fingerprint,
        "entries": tuple(sorted(entries, key=lambda item: (item["order"], item["package_id"]))),
        "features": features,
        "policies": policies,
        "compatibility": {
            key: strings(compatibility.get(key), f"{sid}.compatibility.{key}")
            for key in ("platforms", "architectures")
        },
    }


def cycle(selected: set[str], packages: dict[str, dict[str, object]]) -> tuple[str, ...]:
    state, stack, positions = {}, [], {}

    def visit(pid: str) -> tuple[str, ...] | None:
        state[pid] = 1
        positions[pid] = len(stack)
        stack.append(pid)
        for dep in sorted(d["package_id"] for d in packages[pid]["dependencies"] if d["package_id"] in selected):
            if state.get(dep, 0) == 0:
                found = visit(dep)
                if found:
                    return found
            elif state.get(dep) == 1:
                body = stack[positions[dep]:]
                start = min(range(len(body)), key=lambda i: body[i])
                body = body[start:] + body[:start]
                return tuple(body + [body[0]])
        stack.pop()
        positions.pop(pid)
        state[pid] = 2
        return None

    for pid in sorted(selected):
        if state.get(pid, 0) == 0:
            found = visit(pid)
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
    selected, excluded, features = tuple(selected), tuple(excluded), tuple(features)
    suite, packages = load_suite(installer, suite_name), load_packages(installer)
    match_context(f"Suite {suite['id']}", suite["compatibility"], context)
    entries = {entry["package_id"]: entry for entry in suite["entries"]}
    user_selected = {identity(value, "selected package") for value in selected}
    user_excluded = {identity(value, "excluded package") for value in excluded}
    chosen_features = {identity(value, "selected feature") for value in features}
    if user_selected & user_excluded:
        raise ResolverError("A package cannot be selected and excluded.")
    unknown = sorted((user_selected | user_excluded) - entries.keys())
    if unknown:
        raise ResolverError("User selection references packages outside the suite: " + ", ".join(unknown))
    unknown_features = sorted(chosen_features - suite["features"].keys())
    if unknown_features:
        raise ResolverError("Unknown suite features: " + ", ".join(unknown_features))

    chosen, reasons = set(), {}
    for entry in suite["entries"]:
        pid, selection = entry["package_id"], entry["selection"]
        if selection == "required" and pid in user_excluded:
            raise ResolverError(f"Required package {pid} cannot be excluded.")
        if selection == "required" or (selection == "default" and pid not in user_excluded) or pid in user_selected:
            chosen.add(pid)
            reasons.setdefault(pid, set()).add(f"suite:{selection}")
    for fid in sorted(chosen_features):
        for pid in suite["features"][fid]:
            if pid in user_excluded:
                raise ResolverError(f"Feature {fid} requires excluded package {pid}.")
            chosen.add(pid)
            reasons.setdefault(pid, set()).add(f"feature:{fid}")
    for pid in user_selected:
        reasons.setdefault(pid, set()).add("user:selected")

    pending, validated, warnings = list(chosen), set(), set()
    heapq.heapify(pending)
    while pending:
        pid = heapq.heappop(pending)
        if pid in validated:
            continue
        package = packages.get(pid)
        if not package:
            raise ResolverError(f"Selected package {pid} has no package.json.")
        if package["status"] in {"planned", "blocked"}:
            raise ResolverError(f"Package {pid} is not installable while status is {package['status']!r}.")
        if package["legal"]["redistribution_review"] not in {"approved", "not-applicable"}:
            raise ResolverError(f"Package {pid} lacks approved redistribution review.")
        match_context(f"Package {pid}", package["compatibility"], context)
        if package["status"] in {"experimental", "deprecated"}:
            warnings.add(f"Package {pid} has lifecycle status {package['status']}.")
        validated.add(pid)
        for dep in package["dependencies"]:
            did = dep["package_id"]
            if dep["required"] and did not in packages:
                raise ResolverError(f"Package {pid} requires missing package {did}.")
            if dep["required"]:
                if did in user_excluded:
                    raise ResolverError(f"Package {pid} requires excluded package {did}.")
                reasons.setdefault(did, set()).add(f"dependency:{pid}")
                if did not in chosen:
                    chosen.add(did)
                    heapq.heappush(pending, did)

    for pid in sorted(chosen):
        for dep in packages[pid]["dependencies"]:
            did = dep["package_id"]
            if did in chosen and not dep["range"].matches(packages[did]["version"]):
                raise ResolverError(
                    f"Package {pid} requires {did} {dep['range'].source}, "
                    f"but selected version is {packages[did]['version_text']}."
                )
    pairs = {
        tuple(sorted((pid, conflict)))
        for pid in chosen for conflict in packages[pid]["conflicts"] if conflict in chosen
    }
    if pairs:
        raise ResolverError("Selected packages conflict: " + ", ".join(f"{a} <-> {b}" for a, b in sorted(pairs)))

    elevated = sorted(pid for pid in chosen if packages[pid]["lifecycle"]["elevation_required"])
    if elevated and not suite["policies"]["elevation_allowed"]:
        raise ResolverError("suite forbids elevation required by: " + ", ".join(elevated))

    dependents = {pid: set() for pid in chosen}
    indegree = {pid: 0 for pid in chosen}
    for pid in chosen:
        for dep in packages[pid]["dependencies"]:
            did = dep["package_id"]
            if did in chosen and pid not in dependents[did]:
                dependents[did].add(pid)
                indegree[pid] += 1
    ready = [pid for pid, degree in indegree.items() if degree == 0]
    heapq.heapify(ready)
    order = []
    while ready:
        pid = heapq.heappop(ready)
        order.append(pid)
        for child in sorted(dependents[pid]):
            indegree[child] -= 1
            if indegree[child] == 0:
                heapq.heappush(ready, child)
    if len(order) != len(chosen):
        found = cycle(chosen, packages)
        raise ResolverError("Dependency cycle detected: " + " -> ".join(found))

    destinations, rows, files, size = {}, [], 0, 0
    for pid in order:
        package = packages[pid]
        payload = []
        for item in package["payload"]:
            key = path_key(item["destination"])
            if key in destinations:
                raise ResolverError(
                    f"destination collision at {item['destination']!r}: {destinations[key]} and {pid}."
                )
            destinations[key] = pid
            payload.append(dict(item))
            files += 1
            size += item["size_bytes"]
        rows.append({
            "package_id": pid,
            "display_name": package["display"],
            "version": package["version_text"],
            "kind": package["kind"],
            "status": package["status"],
            "selection_reasons": sorted(reasons.get(pid, {"dependency:implicit"})),
            "dependency_ids": sorted(dep["package_id"] for dep in package["dependencies"] if dep["package_id"] in chosen),
            "capabilities": list(package["capabilities"]),
            "manifest_sha256": package["manifest_sha256"],
            "source": package["source"],
            "lifecycle": {
                key: package["lifecycle"][key] for key in (
                    "install_scope", "elevation_required", "repair_supported", "upgrade_supported",
                    "uninstall_supported", "rollback_required", "preserve_external_workspaces",
                )
            },
            "legal": package["legal"],
            "payload": payload,
        })

    base = {
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
        "summary": {"package_count": len(rows), "payload_file_count": files, "payload_size_bytes": size},
        "warnings": sorted(warnings),
    }
    return {**base, "plan_sha256": sha256(canonical_json(base))}


ResolutionContext = Context
canonical_json_bytes = canonical_json


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
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("wb", dir=path.parent, prefix=f".{path.name}.", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except OSError as exc:
        if temporary:
            temporary.unlink(missing_ok=True)
        raise ResolverError(f"Unable to publish {path}: {exc}") from exc


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
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


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        plan = resolve(
            args.installer_root,
            args.suite,
            Context(
                text(args.platform, "platform"),
                text(args.architecture, "architecture"),
                text(args.runtime_target, "runtime target"),
                text(args.game_version, "game version", True),
                text(args.branch, "branch", True),
            ),
            selected=args.select,
            excluded=args.exclude,
            features=args.feature,
        )
        data = canonical_json(plan)
        if args.output:
            atomic_write(args.output, data)
        else:
            sys.stdout.buffer.write(data)
        return 0
    except (OSError, ResolverError) as exc:
        print(f"Installer suite resolution failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
