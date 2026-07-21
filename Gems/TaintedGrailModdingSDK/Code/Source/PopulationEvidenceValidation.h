/*
 * Copyright (c) Contributors to the Open 3D Engine Project.
 * For complete copyright and license terms please see the LICENSE at the root of this distribution.
 *
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 */

#pragma once

#include "ResearchContractValidation.h"
#include "SourceEvidenceRegistry.h"

#include <AzCore/std/algorithm.h>
#include <AzCore/std/containers/vector.h>
#include <AzCore/std/sort.h>
#include <AzCore/std/string/string.h>

namespace TaintedGrailModdingSDK
{
    inline void AppendUniquePopulationEvidenceId(
        AZStd::vector<AZStd::string>& values,
        const AZStd::string& value)
    {
        if (!value.empty()
            && AZStd::find(values.begin(), values.end(), value) == values.end())
        {
            values.push_back(value);
        }
    }

    inline void AppendUniquePopulationEvidenceIds(
        AZStd::vector<AZStd::string>& values,
        const AZStd::vector<AZStd::string>& additions)
    {
        for (const AZStd::string& value : additions)
        {
            AppendUniquePopulationEvidenceId(values, value);
        }
    }

    inline void AppendUniquePopulationRequiredSubject(
        AZStd::vector<AZStd::string>& values,
        const AZStd::string& value)
    {
        if (!value.empty()
            && AZStd::find(values.begin(), values.end(), value) == values.end())
        {
            values.push_back(value);
        }
    }

    inline bool IsBoundedPopulationEvidenceSubject(
        const AZStd::string& value)
    {
        if (value.empty() || value.size() > 1024)
        {
            return false;
        }
        for (char character : value)
        {
            const unsigned char byte = static_cast<unsigned char>(character);
            if (byte < 0x20 || byte == 0x7f)
            {
                return false;
            }
        }
        return true;
    }

    inline bool PopulationEvidenceIsCompleteAndBound(
        const EvidenceRecord& evidence,
        const SourceRecord& source,
        const GameProfile& profile)
    {
        return !evidence.m_claim.empty()
            && !evidence.m_evidenceKind.empty()
            && !evidence.m_confidence.empty()
            && !evidence.m_locator.empty()
            && !evidence.m_recordPath.empty()
            && IsSha256Fingerprint(evidence.m_sourceFingerprint)
            && IsStrictUtcTimestamp(evidence.m_extractedAt)
            && IsSha256Fingerprint(source.m_fingerprint)
            && IsStrictUtcTimestamp(source.m_capturedAt)
            && IsStrictUtcTimestamp(source.m_importedAt)
            && IsUsableImportStatus(source.m_importStatus)
            && evidence.m_sourceId == source.m_sourceId
            && evidence.m_sourceFingerprint == source.m_fingerprint
            && evidence.m_profileId == profile.m_profileId
            && evidence.m_gameVersion == profile.m_gameVersion
            && evidence.m_branch == profile.m_branch
            && source.m_profileId == profile.m_profileId
            && source.m_gameVersion == profile.m_gameVersion
            && source.m_branch == profile.m_branch
            && source.m_runtimeTarget == profile.m_runtimeTarget
            && source.m_capturedAt <= evidence.m_extractedAt
            && evidence.m_extractedAt <= source.m_importedAt;
    }

    //! Requires every supplied evidence row to bind to an expected subject and
    //! every expected subject to be covered by at least one complete evidence row.
    //! Callers may combine the authored row's evidence with the exact canonical
    //! records that establish related template, leader, troop, or actor bindings.
    inline bool ValidatePopulationEvidenceCoverage(
        const AZStd::vector<AZStd::string>& evidenceIds,
        const AZStd::vector<AZStd::string>& requiredSubjects,
        const GameProfile& profile,
        const SourceEvidenceRegistry& sourceRegistry,
        const char* authoredArea,
        AZStd::string& error)
    {
        if (evidenceIds.empty() || requiredSubjects.empty())
        {
            error = AZStd::string(authoredArea)
                + " requires evidence for every exact authored binding.";
            return false;
        }

        AZStd::vector<AZStd::string> canonicalEvidenceIds = evidenceIds;
        AZStd::sort(canonicalEvidenceIds.begin(), canonicalEvidenceIds.end());
        if (AZStd::adjacent_find(
                canonicalEvidenceIds.begin(),
                canonicalEvidenceIds.end()) != canonicalEvidenceIds.end())
        {
            error = AZStd::string(authoredArea)
                + " evidence IDs must be unique.";
            return false;
        }

        AZStd::vector<AZStd::string> canonicalSubjects = requiredSubjects;
        for (const AZStd::string& subject : canonicalSubjects)
        {
            if (!IsBoundedPopulationEvidenceSubject(subject))
            {
                error = AZStd::string(authoredArea)
                    + " requires bounded, non-empty exact subjects.";
                return false;
            }
        }
        AZStd::sort(canonicalSubjects.begin(), canonicalSubjects.end());
        if (AZStd::adjacent_find(
                canonicalSubjects.begin(),
                canonicalSubjects.end()) != canonicalSubjects.end())
        {
            error = AZStd::string(authoredArea)
                + " required subjects must be unique.";
            return false;
        }

        AZStd::vector<bool> covered(canonicalSubjects.size(), false);
        for (const AZStd::string& evidenceId : canonicalEvidenceIds)
        {
            if (!IsStableContractId(evidenceId))
            {
                error = AZStd::string(authoredArea)
                    + " evidence IDs must be stable bounded identities.";
                return false;
            }

            const EvidenceRecord* evidence =
                sourceRegistry.FindEvidence(evidenceId);
            const SourceRecord* source = evidence
                ? sourceRegistry.FindSource(evidence->m_sourceId)
                : nullptr;
            if (!evidence
                || !source
                || !PopulationEvidenceIsCompleteAndBound(
                    *evidence,
                    *source,
                    profile))
            {
                error = AZStd::string(authoredArea)
                    + " evidence is missing, incomplete, or bound to a different "
                      "profile: "
                    + evidenceId;
                return false;
            }

            const auto subject = AZStd::lower_bound(
                canonicalSubjects.begin(),
                canonicalSubjects.end(),
                evidence->m_subjectRef);
            if (subject == canonicalSubjects.end()
                || *subject != evidence->m_subjectRef)
            {
                error = AZStd::string(authoredArea)
                    + " evidence proves an unrelated subject: " + evidenceId;
                return false;
            }
            covered[static_cast<size_t>(subject - canonicalSubjects.begin())] = true;
        }

        for (size_t index = 0; index < canonicalSubjects.size(); ++index)
        {
            if (!covered[index])
            {
                error = AZStd::string(authoredArea)
                    + " is missing evidence for exact subject "
                    + canonicalSubjects[index] + ".";
                return false;
            }
        }
        return true;
    }
} // namespace TaintedGrailModdingSDK
