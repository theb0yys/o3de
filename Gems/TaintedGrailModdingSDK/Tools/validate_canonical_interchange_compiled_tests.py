#!/usr/bin/env python3
# Copyright (c) Contributors to the Open 3D Engine Project.
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Require the dedicated Core-only canonical-interchange compiled test target."""
from __future__ import annotations

import re
import sys
from pathlib import Path


class CanonicalInterchangeCompiledTestError(RuntimeError):
    pass


def validate(repo_root: Path) -> None:
    code = repo_root / "Gems/TaintedGrailModdingSDK/Code"
    cmake = (code / "CMakeLists.txt").read_text(encoding="utf-8")
    match = re.search(
        r"ly_add_target\(\s*NAME \$\{gem_name\}\.CanonicalInterchange\.Tests.*?\n\s*\)",
        cmake,
        flags=re.DOTALL,
    )
    if match is None:
        raise CanonicalInterchangeCompiledTestError("Dedicated canonical-interchange compiled target is missing.")
    target = match.group(0)
    for required in (
        "taintedgrailmoddingsdk_canonical_interchange_tests_files.cmake",
        "Gem::${gem_name}.Core.Static",
        "AZ::AzTest",
        "NO_UNITY",
    ):
        if required not in target:
            raise CanonicalInterchangeCompiledTestError(f"Canonical target is missing {required!r}.")
    for forbidden in ("Framework.Static", "AzToolsFramework", "Qt", "Editor"):
        if forbidden in target:
            raise CanonicalInterchangeCompiledTestError(f"Canonical target has forbidden dependency {forbidden!r}.")
    manifest = (code / "taintedgrailmoddingsdk_canonical_interchange_tests_files.cmake").read_text(encoding="utf-8")
    if "Tests/CanonicalInterchangeContractTests.cpp" not in manifest:
        raise CanonicalInterchangeCompiledTestError("Canonical test manifest is incomplete.")
    test = (code / "Tests/CanonicalInterchangeContractTests.cpp").read_text(encoding="utf-8")
    for marker in (
        "FixedBasisUsesAcceptedHyphenatedTokens",
        "ExactVersionGrammarFailsClosed",
        "FiniteNumbersUseShortestRoundTripBytes",
        "DefaultManifestSerializesAcceptedBasisTokens",
    ):
        if marker not in test:
            raise CanonicalInterchangeCompiledTestError(f"Canonical golden coverage is missing {marker!r}.")


def main() -> int:
    try:
        validate(Path(__file__).resolve().parents[3])
    except (OSError, CanonicalInterchangeCompiledTestError) as exc:
        print(f"Canonical interchange compiled-test validation failed: {exc}", file=sys.stderr)
        return 1
    print("Canonical interchange Core-only compiled-test target validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
