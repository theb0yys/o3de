#!/usr/bin/env python3
#
# Copyright (c) Contributors to the Open 3D Engine Project.
# For complete copyright and license terms please see the LICENSE at the root of this distribution.
#
# SPDX-License-Identifier: Apache-2.0 OR MIT
#

"""Validate the Core-only, non-executing external-tool interchange Gate 0."""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path
from typing import Iterable


class ExternalToolInterchangeContractError(RuntimeError):
    """Raised when Gate 0 contracts are incomplete or cross their authority boundary."""


def read_text(path: Path) -> str:
    if not path.is_file():
        raise ExternalToolInterchangeContractError(
            f"Required external-tool interchange contract file is missing: {path}"
        )
    return path.read_text(encoding="utf-8")


def require_fragments(text: str, fragments: Iterable[str], label: str) -> None:
    for fragment in fragments:
        if fragment not in text:
            raise ExternalToolInterchangeContractError(
                f"{label} is missing required fragment {fragment!r}."
            )


def reject_fragments(text: str, fragments: Iterable[str], label: str) -> None:
    for fragment in fragments:
        if fragment in text:
            raise ExternalToolInterchangeContractError(
                f"{label} contains forbidden fragment {fragment!r}."
            )


def reject_patterns(
    text: str,
    patterns: Iterable[tuple[str, str]],
    label: str,
) -> None:
    for pattern, description in patterns:
        if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
            raise ExternalToolInterchangeContractError(
                f"{label} contains forbidden {description}."
            )


def manifest_entries(path: Path) -> tuple[str, ...]:
    return tuple(
        re.findall(
            r"^\s+((?:Source|Tests)/[^\s)]+\.(?:cpp|h))\s*$",
            read_text(path),
            re.MULTILINE,
        )
    )


def validate_external_tool_interchange_contracts(repo_root: Path) -> None:
    gem_root = repo_root / "Gems/TaintedGrailModdingSDK"
    code_root = gem_root / "Code"
    source_root = code_root / "Source"
    tests_root = code_root / "Tests"

    core_manifest = read_text(code_root / "taintedgrailmoddingsdk_core_files.cmake")
    test_manifest = (
        code_root
        / "taintedgrailmoddingsdk_external_tool_interchange_tests_files.cmake"
    )
    cmake = read_text(code_root / "CMakeLists.txt")

    expected_source_files = (
        "ExternalToolInterchangeCanonical.cpp",
        "ExternalToolInterchangeCanonical.h",
        "ExternalToolInterchangeContracts.cpp",
        "ExternalToolInterchangeContracts.h",
    )
    actual_source_files = tuple(
        sorted(
            path.name
            for path in source_root.glob("ExternalToolInterchange*")
            if path.suffix in {".cpp", ".h"}
        )
    )
    if actual_source_files != expected_source_files:
        raise ExternalToolInterchangeContractError(
            "The permanently inert Gate 0 source family must contain exactly "
            f"{expected_source_files!r}; found {actual_source_files!r}."
        )

    require_fragments(
        core_manifest,
        (
            "Source/ExternalToolInterchangeContracts.cpp",
            "Source/ExternalToolInterchangeContracts.h",
            "Source/ExternalToolInterchangeCanonical.cpp",
            "Source/ExternalToolInterchangeCanonical.h",
        ),
        "Core manifest",
    )
    for source_file in expected_source_files:
        if core_manifest.count(f"Source/{source_file}") != 1:
            raise ExternalToolInterchangeContractError(
                f"Core manifest must own Source/{source_file} exactly once."
            )
    if manifest_entries(test_manifest) != (
        "Tests/ExternalToolInterchangeContractTests.cpp",
    ):
        raise ExternalToolInterchangeContractError(
            "External-tool interchange test ownership must contain only "
            "Tests/ExternalToolInterchangeContractTests.cpp."
        )
    catalog_test_target = re.search(
        r"NAME\s+\$\{gem_name\}\.Catalog\.Tests.*?FILES_CMAKE(?P<files>.*?)INCLUDE_DIRECTORIES",
        cmake,
        re.DOTALL,
    )
    if (
        catalog_test_target is None
        or catalog_test_target.group("files").count(
            "taintedgrailmoddingsdk_external_tool_interchange_tests_files.cmake"
        )
        != 1
    ):
        raise ExternalToolInterchangeContractError(
            "The Gate 0 compiled-test manifest must be linked exactly once by "
            "TaintedGrailModdingSDK.Catalog.Tests."
        )

    contracts = "\n".join(
        (
            read_text(source_root / "ExternalToolInterchangeContracts.h"),
            read_text(source_root / "ExternalToolInterchangeContracts.cpp"),
        )
    )
    canonical = "\n".join(
        (
            read_text(source_root / "ExternalToolInterchangeCanonical.h"),
            read_text(source_root / "ExternalToolInterchangeCanonical.cpp"),
        )
    )
    require_fragments(
        contracts,
        (
            "enum class UnityConversionDirectionV1",
            "InterchangeToUnity",
            "UnityToInterchange",
            "enum class ExternalToolExecutionOutcomeV1",
            "enum class UnityConversionOutcomeV1",
            "struct ExternalToolHandoffV1",
            "struct UnityConversionRequestV1",
            "struct ExternalToolExecutionResultV1",
            "struct UnityConversionResultV1",
            "IsExternalToolExactVersion",
            "2022.3.22f1",
            "ValidateExternalToolHandoffV1",
            "ValidateUnityConversionRequestV1",
            "ValidateExternalToolExecutionResultV1",
            "ValidateUnityConversionResultV1",
            "request.m_unityProviderId != handoff.m_providerId",
            "request.m_unityExtensionId != handoff.m_extensionId",
            "m_executionAllowed = false",
            "m_buildAllowed = false",
            "m_deploymentAllowed = false",
            "m_executionAttempted = false",
            "m_conversionAttempted = false",
            "m_projectMutated = false",
            "m_buildPerformed = false",
            "m_deploymentPerformed = false",
            "m_interchangeSchemaVersion = 0",
            "MaximumSetEntryCountV1 = 256",
            "ValidateOptionalSourceBinding",
            "Gate 0 handoffs never authorize execution, build, or deployment",
            "Gate 0 V1 is permanently inert: execution results must be not_attempted",
            "Gate 0 V1 is permanently inert: Unity conversion results must be not_attempted",
            "IsSafePackageRelativePath",
            "IsSha256Fingerprint",
            "IsStrictUtcTimestamp",
        ),
        "External-tool interchange contracts",
    )
    require_fragments(
        canonical,
        (
            "SerializeCanonicalExternalToolHandoffV1",
            "CalculateExternalToolHandoffFingerprintV1",
            "SerializeCanonicalUnityConversionRequestV1",
            "CalculateUnityConversionRequestFingerprintV1",
            "SerializeCanonicalExternalToolExecutionResultV1",
            "CalculateExternalToolExecutionResultFingerprintV1",
            "SerializeCanonicalUnityConversionResultV1",
            "CalculateUnityConversionResultFingerprintV1",
            '"ExecutionAllowed"',
            '"BuildAllowed"',
            '"DeploymentAllowed"',
            '"ExecutionAttempted"',
            '"ConversionAttempted"',
            '"ProjectMutated"',
            '"BuildPerformed"',
            '"DeploymentPerformed"',
            "AppendSortedStringArray",
            "CalculateCanonicalSha256",
        ),
        "Canonical external-tool interchange serialization",
    )

    reject_fragments(
        contracts + canonical,
        (
            "#include <Q",
            "#include <Qt",
            "AzFramework",
            "AzToolsFramework",
            "#include <ExternalToolchain",
            '"foa.unity-editor"',
            '"com.foa.sdk.interchange"',
            "Succeeded",
            "SucceededWithLosses",
            "Failed",
            "Cancelled",
            "TimedOut",
            "QProcess",
            "ProcessWatcher",
            "CreateProcess",
            "ShellExecute",
            "WriteProcessMemory",
            "popen(",
            "std::filesystem",
            "AZ::IO",
            "FileIOBase",
            "QFile",
            "QSaveFile",
            "SettingsRegistry",
            "PersistenceJsonUtils",
            "SaveObjectToFile",
            "RegisterEnvelope",
            "RegisterSource",
            "RegisterEvidence",
            "ExecuteWorkOrder",
            "DispatchWorkOrder",
            "LaunchFoA",
            "DeployWorkOrder",
            "SaveGame",
            "curl",
            "socket(",
        ),
        "Core external-tool interchange contracts",
    )
    reject_patterns(
        contracts + canonical,
        (
            (
                r"^\s*#\s*include\s*[<\"][^>\"]*(?:AzFramework|AzToolsFramework|ExternalToolchain|filesystem|fstream|unistd\.h|sys/socket\.h|winsock|windows\.h)[^>\"]*[>\"]",
                "framework, filesystem, process, or socket include",
            ),
            (
                r"\b(?:std\s*::\s*)?(?:system|popen|_popen|fopen|freopen)\s*\(",
                "shell or file-opening call",
            ),
            (
                r"\b(?:fork|vfork|exec[a-z0-9_]*|posix_spawn[a-z0-9_]*|CreateProcess[a-z0-9_]*|ShellExecute[a-z0-9_]*|WinExec)\s*\(",
                "process-launch call",
            ),
            (
                r"\b(?:socket|connect|bind|listen|accept|send|recv)\s*\(",
                "socket or network call",
            ),
            (
                r"\b(?:std\s*::\s*)?(?:filesystem|ifstream|ofstream|fstream)\b|\bAZ\s*::\s*IO\b",
                "filesystem API",
            ),
            (
                r"\b(?:SettingsRegistry|FileIOBase|QFile|QSaveFile|QProcess)\b",
                "registry, persistence, Qt file, or Qt process API",
            ),
        ),
        "Core external-tool interchange contracts",
    )

    tests = read_text(tests_root / "ExternalToolInterchangeContractTests.cpp")
    require_fragments(
        tests,
        (
            "TypedVocabulariesRejectUnknownValuesAndAcceptNativeUnityVersions",
            "CompleteGateZeroChainIsValidWhileAllAuthorityRemainsFalse",
            "CanonicalGateZeroChainMatchesGoldenV1Vectors",
            "sha256:e235dc035c2fb3c822f542c0e35d6b714e30bd2b5b9901d56cfb9a777dd02088",
            "FutureGateBindingsMayRemainUnselected",
            "AuthorityExecutionAndMutationClaimsFailClosed",
            "EveryPerformedAndOutputClaimIsRejected",
            "ExactCanonicalUpstreamBindingsAreRequired",
            "CallerSelectedAndStaleFingerprintsFailClosed",
            "UnsafePathsDuplicateIdsAndClaimedOutputsFailClosed",
            '"C:/outside"',
            '"staging/CON/file"',
            "CanonicalSerializationIsOrderIndependentAndContentSensitive",
            "ValidationDoesNotMutateInputsAndRejectsImpossibleUtcDates",
            'EXPECT_FALSE(handoff.m_executionAllowed)',
            'EXPECT_FALSE(conversionResult.m_projectMutated)',
        ),
        "External-tool interchange compiled tests",
    )

    data_formats = read_text(repo_root / "docs/tainted-grail-sdk/DATA_FORMATS.md")
    require_fragments(
        data_formats,
        (
            "External-tool interchange Gate 0 envelopes",
            "ExternalToolHandoffV1",
            "UnityConversionRequestV1",
            "ExternalToolExecutionResultV1",
            "UnityConversionResultV1",
            "2022.3.22f1",
            "not_attempted",
            "ExecutionAllowed",
            "BuildAllowed",
            "DeploymentAllowed",
            "permanently inert",
            "no process is launched",
        ),
        "Data-format documentation",
    )

    docs_root = repo_root / "docs/tainted-grail-sdk"
    gate_document = read_text(docs_root / "EXTERNAL_TOOL_INTERCHANGE_GATE_0.md")
    design = read_text(docs_root / "EDITOR_TOOLCHAIN_UNITY_INTERCHANGE_DESIGN.md")
    docs_index = read_text(docs_root / "README.md")
    roadmap = read_text(repo_root / "ROADMAP.md")
    require_fragments(
        gate_document,
        (
            "contract-only precursor",
            "Version 1 remains permanently inert",
            "Passing Gate 0 grants no permission to begin Gate 1",
            "No service consumes these documents",
        ),
        "Gate 0 documentation",
    )
    require_fragments(
        design,
        (
            "Gate 0 contract-only precursor in development",
            "Gate 0 is the only implementation unit authorised before",
            "Version 1 stays permanently inert",
            "Gates 1 and later do not begin until the",
            "Phase 9 entry prerequisite is satisfied",
        ),
        "Editor-toolchain design",
    )
    require_fragments(
        roadmap,
        (
            "Gate 0 contract-only precursor in development",
            "Gate 0 adds only inert Core handoff/result envelopes",
            "Phase 9 provider and execution work remains proposed",
        ),
        "Roadmap",
    )
    require_fragments(
        docs_index,
        (
            "External Tool Interchange Gate 0",
            "O3DE-to-Unity Bridge Research Archive",
        ),
        "Documentation index",
    )

    research_root = (
        repo_root / "Research/o3de-to-unity-conversion-and-runtime-bridge"
    )
    research_index = read_text(research_root / "README.md")
    source_register = read_text(research_root / "SOURCE_REGISTER.md")
    claim_register = read_text(research_root / "CLAIM_REGISTER.md")
    gate_mapping = read_text(research_root / "gates/IMPLEMENTATION_GATE_MAPPING.md")
    report_path = (
        research_root
        / "inputs/FOA_SDK_O3DE_TO_UNITY_CONVERSION_AND_RUNTIME_BRIDGE_RESEARCH_REPORT.md"
    )
    report_bytes = report_path.read_bytes()
    report_sha256 = hashlib.sha256(report_bytes).hexdigest()
    expected_report_sha256 = (
        "b17850a12efe97dbd92a8bdf9cfcd155204105c49e230c51cf9b10aceba9c048"
    )
    if report_sha256 != expected_report_sha256:
        raise ExternalToolInterchangeContractError(
            "The preserved bridge research report no longer matches its intake fingerprint."
        )
    require_fragments(
        research_index,
        ("opaque", "not durable"),
        "Research topic index",
    )
    require_fragments(
        source_register,
        (expected_report_sha256, "opaque", "non-durable"),
        "Research source register",
    )
    require_fragments(
        claim_register,
        ("Gate 1 independently requires Phase 9 entry",),
        "Research claim register",
    )
    require_fragments(
        gate_mapping,
        (
            "Gate 0 is the sole implementation exception before Phase 9",
            "result outcomes remain `NotAttempted`",
        ),
        "Research implementation-gate mapping",
    )


def main() -> int:
    repo_root = Path(__file__).resolve().parents[3]
    try:
        validate_external_tool_interchange_contracts(repo_root)
    except (OSError, ExternalToolInterchangeContractError) as exc:
        print(
            f"External-tool interchange Gate 0 validation failed: {exc}",
            file=sys.stderr,
        )
        return 1
    print(
        "External-tool interchange Gate 0 passed: exact canonical bindings, "
        "bounded versions and paths, and zero execution/build/deployment authority are wired."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
