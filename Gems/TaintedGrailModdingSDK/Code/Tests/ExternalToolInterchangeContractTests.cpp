/*
 * Copyright (c) Contributors to the Open 3D Engine Project.
 * For complete copyright and license terms please see the LICENSE at the root of this distribution.
 *
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 */

#include "ExternalToolInterchangeCanonical.h"
#include "ExternalToolInterchangeContracts.h"

#include <AzTest/AzTest.h>

#include <AzCore/std/algorithm.h>

namespace TaintedGrailModdingSDK
{
    namespace
    {
        AZStd::string Fingerprint(char value)
        {
            return "sha256:" + AZStd::string(64, value);
        }

        ExternalToolHandoffV1 MakeHandoff()
        {
            ExternalToolHandoffV1 handoff;
            handoff.m_handoffId = "handoff.unity.synthetic";
            handoff.m_workspaceId = "workspace.synthetic";
            handoff.m_packId = "pack.synthetic";
            handoff.m_profileId = "profile.unity.synthetic";
            handoff.m_providerId = "provider.unity.synthetic";
            handoff.m_providerVersion = "0.1.0";
            handoff.m_hostApiVersion = "1.1.0";
            handoff.m_applicationId = "unity.editor";
            handoff.m_applicationVersion = "2022.3.22f1";
            handoff.m_extensionId = "extension.unity.synthetic";
            handoff.m_extensionVersion = "0.1.0";
            handoff.m_extensionRevision = "abcdef1";
            handoff.m_extensionFingerprint = Fingerprint('a');
            handoff.m_commandId = "convert-interchange";
            handoff.m_qualificationEvidenceIds = {
                "evidence.unity.fixture",
                "evidence.unity.license",
            };
            handoff.m_toolchainLockFingerprint = Fingerprint('b');
            handoff.m_configurationFingerprint = Fingerprint('c');
            handoff.m_sourcePackageId = "package.synthetic.scene";
            handoff.m_sourceManifestId = "manifest.synthetic.scene";
            handoff.m_sourceManifestFingerprint = Fingerprint('d');
            handoff.m_stagingRoot = "staging/unity";
            handoff.m_handoffFingerprint =
                CalculateExternalToolHandoffFingerprintV1(handoff);
            return handoff;
        }

        UnityConversionRequestV1 MakeRequest(
            const ExternalToolHandoffV1& handoff)
        {
            UnityConversionRequestV1 request;
            request.m_requestId = "request.unity.synthetic";
            request.m_handoffId = handoff.m_handoffId;
            request.m_handoffCanonicalJson =
                SerializeCanonicalExternalToolHandoffV1(handoff);
            request.m_handoffFingerprint = handoff.m_handoffFingerprint;
            request.m_direction =
                UnityConversionDirectionV1::InterchangeToUnity;
            request.m_unityProviderId = handoff.m_providerId;
            request.m_unityEditorId = handoff.m_applicationId;
            request.m_unityEditorVersion = handoff.m_applicationVersion;
            request.m_unityExtensionId = handoff.m_extensionId;
            request.m_unityExtensionVersion = handoff.m_extensionVersion;
            request.m_unityExtensionRevision = handoff.m_extensionRevision;
            request.m_unityExtensionFingerprint =
                handoff.m_extensionFingerprint;
            request.m_testProjectId = "project.unity.synthetic";
            request.m_sourcePackageId = handoff.m_sourcePackageId;
            request.m_sourceManifestId = handoff.m_sourceManifestId;
            request.m_sourceManifestFingerprint =
                handoff.m_sourceManifestFingerprint;
            request.m_requestedAssetIds = {
                "asset.synthetic.material",
                "asset.synthetic.mesh",
            };
            request.m_requestFingerprint =
                CalculateUnityConversionRequestFingerprintV1(request);
            return request;
        }

        ExternalToolExecutionResultV1 MakeExecutionResult(
            const ExternalToolHandoffV1& handoff)
        {
            ExternalToolExecutionResultV1 result;
            result.m_resultId = "result.external-tool.synthetic";
            result.m_handoffId = handoff.m_handoffId;
            result.m_handoffCanonicalJson =
                SerializeCanonicalExternalToolHandoffV1(handoff);
            result.m_handoffFingerprint = handoff.m_handoffFingerprint;
            result.m_providerId = handoff.m_providerId;
            result.m_providerVersion = handoff.m_providerVersion;
            result.m_commandId = handoff.m_commandId;
            result.m_capturedAtUtc = "2026-07-20T12:00:00Z";
            result.m_reasonCodes = { "external_tool.gate_zero_disabled" };
            result.m_resultFingerprint =
                CalculateExternalToolExecutionResultFingerprintV1(result);
            return result;
        }

        UnityConversionResultV1 MakeConversionResult(
            const UnityConversionRequestV1& request,
            const ExternalToolExecutionResultV1& executionResult)
        {
            UnityConversionResultV1 result;
            result.m_resultId = "result.unity-conversion.synthetic";
            result.m_requestId = request.m_requestId;
            result.m_requestCanonicalJson =
                SerializeCanonicalUnityConversionRequestV1(request);
            result.m_requestFingerprint = request.m_requestFingerprint;
            result.m_executionResultId = executionResult.m_resultId;
            result.m_executionResultCanonicalJson =
                SerializeCanonicalExternalToolExecutionResultV1(
                    executionResult);
            result.m_executionResultFingerprint =
                executionResult.m_resultFingerprint;
            result.m_direction = request.m_direction;
            result.m_unityProviderId = request.m_unityProviderId;
            result.m_unityEditorVersion = request.m_unityEditorVersion;
            result.m_unityExtensionId = request.m_unityExtensionId;
            result.m_unityExtensionVersion =
                request.m_unityExtensionVersion;
            result.m_capturedAtUtc = "2026-07-20T12:00:01Z";
            result.m_reasonCodes = { "unity_conversion.gate_zero_disabled" };
            result.m_resultFingerprint =
                CalculateUnityConversionResultFingerprintV1(result);
            return result;
        }
    } // namespace

    TEST(
        ExternalToolInterchangeContractTests,
        TypedVocabulariesRejectUnknownValuesAndAcceptNativeUnityVersions)
    {
        UnityConversionDirectionV1 direction;
        ExternalToolExecutionOutcomeV1 executionOutcome;
        UnityConversionOutcomeV1 conversionOutcome;

        EXPECT_TRUE(TryParseUnityConversionDirectionV1(
            "interchange_to_unity",
            direction));
        EXPECT_TRUE(TryParseUnityConversionDirectionV1(
            "unity_to_interchange",
            direction));
        EXPECT_FALSE(TryParseUnityConversionDirectionV1("import", direction));
        EXPECT_TRUE(TryParseExternalToolExecutionOutcomeV1(
            "not_attempted",
            executionOutcome));
        EXPECT_FALSE(TryParseExternalToolExecutionOutcomeV1(
            "timed_out",
            executionOutcome));
        EXPECT_FALSE(TryParseExternalToolExecutionOutcomeV1(
            "timeout",
            executionOutcome));
        EXPECT_FALSE(TryParseUnityConversionOutcomeV1(
            "succeeded_with_losses",
            conversionOutcome));
        EXPECT_FALSE(TryParseUnityConversionOutcomeV1(
            "partial",
            conversionOutcome));

        EXPECT_TRUE(IsExternalToolExactVersion("2022.3.22f1"));
        EXPECT_TRUE(IsExternalToolExactVersion("4.2.0-alpha+build1"));
        EXPECT_FALSE(IsExternalToolExactVersion("2022.3.22 f1"));
        EXPECT_FALSE(IsExternalToolExactVersion("../2022.3.22f1"));
        EXPECT_TRUE(IsExternalToolCommandId("convert-interchange"));
        EXPECT_FALSE(IsExternalToolCommandId("Convert Interchange"));
    }

    TEST(
        ExternalToolInterchangeContractTests,
        CompleteGateZeroChainIsValidWhileAllAuthorityRemainsFalse)
    {
        const ExternalToolHandoffV1 handoff = MakeHandoff();
        const UnityConversionRequestV1 request = MakeRequest(handoff);
        const ExternalToolExecutionResultV1 executionResult =
            MakeExecutionResult(handoff);
        const UnityConversionResultV1 conversionResult =
            MakeConversionResult(request, executionResult);
        AZStd::string error = "stale";

        EXPECT_TRUE(ValidateExternalToolHandoffV1(handoff, &error))
            << error.c_str();
        EXPECT_TRUE(error.empty());
        EXPECT_TRUE(ValidateUnityConversionRequestV1(
            handoff,
            request,
            &error)) << error.c_str();
        EXPECT_TRUE(ValidateExternalToolExecutionResultV1(
            handoff,
            executionResult,
            &error)) << error.c_str();
        EXPECT_TRUE(ValidateUnityConversionResultV1(
            handoff,
            request,
            executionResult,
            conversionResult,
            &error)) << error.c_str();

        EXPECT_FALSE(handoff.m_executionAllowed);
        EXPECT_FALSE(handoff.m_buildAllowed);
        EXPECT_FALSE(handoff.m_deploymentAllowed);
        EXPECT_FALSE(request.m_executionAllowed);
        EXPECT_FALSE(executionResult.m_executionAttempted);
        EXPECT_FALSE(conversionResult.m_conversionAttempted);
        EXPECT_FALSE(conversionResult.m_projectMutated);
        EXPECT_FALSE(conversionResult.m_buildPerformed);
        EXPECT_FALSE(conversionResult.m_deploymentPerformed);
    }

    TEST(
        ExternalToolInterchangeContractTests,
        CanonicalGateZeroChainMatchesGoldenV1Vectors)
    {
        const ExternalToolHandoffV1 handoff = MakeHandoff();
        const UnityConversionRequestV1 request = MakeRequest(handoff);
        const ExternalToolExecutionResultV1 executionResult =
            MakeExecutionResult(handoff);
        const UnityConversionResultV1 conversionResult =
            MakeConversionResult(request, executionResult);
        const AZStd::string expectedHandoff =
            "{\"ContractVersion\":1,\"HandoffId\":\"handoff.unity.synthetic\","
            "\"WorkspaceId\":\"workspace.synthetic\",\"PackId\":\"pack.synthetic\","
            "\"ProfileId\":\"profile.unity.synthetic\","
            "\"ProviderId\":\"provider.unity.synthetic\","
            "\"ProviderVersion\":\"0.1.0\",\"HostApiVersion\":\"1.1.0\","
            "\"ApplicationId\":\"unity.editor\","
            "\"ApplicationVersion\":\"2022.3.22f1\","
            "\"ExtensionId\":\"extension.unity.synthetic\","
            "\"ExtensionVersion\":\"0.1.0\","
            "\"ExtensionRevision\":\"abcdef1\","
            "\"ExtensionFingerprint\":\"sha256:"
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\","
            "\"CommandId\":\"convert-interchange\","
            "\"QualificationEvidenceIds\":[\"evidence.unity.fixture\","
            "\"evidence.unity.license\"],\"ToolchainLockFingerprint\":\"sha256:"
            "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb\","
            "\"ConfigurationFingerprint\":\"sha256:"
            "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc\","
            "\"SourcePackageId\":\"package.synthetic.scene\","
            "\"SourceManifestId\":\"manifest.synthetic.scene\","
            "\"SourceManifestFingerprint\":\"sha256:"
            "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd\","
            "\"StagingRoot\":\"staging/unity\",\"ExecutionAllowed\":false,"
            "\"BuildAllowed\":false,\"DeploymentAllowed\":false}";

        EXPECT_EQ(
            SerializeCanonicalExternalToolHandoffV1(handoff),
            expectedHandoff);
        EXPECT_EQ(
            handoff.m_handoffFingerprint,
            "sha256:e235dc035c2fb3c822f542c0e35d6b714e30bd2b5b9901d56cfb9a777dd02088");
        EXPECT_EQ(
            request.m_requestFingerprint,
            "sha256:5b458fa29e43c5e6d3239aebb4d10adde2502c7fb3c3f9cc0ed3244f85ab591a");
        EXPECT_EQ(
            executionResult.m_resultFingerprint,
            "sha256:ca4f3c273e7ae41038035d1afd064c6829338ecc01e2a677f86536dac23c1f69");
        EXPECT_EQ(
            conversionResult.m_resultFingerprint,
            "sha256:64612cbb87334129653b04f29c669ba6fbf629eb8c2b28601513de6cfc096f53");
    }

    TEST(
        ExternalToolInterchangeContractTests,
        FutureGateBindingsMayRemainUnselected)
    {
        ExternalToolHandoffV1 handoff = MakeHandoff();
        handoff.m_sourceManifestFingerprint.clear();
        handoff.m_handoffFingerprint =
            CalculateExternalToolHandoffFingerprintV1(handoff);
        AZStd::string error;
        EXPECT_FALSE(ValidateExternalToolHandoffV1(handoff, &error));
        EXPECT_NE(error.find("absent or complete"), AZStd::string::npos);

        handoff = MakeHandoff();
        handoff.m_qualificationEvidenceIds.clear();
        handoff.m_sourcePackageId.clear();
        handoff.m_sourceManifestId.clear();
        handoff.m_sourceManifestFingerprint.clear();
        handoff.m_handoffFingerprint =
            CalculateExternalToolHandoffFingerprintV1(handoff);

        EXPECT_TRUE(ValidateExternalToolHandoffV1(handoff, &error))
            << error.c_str();

        UnityConversionRequestV1 request = MakeRequest(handoff);
        request.m_requestedAssetIds.clear();
        request.m_requestFingerprint =
            CalculateUnityConversionRequestFingerprintV1(request);
        EXPECT_EQ(request.m_interchangeSchemaVersion, 0);
        EXPECT_TRUE(ValidateUnityConversionRequestV1(
            handoff,
            request,
            &error)) << error.c_str();
    }

    TEST(
        ExternalToolInterchangeContractTests,
        AuthorityExecutionAndMutationClaimsFailClosed)
    {
        AZStd::string error;
        ExternalToolHandoffV1 handoff = MakeHandoff();
        handoff.m_executionAllowed = true;
        handoff.m_handoffFingerprint =
            CalculateExternalToolHandoffFingerprintV1(handoff);
        EXPECT_FALSE(ValidateExternalToolHandoffV1(handoff, &error));
        EXPECT_NE(error.find("never authorize"), AZStd::string::npos);

        handoff = MakeHandoff();
        UnityConversionRequestV1 request = MakeRequest(handoff);
        request.m_buildAllowed = true;
        request.m_requestFingerprint =
            CalculateUnityConversionRequestFingerprintV1(request);
        EXPECT_FALSE(ValidateUnityConversionRequestV1(
            handoff,
            request,
            &error));

        request = MakeRequest(handoff);
        ExternalToolExecutionResultV1 executionResult =
            MakeExecutionResult(handoff);
        executionResult.m_outcome =
            static_cast<ExternalToolExecutionOutcomeV1>(1);
        executionResult.m_executionAttempted = true;
        executionResult.m_hasExitCode = true;
        executionResult.m_startedAtUtc = "2026-07-20T12:00:00Z";
        executionResult.m_completedAtUtc = "2026-07-20T12:00:01Z";
        executionResult.m_resultFingerprint =
            CalculateExternalToolExecutionResultFingerprintV1(executionResult);
        EXPECT_FALSE(ValidateExternalToolExecutionResultV1(
            handoff,
            executionResult,
            &error));
        EXPECT_NE(error.find("not_attempted"), AZStd::string::npos);

        request = MakeRequest(handoff);
        executionResult = MakeExecutionResult(handoff);
        UnityConversionResultV1 conversionResult =
            MakeConversionResult(request, executionResult);
        conversionResult.m_projectMutated = true;
        conversionResult.m_resultFingerprint =
            CalculateUnityConversionResultFingerprintV1(conversionResult);
        EXPECT_FALSE(ValidateUnityConversionResultV1(
            handoff,
            request,
            executionResult,
            conversionResult,
            &error));
        EXPECT_NE(error.find("cannot mutate"), AZStd::string::npos);
    }

    TEST(
        ExternalToolInterchangeContractTests,
        EveryPerformedAndOutputClaimIsRejected)
    {
        const ExternalToolHandoffV1 handoff = MakeHandoff();
        const UnityConversionRequestV1 baseRequest = MakeRequest(handoff);
        const ExternalToolExecutionResultV1 baseExecutionResult =
            MakeExecutionResult(handoff);
        AZStd::string error;

        auto requestFails = [&](UnityConversionRequestV1 candidate)
        {
            candidate.m_requestFingerprint =
                CalculateUnityConversionRequestFingerprintV1(candidate);
            EXPECT_FALSE(ValidateUnityConversionRequestV1(
                handoff,
                candidate,
                &error));
        };
        UnityConversionRequestV1 request = baseRequest;
        request.m_executionAllowed = true;
        requestFails(request);
        request = baseRequest;
        request.m_buildAllowed = true;
        requestFails(request);
        request = baseRequest;
        request.m_deploymentAllowed = true;
        requestFails(request);

        auto executionFails = [&](ExternalToolExecutionResultV1 candidate)
        {
            candidate.m_resultFingerprint =
                CalculateExternalToolExecutionResultFingerprintV1(candidate);
            EXPECT_FALSE(ValidateExternalToolExecutionResultV1(
                handoff,
                candidate,
                &error));
        };
        ExternalToolExecutionResultV1 executionResult = baseExecutionResult;
        executionResult.m_buildPerformed = true;
        executionFails(executionResult);
        executionResult = baseExecutionResult;
        executionResult.m_deploymentPerformed = true;
        executionFails(executionResult);
        executionResult = baseExecutionResult;
        executionResult.m_outputManifestId = "manifest.unexpected.output";
        executionResult.m_outputManifestFingerprint = Fingerprint('e');
        executionFails(executionResult);

        auto conversionFails = [&](UnityConversionResultV1 candidate)
        {
            candidate.m_resultFingerprint =
                CalculateUnityConversionResultFingerprintV1(candidate);
            EXPECT_FALSE(ValidateUnityConversionResultV1(
                handoff,
                baseRequest,
                baseExecutionResult,
                candidate,
                &error));
        };
        const UnityConversionResultV1 baseConversionResult =
            MakeConversionResult(baseRequest, baseExecutionResult);
        UnityConversionResultV1 conversionResult = baseConversionResult;
        conversionResult.m_conversionAttempted = true;
        conversionFails(conversionResult);
        conversionResult = baseConversionResult;
        conversionResult.m_projectMutated = true;
        conversionFails(conversionResult);
        conversionResult = baseConversionResult;
        conversionResult.m_buildPerformed = true;
        conversionFails(conversionResult);
        conversionResult = baseConversionResult;
        conversionResult.m_deploymentPerformed = true;
        conversionFails(conversionResult);
        conversionResult = baseConversionResult;
        conversionResult.m_outputPackageId = "package.unexpected.output";
        conversionFails(conversionResult);
        conversionResult = baseConversionResult;
        conversionResult.m_lossReportId = "loss.unexpected.output";
        conversionResult.m_lossReportFingerprint = Fingerprint('f');
        conversionFails(conversionResult);
    }

    TEST(
        ExternalToolInterchangeContractTests,
        ExactCanonicalUpstreamBindingsAreRequired)
    {
        const ExternalToolHandoffV1 handoff = MakeHandoff();
        AZStd::string error;
        UnityConversionRequestV1 request = MakeRequest(handoff);
        request.m_handoffCanonicalJson += " ";
        request.m_requestFingerprint =
            CalculateUnityConversionRequestFingerprintV1(request);
        EXPECT_FALSE(ValidateUnityConversionRequestV1(
            handoff,
            request,
            &error));
        EXPECT_NE(error.find("exact canonical handoff"), AZStd::string::npos);

        request = MakeRequest(handoff);
        request.m_unityProviderId = "provider.unity.other";
        request.m_requestFingerprint =
            CalculateUnityConversionRequestFingerprintV1(request);
        EXPECT_FALSE(ValidateUnityConversionRequestV1(
            handoff,
            request,
            &error));
        EXPECT_NE(error.find("exact provider"), AZStd::string::npos);

        request = MakeRequest(handoff);
        const ExternalToolExecutionResultV1 executionResult =
            MakeExecutionResult(handoff);
        UnityConversionResultV1 conversionResult =
            MakeConversionResult(request, executionResult);
        conversionResult.m_requestFingerprint = Fingerprint('e');
        conversionResult.m_resultFingerprint =
            CalculateUnityConversionResultFingerprintV1(conversionResult);
        EXPECT_FALSE(ValidateUnityConversionResultV1(
            handoff,
            request,
            executionResult,
            conversionResult,
            &error));
        EXPECT_NE(error.find("exact canonical request"), AZStd::string::npos);
    }

    TEST(
        ExternalToolInterchangeContractTests,
        CallerSelectedAndStaleFingerprintsFailClosed)
    {
        AZStd::string error;
        ExternalToolHandoffV1 handoff = MakeHandoff();
        handoff.m_handoffFingerprint = Fingerprint('f');
        EXPECT_FALSE(ValidateExternalToolHandoffV1(handoff, &error));
        EXPECT_NE(error.find("deterministic"), AZStd::string::npos);

        handoff = MakeHandoff();
        UnityConversionRequestV1 request = MakeRequest(handoff);
        request.m_requestedAssetIds.push_back("asset.synthetic.texture");
        EXPECT_FALSE(ValidateUnityConversionRequestV1(
            handoff,
            request,
            &error));
        EXPECT_NE(error.find("deterministic"), AZStd::string::npos);

        ExternalToolExecutionResultV1 executionResult =
            MakeExecutionResult(handoff);
        executionResult.m_reasonCodes.push_back(
            "external_tool.additional_reason");
        EXPECT_FALSE(ValidateExternalToolExecutionResultV1(
            handoff,
            executionResult,
            &error));
        EXPECT_NE(error.find("deterministic"), AZStd::string::npos);

        request = MakeRequest(handoff);
        executionResult = MakeExecutionResult(handoff);
        UnityConversionResultV1 conversionResult =
            MakeConversionResult(request, executionResult);
        conversionResult.m_reasonCodes.push_back(
            "unity_conversion.additional_reason");
        EXPECT_FALSE(ValidateUnityConversionResultV1(
            handoff,
            request,
            executionResult,
            conversionResult,
            &error));
        EXPECT_NE(error.find("deterministic"), AZStd::string::npos);
    }

    TEST(
        ExternalToolInterchangeContractTests,
        UnsafePathsDuplicateIdsAndClaimedOutputsFailClosed)
    {
        AZStd::string error;
        for (const char* unsafeRoot : {
                 "../outside",
                 "C:/outside",
                 "staging/CON/file",
             })
        {
            ExternalToolHandoffV1 unsafe = MakeHandoff();
            unsafe.m_stagingRoot = unsafeRoot;
            unsafe.m_handoffFingerprint =
                CalculateExternalToolHandoffFingerprintV1(unsafe);
            EXPECT_FALSE(ValidateExternalToolHandoffV1(unsafe, &error))
                << unsafeRoot;
            EXPECT_NE(error.find("package-relative"), AZStd::string::npos)
                << unsafeRoot;
        }

        ExternalToolHandoffV1 handoff = MakeHandoff();
        handoff.m_qualificationEvidenceIds.push_back(
            handoff.m_qualificationEvidenceIds.front());
        handoff.m_handoffFingerprint =
            CalculateExternalToolHandoffFingerprintV1(handoff);
        EXPECT_FALSE(ValidateExternalToolHandoffV1(handoff, &error));
        EXPECT_NE(error.find("unique"), AZStd::string::npos);

        handoff = MakeHandoff();
        UnityConversionRequestV1 request = MakeRequest(handoff);
        request.m_requestedAssetIds.push_back(
            request.m_requestedAssetIds.front());
        request.m_requestFingerprint =
            CalculateUnityConversionRequestFingerprintV1(request);
        EXPECT_FALSE(ValidateUnityConversionRequestV1(
            handoff,
            request,
            &error));

        request = MakeRequest(handoff);
        request.m_requestedAssetIds.clear();
        for (size_t index = 0; index < 257; ++index)
        {
            request.m_requestedAssetIds.push_back(
                AZStd::string::format("asset.synthetic.%zu", index));
        }
        request.m_requestFingerprint =
            CalculateUnityConversionRequestFingerprintV1(request);
        EXPECT_FALSE(ValidateUnityConversionRequestV1(
            handoff,
            request,
            &error));
        EXPECT_NE(error.find("bounded"), AZStd::string::npos);

        ExternalToolExecutionResultV1 executionResult =
            MakeExecutionResult(handoff);
        executionResult.m_outputManifestId = "manifest.unexpected.output";
        executionResult.m_outputManifestFingerprint = Fingerprint('e');
        executionResult.m_resultFingerprint =
            CalculateExternalToolExecutionResultFingerprintV1(executionResult);
        EXPECT_FALSE(ValidateExternalToolExecutionResultV1(
            handoff,
            executionResult,
            &error));
        EXPECT_NE(error.find("cannot claim"), AZStd::string::npos);
    }

    TEST(
        ExternalToolInterchangeContractTests,
        CanonicalSerializationIsOrderIndependentAndContentSensitive)
    {
        const ExternalToolHandoffV1 handoff = MakeHandoff();
        ExternalToolHandoffV1 reordered = handoff;
        AZStd::reverse(
            reordered.m_qualificationEvidenceIds.begin(),
            reordered.m_qualificationEvidenceIds.end());
        EXPECT_EQ(
            SerializeCanonicalExternalToolHandoffV1(handoff),
            SerializeCanonicalExternalToolHandoffV1(reordered));

        const UnityConversionRequestV1 request = MakeRequest(handoff);
        UnityConversionRequestV1 reorderedRequest = request;
        AZStd::reverse(
            reorderedRequest.m_requestedAssetIds.begin(),
            reorderedRequest.m_requestedAssetIds.end());
        EXPECT_EQ(
            SerializeCanonicalUnityConversionRequestV1(request),
            SerializeCanonicalUnityConversionRequestV1(reorderedRequest));

        reorderedRequest.m_unityEditorVersion = "2022.3.23f1";
        EXPECT_NE(
            SerializeCanonicalUnityConversionRequestV1(request),
            SerializeCanonicalUnityConversionRequestV1(reorderedRequest));
    }

    TEST(
        ExternalToolInterchangeContractTests,
        ValidationDoesNotMutateInputsAndRejectsImpossibleUtcDates)
    {
        const ExternalToolHandoffV1 handoff = MakeHandoff();
        const UnityConversionRequestV1 request = MakeRequest(handoff);
        ExternalToolExecutionResultV1 executionResult =
            MakeExecutionResult(handoff);
        const AZStd::vector<AZStd::string> originalEvidence =
            handoff.m_qualificationEvidenceIds;
        const AZStd::vector<AZStd::string> originalAssets =
            request.m_requestedAssetIds;
        AZStd::string error;

        EXPECT_TRUE(ValidateExternalToolHandoffV1(handoff, &error));
        EXPECT_TRUE(ValidateUnityConversionRequestV1(
            handoff,
            request,
            &error));
        EXPECT_EQ(handoff.m_qualificationEvidenceIds, originalEvidence);
        EXPECT_EQ(request.m_requestedAssetIds, originalAssets);

        executionResult.m_capturedAtUtc = "2026-02-31T12:00:00Z";
        executionResult.m_resultFingerprint =
            CalculateExternalToolExecutionResultFingerprintV1(executionResult);
        EXPECT_FALSE(ValidateExternalToolExecutionResultV1(
            handoff,
            executionResult,
            &error));
        EXPECT_NE(error.find("UTC capture time"), AZStd::string::npos);
    }
} // namespace TaintedGrailModdingSDK
