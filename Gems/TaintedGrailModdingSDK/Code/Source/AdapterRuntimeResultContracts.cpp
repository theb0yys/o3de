/*
 * Copyright (c) Contributors to the Open 3D Engine Project.
 * For complete copyright and license terms please see the LICENSE at the root of this distribution.
 *
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 */

#include "AdapterRuntimeResultContracts.h"

#include <AzCore/std/algorithm.h>
#include <AzCore/std/utility/move.h>

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

        constexpr EnumName<AdapterRuntimeOutcome> Outcomes[] = {
            { AdapterRuntimeOutcome::NotAttempted, "not_attempted" },
            { AdapterRuntimeOutcome::Succeeded, "succeeded" },
            { AdapterRuntimeOutcome::Failed, "failed" },
            { AdapterRuntimeOutcome::Skipped, "skipped" },
        };

        constexpr EnumName<AdapterRuntimeFailureKind> FailureKinds[] = {
            { AdapterRuntimeFailureKind::Contract, "contract" },
            { AdapterRuntimeFailureKind::Capability, "capability" },
            { AdapterRuntimeFailureKind::Runtime, "runtime" },
            { AdapterRuntimeFailureKind::Persistence, "persistence" },
            { AdapterRuntimeFailureKind::Cleanup, "cleanup" },
            { AdapterRuntimeFailureKind::Rollback, "rollback" },
            { AdapterRuntimeFailureKind::Unknown, "unknown" },
        };

        constexpr EnumName<AdapterRuntimeLogKind> LogKinds[] = {
            { AdapterRuntimeLogKind::Adapter, "adapter" },
            { AdapterRuntimeLogKind::Game, "game" },
            { AdapterRuntimeLogKind::Diagnostic, "diagnostic" },
            { AdapterRuntimeLogKind::Cleanup, "cleanup" },
            { AdapterRuntimeLogKind::Rollback, "rollback" },
        };

        template<class EnumType, size_t Count>
        AZStd::string ToEnumString(
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

        bool Contains(
            const AZStd::vector<AZStd::string>& values,
            const AZStd::string& value)
        {
            return AZStd::find(values.begin(), values.end(), value) != values.end();
        }

        bool HasDuplicate(const AZStd::vector<AZStd::string>& values)
        {
            AZStd::vector<AZStd::string> sorted = values;
            AZStd::sort(sorted.begin(), sorted.end());
            return AZStd::adjacent_find(sorted.begin(), sorted.end()) != sorted.end();
        }

        bool IsAsciiAlphaNumeric(char value)
        {
            return (value >= 'a' && value <= 'z')
                || (value >= 'A' && value <= 'Z')
                || (value >= '0' && value <= '9');
        }

        bool IsLowerAlphaNumeric(char value)
        {
            return (value >= 'a' && value <= 'z')
                || (value >= '0' && value <= '9');
        }

        bool IsOpaqueIdentity(const AZStd::string& value)
        {
            if (value.empty())
            {
                return false;
            }
            for (char character : value)
            {
                const unsigned char byte = static_cast<unsigned char>(character);
                if (byte <= 0x20 || byte == 0x7f)
                {
                    return false;
                }
            }
            return true;
        }

        bool IsLowerToken(const AZStd::string& value)
        {
            if (value.empty() || !IsLowerAlphaNumeric(value.front())
                || !IsLowerAlphaNumeric(value.back()))
            {
                return false;
            }
            for (char character : value)
            {
                if (!IsLowerAlphaNumeric(character)
                    && character != '.'
                    && character != '-'
                    && character != '_')
                {
                    return false;
                }
            }
            return true;
        }

        bool OutcomeIsAttempted(AdapterRuntimeOutcome outcome)
        {
            return outcome == AdapterRuntimeOutcome::Succeeded
                || outcome == AdapterRuntimeOutcome::Failed;
        }

        bool OutcomeRequiresFailure(AdapterRuntimeOutcome outcome)
        {
            return outcome == AdapterRuntimeOutcome::Failed
                || outcome == AdapterRuntimeOutcome::Skipped;
        }

        bool ValidateOutcomeShape(
            AdapterRuntimeOutcome outcome,
            bool attempted,
            const AZStd::vector<AZStd::string>& failureIds,
            const AZStd::string& outputFingerprint,
            AZStd::string& error)
        {
            if (attempted != OutcomeIsAttempted(outcome))
            {
                error = "Attempted must be true only for succeeded or failed outcomes.";
                return false;
            }
            if (OutcomeRequiresFailure(outcome) != !failureIds.empty())
            {
                error = "Failed and skipped outcomes require failures; succeeded and not_attempted do not.";
                return false;
            }
            if (outcome == AdapterRuntimeOutcome::Succeeded
                && !IsAdapterRuntimeFingerprint(outputFingerprint))
            {
                error = "Succeeded step results require a lowercase SHA-256 output fingerprint.";
                return false;
            }
            if (!outputFingerprint.empty()
                && !IsAdapterRuntimeFingerprint(outputFingerprint))
            {
                error = "Step output fingerprints must use lowercase sha256:<64 hex>.";
                return false;
            }
            if (HasDuplicate(failureIds))
            {
                error = "Step failure references must be unique.";
                return false;
            }
            return true;
        }

        bool ValidateRecoveryShape(
            const AdapterRuntimeRecoveryResult& recovery,
            AZStd::string& error)
        {
            if (!IsOpaqueIdentity(recovery.m_stepId))
            {
                error = "Cleanup and rollback results require an exact step identity.";
                return false;
            }
            const bool attempted = OutcomeIsAttempted(recovery.m_outcome);
            return ValidateOutcomeShape(
                recovery.m_outcome,
                attempted,
                recovery.m_failureIds,
                recovery.m_outputFingerprint,
                error);
        }

        bool ValidateEnvelopeShape(
            const AdapterRuntimeResultEnvelope& envelope,
            AZStd::string& error)
        {
            if (envelope.m_contractVersion != 1)
            {
                error = "Adapter runtime result contract version must be 1.";
                return false;
            }
            if (!IsAdapterRuntimeStableId(envelope.m_resultId))
            {
                error = "ResultId must be a lowercase namespaced stable ID.";
                return false;
            }
            if (!IsOpaqueIdentity(envelope.m_planId)
                || envelope.m_planCanonicalJson.empty())
            {
                error = "An exact plan ID and canonical plan JSON are required.";
                return false;
            }
            if (!IsAdapterRuntimeFingerprint(envelope.m_planFingerprint)
                || !IsAdapterRuntimeFingerprint(envelope.m_resultFingerprint))
            {
                error = "Plan and result fingerprints must use lowercase sha256:<64 hex>.";
                return false;
            }
            if (envelope.m_packId.empty()
                || envelope.m_packVersion.empty()
                || envelope.m_adapterId.empty()
                || envelope.m_adapterVersion.empty()
                || envelope.m_profileId.empty()
                || envelope.m_gameVersion.empty()
                || envelope.m_branch.empty()
                || envelope.m_runtimeTarget.empty()
                || envelope.m_capturedAt.empty())
            {
                error = "Pack, adapter, profile, build, branch, runtime target, and capture time are required.";
                return false;
            }
            if (envelope.m_stepResults.empty())
            {
                error = "At least one attempted-plan step result is required.";
                return false;
            }

            AZStd::vector<AZStd::string> stepIds;
            stepIds.reserve(envelope.m_stepResults.size());
            for (const AdapterRuntimeStepResult& step : envelope.m_stepResults)
            {
                if (!IsOpaqueIdentity(step.m_stepId)
                    || step.m_sequence == 0
                    || step.m_capability.empty()
                    || step.m_subjectKind.empty()
                    || step.m_subjectId.empty()
                    || step.m_subjectRef.empty())
                {
                    error = "Every step result requires exact identity, sequence, capability, and subject binding.";
                    return false;
                }
                AZStd::string outcomeError;
                if (!ValidateOutcomeShape(
                        step.m_outcome,
                        step.m_attempted,
                        step.m_failureIds,
                        step.m_outputFingerprint,
                        outcomeError))
                {
                    error = step.m_stepId + ": " + outcomeError;
                    return false;
                }
                if (HasDuplicate(step.m_logReferenceIds))
                {
                    error = step.m_stepId + ": log references must be unique.";
                    return false;
                }
                stepIds.push_back(step.m_stepId);
            }
            if (HasDuplicate(stepIds))
            {
                error = "Attempted step identities must be unique.";
                return false;
            }

            AZStd::vector<AZStd::string> failureIds;
            failureIds.reserve(envelope.m_failures.size());
            for (const AdapterRuntimeFailure& failure : envelope.m_failures)
            {
                if (!IsAdapterRuntimeStableId(failure.m_failureId)
                    || !IsLowerToken(failure.m_code)
                    || failure.m_message.empty())
                {
                    error = "Failures require a stable ID, lowercase code, and non-empty message.";
                    return false;
                }
                if (!failure.m_stepId.empty() && !Contains(stepIds, failure.m_stepId))
                {
                    error = failure.m_failureId + ": failure references an unknown step.";
                    return false;
                }
                if (HasDuplicate(failure.m_logReferenceIds))
                {
                    error = failure.m_failureId + ": log references must be unique.";
                    return false;
                }
                failureIds.push_back(failure.m_failureId);
            }
            if (HasDuplicate(failureIds))
            {
                error = "Failure identities must be unique.";
                return false;
            }

            AZStd::vector<AZStd::string> logIds;
            logIds.reserve(envelope.m_logReferences.size());
            for (const AdapterRuntimeLogReference& log : envelope.m_logReferences)
            {
                if (!IsAdapterRuntimeStableId(log.m_logId)
                    || !IsAdapterRuntimeLogReference(log.m_reference)
                    || !IsAdapterRuntimeFingerprint(log.m_fingerprint))
                {
                    error = "Log references require stable IDs, safe relative locators, and SHA-256 fingerprints.";
                    return false;
                }
                if (HasDuplicate(log.m_stepIds))
                {
                    error = log.m_logId + ": step references must be unique.";
                    return false;
                }
                for (const AZStd::string& stepId : log.m_stepIds)
                {
                    if (!Contains(stepIds, stepId))
                    {
                        error = log.m_logId + ": log references an unknown step.";
                        return false;
                    }
                }
                logIds.push_back(log.m_logId);
            }
            if (HasDuplicate(logIds))
            {
                error = "Log identities must be unique.";
                return false;
            }

            for (const AdapterRuntimeStepResult& step : envelope.m_stepResults)
            {
                for (const AZStd::string& failureId : step.m_failureIds)
                {
                    if (!Contains(failureIds, failureId))
                    {
                        error = step.m_stepId + ": step references an unknown failure.";
                        return false;
                    }
                }
                for (const AZStd::string& logId : step.m_logReferenceIds)
                {
                    if (!Contains(logIds, logId))
                    {
                        error = step.m_stepId + ": step references an unknown log.";
                        return false;
                    }
                }
            }
            for (const AdapterRuntimeFailure& failure : envelope.m_failures)
            {
                for (const AZStd::string& logId : failure.m_logReferenceIds)
                {
                    if (!Contains(logIds, logId))
                    {
                        error = failure.m_failureId + ": failure references an unknown log.";
                        return false;
                    }
                }
            }

            if (!ValidateRecoveryShape(envelope.m_cleanupResult, error)
                || !ValidateRecoveryShape(envelope.m_rollbackResult, error))
            {
                return false;
            }
            for (const AdapterRuntimeRecoveryResult* recovery : {
                     &envelope.m_cleanupResult,
                     &envelope.m_rollbackResult })
            {
                if (!Contains(stepIds, recovery->m_stepId))
                {
                    error = "Cleanup or rollback summary references an unknown step.";
                    return false;
                }
                for (const AZStd::string& failureId : recovery->m_failureIds)
                {
                    if (!Contains(failureIds, failureId))
                    {
                        error = "Cleanup or rollback summary references an unknown failure.";
                        return false;
                    }
                }
                for (const AZStd::string& logId : recovery->m_logReferenceIds)
                {
                    if (!Contains(logIds, logId))
                    {
                        error = "Cleanup or rollback summary references an unknown log.";
                        return false;
                    }
                }
            }
            return true;
        }
    } // namespace

    AZStd::string ToString(AdapterRuntimeOutcome outcome)
    {
        return ToEnumString(outcome, Outcomes);
    }

    AZStd::string ToString(AdapterRuntimeFailureKind kind)
    {
        return ToEnumString(kind, FailureKinds);
    }

    AZStd::string ToString(AdapterRuntimeLogKind kind)
    {
        return ToEnumString(kind, LogKinds);
    }

    bool TryParseAdapterRuntimeOutcome(
        const AZStd::string& value,
        AdapterRuntimeOutcome& outcome)
    {
        return TryParseEnum(value, outcome, Outcomes);
    }

    bool TryParseAdapterRuntimeFailureKind(
        const AZStd::string& value,
        AdapterRuntimeFailureKind& kind)
    {
        return TryParseEnum(value, kind, FailureKinds);
    }

    bool TryParseAdapterRuntimeLogKind(
        const AZStd::string& value,
        AdapterRuntimeLogKind& kind)
    {
        return TryParseEnum(value, kind, LogKinds);
    }

    bool IsAdapterRuntimeStableId(const AZStd::string& value)
    {
        if (value.size() < 3
            || !IsLowerAlphaNumeric(value.front())
            || !IsLowerAlphaNumeric(value.back())
            || value.find('.') == AZStd::string::npos)
        {
            return false;
        }
        bool previousSeparator = false;
        for (char character : value)
        {
            const bool separator = character == '.' || character == '-' || character == '_';
            if (!IsLowerAlphaNumeric(character) && !separator)
            {
                return false;
            }
            if (separator && previousSeparator)
            {
                return false;
            }
            previousSeparator = separator;
        }
        return true;
    }

    bool IsAdapterRuntimeFingerprint(const AZStd::string& value)
    {
        constexpr const char* Prefix = "sha256:";
        constexpr size_t PrefixSize = 7;
        if (value.size() != PrefixSize + 64 || value.compare(0, PrefixSize, Prefix) != 0)
        {
            return false;
        }
        for (size_t index = PrefixSize; index < value.size(); ++index)
        {
            const char character = value[index];
            if (!((character >= '0' && character <= '9')
                || (character >= 'a' && character <= 'f')))
            {
                return false;
            }
        }
        return true;
    }

    bool IsAdapterRuntimeLogReference(const AZStd::string& value)
    {
        if (value.empty()
            || value.front() == '/'
            || value.front() == '\\'
            || value.find("..") != AZStd::string::npos)
        {
            return false;
        }
        for (char character : value)
        {
            if (!IsAsciiAlphaNumeric(character)
                && character != '.'
                && character != '-'
                && character != '_'
                && character != '/')
            {
                return false;
            }
        }
        return true;
    }

    AdapterRuntimeResultRegistry& AdapterRuntimeResultRegistry::Get()
    {
        static AdapterRuntimeResultRegistry registry;
        return registry;
    }

    bool AdapterRuntimeResultRegistry::RegisterEnvelope(
        const AdapterRuntimeResultEnvelope& envelope,
        AZStd::string* error)
    {
        AZStd::string validationError;
        if (!ValidateEnvelopeShape(envelope, validationError))
        {
            if (error)
            {
                *error = AZStd::move(validationError);
            }
            return false;
        }
        for (const AdapterRuntimeResultEnvelope& existing : m_envelopes)
        {
            if (existing.m_resultId == envelope.m_resultId)
            {
                if (error)
                {
                    *error = "Adapter runtime result ID is already registered.";
                }
                return false;
            }
            if (existing.m_profileId == envelope.m_profileId
                && existing.m_resultFingerprint == envelope.m_resultFingerprint)
            {
                if (error)
                {
                    *error = "Adapter runtime result fingerprint is already registered for this profile.";
                }
                return false;
            }
        }
        m_envelopes.push_back(envelope);
        AZStd::sort(
            m_envelopes.begin(),
            m_envelopes.end(),
            [](const AdapterRuntimeResultEnvelope& left, const AdapterRuntimeResultEnvelope& right)
            {
                return left.m_resultId < right.m_resultId;
            });
        return true;
    }

    void AdapterRuntimeResultRegistry::Clear()
    {
        m_envelopes.clear();
    }

    const AdapterRuntimeResultEnvelope* AdapterRuntimeResultRegistry::FindByResultId(
        const AZStd::string& resultId) const
    {
        for (const AdapterRuntimeResultEnvelope& envelope : m_envelopes)
        {
            if (envelope.m_resultId == resultId)
            {
                return &envelope;
            }
        }
        return nullptr;
    }

    const AZStd::vector<AdapterRuntimeResultEnvelope>&
    AdapterRuntimeResultRegistry::GetEnvelopes() const
    {
        return m_envelopes;
    }
} // namespace TaintedGrailModdingSDK
