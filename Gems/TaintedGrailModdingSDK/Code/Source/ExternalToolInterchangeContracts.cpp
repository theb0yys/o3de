/*
 * Copyright (c) Contributors to the Open 3D Engine Project.
 * For complete copyright and license terms please see the LICENSE at the root of this distribution.
 *
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 */

#include "ExternalToolInterchangeContracts.h"

#include "CanonicalFingerprint.h"
#include "ExternalToolInterchangeCanonical.h"
#include "PackagePathValidation.h"
#include "ResearchContractValidation.h"

#include <AzCore/std/algorithm.h>
#include <AzCore/std/sort.h>

namespace TaintedGrailModdingSDK
{
    namespace
    {
        template<class EnumType>
        struct EnumName
        {
            EnumType m_value;
            const char* m_name;
        };

        constexpr EnumName<UnityConversionDirectionV1> ConversionDirections[] = {
            { UnityConversionDirectionV1::InterchangeToUnity,
              "interchange_to_unity" },
            { UnityConversionDirectionV1::UnityToInterchange,
              "unity_to_interchange" },
        };

        constexpr EnumName<ExternalToolExecutionOutcomeV1> ExecutionOutcomes[] = {
            { ExternalToolExecutionOutcomeV1::NotAttempted, "not_attempted" },
        };

        constexpr EnumName<UnityConversionOutcomeV1> ConversionOutcomes[] = {
            { UnityConversionOutcomeV1::NotAttempted, "not_attempted" },
        };

        constexpr size_t MaximumSetEntryCountV1 = 256;

        template<class EnumType, size_t Count>
        AZStd::string EnumToString(
            EnumType value,
            const EnumName<EnumType> (&names)[Count])
        {
            for (const EnumName<EnumType>& name : names)
            {
                if (name.m_value == value)
                {
                    return name.m_name;
                }
            }
            return "unknown";
        }

        template<class EnumType, size_t Count>
        bool TryParseEnum(
            const AZStd::string& value,
            EnumType& result,
            const EnumName<EnumType> (&names)[Count])
        {
            for (const EnumName<EnumType>& name : names)
            {
                if (value == name.m_name)
                {
                    result = name.m_value;
                    return true;
                }
            }
            return false;
        }

        template<class EnumType, size_t Count>
        bool IsKnownEnum(
            EnumType value,
            const EnumName<EnumType> (&names)[Count])
        {
            for (const EnumName<EnumType>& name : names)
            {
                if (name.m_value == value)
                {
                    return true;
                }
            }
            return false;
        }

        void SetError(AZStd::string* error, const char* message)
        {
            if (error)
            {
                *error = message;
            }
        }

        bool Succeed(AZStd::string* error)
        {
            if (error)
            {
                error->clear();
            }
            return true;
        }

        bool IsAsciiAlphaNumeric(char value)
        {
            return (value >= 'a' && value <= 'z')
                || (value >= 'A' && value <= 'Z')
                || (value >= '0' && value <= '9');
        }

        bool IsLowerAsciiAlphaNumeric(char value)
        {
            return (value >= 'a' && value <= 'z')
                || (value >= '0' && value <= '9');
        }

        bool HasDuplicate(const AZStd::vector<AZStd::string>& values)
        {
            AZStd::vector<AZStd::string> sorted = values;
            AZStd::sort(sorted.begin(), sorted.end());
            return AZStd::adjacent_find(sorted.begin(), sorted.end())
                != sorted.end();
        }

        bool ValidateStableIdCollection(
            const AZStd::vector<AZStd::string>& values,
            bool requireValue)
        {
            if ((requireValue && values.empty())
                || values.size() > MaximumSetEntryCountV1
                || HasDuplicate(values))
            {
                return false;
            }
            for (const AZStd::string& value : values)
            {
                if (!IsStableContractId(value))
                {
                    return false;
                }
            }
            return true;
        }

        bool ValidateOptionalSourceBinding(
            const AZStd::string& packageId,
            const AZStd::string& manifestId,
            const AZStd::string& manifestFingerprint)
        {
            const bool anyPresent = !packageId.empty()
                || !manifestId.empty()
                || !manifestFingerprint.empty();
            if (!anyPresent)
            {
                return true;
            }
            return IsStableContractId(packageId)
                && IsStableContractId(manifestId)
                && IsSha256Fingerprint(manifestFingerprint);
        }

        bool HandoffBindingMatches(
            const ExternalToolHandoffV1& handoff,
            const AZStd::string& handoffId,
            const AZStd::string& canonicalJson,
            const AZStd::string& fingerprint)
        {
            const AZStd::string expected =
                SerializeCanonicalExternalToolHandoffV1(handoff);
            return handoffId == handoff.m_handoffId
                && canonicalJson == expected
                && fingerprint == handoff.m_handoffFingerprint
                && CanonicalSha256Matches(canonicalJson, fingerprint);
        }
    } // namespace

    AZStd::string ToString(UnityConversionDirectionV1 direction)
    {
        return EnumToString(direction, ConversionDirections);
    }

    AZStd::string ToString(ExternalToolExecutionOutcomeV1 outcome)
    {
        return EnumToString(outcome, ExecutionOutcomes);
    }

    AZStd::string ToString(UnityConversionOutcomeV1 outcome)
    {
        return EnumToString(outcome, ConversionOutcomes);
    }

    bool TryParseUnityConversionDirectionV1(
        const AZStd::string& value,
        UnityConversionDirectionV1& direction)
    {
        return TryParseEnum(value, direction, ConversionDirections);
    }

    bool TryParseExternalToolExecutionOutcomeV1(
        const AZStd::string& value,
        ExternalToolExecutionOutcomeV1& outcome)
    {
        return TryParseEnum(value, outcome, ExecutionOutcomes);
    }

    bool TryParseUnityConversionOutcomeV1(
        const AZStd::string& value,
        UnityConversionOutcomeV1& outcome)
    {
        return TryParseEnum(value, outcome, ConversionOutcomes);
    }

    bool IsExternalToolExactVersion(const AZStd::string& value)
    {
        if (value.empty()
            || value.size() > 128
            || !IsAsciiAlphaNumeric(value.front())
            || !IsAsciiAlphaNumeric(value.back()))
        {
            return false;
        }
        for (char character : value)
        {
            if (!(IsAsciiAlphaNumeric(character)
                    || character == '.'
                    || character == '-'
                    || character == '_'
                    || character == '+'))
            {
                return false;
            }
        }
        return true;
    }

    bool IsExternalToolCommandId(const AZStd::string& value)
    {
        if (value.empty()
            || value.size() > 160
            || !IsLowerAsciiAlphaNumeric(value.front())
            || !IsLowerAsciiAlphaNumeric(value.back()))
        {
            return false;
        }
        for (char character : value)
        {
            if (!(IsLowerAsciiAlphaNumeric(character)
                    || character == '.'
                    || character == '-'
                    || character == '_'))
            {
                return false;
            }
        }
        return true;
    }

    bool ValidateExternalToolHandoffV1(
        const ExternalToolHandoffV1& handoff,
        AZStd::string* error)
    {
        if (handoff.m_contractVersion != 1)
        {
            SetError(error, "External-tool handoff contract version must be 1.");
            return false;
        }
        if (!IsStableContractId(handoff.m_handoffId)
            || !IsStableContractId(handoff.m_workspaceId)
            || !IsStableContractId(handoff.m_packId)
            || !IsStableContractId(handoff.m_profileId))
        {
            SetError(
                error,
                "External-tool handoff, workspace, pack, and profile identities must be stable namespaced IDs.");
            return false;
        }
        if (!IsStableContractId(handoff.m_providerId)
            || !IsStrictSemanticVersion(handoff.m_providerVersion)
            || !IsStrictSemanticVersion(handoff.m_hostApiVersion)
            || !IsStableContractId(handoff.m_applicationId)
            || !IsExternalToolExactVersion(handoff.m_applicationVersion))
        {
            SetError(
                error,
                "External-tool provider and application bindings require stable IDs, strict provider and host versions, and one bounded exact application version.");
            return false;
        }
        if (!IsStableContractId(handoff.m_extensionId)
            || !IsStrictSemanticVersion(handoff.m_extensionVersion)
            || !IsExternalToolExactVersion(handoff.m_extensionRevision)
            || !IsSha256Fingerprint(handoff.m_extensionFingerprint)
            || !IsExternalToolCommandId(handoff.m_commandId))
        {
            SetError(
                error,
                "External-tool extension and command bindings require exact IDs, versions, revision, SHA-256, and a bounded lowercase command ID.");
            return false;
        }
        if (!ValidateStableIdCollection(
                handoff.m_qualificationEvidenceIds,
                false))
        {
            SetError(
                error,
                "Declared qualification evidence IDs must be stable, unique, and bounded when present.");
            return false;
        }
        if (!IsSha256Fingerprint(handoff.m_toolchainLockFingerprint)
            || !IsSha256Fingerprint(handoff.m_configurationFingerprint)
            || !ValidateOptionalSourceBinding(
                handoff.m_sourcePackageId,
                handoff.m_sourceManifestId,
                handoff.m_sourceManifestFingerprint))
        {
            SetError(
                error,
                "Toolchain and configuration fingerprints are required; a future source binding must be absent or complete.");
            return false;
        }
        if (!IsSafePackageRelativePath(handoff.m_stagingRoot))
        {
            SetError(
                error,
                "The staging root must be a bounded safe package-relative path.");
            return false;
        }
        if (handoff.m_executionAllowed
            || handoff.m_buildAllowed
            || handoff.m_deploymentAllowed)
        {
            SetError(
                error,
                "Gate 0 handoffs never authorize execution, build, or deployment.");
            return false;
        }
        if (!IsSha256Fingerprint(handoff.m_handoffFingerprint)
            || !ExternalToolHandoffFingerprintMatchesV1(handoff))
        {
            SetError(
                error,
                "Handoff fingerprint must hash the deterministic Gate 0 handoff payload.");
            return false;
        }
        return Succeed(error);
    }

    bool ValidateUnityConversionRequestV1(
        const ExternalToolHandoffV1& handoff,
        const UnityConversionRequestV1& request,
        AZStd::string* error)
    {
        AZStd::string upstreamError;
        if (!ValidateExternalToolHandoffV1(handoff, &upstreamError))
        {
            if (error)
            {
                *error = "Invalid upstream handoff: " + upstreamError;
            }
            return false;
        }
        if (request.m_contractVersion != 1
            || !IsStableContractId(request.m_requestId))
        {
            SetError(
                error,
                "Unity conversion request contract version must be 1 and request identity must be stable.");
            return false;
        }
        if (!HandoffBindingMatches(
                handoff,
                request.m_handoffId,
                request.m_handoffCanonicalJson,
                request.m_handoffFingerprint))
        {
            SetError(
                error,
                "Unity conversion request must bind the exact canonical handoff and fingerprint.");
            return false;
        }
        if (!IsKnownEnum(request.m_direction, ConversionDirections))
        {
            SetError(error, "Unity conversion direction must be a known V1 value.");
            return false;
        }
        if (request.m_unityProviderId != handoff.m_providerId
            || !IsStableContractId(request.m_unityProviderId)
            || request.m_unityEditorId != handoff.m_applicationId
            || request.m_unityEditorVersion != handoff.m_applicationVersion
            || !IsExternalToolExactVersion(request.m_unityEditorVersion))
        {
            SetError(
                error,
                "Unity conversion requests require the exact provider and editor binding from the handoff.");
            return false;
        }
        if (request.m_unityExtensionId != handoff.m_extensionId
            || !IsStableContractId(request.m_unityExtensionId)
            || request.m_unityExtensionVersion != handoff.m_extensionVersion
            || request.m_unityExtensionRevision != handoff.m_extensionRevision
            || request.m_unityExtensionFingerprint
                != handoff.m_extensionFingerprint)
        {
            SetError(
                error,
                "Unity conversion requests require the exact reviewed extension binding from the handoff.");
            return false;
        }
        if (request.m_interchangeSchemaVersion != 0
            || !IsStableContractId(request.m_testProjectId)
            || request.m_sourcePackageId != handoff.m_sourcePackageId
            || request.m_sourceManifestId != handoff.m_sourceManifestId
            || request.m_sourceManifestFingerprint
                != handoff.m_sourceManifestFingerprint)
        {
            SetError(
                error,
                "Gate 0 leaves the interchange schema unselected and requires a test-project ID plus the exact optional source binding.");
            return false;
        }
        if (!ValidateStableIdCollection(request.m_requestedAssetIds, false))
        {
            SetError(
                error,
                "Requested asset identities must be stable, unique, and bounded when present.");
            return false;
        }
        if (request.m_executionAllowed
            || request.m_buildAllowed
            || request.m_deploymentAllowed)
        {
            SetError(
                error,
                "Gate 0 Unity requests never authorize execution, build, or deployment.");
            return false;
        }
        if (!IsSha256Fingerprint(request.m_requestFingerprint)
            || !UnityConversionRequestFingerprintMatchesV1(request))
        {
            SetError(
                error,
                "Request fingerprint must hash the deterministic Gate 0 Unity request payload.");
            return false;
        }
        return Succeed(error);
    }

    bool ValidateExternalToolExecutionResultV1(
        const ExternalToolHandoffV1& handoff,
        const ExternalToolExecutionResultV1& result,
        AZStd::string* error)
    {
        AZStd::string upstreamError;
        if (!ValidateExternalToolHandoffV1(handoff, &upstreamError))
        {
            if (error)
            {
                *error = "Invalid upstream handoff: " + upstreamError;
            }
            return false;
        }
        if (result.m_contractVersion != 1
            || !IsStableContractId(result.m_resultId))
        {
            SetError(
                error,
                "External-tool execution result contract version must be 1 and result identity must be stable.");
            return false;
        }
        if (!HandoffBindingMatches(
                handoff,
                result.m_handoffId,
                result.m_handoffCanonicalJson,
                result.m_handoffFingerprint))
        {
            SetError(
                error,
                "External-tool execution result must bind the exact canonical handoff and fingerprint.");
            return false;
        }
        if (result.m_providerId != handoff.m_providerId
            || result.m_providerVersion != handoff.m_providerVersion
            || result.m_commandId != handoff.m_commandId)
        {
            SetError(
                error,
                "External-tool execution result provider, version, and command must match the handoff exactly.");
            return false;
        }
        if (!IsKnownEnum(result.m_outcome, ExecutionOutcomes)
            || result.m_outcome
                != ExternalToolExecutionOutcomeV1::NotAttempted
            || result.m_executionAttempted
            || result.m_hasExitCode
            || result.m_exitCode != 0
            || !result.m_startedAtUtc.empty()
            || !result.m_completedAtUtc.empty())
        {
            SetError(
                error,
                "Gate 0 V1 is permanently inert: execution results must be not_attempted with no execution timing or exit status.");
            return false;
        }
        if (!IsStrictUtcTimestamp(result.m_capturedAtUtc))
        {
            SetError(
                error,
                "External-tool execution results require a real whole-second UTC capture time.");
            return false;
        }
        if (!result.m_outputManifestId.empty()
            || !result.m_outputManifestFingerprint.empty())
        {
            SetError(
                error,
                "Gate 0 execution results cannot claim an output manifest.");
            return false;
        }
        if (!ValidateStableIdCollection(result.m_reasonCodes, true))
        {
            SetError(
                error,
                "Gate 0 execution result reason codes must be non-empty, stable, and unique.");
            return false;
        }
        if (result.m_buildPerformed || result.m_deploymentPerformed)
        {
            SetError(
                error,
                "Gate 0 execution results cannot report build or deployment behavior.");
            return false;
        }
        if (!IsSha256Fingerprint(result.m_resultFingerprint)
            || !ExternalToolExecutionResultFingerprintMatchesV1(result))
        {
            SetError(
                error,
                "Execution result fingerprint must hash the deterministic Gate 0 result payload.");
            return false;
        }
        return Succeed(error);
    }

    bool ValidateUnityConversionResultV1(
        const ExternalToolHandoffV1& handoff,
        const UnityConversionRequestV1& request,
        const ExternalToolExecutionResultV1& executionResult,
        const UnityConversionResultV1& result,
        AZStd::string* error)
    {
        AZStd::string upstreamError;
        if (!ValidateUnityConversionRequestV1(
                handoff,
                request,
                &upstreamError))
        {
            if (error)
            {
                *error = "Invalid upstream Unity request: " + upstreamError;
            }
            return false;
        }
        if (!ValidateExternalToolExecutionResultV1(
                handoff,
                executionResult,
                &upstreamError))
        {
            if (error)
            {
                *error = "Invalid upstream execution result: " + upstreamError;
            }
            return false;
        }
        if (result.m_contractVersion != 1
            || !IsStableContractId(result.m_resultId))
        {
            SetError(
                error,
                "Unity conversion result contract version must be 1 and result identity must be stable.");
            return false;
        }

        const AZStd::string requestCanonical =
            SerializeCanonicalUnityConversionRequestV1(request);
        if (result.m_requestId != request.m_requestId
            || result.m_requestCanonicalJson != requestCanonical
            || result.m_requestFingerprint != request.m_requestFingerprint
            || !CanonicalSha256Matches(
                result.m_requestCanonicalJson,
                result.m_requestFingerprint))
        {
            SetError(
                error,
                "Unity conversion result must bind the exact canonical request and fingerprint.");
            return false;
        }

        const AZStd::string executionCanonical =
            SerializeCanonicalExternalToolExecutionResultV1(executionResult);
        if (result.m_executionResultId != executionResult.m_resultId
            || result.m_executionResultCanonicalJson != executionCanonical
            || result.m_executionResultFingerprint
                != executionResult.m_resultFingerprint
            || !CanonicalSha256Matches(
                result.m_executionResultCanonicalJson,
                result.m_executionResultFingerprint))
        {
            SetError(
                error,
                "Unity conversion result must bind the exact canonical execution result and fingerprint.");
            return false;
        }
        if (result.m_direction != request.m_direction
            || result.m_unityProviderId != request.m_unityProviderId
            || result.m_unityEditorVersion != request.m_unityEditorVersion
            || result.m_unityExtensionId != request.m_unityExtensionId
            || result.m_unityExtensionVersion
                != request.m_unityExtensionVersion)
        {
            SetError(
                error,
                "Unity conversion result direction and Unity lock must match the request exactly.");
            return false;
        }
        if (!IsKnownEnum(result.m_outcome, ConversionOutcomes)
            || result.m_outcome != UnityConversionOutcomeV1::NotAttempted
            || result.m_conversionAttempted
            || result.m_projectMutated)
        {
            SetError(
                error,
                "Gate 0 V1 is permanently inert: Unity conversion results must be not_attempted and cannot mutate a project.");
            return false;
        }
        if (!result.m_outputPackageId.empty()
            || !result.m_outputManifestId.empty()
            || !result.m_outputManifestFingerprint.empty()
            || !result.m_lossReportId.empty()
            || !result.m_lossReportFingerprint.empty())
        {
            SetError(
                error,
                "Gate 0 Unity conversion results cannot claim output or loss-report artifacts.");
            return false;
        }
        if (!IsStrictUtcTimestamp(result.m_capturedAtUtc)
            || !ValidateStableIdCollection(result.m_reasonCodes, true))
        {
            SetError(
                error,
                "Unity conversion results require a real UTC capture time and unique stable reason codes.");
            return false;
        }
        if (result.m_buildPerformed || result.m_deploymentPerformed)
        {
            SetError(
                error,
                "Gate 0 Unity conversion results cannot report build or deployment behavior.");
            return false;
        }
        if (!IsSha256Fingerprint(result.m_resultFingerprint)
            || !UnityConversionResultFingerprintMatchesV1(result))
        {
            SetError(
                error,
                "Unity conversion result fingerprint must hash the deterministic Gate 0 result payload.");
            return false;
        }
        return Succeed(error);
    }
} // namespace TaintedGrailModdingSDK
