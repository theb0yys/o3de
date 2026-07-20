/*
 * Copyright (c) Contributors to the Open 3D Engine Project.
 * For complete copyright and license terms please see the LICENSE at the root of this distribution.
 *
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 */

#include "ExternalToolInterchangeCanonical.h"

#include "CanonicalFingerprint.h"
#include "DeterministicContractJson.h"

namespace TaintedGrailModdingSDK
{
    namespace
    {
        namespace Json = DeterministicContractJson;

        AZStd::string SignedString(AZ::s64 value)
        {
            if (value >= 0)
            {
                return Json::UnsignedString(static_cast<AZ::u64>(value));
            }
            const AZ::u64 magnitude =
                static_cast<AZ::u64>(-(value + 1)) + 1;
            return "-" + Json::UnsignedString(magnitude);
        }

        void AppendSigned(
            AZStd::string& output,
            const char* name,
            AZ::s64 value,
            bool comma = true)
        {
            Json::AppendName(output, name);
            output += SignedString(value);
            if (comma)
            {
                output.push_back(',');
            }
        }
    } // namespace

    AZStd::string SerializeCanonicalExternalToolHandoffV1(
        const ExternalToolHandoffV1& handoff)
    {
        AZStd::string output;
        output.push_back('{');
        Json::AppendUnsigned(output, "ContractVersion", handoff.m_contractVersion);
        Json::AppendString(output, "HandoffId", handoff.m_handoffId);
        Json::AppendString(output, "WorkspaceId", handoff.m_workspaceId);
        Json::AppendString(output, "PackId", handoff.m_packId);
        Json::AppendString(output, "ProfileId", handoff.m_profileId);
        Json::AppendString(output, "ProviderId", handoff.m_providerId);
        Json::AppendString(output, "ProviderVersion", handoff.m_providerVersion);
        Json::AppendString(output, "HostApiVersion", handoff.m_hostApiVersion);
        Json::AppendString(output, "ApplicationId", handoff.m_applicationId);
        Json::AppendString(
            output,
            "ApplicationVersion",
            handoff.m_applicationVersion);
        Json::AppendString(output, "ExtensionId", handoff.m_extensionId);
        Json::AppendString(output, "ExtensionVersion", handoff.m_extensionVersion);
        Json::AppendString(
            output,
            "ExtensionRevision",
            handoff.m_extensionRevision);
        Json::AppendString(
            output,
            "ExtensionFingerprint",
            handoff.m_extensionFingerprint);
        Json::AppendString(output, "CommandId", handoff.m_commandId);
        Json::AppendSortedStringArray(
            output,
            "QualificationEvidenceIds",
            handoff.m_qualificationEvidenceIds);
        Json::AppendString(
            output,
            "ToolchainLockFingerprint",
            handoff.m_toolchainLockFingerprint);
        Json::AppendString(
            output,
            "ConfigurationFingerprint",
            handoff.m_configurationFingerprint);
        Json::AppendString(output, "SourcePackageId", handoff.m_sourcePackageId);
        Json::AppendString(output, "SourceManifestId", handoff.m_sourceManifestId);
        Json::AppendString(
            output,
            "SourceManifestFingerprint",
            handoff.m_sourceManifestFingerprint);
        Json::AppendString(output, "StagingRoot", handoff.m_stagingRoot);
        Json::AppendBool(output, "ExecutionAllowed", handoff.m_executionAllowed);
        Json::AppendBool(output, "BuildAllowed", handoff.m_buildAllowed);
        Json::AppendBool(
            output,
            "DeploymentAllowed",
            handoff.m_deploymentAllowed,
            false);
        output.push_back('}');
        return output;
    }

    AZStd::string CalculateExternalToolHandoffFingerprintV1(
        const ExternalToolHandoffV1& handoff)
    {
        return CalculateCanonicalSha256(
            SerializeCanonicalExternalToolHandoffV1(handoff));
    }

    bool ExternalToolHandoffFingerprintMatchesV1(
        const ExternalToolHandoffV1& handoff)
    {
        return handoff.m_handoffFingerprint
            == CalculateExternalToolHandoffFingerprintV1(handoff);
    }

    AZStd::string SerializeCanonicalUnityConversionRequestV1(
        const UnityConversionRequestV1& request)
    {
        AZStd::string output;
        output.push_back('{');
        Json::AppendUnsigned(output, "ContractVersion", request.m_contractVersion);
        Json::AppendString(output, "RequestId", request.m_requestId);
        Json::AppendString(output, "HandoffId", request.m_handoffId);
        Json::AppendString(
            output,
            "HandoffCanonicalJson",
            request.m_handoffCanonicalJson);
        Json::AppendString(
            output,
            "HandoffFingerprint",
            request.m_handoffFingerprint);
        Json::AppendString(output, "Direction", ToString(request.m_direction));
        Json::AppendString(output, "UnityProviderId", request.m_unityProviderId);
        Json::AppendString(output, "UnityEditorId", request.m_unityEditorId);
        Json::AppendString(
            output,
            "UnityEditorVersion",
            request.m_unityEditorVersion);
        Json::AppendString(
            output,
            "UnityExtensionId",
            request.m_unityExtensionId);
        Json::AppendString(
            output,
            "UnityExtensionVersion",
            request.m_unityExtensionVersion);
        Json::AppendString(
            output,
            "UnityExtensionRevision",
            request.m_unityExtensionRevision);
        Json::AppendString(
            output,
            "UnityExtensionFingerprint",
            request.m_unityExtensionFingerprint);
        Json::AppendUnsigned(
            output,
            "InterchangeSchemaVersion",
            request.m_interchangeSchemaVersion);
        Json::AppendString(output, "TestProjectId", request.m_testProjectId);
        Json::AppendString(output, "SourcePackageId", request.m_sourcePackageId);
        Json::AppendString(output, "SourceManifestId", request.m_sourceManifestId);
        Json::AppendString(
            output,
            "SourceManifestFingerprint",
            request.m_sourceManifestFingerprint);
        Json::AppendSortedStringArray(
            output,
            "RequestedAssetIds",
            request.m_requestedAssetIds);
        Json::AppendBool(output, "ExecutionAllowed", request.m_executionAllowed);
        Json::AppendBool(output, "BuildAllowed", request.m_buildAllowed);
        Json::AppendBool(
            output,
            "DeploymentAllowed",
            request.m_deploymentAllowed,
            false);
        output.push_back('}');
        return output;
    }

    AZStd::string CalculateUnityConversionRequestFingerprintV1(
        const UnityConversionRequestV1& request)
    {
        return CalculateCanonicalSha256(
            SerializeCanonicalUnityConversionRequestV1(request));
    }

    bool UnityConversionRequestFingerprintMatchesV1(
        const UnityConversionRequestV1& request)
    {
        return request.m_requestFingerprint
            == CalculateUnityConversionRequestFingerprintV1(request);
    }

    AZStd::string SerializeCanonicalExternalToolExecutionResultV1(
        const ExternalToolExecutionResultV1& result)
    {
        AZStd::string output;
        output.push_back('{');
        Json::AppendUnsigned(output, "ContractVersion", result.m_contractVersion);
        Json::AppendString(output, "ResultId", result.m_resultId);
        Json::AppendString(output, "HandoffId", result.m_handoffId);
        Json::AppendString(
            output,
            "HandoffCanonicalJson",
            result.m_handoffCanonicalJson);
        Json::AppendString(
            output,
            "HandoffFingerprint",
            result.m_handoffFingerprint);
        Json::AppendString(output, "ProviderId", result.m_providerId);
        Json::AppendString(output, "ProviderVersion", result.m_providerVersion);
        Json::AppendString(output, "CommandId", result.m_commandId);
        Json::AppendString(output, "Outcome", ToString(result.m_outcome));
        Json::AppendBool(
            output,
            "ExecutionAttempted",
            result.m_executionAttempted);
        Json::AppendBool(output, "HasExitCode", result.m_hasExitCode);
        AppendSigned(output, "ExitCode", result.m_exitCode);
        Json::AppendString(output, "CapturedAtUtc", result.m_capturedAtUtc);
        Json::AppendString(output, "StartedAtUtc", result.m_startedAtUtc);
        Json::AppendString(output, "CompletedAtUtc", result.m_completedAtUtc);
        Json::AppendString(output, "OutputManifestId", result.m_outputManifestId);
        Json::AppendString(
            output,
            "OutputManifestFingerprint",
            result.m_outputManifestFingerprint);
        Json::AppendSortedStringArray(
            output,
            "ReasonCodes",
            result.m_reasonCodes);
        Json::AppendBool(output, "BuildPerformed", result.m_buildPerformed);
        Json::AppendBool(
            output,
            "DeploymentPerformed",
            result.m_deploymentPerformed,
            false);
        output.push_back('}');
        return output;
    }

    AZStd::string CalculateExternalToolExecutionResultFingerprintV1(
        const ExternalToolExecutionResultV1& result)
    {
        return CalculateCanonicalSha256(
            SerializeCanonicalExternalToolExecutionResultV1(result));
    }

    bool ExternalToolExecutionResultFingerprintMatchesV1(
        const ExternalToolExecutionResultV1& result)
    {
        return result.m_resultFingerprint
            == CalculateExternalToolExecutionResultFingerprintV1(result);
    }

    AZStd::string SerializeCanonicalUnityConversionResultV1(
        const UnityConversionResultV1& result)
    {
        AZStd::string output;
        output.push_back('{');
        Json::AppendUnsigned(output, "ContractVersion", result.m_contractVersion);
        Json::AppendString(output, "ResultId", result.m_resultId);
        Json::AppendString(output, "RequestId", result.m_requestId);
        Json::AppendString(
            output,
            "RequestCanonicalJson",
            result.m_requestCanonicalJson);
        Json::AppendString(
            output,
            "RequestFingerprint",
            result.m_requestFingerprint);
        Json::AppendString(
            output,
            "ExecutionResultId",
            result.m_executionResultId);
        Json::AppendString(
            output,
            "ExecutionResultCanonicalJson",
            result.m_executionResultCanonicalJson);
        Json::AppendString(
            output,
            "ExecutionResultFingerprint",
            result.m_executionResultFingerprint);
        Json::AppendString(output, "Direction", ToString(result.m_direction));
        Json::AppendString(output, "UnityProviderId", result.m_unityProviderId);
        Json::AppendString(
            output,
            "UnityEditorVersion",
            result.m_unityEditorVersion);
        Json::AppendString(
            output,
            "UnityExtensionId",
            result.m_unityExtensionId);
        Json::AppendString(
            output,
            "UnityExtensionVersion",
            result.m_unityExtensionVersion);
        Json::AppendString(output, "Outcome", ToString(result.m_outcome));
        Json::AppendBool(
            output,
            "ConversionAttempted",
            result.m_conversionAttempted);
        Json::AppendBool(output, "ProjectMutated", result.m_projectMutated);
        Json::AppendString(output, "OutputPackageId", result.m_outputPackageId);
        Json::AppendString(output, "OutputManifestId", result.m_outputManifestId);
        Json::AppendString(
            output,
            "OutputManifestFingerprint",
            result.m_outputManifestFingerprint);
        Json::AppendString(output, "LossReportId", result.m_lossReportId);
        Json::AppendString(
            output,
            "LossReportFingerprint",
            result.m_lossReportFingerprint);
        Json::AppendString(output, "CapturedAtUtc", result.m_capturedAtUtc);
        Json::AppendSortedStringArray(
            output,
            "ReasonCodes",
            result.m_reasonCodes);
        Json::AppendBool(output, "BuildPerformed", result.m_buildPerformed);
        Json::AppendBool(
            output,
            "DeploymentPerformed",
            result.m_deploymentPerformed,
            false);
        output.push_back('}');
        return output;
    }

    AZStd::string CalculateUnityConversionResultFingerprintV1(
        const UnityConversionResultV1& result)
    {
        return CalculateCanonicalSha256(
            SerializeCanonicalUnityConversionResultV1(result));
    }

    bool UnityConversionResultFingerprintMatchesV1(
        const UnityConversionResultV1& result)
    {
        return result.m_resultFingerprint
            == CalculateUnityConversionResultFingerprintV1(result);
    }
} // namespace TaintedGrailModdingSDK
