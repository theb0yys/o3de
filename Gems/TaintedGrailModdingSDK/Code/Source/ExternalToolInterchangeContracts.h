/*
 * Copyright (c) Contributors to the Open 3D Engine Project.
 * For complete copyright and license terms please see the LICENSE at the root of this distribution.
 *
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 */

#pragma once

#include <AzCore/base.h>
#include <AzCore/std/containers/vector.h>
#include <AzCore/std/string/string.h>

namespace TaintedGrailModdingSDK
{
    // Gate 0 V1 is permanently inert. The additional outcome vocabulary is
    // reserved for unambiguous parsing and design continuity, but V1 validators
    // accept only not_attempted. Any future executable contract must version
    // forward instead of relaxing these validators.
    enum class UnityConversionDirectionV1 : AZ::u8
    {
        InterchangeToUnity,
        UnityToInterchange,
    };

    enum class ExternalToolExecutionOutcomeV1 : AZ::u8
    {
        NotAttempted,
    };

    enum class UnityConversionOutcomeV1 : AZ::u8
    {
        NotAttempted,
    };

    AZStd::string ToString(UnityConversionDirectionV1 direction);
    AZStd::string ToString(ExternalToolExecutionOutcomeV1 outcome);
    AZStd::string ToString(UnityConversionOutcomeV1 outcome);

    bool TryParseUnityConversionDirectionV1(
        const AZStd::string& value,
        UnityConversionDirectionV1& direction);
    bool TryParseExternalToolExecutionOutcomeV1(
        const AZStd::string& value,
        ExternalToolExecutionOutcomeV1& outcome);
    bool TryParseUnityConversionOutcomeV1(
        const AZStd::string& value,
        UnityConversionOutcomeV1& outcome);

    // Application versions are exact bounded tokens rather than SemVer. This
    // deliberately accepts native versions such as Unity 2022.3.22f1 without
    // permitting whitespace, path separators, or control characters.
    bool IsExternalToolExactVersion(const AZStd::string& value);
    bool IsExternalToolCommandId(const AZStd::string& value);

    struct ExternalToolHandoffV1
    {
        AZ::u32 m_contractVersion = 1;
        AZStd::string m_handoffId;
        AZStd::string m_workspaceId;
        AZStd::string m_packId;
        AZStd::string m_profileId;
        AZStd::string m_providerId;
        AZStd::string m_providerVersion;
        AZStd::string m_hostApiVersion;
        AZStd::string m_applicationId;
        AZStd::string m_applicationVersion;
        AZStd::string m_extensionId;
        AZStd::string m_extensionVersion;
        AZStd::string m_extensionRevision;
        AZStd::string m_extensionFingerprint;
        AZStd::string m_commandId;
        AZStd::vector<AZStd::string> m_qualificationEvidenceIds;
        AZStd::string m_toolchainLockFingerprint;
        AZStd::string m_configurationFingerprint;
        AZStd::string m_sourcePackageId;
        AZStd::string m_sourceManifestId;
        AZStd::string m_sourceManifestFingerprint;
        AZStd::string m_stagingRoot;
        AZStd::string m_handoffFingerprint;
        bool m_executionAllowed = false;
        bool m_buildAllowed = false;
        bool m_deploymentAllowed = false;
    };

    struct UnityConversionRequestV1
    {
        AZ::u32 m_contractVersion = 1;
        AZStd::string m_requestId;
        AZStd::string m_handoffId;
        AZStd::string m_handoffCanonicalJson;
        AZStd::string m_handoffFingerprint;
        UnityConversionDirectionV1 m_direction =
            UnityConversionDirectionV1::InterchangeToUnity;
        AZStd::string m_unityProviderId;
        AZStd::string m_unityEditorId;
        AZStd::string m_unityEditorVersion;
        AZStd::string m_unityExtensionId;
        AZStd::string m_unityExtensionVersion;
        AZStd::string m_unityExtensionRevision;
        AZStd::string m_unityExtensionFingerprint;
        // Gate 5 owns interchange schema selection. Zero remains explicitly
        // unselected for permanently inert Gate 0 V1 requests.
        AZ::u32 m_interchangeSchemaVersion = 0;
        AZStd::string m_testProjectId;
        AZStd::string m_sourcePackageId;
        AZStd::string m_sourceManifestId;
        AZStd::string m_sourceManifestFingerprint;
        AZStd::vector<AZStd::string> m_requestedAssetIds;
        AZStd::string m_requestFingerprint;
        bool m_executionAllowed = false;
        bool m_buildAllowed = false;
        bool m_deploymentAllowed = false;
    };

    struct ExternalToolExecutionResultV1
    {
        AZ::u32 m_contractVersion = 1;
        AZStd::string m_resultId;
        AZStd::string m_handoffId;
        AZStd::string m_handoffCanonicalJson;
        AZStd::string m_handoffFingerprint;
        AZStd::string m_providerId;
        AZStd::string m_providerVersion;
        AZStd::string m_commandId;
        ExternalToolExecutionOutcomeV1 m_outcome =
            ExternalToolExecutionOutcomeV1::NotAttempted;
        bool m_executionAttempted = false;
        bool m_hasExitCode = false;
        AZ::s64 m_exitCode = 0;
        AZStd::string m_capturedAtUtc;
        AZStd::string m_startedAtUtc;
        AZStd::string m_completedAtUtc;
        AZStd::string m_outputManifestId;
        AZStd::string m_outputManifestFingerprint;
        AZStd::vector<AZStd::string> m_reasonCodes;
        AZStd::string m_resultFingerprint;
        bool m_buildPerformed = false;
        bool m_deploymentPerformed = false;
    };

    struct UnityConversionResultV1
    {
        AZ::u32 m_contractVersion = 1;
        AZStd::string m_resultId;
        AZStd::string m_requestId;
        AZStd::string m_requestCanonicalJson;
        AZStd::string m_requestFingerprint;
        AZStd::string m_executionResultId;
        AZStd::string m_executionResultCanonicalJson;
        AZStd::string m_executionResultFingerprint;
        UnityConversionDirectionV1 m_direction =
            UnityConversionDirectionV1::InterchangeToUnity;
        AZStd::string m_unityProviderId;
        AZStd::string m_unityEditorVersion;
        AZStd::string m_unityExtensionId;
        AZStd::string m_unityExtensionVersion;
        UnityConversionOutcomeV1 m_outcome =
            UnityConversionOutcomeV1::NotAttempted;
        bool m_conversionAttempted = false;
        bool m_projectMutated = false;
        AZStd::string m_outputPackageId;
        AZStd::string m_outputManifestId;
        AZStd::string m_outputManifestFingerprint;
        AZStd::string m_lossReportId;
        AZStd::string m_lossReportFingerprint;
        AZStd::string m_capturedAtUtc;
        AZStd::vector<AZStd::string> m_reasonCodes;
        AZStd::string m_resultFingerprint;
        bool m_buildPerformed = false;
        bool m_deploymentPerformed = false;
    };

    bool ValidateExternalToolHandoffV1(
        const ExternalToolHandoffV1& handoff,
        AZStd::string* error = nullptr);

    bool ValidateUnityConversionRequestV1(
        const ExternalToolHandoffV1& handoff,
        const UnityConversionRequestV1& request,
        AZStd::string* error = nullptr);

    bool ValidateExternalToolExecutionResultV1(
        const ExternalToolHandoffV1& handoff,
        const ExternalToolExecutionResultV1& result,
        AZStd::string* error = nullptr);

    bool ValidateUnityConversionResultV1(
        const ExternalToolHandoffV1& handoff,
        const UnityConversionRequestV1& request,
        const ExternalToolExecutionResultV1& executionResult,
        const UnityConversionResultV1& result,
        AZStd::string* error = nullptr);
} // namespace TaintedGrailModdingSDK
