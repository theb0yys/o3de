/*
 * Copyright (c) Contributors to the Open 3D Engine Project.
 * For complete copyright and license terms please see the LICENSE at the root of this distribution.
 *
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 */

#pragma once

#include "AdapterCompatibilityService.h"

#include <AzCore/base.h>
#include <AzCore/std/containers/vector.h>
#include <AzCore/std/string/string.h>

namespace TaintedGrailModdingSDK
{
    struct AdapterWorkOrderArgument
    {
        AZStd::string m_key;
        AZStd::string m_value;
    };

    struct AdapterWorkOrderStep
    {
        AZStd::string m_stepId;
        AZ::u64 m_sequence = 0;
        AZStd::string m_capability;
        AZStd::string m_subjectKind;
        AZStd::string m_subjectId;
        AZStd::string m_subjectRef;
        AZStd::string m_sourceRecordId;
        AZStd::string m_relationshipId;
        AZStd::string m_targetRecordId;
        AZStd::string m_targetSubjectRef;
        AZStd::vector<AdapterWorkOrderArgument> m_arguments;
        AZStd::vector<AZStd::string> m_inputEvidenceIds;
        AZStd::vector<AZStd::string> m_declarationEvidenceIds;
        AZStd::vector<AZStd::string> m_permissionEventIds;
        AZStd::vector<AZStd::string> m_permissionEvidenceIds;
        AZStd::vector<AZStd::string> m_validationProofIds;
        bool m_executionAllowed = false;
    };

    struct AdapterWorkOrderPlan
    {
        AZ::u32 m_formatVersion = 1;
        AZStd::string m_planId;
        AZStd::string m_packId;
        AZStd::string m_packVersion;
        AZStd::string m_adapterId;
        AZStd::string m_adapterVersion;
        AZStd::string m_requiredAdapterVersion;
        AZStd::string m_profileId;
        AZStd::string m_gameVersion;
        AZStd::string m_branch;
        AZStd::string m_runtimeTarget;
        AZStd::vector<AdapterWorkOrderStep> m_steps;
        AZStd::string m_canonicalJson;
        bool m_executionAllowed = false;
    };

    struct AdapterWorkOrderRefusal
    {
        AZStd::string m_planId;
        AZStd::string m_packId;
        AZStd::string m_adapterId;
        AZStd::string m_adapterVersion;
        AZStd::string m_runtimeTarget;
        AZStd::vector<AZStd::string> m_failedCapabilities;
        AZStd::vector<AZStd::string> m_compatibilityStatuses;
        AZStd::vector<AZStd::string> m_subjectIds;
        AZStd::vector<AZStd::string> m_reasons;
    };

    struct AdapterWorkOrderPlanSet
    {
        AZ::u64 m_candidatePlanCount = 0;
        AZ::u64 m_generatedPlanCount = 0;
        AZ::u64 m_refusedPlanCount = 0;
        AZ::u64 m_stepCount = 0;
        AZStd::vector<AdapterWorkOrderPlan> m_plans;
        AZStd::vector<AdapterWorkOrderRefusal> m_refusals;
    };

    class AdapterWorkOrderPlanningService
    {
    public:
        AdapterWorkOrderPlanSet BuildPlans(
            const WorkspaceModel& workspace,
            const AZStd::vector<PackManifest>& packs,
            const AdapterContractRegistry& adapterRegistry,
            const SourceEvidenceRegistry& sourceRegistry,
            const CatalogDatabase& catalog,
            const AZStd::vector<BlockerRecord>& blockers) const;

        AZStd::string SerializeCanonicalPlan(const AdapterWorkOrderPlan& plan) const;
    };
} // namespace TaintedGrailModdingSDK
