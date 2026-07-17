/*
 * Copyright (c) Contributors to the Open 3D Engine Project.
 * For complete copyright and license terms please see the LICENSE at the root of this distribution.
 *
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 */

#include "FoundationService.h"

namespace TaintedGrailModdingSDK
{
    namespace
    {
        bool ValidateEvidenceForSubjects(
            const AZStd::vector<AZStd::string>& evidenceIds,
            const AZStd::vector<AZStd::string>& allowedSubjectRefs,
            const SourceEvidenceRegistry& registry,
            AZStd::string& error)
        {
            if (evidenceIds.empty())
            {
                error = "Economy authoring requires evidence IDs.";
                return false;
            }
            for (const AZStd::string& evidenceId : evidenceIds)
            {
                const EvidenceRecord* evidence = registry.FindEvidence(evidenceId);
                if (!evidence)
                {
                    error = "Economy authoring references missing evidence: ";
                    error += evidenceId;
                    return false;
                }
                bool subjectAllowed = false;
                for (const AZStd::string& subjectRef : allowedSubjectRefs)
                {
                    if (!subjectRef.empty() && evidence->m_subjectRef == subjectRef)
                    {
                        subjectAllowed = true;
                        break;
                    }
                }
                if (!subjectAllowed)
                {
                    error = "Economy evidence belongs to a different catalog subject: ";
                    error += evidenceId;
                    return false;
                }
            }
            return true;
        }

        AZStd::vector<AZStd::string> BuildJoinSubjectRefs(
            const CatalogDatabase& catalog,
            const AZStd::string& recipeRecordId,
            const AZStd::string& itemRecordId,
            const AZStd::string& unresolvedItemSubjectRef)
        {
            AZStd::vector<AZStd::string> subjectRefs;
            if (const CatalogRecord* recipe = catalog.FindByRecordId(recipeRecordId))
            {
                subjectRefs.push_back(recipe->m_subjectRef);
            }
            if (const CatalogRecord* item = catalog.FindByRecordId(itemRecordId))
            {
                subjectRefs.push_back(item->m_subjectRef);
            }
            if (!unresolvedItemSubjectRef.empty())
            {
                subjectRefs.push_back(unresolvedItemSubjectRef);
            }
            return subjectRefs;
        }
    } // namespace

    bool FoundationService::UpsertEconomyItemProfile(
        const EconomyItemProfile& profile,
        AZStd::string* error)
    {
        const CatalogRecord* record = m_catalog.FindByRecordId(profile.m_recordId);
        AZStd::string evidenceError;
        if (!record || !ValidateEvidenceForSubjects(
                profile.m_evidenceIds,
                { record->m_subjectRef },
                m_sourceRegistry,
                evidenceError))
        {
            if (error)
            {
                *error = record ? evidenceError : AZStd::string("The canonical item record does not exist.");
            }
            return false;
        }

        CatalogDatabase candidate = m_catalog;
        AZStd::string catalogError;
        if (!candidate.UpsertEconomyItem(profile, &catalogError))
        {
            if (error)
            {
                *error = catalogError;
            }
            return false;
        }
        return PersistCatalogCandidate(candidate, error);
    }

    bool FoundationService::UpsertEconomyRecipeProfile(
        const EconomyRecipeProfile& profile,
        AZStd::string* error)
    {
        const CatalogRecord* record = m_catalog.FindByRecordId(profile.m_recordId);
        AZStd::string evidenceError;
        if (!record || !ValidateEvidenceForSubjects(
                profile.m_evidenceIds,
                { record->m_subjectRef },
                m_sourceRegistry,
                evidenceError))
        {
            if (error)
            {
                *error = record ? evidenceError : AZStd::string("The canonical recipe record does not exist.");
            }
            return false;
        }

        CatalogDatabase candidate = m_catalog;
        AZStd::string catalogError;
        if (!candidate.UpsertEconomyRecipe(profile, &catalogError))
        {
            if (error)
            {
                *error = catalogError;
            }
            return false;
        }
        return PersistCatalogCandidate(candidate, error);
    }

    bool FoundationService::UpsertEconomyRecipeIngredient(
        const EconomyRecipeIngredient& ingredient,
        AZStd::string* error)
    {
        AZStd::string evidenceError;
        if (!ValidateEvidenceForSubjects(
                ingredient.m_evidenceIds,
                BuildJoinSubjectRefs(
                    m_catalog,
                    ingredient.m_recipeRecordId,
                    ingredient.m_itemRecordId,
                    ingredient.m_itemSubjectRef),
                m_sourceRegistry,
                evidenceError))
        {
            if (error)
            {
                *error = evidenceError;
            }
            return false;
        }

        CatalogDatabase candidate = m_catalog;
        AZStd::string catalogError;
        if (!candidate.UpsertRecipeIngredient(ingredient, &catalogError))
        {
            if (error)
            {
                *error = catalogError;
            }
            return false;
        }
        return PersistCatalogCandidate(candidate, error);
    }

    bool FoundationService::UpsertEconomyRecipeOutput(
        const EconomyRecipeOutput& output,
        AZStd::string* error)
    {
        AZStd::string evidenceError;
        if (!ValidateEvidenceForSubjects(
                output.m_evidenceIds,
                BuildJoinSubjectRefs(
                    m_catalog,
                    output.m_recipeRecordId,
                    output.m_itemRecordId,
                    output.m_itemSubjectRef),
                m_sourceRegistry,
                evidenceError))
        {
            if (error)
            {
                *error = evidenceError;
            }
            return false;
        }

        CatalogDatabase candidate = m_catalog;
        AZStd::string catalogError;
        if (!candidate.UpsertRecipeOutput(output, &catalogError))
        {
            if (error)
            {
                *error = catalogError;
            }
            return false;
        }
        return PersistCatalogCandidate(candidate, error);
    }
} // namespace TaintedGrailModdingSDK
