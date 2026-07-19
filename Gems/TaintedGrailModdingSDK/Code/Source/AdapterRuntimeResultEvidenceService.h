/*
 * Copyright (c) Contributors to the Open 3D Engine Project.
 * For complete copyright and license terms please see the LICENSE at the root of this distribution.
 *
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 */

#pragma once

#include "AdapterRuntimeResultContracts.h"
#include "AdapterWorkOrderPlanningService.h"
#include "FoundationModels.h"

namespace TaintedGrailModdingSDK
{
    struct AdapterRuntimeResultIssue
    {
        AZStd::string m_code;
        AZStd::string m_message;
        AZStd::string m_stepId;
    };

    struct AdapterRuntimeEvidenceReturn
    {
        AZStd::string m_resultId;
        AZStd::string m_planId;
        AZStd::string m_planFingerprint;
        AZStd::string m_resultFingerprint;
        AZ::u64 m_stepResultCount = 0;
        AZ::u64 m_failureCount = 0;
        AZ::u64 m_logReferenceCount = 0;
        AZ::u64 m_sourceDocumentCount = 0;
        AZ::u64 m_evidenceRecordCount = 0;
        AZStd::vector<SourceDocument> m_sourceDocuments;
        AZStd::vector<EvidenceDocument> m_evidenceDocuments;
        AZStd::vector<AdapterRuntimeResultIssue> m_issues;
        bool m_accepted = false;
    };

    class AdapterRuntimeResultEvidenceService
    {
    public:
        AdapterRuntimeEvidenceReturn BuildEvidenceReturn(
            const AdapterWorkOrderPlan& plan,
            const AdapterRuntimeResultEnvelope& envelope) const;
    };
} // namespace TaintedGrailModdingSDK
