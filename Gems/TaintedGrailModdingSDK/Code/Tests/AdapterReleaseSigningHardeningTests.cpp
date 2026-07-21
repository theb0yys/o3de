/*
 * Copyright (c) Contributors to the Open 3D Engine Project.
 * For complete copyright and license terms please see the LICENSE at the root of this distribution.
 *
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 */

#include "AdapterReleaseSigningEvidenceService.h"
#include "AdapterReleaseSigningHardening.h"
#include "CanonicalFingerprint.h"

#include <AzTest/AzTest.h>

namespace TaintedGrailModdingSDK
{
    namespace
    {
        AZStd::string Fingerprint(char digit)
        {
            return "sha256:" + AZStd::string(64, digit);
        }

        AdapterReleaseArtifactEnvelope BuildReadyArtifact()
        {
            AdapterReleaseArtifactEnvelope artifact;
            artifact.m_artifactId = "release.artifact.signing.hardening";
            artifact.m_reconciliationId = "reconciliation.signing.hardening";
            artifact.m_packagePreviewId = "package.preview.signing.hardening";
            artifact.m_manifestId = "manifest.signing.hardening";
            artifact.m_manifestFingerprint = Fingerprint('1');
            artifact.m_packId = "pack.signing.hardening";
            artifact.m_packVersion = "1.0.0";
            artifact.m_profileId = "profile.signing.hardening";
            artifact.m_gameVersion = "1.0.0";
            artifact.m_branch = "stable";
            artifact.m_runtimeTarget = "Mono";
            artifact.m_status = AdapterReleaseArtifactEnvelopeStatus::Ready;
            artifact.m_metadataReady = true;
            artifact.m_canonicalJson =
                "{\"ArtifactId\":\"release.artifact.signing.hardening\","
                "\"ContractVersion\":1}";

            AdapterReleaseArtifactContent content;
            content.m_contentId = "content.signing.hardening";
            content.m_packagePath = "package/content.bin";
            content.m_expectedChecksum = Fingerprint('2');
            artifact.m_contents.push_back(content);
            artifact.m_contentCount = 1;

            artifact.m_signingIntent.m_intentId =
                "signing.intent.hardening";
            artifact.m_signingIntent.m_decision =
                AdapterReleaseSigningIntentDecision::SignExternally;
            artifact.m_signingIntent.m_identityKind =
                AdapterReleaseSigningIdentityKind::Pgp;
            artifact.m_signingIntent.m_signerId =
                "signer.release.hardening";
            artifact.m_signingIntent.m_identityLocator =
                "signing-identities/release-hardening";
            artifact.m_signingIntent.m_identityFingerprint = Fingerprint('3');
            artifact.m_signingIntent.m_reviewer = "release-reviewer";
            artifact.m_signingIntent.m_evidenceIds = {
                "evidence.signing.intent.hardening",
            };
            artifact.m_signingIntent.m_reviewedAtUtc =
                "2026-07-20T10:00:00Z";
            return artifact;
        }

        AdapterReleaseAssemblyResultEnvelope BuildAssemblyResult(
            const AdapterReleaseArtifactEnvelope& artifact)
        {
            AdapterReleaseAssemblyResultEnvelope envelope;
            envelope.m_resultId = "release.assembly.signing.hardening";
            envelope.m_artifactId = artifact.m_artifactId;
            envelope.m_artifactCanonicalJson = artifact.m_canonicalJson;
            envelope.m_artifactFingerprint =
                CalculateCanonicalSha256(artifact.m_canonicalJson);
            envelope.m_reconciliationId = artifact.m_reconciliationId;
            envelope.m_packagePreviewId = artifact.m_packagePreviewId;
            envelope.m_manifestId = artifact.m_manifestId;
            envelope.m_manifestFingerprint = artifact.m_manifestFingerprint;
            envelope.m_packId = artifact.m_packId;
            envelope.m_packVersion = artifact.m_packVersion;
            envelope.m_profileId = artifact.m_profileId;
            envelope.m_gameVersion = artifact.m_gameVersion;
            envelope.m_branch = artifact.m_branch;
            envelope.m_runtimeTarget = artifact.m_runtimeTarget;
            envelope.m_capturedAtUtc = "2026-07-20T11:45:00Z";
            envelope.m_resultFingerprint = Fingerprint('4');

            envelope.m_assemblerReview.m_reviewId =
                "review.assembler.signing.hardening";
            envelope.m_assemblerReview.m_assemblerId =
                "assembler.external.signing.hardening";
            envelope.m_assemblerReview.m_assemblerVersion = "1.0.0";
            envelope.m_assemblerReview.m_assemblerFingerprint = Fingerprint('5');
            envelope.m_assemblerReview.m_decision =
                AdapterReleaseAssemblerReviewDecision::Accepted;
            envelope.m_assemblerReview.m_reviewer = "assembly-reviewer";
            envelope.m_assemblerReview.m_capabilities = {
                AdapterReleaseAssemblerCapability::ContentChecksum,
                AdapterReleaseAssemblerCapability::ArchiveAssembly,
                AdapterReleaseAssemblerCapability::ArchiveChecksum,
            };
            envelope.m_assemblerReview.m_evidenceIds = {
                "evidence.assembler.review.hardening",
            };
            envelope.m_assemblerReview.m_reviewedAtUtc =
                "2026-07-20T10:30:00Z";

            envelope.m_archive.m_archiveId =
                "archive.release.signing.hardening";
            envelope.m_archive.m_archivePath =
                "archives/release-signing-hardening.zip";
            envelope.m_archive.m_archiveFormat = "zip";
            envelope.m_archive.m_outcome =
                AdapterReleaseAssemblyOutcome::Succeeded;
            envelope.m_archive.m_attempted = true;
            envelope.m_archive.m_archivePresent = true;
            envelope.m_archive.m_byteSize = 4096;
            envelope.m_archive.m_archiveFingerprint = Fingerprint('6');
            envelope.m_archive.m_completedAtUtc =
                "2026-07-20T11:30:00Z";

            AdapterReleaseChecksumObservation observation;
            observation.m_observationId =
                "observation.signing.content.hardening";
            observation.m_contentId = artifact.m_contents[0].m_contentId;
            observation.m_packagePath = artifact.m_contents[0].m_packagePath;
            observation.m_expectedChecksum =
                artifact.m_contents[0].m_expectedChecksum;
            observation.m_observedChecksum =
                artifact.m_contents[0].m_expectedChecksum;
            observation.m_attempted = true;
            observation.m_observationRecorded = true;
            observation.m_outcome =
                AdapterReleaseChecksumObservationOutcome::Matched;
            observation.m_observedAtUtc = "2026-07-20T11:15:00Z";
            envelope.m_checksumObservations.push_back(observation);
            return envelope;
        }

        AdapterReleaseSigningResultEnvelope BuildSucceededSigningResult(
            const AdapterReleaseArtifactEnvelope& artifact,
            const AdapterReleaseAssemblyResultEnvelope& assembly)
        {
            AdapterReleaseSigningResultEnvelope envelope;
            envelope.m_resultId = "release.signing.result.hardening";
            envelope.m_resultFingerprint = Fingerprint('7');
            envelope.m_artifactId = artifact.m_artifactId;
            envelope.m_artifactFingerprint =
                CalculateCanonicalSha256(artifact.m_canonicalJson);
            envelope.m_assemblyResultId = assembly.m_resultId;
            envelope.m_assemblyResultFingerprint =
                assembly.m_resultFingerprint;
            envelope.m_archiveId = assembly.m_archive.m_archiveId;
            envelope.m_archivePath = assembly.m_archive.m_archivePath;
            envelope.m_archiveFormat = assembly.m_archive.m_archiveFormat;
            envelope.m_archiveByteSize = assembly.m_archive.m_byteSize;
            envelope.m_archiveFingerprint =
                assembly.m_archive.m_archiveFingerprint;
            envelope.m_reconciliationId = artifact.m_reconciliationId;
            envelope.m_packagePreviewId = artifact.m_packagePreviewId;
            envelope.m_manifestId = artifact.m_manifestId;
            envelope.m_manifestFingerprint = artifact.m_manifestFingerprint;
            envelope.m_packId = artifact.m_packId;
            envelope.m_packVersion = artifact.m_packVersion;
            envelope.m_profileId = artifact.m_profileId;
            envelope.m_gameVersion = artifact.m_gameVersion;
            envelope.m_branch = artifact.m_branch;
            envelope.m_runtimeTarget = artifact.m_runtimeTarget;
            envelope.m_signingIntentId = artifact.m_signingIntent.m_intentId;
            envelope.m_signingIntentDecision =
                artifact.m_signingIntent.m_decision;
            envelope.m_signingIdentityKind =
                artifact.m_signingIntent.m_identityKind;
            envelope.m_signerId = artifact.m_signingIntent.m_signerId;
            envelope.m_identityLocator =
                artifact.m_signingIntent.m_identityLocator;
            envelope.m_identityFingerprint =
                artifact.m_signingIntent.m_identityFingerprint;

            envelope.m_signerReview.m_reviewId = "review.signer.hardening";
            envelope.m_signerReview.m_signerToolId = "signer.tool.hardening";
            envelope.m_signerReview.m_signerToolVersion = "1.0.0";
            envelope.m_signerReview.m_signerToolFingerprint = Fingerprint('8');
            envelope.m_signerReview.m_decision =
                AdapterReleaseSignerReviewDecision::Accepted;
            envelope.m_signerReview.m_reviewer = "signer-reviewer";
            envelope.m_signerReview.m_capabilities = {
                AdapterReleaseSignerCapability::ArchiveSigning,
                AdapterReleaseSignerCapability::SignatureArtifactFingerprint,
            };
            envelope.m_signerReview.m_evidenceIds = {
                "evidence.signer.review.hardening",
            };
            envelope.m_signerReview.m_reviewedAtUtc =
                "2026-07-20T11:50:00Z";
            envelope.m_signerReview.m_notes =
                "Reviewed project-owned signer metadata.";

            envelope.m_attempted = true;
            envelope.m_outcome = AdapterReleaseSigningOutcome::Succeeded;
            envelope.m_completedAtUtc = "2026-07-20T12:30:00Z";
            envelope.m_capturedAtUtc = "2026-07-20T13:00:00Z";

            AdapterReleaseSignatureArtifact signatureArtifact;
            signatureArtifact.m_signatureArtifactId =
                "signature.artifact.hardening";
            signatureArtifact.m_kind =
                AdapterReleaseSignatureArtifactKind::DetachedSignature;
            signatureArtifact.m_reference =
                "signatures/release-signing-hardening.zip.sig";
            signatureArtifact.m_mediaType = "application/pgp-signature";
            signatureArtifact.m_byteSize = 96;
            signatureArtifact.m_fingerprint = Fingerprint('9');
            signatureArtifact.m_createdAtUtc = "2026-07-20T12:25:00Z";
            signatureArtifact.m_archiveId = envelope.m_archiveId;
            signatureArtifact.m_archiveFingerprint =
                envelope.m_archiveFingerprint;
            envelope.m_signatureArtifacts.push_back(signatureArtifact);
            return envelope;
        }

        AdapterReleaseSigningEvidenceReturn BuildEvidence(
            const AdapterReleaseArtifactEnvelope& artifact,
            const AdapterReleaseAssemblyResultEnvelope& assembly,
            const AdapterReleaseAssemblyEvidenceReturn& assemblyEvidence,
            const AdapterReleaseSigningResultEnvelope& signing)
        {
            return AdapterReleaseSigningEvidenceService{}.BuildEvidenceReturn(
                artifact,
                assembly,
                assemblyEvidence,
                signing);
        }

        void ConvertToFailedResult(
            AdapterReleaseSigningResultEnvelope& signing,
            AdapterReleaseSigningFailureKind kind,
            AZStd::string message = "External signer reported a failure.")
        {
            signing.m_outcome = AdapterReleaseSigningOutcome::Failed;
            AdapterReleaseSigningFailure failure;
            failure.m_failureId = "failure.signing.hardening";
            failure.m_kind = kind;
            failure.m_code = "signing_failed";
            failure.m_message = AZStd::move(message);
            signing.m_failures.push_back(failure);
            signing.m_failureIds.push_back(failure.m_failureId);
        }
    } // namespace

    TEST(AdapterReleaseSigningHardeningTests, MutatedAssemblyReturnFailsClosed)
    {
        const AdapterReleaseArtifactEnvelope artifact = BuildReadyArtifact();
        const AdapterReleaseAssemblyResultEnvelope assembly =
            BuildAssemblyResult(artifact);
        AdapterReleaseAssemblyEvidenceReturn assemblyEvidence =
            RebuildReleaseAssemblyEvidence(artifact, assembly);
        ASSERT_TRUE(assemblyEvidence.m_contractValid);
        assemblyEvidence.m_filesRead = true;

        const AdapterReleaseSigningEvidenceReturn result = BuildEvidence(
            artifact,
            assembly,
            assemblyEvidence,
            BuildSucceededSigningResult(artifact, assembly));

        EXPECT_FALSE(result.m_contractValid);
        EXPECT_EQ(
            result.m_status,
            AdapterReleaseSigningEnvelopeStatus::AssemblyResultNotAccepted);
        EXPECT_TRUE(result.m_sourceDocuments.empty());
    }

    TEST(AdapterReleaseSigningHardeningTests, UnknownNumericEnumsFailClosed)
    {
        const AdapterReleaseArtifactEnvelope artifact = BuildReadyArtifact();
        const AdapterReleaseAssemblyResultEnvelope assembly =
            BuildAssemblyResult(artifact);
        const AdapterReleaseAssemblyEvidenceReturn assemblyEvidence =
            RebuildReleaseAssemblyEvidence(artifact, assembly);
        AdapterReleaseSigningResultEnvelope signing =
            BuildSucceededSigningResult(artifact, assembly);
        signing.m_outcome = static_cast<AdapterReleaseSigningOutcome>(255);

        const AdapterReleaseSigningEvidenceReturn result = BuildEvidence(
            artifact,
            assembly,
            assemblyEvidence,
            signing);

        EXPECT_FALSE(result.m_contractValid);
        EXPECT_EQ(
            result.m_status,
            AdapterReleaseSigningEnvelopeStatus::EnvelopeInvalid);
    }

    TEST(AdapterReleaseSigningHardeningTests, UnknownExternalFailureIsRepresentable)
    {
        AdapterReleaseSigningFailureKind parsed =
            AdapterReleaseSigningFailureKind::Internal;
        EXPECT_TRUE(TryParseAdapterReleaseSigningFailureKind("unknown", parsed));
        EXPECT_EQ(parsed, AdapterReleaseSigningFailureKind::Unknown);

        const AdapterReleaseArtifactEnvelope artifact = BuildReadyArtifact();
        const AdapterReleaseAssemblyResultEnvelope assembly =
            BuildAssemblyResult(artifact);
        const AdapterReleaseAssemblyEvidenceReturn assemblyEvidence =
            RebuildReleaseAssemblyEvidence(artifact, assembly);
        AdapterReleaseSigningResultEnvelope signing =
            BuildSucceededSigningResult(artifact, assembly);
        ConvertToFailedResult(
            signing,
            AdapterReleaseSigningFailureKind::Unknown);

        const AdapterReleaseSigningEvidenceReturn result = BuildEvidence(
            artifact,
            assembly,
            assemblyEvidence,
            signing);
        EXPECT_TRUE(result.m_contractValid);
        EXPECT_TRUE(result.m_accepted);
    }

    TEST(AdapterReleaseSigningHardeningTests, SignatureBeforeArchiveOrReviewIsRejected)
    {
        const AdapterReleaseArtifactEnvelope artifact = BuildReadyArtifact();
        const AdapterReleaseAssemblyResultEnvelope assembly =
            BuildAssemblyResult(artifact);
        const AdapterReleaseAssemblyEvidenceReturn assemblyEvidence =
            RebuildReleaseAssemblyEvidence(artifact, assembly);
        AdapterReleaseSigningResultEnvelope signing =
            BuildSucceededSigningResult(artifact, assembly);
        signing.m_signatureArtifacts[0].m_createdAtUtc =
            "2026-07-20T11:00:00Z";

        const AdapterReleaseSigningEvidenceReturn result = BuildEvidence(
            artifact,
            assembly,
            assemblyEvidence,
            signing);
        EXPECT_FALSE(result.m_contractValid);
        EXPECT_EQ(
            result.m_status,
            AdapterReleaseSigningEnvelopeStatus::SigningOutcomeMismatch);
    }

    TEST(AdapterReleaseSigningHardeningTests, SecretLikePublicMetadataIsRejected)
    {
        const AdapterReleaseArtifactEnvelope artifact = BuildReadyArtifact();
        const AdapterReleaseAssemblyResultEnvelope assembly =
            BuildAssemblyResult(artifact);
        const AdapterReleaseAssemblyEvidenceReturn assemblyEvidence =
            RebuildReleaseAssemblyEvidence(artifact, assembly);
        AdapterReleaseSigningResultEnvelope signing =
            BuildSucceededSigningResult(artifact, assembly);
        ConvertToFailedResult(
            signing,
            AdapterReleaseSigningFailureKind::Signing,
            "authorization: Bearer project-secret");

        const AdapterReleaseSigningEvidenceReturn result = BuildEvidence(
            artifact,
            assembly,
            assemblyEvidence,
            signing);
        EXPECT_FALSE(result.m_contractValid);
        EXPECT_EQ(
            result.m_status,
            AdapterReleaseSigningEnvelopeStatus::EnvelopeInvalid);
        EXPECT_TRUE(result.m_sourceDocuments.empty());
    }

    TEST(AdapterReleaseSigningHardeningTests, OversizedEnvelopeStopsBeforeEvidenceConstruction)
    {
        const AdapterReleaseArtifactEnvelope artifact = BuildReadyArtifact();
        const AdapterReleaseAssemblyResultEnvelope assembly =
            BuildAssemblyResult(artifact);
        const AdapterReleaseAssemblyEvidenceReturn assemblyEvidence =
            RebuildReleaseAssemblyEvidence(artifact, assembly);
        AdapterReleaseSigningResultEnvelope signing =
            BuildSucceededSigningResult(artifact, assembly);
        const AdapterReleaseSignatureArtifact prototype =
            signing.m_signatureArtifacts.front();
        for (size_t index = 1;
             index <= MaximumReleaseSigningSignatureArtifacts;
             ++index)
        {
            AdapterReleaseSignatureArtifact extra = prototype;
            extra.m_signatureArtifactId =
                "signature.artifact.hardening." +
                DeterministicContractJson::UnsignedString(index);
            extra.m_reference =
                "signatures/release-signing-hardening-" +
                DeterministicContractJson::UnsignedString(index) + ".sig";
            signing.m_signatureArtifacts.push_back(AZStd::move(extra));
        }
        ASSERT_GT(
            signing.m_signatureArtifacts.size(),
            MaximumReleaseSigningSignatureArtifacts);

        const AdapterReleaseSigningEvidenceReturn result = BuildEvidence(
            artifact,
            assembly,
            assemblyEvidence,
            signing);
        EXPECT_FALSE(result.m_contractValid);
        EXPECT_EQ(
            result.m_status,
            AdapterReleaseSigningEnvelopeStatus::EnvelopeInvalid);
        EXPECT_TRUE(result.m_sourceDocuments.empty());
        EXPECT_TRUE(result.m_evidenceDocuments.empty());
    }

    TEST(AdapterReleaseSigningHardeningTests, ReportedFingerprintCannotControlSourceIdentity)
    {
        const AdapterReleaseArtifactEnvelope artifact = BuildReadyArtifact();
        const AdapterReleaseAssemblyResultEnvelope assembly =
            BuildAssemblyResult(artifact);
        const AdapterReleaseAssemblyEvidenceReturn assemblyEvidence =
            RebuildReleaseAssemblyEvidence(artifact, assembly);
        AdapterReleaseSigningResultEnvelope left =
            BuildSucceededSigningResult(artifact, assembly);
        AdapterReleaseSigningResultEnvelope right = left;
        right.m_resultFingerprint = Fingerprint('a');

        const AdapterReleaseSigningEvidenceReturn leftResult = BuildEvidence(
            artifact,
            assembly,
            assemblyEvidence,
            left);
        const AdapterReleaseSigningEvidenceReturn rightResult = BuildEvidence(
            artifact,
            assembly,
            assemblyEvidence,
            right);
        ASSERT_TRUE(leftResult.m_contractValid);
        ASSERT_TRUE(rightResult.m_contractValid);
        EXPECT_NE(
            leftResult.m_reportedResultFingerprint,
            rightResult.m_reportedResultFingerprint);
        EXPECT_EQ(
            leftResult.m_authoritativeResultFingerprint,
            rightResult.m_authoritativeResultFingerprint);
        ASSERT_EQ(leftResult.m_sourceDocuments.size(), 1);
        ASSERT_EQ(rightResult.m_sourceDocuments.size(), 1);
        EXPECT_EQ(
            leftResult.m_sourceDocuments[0].m_source.m_fingerprint,
            leftResult.m_authoritativeResultFingerprint);
        EXPECT_EQ(
            rightResult.m_sourceDocuments[0].m_source.m_fingerprint,
            rightResult.m_authoritativeResultFingerprint);
    }

    TEST(AdapterReleaseSigningHardeningTests, RegistryRejectsUnsafeDiagnosticPath)
    {
        AdapterReleaseSigningResultRegistry& registry =
            AdapterReleaseSigningResultRegistry::Get();
        registry.Clear();
        const AdapterReleaseArtifactEnvelope artifact = BuildReadyArtifact();
        const AdapterReleaseAssemblyResultEnvelope assembly =
            BuildAssemblyResult(artifact);
        AdapterReleaseSigningResultEnvelope signing =
            BuildSucceededSigningResult(artifact, assembly);
        AdapterReleaseSigningDiagnosticReference diagnostic;
        diagnostic.m_diagnosticId = "diagnostic.signing.hardening";
        diagnostic.m_kind = AdapterReleaseSigningDiagnosticKind::Signer;
        diagnostic.m_reference = "C:/private/signer.log";
        diagnostic.m_fingerprint = Fingerprint('b');
        signing.m_diagnosticReferences.push_back(diagnostic);
        signing.m_diagnosticReferenceIds.push_back(diagnostic.m_diagnosticId);
        AZStd::string error;

        EXPECT_FALSE(registry.RegisterEnvelope(signing, &error));
        EXPECT_FALSE(error.empty());
        EXPECT_TRUE(registry.GetEnvelopes().empty());
        registry.Clear();
    }
} // namespace TaintedGrailModdingSDK
