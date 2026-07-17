/*
 * Copyright (c) Contributors to the Open 3D Engine Project.
 * For complete copyright and license terms please see the LICENSE at the root of this distribution.
 *
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 */

#pragma once

#include "CatalogDatabase.h"

#include <AzCore/Outcome/Outcome.h>

namespace TaintedGrailModdingSDK
{
    struct EconomyAcquisitionRequest
    {
        AZStd::string m_relationshipId;
        AZStd::string m_sourceRecordId;
        AZStd::string m_targetRecordId;
        AZStd::string m_targetSubjectRef;
        AZStd::string m_relationshipKind;
        AZStd::vector<AZStd::string> m_evidenceIds;
        AZStd::vector<AZStd::string> m_attributes;
    };

    struct EconomyActionLaneStatus
    {
        AZStd::string m_lane;
        AZStd::string m_status;
    };

    class EconomyAuthoringService
    {
    public:
        AZ::Outcome<CatalogRelationship, AZStd::string> BuildAcquisitionRelationship(
            const EconomyAcquisitionRequest& request,
            const CatalogDatabase& catalog) const;

        AZStd::vector<EconomyActionLaneStatus> BuildActionLaneMatrix(const CatalogRecord& record) const;
    };
} // namespace TaintedGrailModdingSDK
