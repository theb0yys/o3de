/*
 * Copyright (c) Contributors to the Open 3D Engine Project.
 * For complete copyright and license terms please see the LICENSE at the root of this distribution.
 *
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 */

#pragma once

#include "AdapterReleaseArtifactContracts.h"

#include <AzCore/base.h>
#include <AzCore/std/containers/vector.h>
#include <AzCore/std/string/string.h>

namespace TaintedGrailModdingSDK
{
    enum class AdapterReleaseSignerReviewDecision : AZ::u8
    {
        Unknown,
        Accepted,
        Rejected,
    };

    enum class AdapterReleaseSignerCapability : AZ::u8
    {
        ArchiveSigning,
        SignatureArtifactFingerprint,
    };

    enum class AdapterReleaseSigningOutcome : AZ::u8
    {
        NotAttempted,
        Succeeded,
        Failed,
        Skipped,
    };

    enum class AdapterReleaseSignatureArtifactKind : AZ::u8
    {
        DetachedSignature,
        SignatureBundle,
        CertificateBundle,
        TransparencyReceipt,
        Attestation,
        Other,
    };

    enum class AdapterReleaseSigningFailureKind : AZ::u8
    {
        Contract,
        InputBinding,
        SignerUnavailable,
        IdentityUnavailable,
        AccessDenied,
        UnsupportedIdentity,
        UnsupportedFormat,
        ArchiveRead,
        Signing,
        SignatureArtifact,
        Internal,
        Unknown,
    };

    enum class AdapterReleaseSigningDiagnosticKind : AZ::u8
    {
        Signer,
        Identity,
        Archive,
        SignatureArtifact,
        Binding,
        Diagnostic,
    };

    enum class AdapterReleaseSigningEnvelopeStatus : AZ::u8
    {
        Accepted,
        AssemblyResultNotAccepted,
        SigningNotRequested,
        SignerUnreviewed,
        AssemblyBindingMismatch,
        SigningIntentBindingMismatch,
        EnvelopeInvalid,
        SigningOutcomeMismatch,
        SignatureArtifactBindingMismatch,
        FailureDiagnosticBindingMismatch,
    };

    AZStd::string ToString(AdapterReleaseSignerReviewDecision decision);
    AZStd::string ToString(AdapterReleaseSignerCapability capability);
    AZStd::string ToString(AdapterReleaseSigningOutcome outcome);
    AZStd::string ToString(AdapterReleaseSignatureArtifactKind kind);
    AZStd::string ToString(AdapterReleaseSigningFailureKind kind);
    AZStd::string ToString(AdapterReleaseSigningDiagnosticKind kind);
    AZStd::string ToString(AdapterReleaseSigningEnvelopeStatus status);

    bool TryParseAdapterReleaseSignerReviewDecision(
        const AZStd::string& value,
        AdapterReleaseSignerReviewDecision& decision);
    bool TryParseAdapterReleaseSignerCapability(
        const AZStd::string& value,
        AdapterReleaseSignerCapability& capability);
    bool TryParseAdapterReleaseSigningOutcome(
        const AZStd::string& value,
        AdapterReleaseSigningOutcome& outcome);
    bool TryParseAdapterReleaseSignatureArtifactKind(
        const AZStd::string& value,
        AdapterReleaseSignatureArtifactKind& kind);
    bool TryParseAdapterReleaseSigningFailureKind(
        const AZStd::string& value,
        AdapterReleaseSigningFailureKind& kind);
    bool TryParseAdapterReleaseSigningDiagnosticKind(
        const AZStd::string& value,
        AdapterReleaseSigningDiagnosticKind& kind);
    bool TryParseAdapterReleaseSigningEnvelopeStatus(
        const AZStd::string& value,
        AdapterReleaseSigningEnvelopeStatus& status);

    bool IsAdapterReleaseSigningStableId(const AZStd::string& value);
    bool IsAdapterReleaseSigningFingerprint(const AZStd::string& value);
    bool IsAdapterReleaseSigningSafeReference(const AZStd::string& value);
    bool IsAdapterReleaseSigningSemanticVersion(const AZStd::string& value);
    bool IsAdapterReleaseSigningUtcTimestamp(const AZStd::string& value);

    struct AdapterReleaseSignerReview
    {
        AZStd::string m_reviewId;
        AZStd::string m_signerToolId;
        AZStd::string m_signerToolVersion;
        AZStd::string m_signerToolFingerprint;
        AdapterReleaseSignerReviewDecision m_decision =
            AdapterReleaseSignerReviewDecision::Unknown;
        AZStd::string m_reviewer;
        AZStd::vector<AdapterReleaseSignerCapability> m_capabilities;
        AZStd::vector<AZStd::string> m_evidenceIds;
        AZStd::string m_reviewedAtUtc;
        AZStd::string m_notes;
    };

    struct AdapterReleaseSignatureArtifact
    {
        AZStd::string m_signatureArtifactId;
        AdapterReleaseSignatureArtifactKind m_kind =
            AdapterReleaseSignatureArtifactKind::Other;
        AZStd::string m_reference;
        AZStd::string m_mediaType;
        AZ::u64 m_byteSize = 0;
        AZStd::string m_fingerprint;
        AZStd::string m_createdAtUtc;
        AZStd::string m_archiveId;
        AZStd::string m_archiveFingerprint;
        AZStd::vector<AZStd::string> m_diagnosticReferenceIds;
    };

    struct AdapterReleaseSigningFailure
    {
        AZStd::string m_failureId;
        AdapterReleaseSigningFailureKind m_kind =
            AdapterReleaseSigningFailureKind::Unknown;
        AZStd::string m_code;
        AZStd::string m_message;
        AZStd::string m_signatureArtifactId;
        AZStd::vector<AZStd::string> m_diagnosticReferenceIds;
        bool m_retryable = false;
    };

    struct AdapterReleaseSigningDiagnosticReference
    {
        AZStd::string m_diagnosticId;
        AdapterReleaseSigningDiagnosticKind m_kind =
            AdapterReleaseSigningDiagnosticKind::Diagnostic;
        AZStd::string m_reference;
        AZStd::string m_fingerprint;
        AZStd::vector<AZStd::string> m_signatureArtifactIds;
    };

    struct AdapterReleaseSigningResultEnvelope
    {
        AZ::u32 m_contractVersion = 1;
        AZStd::string m_resultId;
        AZStd::string m_resultFingerprint;
        AZStd::string m_artifactId;
        AZStd::string m_artifactFingerprint;
        AZStd::string m_assemblyResultId;
        AZStd::string m_assemblyResultFingerprint;
        AZStd::string m_archiveId;
        AZStd::string m_archivePath;
        AZStd::string m_archiveFormat;
        AZ::u64 m_archiveByteSize = 0;
        AZStd::string m_archiveFingerprint;
        AZStd::string m_reconciliationId;
        AZStd::string m_packagePreviewId;
        AZStd::string m_manifestId;
        AZStd::string m_manifestFingerprint;
        AZStd::string m_packId;
        AZStd::string m_packVersion;
        AZStd::string m_profileId;
        AZStd::string m_gameVersion;
        AZStd::string m_branch;
        AZStd::string m_runtimeTarget;
        AZStd::string m_signingIntentId;
        AdapterReleaseSigningIntentDecision m_signingIntentDecision =
            AdapterReleaseSigningIntentDecision::Unknown;
        AdapterReleaseSigningIdentityKind m_signingIdentityKind =
            AdapterReleaseSigningIdentityKind::None;
        AZStd::string m_signerId;
        AZStd::string m_identityLocator;
        AZStd::string m_identityFingerprint;
        AdapterReleaseSignerReview m_signerReview;
        bool m_attempted = false;
        AdapterReleaseSigningOutcome m_outcome =
            AdapterReleaseSigningOutcome::NotAttempted;
        AZStd::string m_completedAtUtc;
        AZStd::string m_capturedAtUtc;
        AZStd::vector<AZStd::string> m_failureIds;
        AZStd::vector<AZStd::string> m_diagnosticReferenceIds;
        AZStd::vector<AdapterReleaseSignatureArtifact> m_signatureArtifacts;
        AZStd::vector<AdapterReleaseSigningFailure> m_failures;
        AZStd::vector<AdapterReleaseSigningDiagnosticReference>
            m_diagnosticReferences;
    };

    class AdapterReleaseSigningResultRegistry
    {
    public:
        static AdapterReleaseSigningResultRegistry& Get();

        bool RegisterEnvelope(
            const AdapterReleaseSigningResultEnvelope& envelope,
            AZStd::string* error = nullptr);
        void Clear();

        const AdapterReleaseSigningResultEnvelope* FindByResultId(
            const AZStd::string& resultId) const;
        const AZStd::vector<AdapterReleaseSigningResultEnvelope>&
            GetEnvelopes() const;

    private:
        AZStd::vector<AdapterReleaseSigningResultEnvelope> m_envelopes;
    };
} // namespace TaintedGrailModdingSDK
