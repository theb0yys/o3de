#
# Copyright (c) Contributors to the Open 3D Engine Project.
# For complete copyright and license terms please see the LICENSE at the root of this distribution.
#
# SPDX-License-Identifier: Apache-2.0 OR MIT
#

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

TOOLS_ROOT = Path(__file__).resolve().parents[1]
if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))

from validate_external_tool_interchange_contracts import (  # noqa: E402
    ExternalToolInterchangeContractError,
    validate_external_tool_interchange_contracts,
)


class ExternalToolInterchangeValidatorTests(unittest.TestCase):
    def make_repo(self, root: Path) -> Path:
        repo = root / "repo"
        code = repo / "Gems/TaintedGrailModdingSDK/Code"
        source = code / "Source"
        tests = code / "Tests"
        docs = repo / "docs/tainted-grail-sdk"
        research = (
            repo / "Research/o3de-to-unity-conversion-and-runtime-bridge"
        )
        source.mkdir(parents=True)
        tests.mkdir(parents=True)
        docs.mkdir(parents=True)
        (research / "gates").mkdir(parents=True)
        (research / "inputs").mkdir(parents=True)

        (code / "taintedgrailmoddingsdk_core_files.cmake").write_text(
            "set(FILES\n"
            "    Source/ExternalToolInterchangeContracts.cpp\n"
            "    Source/ExternalToolInterchangeContracts.h\n"
            "    Source/ExternalToolInterchangeCanonical.cpp\n"
            "    Source/ExternalToolInterchangeCanonical.h\n"
            ")\n",
            encoding="utf-8",
        )
        (
            code
            / "taintedgrailmoddingsdk_external_tool_interchange_tests_files.cmake"
        ).write_text(
            "set(FILES\n    Tests/ExternalToolInterchangeContractTests.cpp\n)\n",
            encoding="utf-8",
        )
        (code / "CMakeLists.txt").write_text(
            "ly_add_target(\n"
            "    NAME ${gem_name}.Catalog.Tests test\n"
            "    FILES_CMAKE\n"
            "        taintedgrailmoddingsdk_external_tool_interchange_tests_files.cmake\n"
            "    INCLUDE_DIRECTORIES\n"
            "        PRIVATE Source\n"
            ")\n",
            encoding="utf-8",
        )

        contracts = r'''
enum class UnityConversionDirectionV1 InterchangeToUnity UnityToInterchange
enum class ExternalToolExecutionOutcomeV1
enum class UnityConversionOutcomeV1
struct ExternalToolHandoffV1 struct UnityConversionRequestV1
struct ExternalToolExecutionResultV1 struct UnityConversionResultV1
IsExternalToolExactVersion 2022.3.22f1
ValidateExternalToolHandoffV1 ValidateUnityConversionRequestV1
ValidateExternalToolExecutionResultV1 ValidateUnityConversionResultV1
request.m_unityProviderId != handoff.m_providerId
request.m_unityExtensionId != handoff.m_extensionId
m_executionAllowed = false m_buildAllowed = false m_deploymentAllowed = false
m_executionAttempted = false m_conversionAttempted = false m_projectMutated = false
m_buildPerformed = false m_deploymentPerformed = false
m_interchangeSchemaVersion = 0 MaximumSetEntryCountV1 = 256
ValidateOptionalSourceBinding
Gate 0 handoffs never authorize execution, build, or deployment
Gate 0 V1 is permanently inert: execution results must be not_attempted
Gate 0 V1 is permanently inert: Unity conversion results must be not_attempted
IsSafePackageRelativePath IsSha256Fingerprint IsStrictUtcTimestamp
'''
        (source / "ExternalToolInterchangeContracts.h").write_text(
            contracts,
            encoding="utf-8",
        )
        (source / "ExternalToolInterchangeContracts.cpp").write_text(
            contracts,
            encoding="utf-8",
        )

        canonical = '''
SerializeCanonicalExternalToolHandoffV1 CalculateExternalToolHandoffFingerprintV1
SerializeCanonicalUnityConversionRequestV1 CalculateUnityConversionRequestFingerprintV1
SerializeCanonicalExternalToolExecutionResultV1 CalculateExternalToolExecutionResultFingerprintV1
SerializeCanonicalUnityConversionResultV1 CalculateUnityConversionResultFingerprintV1
"ExecutionAllowed" "BuildAllowed" "DeploymentAllowed" "ExecutionAttempted"
"ConversionAttempted" "ProjectMutated" "BuildPerformed" "DeploymentPerformed"
AppendSortedStringArray CalculateCanonicalSha256
'''
        (source / "ExternalToolInterchangeCanonical.h").write_text(
            canonical,
            encoding="utf-8",
        )
        (source / "ExternalToolInterchangeCanonical.cpp").write_text(
            canonical,
            encoding="utf-8",
        )

        test_text = '''
TypedVocabulariesRejectUnknownValuesAndAcceptNativeUnityVersions
CompleteGateZeroChainIsValidWhileAllAuthorityRemainsFalse
CanonicalGateZeroChainMatchesGoldenV1Vectors
sha256:e235dc035c2fb3c822f542c0e35d6b714e30bd2b5b9901d56cfb9a777dd02088
FutureGateBindingsMayRemainUnselected
AuthorityExecutionAndMutationClaimsFailClosed
EveryPerformedAndOutputClaimIsRejected
ExactCanonicalUpstreamBindingsAreRequired
CallerSelectedAndStaleFingerprintsFailClosed
UnsafePathsDuplicateIdsAndClaimedOutputsFailClosed
"C:/outside" "staging/CON/file"
CanonicalSerializationIsOrderIndependentAndContentSensitive
ValidationDoesNotMutateInputsAndRejectsImpossibleUtcDates
EXPECT_FALSE(handoff.m_executionAllowed)
EXPECT_FALSE(conversionResult.m_projectMutated)
'''
        (tests / "ExternalToolInterchangeContractTests.cpp").write_text(
            test_text,
            encoding="utf-8",
        )
        (docs / "DATA_FORMATS.md").write_text(
            "External-tool interchange Gate 0 envelopes ExternalToolHandoffV1 "
            "UnityConversionRequestV1 ExternalToolExecutionResultV1 "
            "UnityConversionResultV1 2022.3.22f1 not_attempted ExecutionAllowed "
            "BuildAllowed DeploymentAllowed permanently inert no process is launched",
            encoding="utf-8",
        )
        (docs / "EXTERNAL_TOOL_INTERCHANGE_GATE_0.md").write_text(
            "contract-only precursor Version 1 remains permanently inert "
            "Passing Gate 0 grants no permission to begin Gate 1 "
            "No service consumes these documents",
            encoding="utf-8",
        )
        (docs / "EDITOR_TOOLCHAIN_UNITY_INTERCHANGE_DESIGN.md").write_text(
            "Gate 0 contract-only precursor in development "
            "Gate 0 is the only implementation unit authorised before "
            "Version 1 stays permanently inert "
            "Gates 1 and later do not begin until the "
            "Phase 9 entry prerequisite is satisfied",
            encoding="utf-8",
        )
        (docs / "README.md").write_text(
            "External Tool Interchange Gate 0 "
            "O3DE-to-Unity Bridge Research Archive",
            encoding="utf-8",
        )
        (repo / "ROADMAP.md").write_text(
            "Gate 0 contract-only precursor in development "
            "Gate 0 adds only inert Core handoff/result envelopes "
            "Phase 9 provider and execution work remains proposed",
            encoding="utf-8",
        )

        report = (
            Path(__file__).resolve().parents[4]
            / "Research/o3de-to-unity-conversion-and-runtime-bridge/inputs/FOA_SDK_O3DE_TO_UNITY_CONVERSION_AND_RUNTIME_BRIDGE_RESEARCH_REPORT.md"
        ).read_bytes()
        (
            research
            / "inputs/FOA_SDK_O3DE_TO_UNITY_CONVERSION_AND_RUNTIME_BRIDGE_RESEARCH_REPORT.md"
        ).write_bytes(report)
        research_contract = (
            "b17850a12efe97dbd92a8bdf9cfcd155204105c49e230c51cf9b10aceba9c048 "
            "opaque not durable non-durable "
            "Gate 0 is the sole implementation exception before Phase 9 "
            "Gate 1 independently requires Phase 9 entry "
            "result outcomes remain `NotAttempted`"
        )
        for path in (
            research / "README.md",
            research / "SOURCE_REGISTER.md",
            research / "CLAIM_REGISTER.md",
            research / "gates/IMPLEMENTATION_GATE_MAPPING.md",
        ):
            path.write_text(research_contract, encoding="utf-8")
        return repo

    def test_complete_gate_zero_contract_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            validate_external_tool_interchange_contracts(
                self.make_repo(Path(temporary))
            )

    def test_process_api_in_core_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self.make_repo(Path(temporary))
            path = (
                repo
                / "Gems/TaintedGrailModdingSDK/Code/Source/ExternalToolInterchangeContracts.cpp"
            )
            path.write_text(
                path.read_text(encoding="utf-8") + "\nQProcess\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                ExternalToolInterchangeContractError,
                "QProcess",
            ):
                validate_external_tool_interchange_contracts(repo)

    def test_additional_contract_family_source_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self.make_repo(Path(temporary))
            path = (
                repo
                / "Gems/TaintedGrailModdingSDK/Code/Source/ExternalToolInterchangeExecutor.cpp"
            )
            path.write_text("int forbidden_extra_source;\n", encoding="utf-8")
            with self.assertRaisesRegex(
                ExternalToolInterchangeContractError,
                "must contain exactly",
            ):
                validate_external_tool_interchange_contracts(repo)

    def test_spaced_shell_call_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self.make_repo(Path(temporary))
            path = (
                repo
                / "Gems/TaintedGrailModdingSDK/Code/Source/ExternalToolInterchangeContracts.cpp"
            )
            path.write_text(
                path.read_text(encoding="utf-8") + "\nstd::system (command);\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                ExternalToolInterchangeContractError,
                "shell or file-opening call",
            ):
                validate_external_tool_interchange_contracts(repo)

    def test_missing_false_authority_field_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self.make_repo(Path(temporary))
            for name in (
                "ExternalToolInterchangeContracts.h",
                "ExternalToolInterchangeContracts.cpp",
            ):
                path = repo / "Gems/TaintedGrailModdingSDK/Code/Source" / name
                path.write_text(
                    path.read_text(encoding="utf-8").replace(
                        "m_deploymentAllowed = false",
                        "deployment authority omitted",
                    ),
                    encoding="utf-8",
                )
            with self.assertRaisesRegex(
                ExternalToolInterchangeContractError,
                "m_deploymentAllowed",
            ):
                validate_external_tool_interchange_contracts(repo)

    def test_missing_exact_binding_test_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self.make_repo(Path(temporary))
            path = (
                repo
                / "Gems/TaintedGrailModdingSDK/Code/Tests/ExternalToolInterchangeContractTests.cpp"
            )
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    "ExactCanonicalUpstreamBindingsAreRequired",
                    "binding coverage omitted",
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                ExternalToolInterchangeContractError,
                "ExactCanonicalUpstreamBindingsAreRequired",
            ):
                validate_external_tool_interchange_contracts(repo)

    def test_extra_test_manifest_owner_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self.make_repo(Path(temporary))
            path = (
                repo
                / "Gems/TaintedGrailModdingSDK/Code/taintedgrailmoddingsdk_external_tool_interchange_tests_files.cmake"
            )
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    ")\n",
                    "    Tests/UnrelatedTests.cpp\n)\n",
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                ExternalToolInterchangeContractError,
                "test ownership",
            ):
                validate_external_tool_interchange_contracts(repo)

    def test_missing_research_gate_mapping_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self.make_repo(Path(temporary))
            path = (
                repo
                / "Research/o3de-to-unity-conversion-and-runtime-bridge/gates/IMPLEMENTATION_GATE_MAPPING.md"
            )
            path.write_text("gate mapping omitted", encoding="utf-8")
            with self.assertRaisesRegex(
                ExternalToolInterchangeContractError,
                "Gate 0 is the sole implementation exception",
            ):
                validate_external_tool_interchange_contracts(repo)


if __name__ == "__main__":
    unittest.main()
