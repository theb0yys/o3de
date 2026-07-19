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
    enum class AdapterRuntimeOutcome : AZ::u8
    {
        NotAttempted,
        Succeeded,
        Failed,
        Skipped,
    };

    enum class AdapterRuntimeFailureKind : AZ::u8
    {
        Contract,
        Capability,
        Runtime,
        Persistence,
        Cleanup,
        Rollback,
        Unknown,
    };

    enum class AdapterRuntimeLogKind : AZ::u8
    {
        Adapter,
        Game,
        Diagnostic,
        Cleanup,
        Rollback,
    };

    AZStd::string ToString(AdapterRuntimeOutcome outcome);
    AZStd::string ToString(AdapterRuntimeFailureKind kind);
    AZStd::string ToString(AdapterRuntimeLogKind kind);
    bool TryParseAdapterRuntimeOutcome(
        const AZStd::string& value,
        AdapterRuntimeOutcome& outcome);
    bool TryParseAdapterRuntimeFailureKind(
        const AZStd::string& value,
        AdapterRuntimeFailureKind& kind);
    bool TryParseAdapterRuntimeLogKind(
        const AZStd::string& value,
        AdapterRuntimeLogKind& kind);
    bool IsAdapterRuntimeStableId(const AZStd::string& value);
    bool IsAdapterRuntimeFingerprint(const AZStd::string& value);
    bool IsAdapterRuntimeLogReference(const AZStd::string& value);

    struct AdapterRuntimeFailure
    {
        AZStd::string m_failureId;
        AdapterRuntimeFailureKind m_kind = AdapterRuntimeFailureKind::Unknown;
        AZStd::string m_code;
        AZStd::string m_message;
        AZStd::string m_stepId;
        AZStd::vector<AZStd::string> m_logReferenceIds;
        bool m_retryable = false;
    };

    struct AdapterRuntimeLogReference
    {
        AZStd::string m_logId;
        AdapterRuntimeLogKind m_kind = AdapterRuntimeLogKind::Diagnostic;
        AZStd::string m_reference;
        AZStd::string m_fingerprint;
        AZStd::vector<AZStd::string> m_stepIds;
    };

    struct AdapterRuntimeStepResult
    {
        AZStd::string m_stepId;
        AZ::u64 m_sequence = 0;
        AZStd::string m_capability;
        AZStd::string m_subjectKind;
        AZStd::string m_subjectId;
        AZStd::string m_subjectRef;
        AdapterRuntimeOutcome m_outcome = AdapterRuntimeOutcome::NotAttempted;
        AZStd::vector<AZStd::string> m_failureIds;
        AZStd::vector<AZStd::string> m_logReferenceIds;
        AZStd::string m_outputFingerprint;
        bool m_attempted = false;
    };

    struct AdapterRuntimeRecoveryResult
    {
        AZStd::string m_stepId;
        AdapterRuntimeOutcome m_outcome = AdapterRuntimeOutcome::NotAttempted;
        AZStd::vector<AZStd::string> m_failureIds;
        AZStd::vector<AZStd::string> m_logReferenceIds;
        AZStd::string m_outputFingerprint;
    };

    struct AdapterRuntimeResultEnvelope
    {
        AZ::u32 m_contractVersion = 1;
        AZStd::string m_resultId;
        AZStd::string m_planId;
        AZStd::string m_planCanonicalJson;
        AZStd::string m_planFingerprint;
        AZStd::string m_packId;
        AZStd::string m_packVersion;
        AZStd::string m_adapterId;
        AZStd::string m_adapterVersion;
        AZStd::string m_profileId;
        AZStd::string m_gameVersion;
        AZStd::string m_branch;
        AZStd::string m_runtimeTarget;
        AZStd::string m_capturedAt;
        AZStd::string m_resultFingerprint;
        AZStd::vector<AdapterRuntimeStepResult> m_stepResults;
        AdapterRuntimeRecoveryResult m_cleanupResult;
        AdapterRuntimeRecoveryResult m_rollbackResult;
        AZStd::vector<AdapterRuntimeFailure> m_failures;
        AZStd::vector<AdapterRuntimeLogReference> m_logReferences;
    };

    class AdapterRuntimeResultRegistry
    {
    public:
        static AdapterRuntimeResultRegistry& Get();

        bool RegisterEnvelope(
            const AdapterRuntimeResultEnvelope& envelope,
            AZStd::string* error = nullptr);
        void Clear();

        const AdapterRuntimeResultEnvelope* FindByResultId(
            const AZStd::string& resultId) const;
        const AZStd::vector<AdapterRuntimeResultEnvelope>& GetEnvelopes() const;

    private:
        AZStd::vector<AdapterRuntimeResultEnvelope> m_envelopes;
    };
} // namespace TaintedGrailModdingSDK
