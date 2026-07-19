/*
 * Copyright (c) Contributors to the Open 3D Engine Project.
 * For complete copyright and license terms please see the LICENSE at the root of this distribution.
 *
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 */

namespace
{
        void AddRecordWithProof(
            ReadyFixture& fixture,
            const CatalogRecord& record,
            const AZStd::vector<AZStd::string>& usages)
        {
            AZStd::string error;
            EXPECT_TRUE(fixture.m_catalog.InsertNew(record, &error)) << error.c_str();
            EXPECT_TRUE(fixture.m_catalog.AddValidationEvent(
                MakeValidation(
                    "validation.record." + record.m_recordId,
                    "record",
                    record.m_recordId,
                    record.m_evidenceIds.front()),
                &error)) << error.c_str();
            for (const AZStd::string& usage : usages)
            {
                EXPECT_TRUE(fixture.m_catalog.AddGovernanceEvent(
                    MakePermission(
                        "permission." + record.m_recordId + "." + usage,
                        record,
                        usage),
                    &error)) << error.c_str();
            }
        }

        void AddRelationshipWithProof(
            ReadyFixture& fixture,
            const CatalogRelationship& relationship,
            bool includeValidationProof)
        {
            AZStd::string error;
            EXPECT_TRUE(fixture.m_catalog.UpsertRelationship(relationship, &error))
                << error.c_str();
            if (includeValidationProof)
            {
                EXPECT_TRUE(fixture.m_catalog.AddValidationEvent(
                    MakeValidation(
                        "validation.relationship." + relationship.m_relationshipId,
                        "relationship",
                        relationship.m_relationshipId,
                        relationship.m_evidenceIds.front()),
                    &error)) << error.c_str();
            }
        }

} // namespace
