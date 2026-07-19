/*
 * Copyright (c) Contributors to the Open 3D Engine Project.
 * For complete copyright and license terms please see the LICENSE at the root of this distribution.
 *
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 */

        void AppendJsonStringArray(
            AZStd::string& output,
            const AZStd::vector<AZStd::string>& values)
        {
            output.push_back('[');
            for (size_t index = 0; index < values.size(); ++index)
            {
                if (index != 0)
                {
                    output.push_back(',');
                }
                AppendJsonString(output, values[index]);
            }
            output.push_back(']');
        }

        void SortStepCollections(AdapterWorkOrderStep& step)
        {
            SortArguments(step.m_arguments);
            SortUnique(step.m_inputEvidenceIds);
            SortUnique(step.m_declarationEvidenceIds);
            SortUnique(step.m_permissionEventIds);
            SortUnique(step.m_permissionEvidenceIds);
            SortUnique(step.m_validationProofIds);
        }

        void SortSteps(AZStd::vector<AdapterWorkOrderStep>& steps)
        {
            for (AdapterWorkOrderStep& step : steps)
            {
                SortStepCollections(step);
            }
            AZStd::sort(
                steps.begin(),
                steps.end(),
                [](const AdapterWorkOrderStep& left, const AdapterWorkOrderStep& right)
                {
                    const AZ::u64 leftRank = CapabilityRank(left.m_capability);
                    const AZ::u64 rightRank = CapabilityRank(right.m_capability);
                    if (leftRank != rightRank)
                    {
                        return leftRank < rightRank;
                    }
                    if (left.m_subjectKind != right.m_subjectKind)
                    {
                        return left.m_subjectKind < right.m_subjectKind;
                    }
                    if (left.m_subjectId != right.m_subjectId)
                    {
                        return left.m_subjectId < right.m_subjectId;
                    }
                    return left.m_stepId < right.m_stepId;
                });
            for (size_t index = 0; index < steps.size(); ++index)
            {
                steps[index].m_sequence = static_cast<AZ::u64>(index + 1);
            }
        }
    } // namespace

    AdapterWorkOrderPlanSet AdapterWorkOrderPlanningService::BuildPlans(
        const WorkspaceModel& workspace,
        const AZStd::vector<PackManifest>& packs,
        const AdapterContractRegistry& adapterRegistry,
        const SourceEvidenceRegistry& sourceRegistry,
        const CatalogDatabase& catalog,
        const AZStd::vector<BlockerRecord>& blockers) const
    {
        AdapterWorkOrderPlanSet result;
        AdapterCompatibilityService compatibilityService;
        const AdapterCapabilityMatrix matrix = compatibilityService.BuildCapabilityMatrix(
            workspace,
            packs,
            adapterRegistry,
            sourceRegistry,
            catalog,
            blockers);
        const GameProfile* profile = workspace.FindActiveGameProfile();
        const AZStd::vector<MatrixGroup> groups = BuildGroups(
            matrix,
            packs,
            adapterRegistry);

        result.m_candidatePlanCount = static_cast<AZ::u64>(groups.size());
        for (const MatrixGroup& group : groups)
        {
            if (!profile || !GroupIsSupported(group))
            {
                AdapterWorkOrderRefusal refusal = BuildCompatibilityRefusal(group, profile);
                if (!profile)
                {
                    AddUnique(
                        refusal.m_reasons,
                        "A canonical work-order plan requires an exact active game profile.");
                }
                SortUnique(refusal.m_reasons);
                result.m_refusals.push_back(AZStd::move(refusal));
                continue;
            }

            AdapterWorkOrderPlan plan;
            plan.m_planId = BuildPlanId(*group.m_pack, group.m_declaration, profile);
            plan.m_packId = group.m_pack->m_packId;
            plan.m_packVersion = group.m_pack->m_version;
            plan.m_adapterId = group.m_declaration->m_adapterId;
            plan.m_adapterVersion = group.m_declaration->m_version;
            plan.m_requiredAdapterVersion = group.m_pack->m_requiredAdapterVersion;
            plan.m_profileId = profile->m_profileId;
            plan.m_gameVersion = profile->m_gameVersion;
            plan.m_branch = profile->m_branch;
            plan.m_runtimeTarget = profile->m_runtimeTarget;

            AZStd::vector<AZStd::string> planningErrors;
            for (AdapterCapability capability : AllCapabilities)
            {
                const AdapterCapabilityMatrixRow* matrixRow = FindMatrixRow(group, capability);
                if (!matrixRow)
                {
                    planningErrors.push_back(
                        "The supported compatibility set is missing capability: "
                        + ToString(capability));
                    continue;
                }

                if (!PermissionIsRequired(capability))
                {
                    plan.m_steps.push_back(BuildPackStep(
                        plan,
                        *group.m_pack,
                        capability,
                        *matrixRow));
                    continue;
                }

                const AZStd::vector<ReadySubject> readySubjects = CollectReadySubjects(
                    *group.m_pack,
                    capability,
                    *profile,
                    sourceRegistry,
                    catalog,
                    blockers);
                if (readySubjects.empty())
                {
                    planningErrors.push_back(
                        "No exact reviewed subject remained ready while building capability: "
                        + ToString(capability));
                    continue;
                }

                for (const ReadySubject& readySubject : readySubjects)
                {
                    AZStd::string payloadError;
                    if (!RecordPayloadIsComplete(
                            *readySubject.m_record,
                            capability,
                            *profile,
                            sourceRegistry,
                            catalog,
                            payloadError))
                    {
                        planningErrors.push_back(
                            readySubject.m_record->m_recordId + ": " + payloadError);
                        continue;
                    }

