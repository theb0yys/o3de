/*
 * Copyright (c) Contributors to the Open 3D Engine Project.
 * For complete copyright and license terms please see the LICENSE at the root of this distribution.
 *
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 */

                AZStd::vector<AZStd::string> acceptedEvidence;
                if (!EvidenceSetIsValidForSubjects(
                        validation.m_evidenceIds,
                        allowedSubjectRefs,
                        profile,
                        sourceRegistry))
                {
                    continue;
                }
                AddAllUnique(acceptedEvidence, validation.m_evidenceIds);
                AddAllUnique(evidenceIds, acceptedEvidence);
                AddUnique(validationIds, validation.m_validationId);
                validProofFound = true;
            }
            SortUnique(evidenceIds);
            SortUnique(validationIds);
            return validProofFound;
        }

        bool CollectPermissionProof(
            const CatalogRecord& record,
            const AZStd::string& usage,
            const GameProfile& profile,
            const SourceEvidenceRegistry& sourceRegistry,
            const CatalogDatabase& catalog,
            ReadySubject& readySubject)
        {
            bool validProofFound = false;
            for (const CatalogGovernanceEvent& event : catalog.GetGovernanceHistory())
            {
                if (event.m_subjectKind != "record"
                    || event.m_subjectId != record.m_recordId
                    || event.m_axis != "permission"
                    || event.m_usage != usage
                    || event.m_newValue != "allow"
                    || event.m_validationIds.empty()
                    || !EvidenceSetIsValid(
                        event.m_evidenceIds,
                        record.m_subjectRef,
                        profile,
                        sourceRegistry))
                {
                    continue;
                }

                bool allValidationProofValid = true;
                AZStd::vector<AZStd::string> validationEvidenceIds;
                for (const AZStd::string& validationId : event.m_validationIds)
                {
                    if (!ValidationProofIsValid(
                        validationId,
                        record,
                        profile,
                        sourceRegistry,
                        catalog,
                        validationEvidenceIds))
                    {
                        allValidationProofValid = false;
                        break;
                    }
                }
                if (!allValidationProofValid)
                {
                    continue;
                }

                validProofFound = true;
                AddUnique(readySubject.m_permissionEventIds, event.m_eventId);
                AddAllUnique(readySubject.m_permissionEvidenceIds, event.m_evidenceIds);
                AddAllUnique(readySubject.m_validationEvidenceIds, validationEvidenceIds);
                AddAllUnique(readySubject.m_validationIds, event.m_validationIds);
            }
            SortUnique(readySubject.m_permissionEventIds);
            SortUnique(readySubject.m_permissionEvidenceIds);
            SortUnique(readySubject.m_validationEvidenceIds);
            SortUnique(readySubject.m_validationIds);
            return validProofFound;
        }

        bool HasOpenBlocker(
            const CatalogRecord& record,
            const AZStd::string& usage,
            const AZStd::vector<BlockerRecord>& blockers)
        {
            for (const BlockerRecord& blocker : blockers)
            {
                if (blocker.m_status != "open" || blocker.m_subjectRef != record.m_subjectRef)
                {
                    continue;
                }
                if (blocker.m_affectedUsages.empty()
                    || Contains(blocker.m_affectedUsages, usage))
                {
                    return true;
                }
            }
            return false;
        }

        AZStd::vector<ReadySubject> CollectReadySubjects(
            const PackManifest& pack,
            AdapterCapability capability,
            const GameProfile& profile,
            const SourceEvidenceRegistry& sourceRegistry,
            const CatalogDatabase& catalog,
            const AZStd::vector<BlockerRecord>& blockers)
        {
            AZStd::vector<ReadySubject> readySubjects;
            if (!PermissionIsRequired(capability))
            {
                return readySubjects;
            }
            const AZStd::string usage = PermissionUsage(capability);
            for (const CatalogRecord& record : catalog.GetRecords())
            {
                if (record.m_ownerPackId != pack.m_packId
                    || !IsEligibleSubject(record, capability, catalog)
                    || !Contains(record.m_allowedUsages, usage)
                    || !IsCurrentValidated(record)
                    || HasOpenBlocker(record, usage, blockers))
                {
                    continue;
                }

                ReadySubject readySubject;
                readySubject.m_record = &record;
                readySubject.m_relationships = FindRelationshipsForCapability(
                    record,
                    capability,
                    catalog);
                if (!CollectPermissionProof(
                        record,
                        usage,
                        profile,
                        sourceRegistry,
                        catalog,
                        readySubject))
                {
                    continue;
                }
                readySubjects.push_back(AZStd::move(readySubject));
            }
            AZStd::sort(
                readySubjects.begin(),
                readySubjects.end(),
                [](const ReadySubject& left, const ReadySubject& right)
                {
                    return left.m_record->m_recordId < right.m_record->m_recordId;
                });
            return readySubjects;
        }

        AZStd::vector<AZStd::string> CollectRecordInputEvidence(
            const CatalogRecord& record,
            const CatalogDatabase& catalog)
        {
            AZStd::vector<AZStd::string> evidenceIds = record.m_evidenceIds;
            if (record.m_recordKind == "item")
            {
                if (const EconomyItemProfile* profile = catalog.FindEconomyItem(record.m_recordId))
                {
                    AddAllUnique(evidenceIds, profile->m_evidenceIds);
                }
            }
            else if (record.m_recordKind == "recipe")
            {
                if (const EconomyRecipeProfile* profile = catalog.FindEconomyRecipe(record.m_recordId))
                {
                    AddAllUnique(evidenceIds, profile->m_evidenceIds);
                }
                for (const EconomyRecipeIngredient& ingredient
                    : catalog.FindIngredientsForRecipe(record.m_recordId))
                {
                    AddAllUnique(evidenceIds, ingredient.m_evidenceIds);
                }
                for (const EconomyRecipeOutput& output
                    : catalog.FindOutputsForRecipe(record.m_recordId))
                {
                    AddAllUnique(evidenceIds, output.m_evidenceIds);
                }
            }
            SortUnique(evidenceIds);
            return evidenceIds;
        }

        void AddRecordArguments(
            AdapterWorkOrderStep& step,
            const CatalogRecord& record,
            const CatalogDatabase& catalog)
        {
            AddArgument(step.m_arguments, "catalog_record_id", record.m_recordId);
            AddArgument(step.m_arguments, "catalog_subject_ref", record.m_subjectRef);
            AddArgument(step.m_arguments, "owner_pack_id", record.m_ownerPackId);
            AddArgument(step.m_arguments, "identity_kind", record.m_identityKind);
            AddArgument(step.m_arguments, "native_ref_exact", record.m_nativeRefExact);

