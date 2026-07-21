/*
 * Copyright (c) Contributors to the Open 3D Engine Project.
 * For complete copyright and license terms please see the LICENSE at the root of this distribution.
 *
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 */

#include "AdapterReleaseSigningResultContracts.h"

#include "AdapterReleaseSigningHardening.h"
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

        constexpr EnumName<AdapterReleaseSignerReviewDecision>
            ReviewDecisions[] = {
                { AdapterReleaseSignerReviewDecision::Unknown, "unknown" },
                { AdapterReleaseSignerReviewDecision::Accepted, "accepted" },
                { AdapterReleaseSignerReviewDecision::Rejected, "rejected" },
            };
        constexpr EnumName<AdapterReleaseSignerCapability> Capabilities[] = {
            { AdapterReleaseSignerCapability::ArchiveSigning,
              "archive_signing" },
            { AdapterReleaseSignerCapability::SignatureArtifactFingerprint,
              "signature_artifact_fingerprint" },
        };
        constexpr EnumName<AdapterReleaseSigningOutcome> SigningOutcomes[] = {
            { AdapterReleaseSigningOutcome::NotAttempted, "not_attempted" },
            { AdapterReleaseSigningOutcome::Succeeded, "succeeded" },
            { AdapterReleaseSigningOutcome::Failed, "failed" },
            { AdapterReleaseSigningOutcome::Skipped, "skipped" },
        };
        constexpr EnumName<AdapterReleaseSignatureArtifactKind>
            SignatureArtifactKinds[] = {
                { AdapterReleaseSignatureArtifactKind::DetachedSignature,
                  "detached_signature" },
                { AdapterReleaseSignatureArtifactKind::SignatureBundle,
                  "signature_bundle" },
                { AdapterReleaseSignatureArtifactKind::CertificateBundle,
                  "certificate_bundle" },
                { AdapterReleaseSignatureArtifactKind::TransparencyReceipt,
                  "transparency_receipt" },
                { AdapterReleaseSignatureArtifactKind::Attestation,
                  "attestation" },
                { AdapterReleaseSignatureArtifactKind::Other, "other" },
            };
        constexpr EnumName<AdapterReleaseSigningFailureKind> FailureKinds[] = {
            { AdapterReleaseSigningFailureKind::Contract, "contract" },
            { AdapterReleaseSigningFailureKind::InputBinding,
              "input_binding" },
            { AdapterReleaseSigningFailureKind::SignerUnavailable,
              "signer_unavailable" },
            { AdapterReleaseSigningFailureKind::IdentityUnavailable,
              "identity_unavailable" },
            { AdapterReleaseSigningFailureKind::AccessDenied, "access_denied" },
            { AdapterReleaseSigningFailureKind::UnsupportedIdentity,
              "unsupported_identity" },
            { AdapterReleaseSigningFailureKind::UnsupportedFormat,
              "unsupported_format" },
            { AdapterReleaseSigningFailureKind::ArchiveRead, "archive_read" },
            { AdapterReleaseSigningFailureKind::Signing, "signing" },
            { AdapterReleaseSigningFailureKind::SignatureArtifact,
              "signature_artifact" },
            { AdapterReleaseSigningFailureKind::Internal, "internal" },
            { AdapterReleaseSigningFailureKind::Unknown, "unknown" },
        };
        constexpr EnumName<AdapterReleaseSigningDiagnosticKind>
            DiagnosticKinds[] = {
                { AdapterReleaseSigningDiagnosticKind::Signer, "signer" },
                { AdapterReleaseSigningDiagnosticKind::Identity, "identity" },
                { AdapterReleaseSigningDiagnosticKind::Archive, "archive" },
                { AdapterReleaseSigningDiagnosticKind::SignatureArtifact,
                  "signature_artifact" },
                { AdapterReleaseSigningDiagnosticKind::Binding, "binding" },
                { AdapterReleaseSigningDiagnosticKind::Diagnostic, "diagnostic" },
            };
        constexpr EnumName<AdapterReleaseSigningEnvelopeStatus>
            EnvelopeStatuses[] = {
                { AdapterReleaseSigningEnvelopeStatus::Accepted, "accepted" },
                { AdapterReleaseSigningEnvelopeStatus::AssemblyResultNotAccepted,
                  "assembly_result_not_accepted" },
                { AdapterReleaseSigningEnvelopeStatus::SigningNotRequested,
                  "signing_not_requested" },
                { AdapterReleaseSigningEnvelopeStatus::SignerUnreviewed,
                  "signer_unreviewed" },
                { AdapterReleaseSigningEnvelopeStatus::AssemblyBindingMismatch,
                  "assembly_binding_mismatch" },
                { AdapterReleaseSigningEnvelopeStatus::SigningIntentBindingMismatch,
                  "signing_intent_binding_mismatch" },
                { AdapterReleaseSigningEnvelopeStatus::EnvelopeInvalid,
                  "envelope_invalid" },
                { AdapterReleaseSigningEnvelopeStatus::SigningOutcomeMismatch,
                  "signing_outcome_mismatch" },
                { AdapterReleaseSigningEnvelopeStatus::SignatureArtifactBindingMismatch,
                  "signature_artifact_binding_mismatch" },
                { AdapterReleaseSigningEnvelopeStatus::FailureDiagnosticBindingMismatch,
                  "failure_diagnostic_binding_mismatch" },
            };

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

        bool HasStableOptionalId(const AZStd::string& value)
        {
            return value.empty() || IsStableContractId(value);
        }

        bool HasUniqueStableIds(
            const AZStd::vector<AZStd::string>& values)
        {
            AZStd::vector<AZStd::string> sorted = values;
            for (const AZStd::string& value : sorted)
            {
                if (!IsStableContractId(value))
                {
                    return false;
                }
            }
            AZStd::sort(sorted.begin(), sorted.end());
            return AZStd::adjacent_find(sorted.begin(), sorted.end())
                == sorted.end();
        }

        bool HasUniqueCapabilities(
            const AZStd::vector<AdapterReleaseSignerCapability>& values)
        {
            for (size_t left = 0; left < values.size(); ++left)
            {
                for (size_t right = left + 1; right < values.size(); ++right)
                {
                    if (values[left] == values[right])
                    {
                        return false;
                    }
                }
            }
            return true;
        }

        bool HasRegistryShape(
            const AdapterReleaseSigningResultEnvelope& envelope)
        {
            if (!IsReleaseSigningEnvelopeWithinLimits(envelope)
                || !AreReleaseSigningEnumsKnown(envelope)
                || !IsReleaseSigningEnvelopePublic(envelope)
                || envelope.m_contractVersion != 1
                || !IsStableContractId(envelope.m_resultId)
                || !IsSha256Fingerprint(envelope.m_resultFingerprint)
                || !IsStableContractId(envelope.m_artifactId)
                || !IsSha256Fingerprint(envelope.m_artifactFingerprint)
                || !IsStableContractId(envelope.m_assemblyResultId)
                || !IsSha256Fingerprint(envelope.m_assemblyResultFingerprint)
                || !IsStableContractId(envelope.m_archiveId)
                || !IsSafePackageRelativePath(envelope.m_archivePath)
                || envelope.m_archiveByteSize == 0
                || !IsSha256Fingerprint(envelope.m_archiveFingerprint)
                || !IsStableContractId(envelope.m_signingIntentId)
                || !IsStableContractId(envelope.m_signerId)
                || !IsSha256Fingerprint(envelope.m_identityFingerprint)
                || !IsStrictUtcTimestamp(envelope.m_capturedAtUtc)
                || !IsStableContractId(envelope.m_signerReview.m_reviewId)
                || !IsStableContractId(envelope.m_signerReview.m_signerToolId)
                || !IsStrictSemanticVersion(
                    envelope.m_signerReview.m_signerToolVersion)
                || !IsSha256Fingerprint(
                    envelope.m_signerReview.m_signerToolFingerprint)
                || !IsStrictUtcTimestamp(
                    envelope.m_signerReview.m_reviewedAtUtc)
                || !HasUniqueCapabilities(
                    envelope.m_signerReview.m_capabilities)
                || !HasUniqueStableIds(envelope.m_signerReview.m_evidenceIds)
                || !HasUniqueStableIds(envelope.m_failureIds)
                || !HasUniqueStableIds(envelope.m_diagnosticReferenceIds))
            {
                return false;
            }

            AZStd::vector<AZStd::string> artifactIds;
            AZStd::vector<AZStd::string> artifactPaths;
            for (const AdapterReleaseSignatureArtifact& artifact :
                 envelope.m_signatureArtifacts)
            {
                PackagePathIdentity pathIdentity;
                if (!IsStableContractId(artifact.m_signatureArtifactId)
                    || !TryBuildPackagePathIdentity(
                        artifact.m_reference,
                        pathIdentity)
                    || artifact.m_byteSize == 0
                    || !IsSha256Fingerprint(artifact.m_fingerprint)
                    || !IsStrictUtcTimestamp(artifact.m_createdAtUtc)
                    || !IsStableContractId(artifact.m_archiveId)
                    || !IsSha256Fingerprint(artifact.m_archiveFingerprint)
                    || !HasUniqueStableIds(
                        artifact.m_diagnosticReferenceIds))
                {
                    return false;
                }
                artifactIds.push_back(artifact.m_signatureArtifactId);
                artifactPaths.push_back(pathIdentity.m_windowsIdentity);
            }
            if (!HasUniqueStableIds(artifactIds))
            {
                return false;
            }
            AZStd::sort(artifactPaths.begin(), artifactPaths.end());
            if (AZStd::adjacent_find(
                    artifactPaths.begin(),
                    artifactPaths.end()) != artifactPaths.end())
            {
                return false;
            }

            AZStd::vector<AZStd::string> failureIds;
            for (const AdapterReleaseSigningFailure& failure : envelope.m_failures)
            {
                if (!IsStableContractId(failure.m_failureId)
                    || !HasStableOptionalId(failure.m_signatureArtifactId)
                    || !HasUniqueStableIds(
                        failure.m_diagnosticReferenceIds))
                {
                    return false;
                }
                failureIds.push_back(failure.m_failureId);
            }
            if (!HasUniqueStableIds(failureIds))
            {
                return false;
            }

            AZStd::vector<AZStd::string> diagnosticIds;
            AZStd::vector<AZStd::string> diagnosticPaths;
            for (const AdapterReleaseSigningDiagnosticReference& diagnostic :
                 envelope.m_diagnosticReferences)
            {
                PackagePathIdentity pathIdentity;
                if (!IsStableContractId(diagnostic.m_diagnosticId)
                    || !TryBuildPackagePathIdentity(
                        diagnostic.m_reference,
                        pathIdentity)
                    || !IsSha256Fingerprint(diagnostic.m_fingerprint)
                    || !HasUniqueStableIds(
                        diagnostic.m_signatureArtifactIds))
                {
                    return false;
                }
                diagnosticIds.push_back(diagnostic.m_diagnosticId);
                diagnosticPaths.push_back(pathIdentity.m_windowsIdentity);
            }
            if (!HasUniqueStableIds(diagnosticIds))
            {
                return false;
            }
            AZStd::sort(diagnosticPaths.begin(), diagnosticPaths.end());
            return AZStd::adjacent_find(
                       diagnosticPaths.begin(),
                       diagnosticPaths.end()) == diagnosticPaths.end();
        }
    } // namespace

    AZStd::string ToString(AdapterReleaseSignerReviewDecision decision)
    {
        return EnumToString(decision, ReviewDecisions);
    }

    AZStd::string ToString(AdapterReleaseSignerCapability capability)
    {
        return EnumToString(capability, Capabilities);
    }

    AZStd::string ToString(AdapterReleaseSigningOutcome outcome)
    {
        return EnumToString(outcome, SigningOutcomes);
    }

    AZStd::string ToString(AdapterReleaseSignatureArtifactKind kind)
    {
        return EnumToString(kind, SignatureArtifactKinds);
    }

    AZStd::string ToString(AdapterReleaseSigningFailureKind kind)
    {
        return EnumToString(kind, FailureKinds);
    }

    AZStd::string ToString(AdapterReleaseSigningDiagnosticKind kind)
    {
        return EnumToString(kind, DiagnosticKinds);
    }

    AZStd::string ToString(AdapterReleaseSigningEnvelopeStatus status)
    {
        return EnumToString(status, EnvelopeStatuses);
    }

    bool TryParseAdapterReleaseSignerReviewDecision(
        const AZStd::string& value,
        AdapterReleaseSignerReviewDecision& decision)
    {
        return TryParseEnum(value, decision, ReviewDecisions);
    }

    bool TryParseAdapterReleaseSignerCapability(
        const AZStd::string& value,
        AdapterReleaseSignerCapability& capability)
    {
        return TryParseEnum(value, capability, Capabilities);
    }

    bool TryParseAdapterReleaseSigningOutcome(
        const AZStd::string& value,
        AdapterReleaseSigningOutcome& outcome)
    {
        return TryParseEnum(value, outcome, SigningOutcomes);
    }

    bool TryParseAdapterReleaseSignatureArtifactKind(
        const AZStd::string& value,
        AdapterReleaseSignatureArtifactKind& kind)
    {
        return TryParseEnum(value, kind, SignatureArtifactKinds);
    }

    bool TryParseAdapterReleaseSigningFailureKind(
        const AZStd::string& value,
        AdapterReleaseSigningFailureKind& kind)
    {
        return TryParseEnum(value, kind, FailureKinds);
    }

    bool TryParseAdapterReleaseSigningDiagnosticKind(
        const AZStd::string& value,
        AdapterReleaseSigningDiagnosticKind& kind)
    {
        return TryParseEnum(value, kind, DiagnosticKinds);
    }

    bool TryParseAdapterReleaseSigningEnvelopeStatus(
        const AZStd::string& value,
        AdapterReleaseSigningEnvelopeStatus& status)
    {
        return TryParseEnum(value, status, EnvelopeStatuses);
    }

    bool IsAdapterReleaseSigningStableId(const AZStd::string& value)
    {
        return IsStableContractId(value);
    }

    bool IsAdapterReleaseSigningFingerprint(const AZStd::string& value)
    {
        return IsSha256Fingerprint(value);
    }

    bool IsAdapterReleaseSigningSafeReference(const AZStd::string& value)
    {
        return IsSafePackageRelativePath(value);
    }

    bool IsAdapterReleaseSigningSemanticVersion(const AZStd::string& value)
    {
        return IsStrictSemanticVersion(value);
    }

    bool IsAdapterReleaseSigningUtcTimestamp(const AZStd::string& value)
    {
        return IsStrictUtcTimestamp(value);
    }

    AdapterReleaseSigningResultRegistry&
    AdapterReleaseSigningResultRegistry::Get()
    {
        static AdapterReleaseSigningResultRegistry registry;
        return registry;
    }

    bool AdapterReleaseSigningResultRegistry::RegisterEnvelope(
        const AdapterReleaseSigningResultEnvelope& envelope,
        AZStd::string* error)
    {
        if (!HasRegistryShape(envelope))
        {
            if (error)
            {
                *error =
                    "Release signing-result registration requires bounded collections, "
                    "known enum values, public metadata, safe relative references, "
                    "stable unique identities, strict timestamps/versioning, and "
                    "lowercase SHA-256 fingerprints.";
            }
            return false;
        }
        if (m_envelopes.size() >= MaximumReleaseSigningRegistryEnvelopes)
        {
            if (error)
            {
                *error =
                    "The transient release signing-result registry reached its fixed "
                    "envelope limit.";
            }
            return false;
        }

        for (const AdapterReleaseSigningResultEnvelope& existing : m_envelopes)
        {
            if (existing.m_resultId == envelope.m_resultId)
            {
                if (error)
                {
                    *error =
                        "A release signing-result envelope with this result identity "
                        "already exists.";
                }
                return false;
            }
        }

        m_envelopes.push_back(envelope);
        if (error)
        {
            error->clear();
        }
        return true;
    }

    void AdapterReleaseSigningResultRegistry::Clear()
    {
        m_envelopes.clear();
    }

    const AdapterReleaseSigningResultEnvelope*
    AdapterReleaseSigningResultRegistry::FindByResultId(
        const AZStd::string& resultId) const
    {
        for (const AdapterReleaseSigningResultEnvelope& envelope : m_envelopes)
        {
            if (envelope.m_resultId == resultId)
            {
                return &envelope;
            }
        }
        return nullptr;
    }

    const AZStd::vector<AdapterReleaseSigningResultEnvelope>&
    AdapterReleaseSigningResultRegistry::GetEnvelopes() const
    {
        return m_envelopes;
    }
} // namespace TaintedGrailModdingSDK
