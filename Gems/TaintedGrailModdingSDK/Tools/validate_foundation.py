#!/usr/bin/env python3
"""Validate the Tainted Grail Modding SDK foundation without building O3DE.

This check deliberately validates only repository structure and the editor-only
product boundary. It is not a substitute for an O3DE configure or compile.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

GEM_NAME = "TaintedGrailModdingSDK"
GEM_PATH = f"Gems/{GEM_NAME}"


def fail(message: str) -> None:
    raise RuntimeError(message)


def load_json(path: Path) -> dict:
    try:
        with path.open("r", encoding="utf-8") as stream:
            value = json.load(stream)
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"Unable to read valid JSON from {path}: {exc}")

    if not isinstance(value, dict):
        fail(f"Expected a JSON object in {path}")
    return value


def require_contains(text: str, fragment: str, path: Path) -> None:
    if fragment not in text:
        fail(f"Missing required fragment {fragment!r} in {path}")


def validate_engine_registration(repo_root: Path) -> None:
    engine_path = repo_root / "engine.json"
    engine = load_json(engine_path)

    external_subdirectories = engine.get("external_subdirectories")
    if not isinstance(external_subdirectories, list):
        fail("engine.json external_subdirectories must be a list")
    if external_subdirectories.count(GEM_PATH) != 1:
        fail(f"{GEM_PATH} must appear exactly once in engine.json external_subdirectories")

    default_gems = engine.get("gem_names", [])
    if GEM_NAME in default_gems:
        fail(
            f"{GEM_NAME} must not be an engine-wide default Gem; it is an editor-only SDK extension"
        )


def validate_gem_metadata(gem_root: Path) -> None:
    gem_path = gem_root / "gem.json"
    gem = load_json(gem_path)

    expected_values = {
        "gem_name": GEM_NAME,
        "display_name": "Tainted Grail Modding SDK",
        "type": "Tool",
    }
    for key, expected in expected_values.items():
        if gem.get(key) != expected:
            fail(f"gem.json {key} must be {expected!r}")

    version = gem.get("version")
    if not isinstance(version, str) or not re.fullmatch(r"\d+\.\d+\.\d+", version):
        fail("gem.json version must use MAJOR.MINOR.PATCH")

    dependencies = gem.get("dependencies")
    if dependencies != []:
        fail("The foundation slice must not add Gem dependencies yet")


def validate_cmake(gem_root: Path) -> None:
    cmake_path = gem_root / "Code" / "CMakeLists.txt"
    cmake = cmake_path.read_text(encoding="utf-8")

    required_fragments = (
        "if(NOT PAL_TRAIT_BUILD_HOST_TOOLS)",
        "NAME ${gem_name}.Editor GEM_MODULE",
        "taintedgrailmoddingsdk_editor_files.cmake",
        "ly_create_alias(NAME ${gem_name}.Tools",
        "ly_create_alias(NAME ${gem_name}.Builders",
        "VARIANTS Tools Builders",
    )
    for fragment in required_fragments:
        require_contains(cmake, fragment, cmake_path)

    forbidden_fragments = (
        "${gem_name}.Clients",
        "${gem_name}.Servers",
        "${gem_name}.Unified",
    )
    for fragment in forbidden_fragments:
        if fragment in cmake:
            fail(f"Editor-only foundation must not expose runtime alias {fragment}")


def validate_source_manifest(gem_root: Path) -> None:
    code_root = gem_root / "Code"
    manifest_path = code_root / "taintedgrailmoddingsdk_editor_files.cmake"
    manifest = manifest_path.read_text(encoding="utf-8")
    entries = set(re.findall(r"^\s+(Source/[^\s\)]+)\s*$", manifest, re.MULTILINE))

    required_entries = {
        "Source/TaintedGrailModdingSDKEditorModule.cpp",
        "Source/TaintedGrailModdingSDKSystemComponent.cpp",
        "Source/TaintedGrailModdingSDKSystemComponent.h",
    }
    if entries != required_entries:
        fail(
            "Editor source manifest mismatch: "
            f"expected {sorted(required_entries)}, found {sorted(entries)}"
        )

    for relative_path in entries:
        if not (code_root / relative_path).is_file():
            fail(f"Manifest entry does not exist: {relative_path}")


def validate_editor_boundary(gem_root: Path) -> None:
    source_root = gem_root / "Code" / "Source"
    source_files = sorted(source_root.glob("*.[ch]pp")) + sorted(source_root.glob("*.h"))
    combined = "\n".join(path.read_text(encoding="utf-8") for path in source_files)

    required_fragments = (
        "AZ_DECLARE_MODULE_CLASS",
        "AZ_COMPONENT(",
        "TaintedGrailModdingSDKService",
        "FoA runtime execution remains disabled",
    )
    for fragment in required_fragments:
        if fragment not in combined:
            fail(f"Editor foundation source is missing {fragment!r}")

    forbidden_runtime_tokens = (
        "BepInEx",
        "HarmonyLib",
        "TG.Main",
        "LocationTemplate",
        "SpawnLocation(",
        "WriteAllBytes",
        "std::ofstream",
    )
    for token in forbidden_runtime_tokens:
        if token in combined:
            fail(f"Editor-only foundation contains forbidden runtime token {token!r}")


def main() -> int:
    repo_root = Path(__file__).resolve().parents[3]
    gem_root = repo_root / GEM_PATH

    try:
        validate_engine_registration(repo_root)
        validate_gem_metadata(gem_root)
        validate_cmake(gem_root)
        validate_source_manifest(gem_root)
        validate_editor_boundary(gem_root)
    except (OSError, RuntimeError) as exc:
        print(f"Tainted Grail SDK foundation validation failed: {exc}", file=sys.stderr)
        return 1

    print("Tainted Grail SDK foundation validation passed.")
    print("Validated: metadata, engine registration, tool variants, source manifest, editor-only boundary.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
