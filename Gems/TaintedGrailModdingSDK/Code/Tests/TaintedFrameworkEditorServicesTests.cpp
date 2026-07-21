/*
 * Copyright (c) Contributors to the Open 3D Engine Project.
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 */
#include <AzTest/AzTest.h>

#include "TaintedFrameworkEditorServices.h"

namespace TaintedGrailModdingSDK
{
    using namespace TaintedFrameworkEditorServices;

    TEST(TaintedFrameworkEditorServicesTests, ExactMonoEvidenceIsReady)
    {
        Service service;
        const auto result = service.EvaluateCompatibility("1.23.401", "Mono", "Mono");
        EXPECT_EQ(result.m_status, ReadinessStatus::Ready);
        EXPECT_TRUE(result.m_blockers.empty());
        EXPECT_EQ(result.m_evidencePath, "mods/tainted-framework/release/manifest.md");
    }

    TEST(TaintedFrameworkEditorServicesTests, Il2CppRemainsBlocked)
    {
        Service service;
        const auto result = service.EvaluateCompatibility("unknown", "IL2CPP", "IL2CPP");
        EXPECT_EQ(result.m_status, ReadinessStatus::Blocked);
        ASSERT_EQ(result.m_blockers.size(), 1);
        EXPECT_EQ(result.m_blockers[0], "upstream_branch_blocked");
    }

    TEST(TaintedFrameworkEditorServicesTests, VersionDriftIsUnsupported)
    {
        Service service;
        const auto result = service.EvaluateCompatibility("1.23.402", "Mono", "Mono");
        EXPECT_EQ(result.m_status, ReadinessStatus::Unsupported);
        ASSERT_EQ(result.m_blockers.size(), 1);
        EXPECT_EQ(result.m_blockers[0], "exact_game_version_not_evidence_backed");
    }

    TEST(TaintedFrameworkEditorServicesTests, OnlyRuntimeReportIsConsumerReady)
    {
        Service service;
        const auto surfaces = service.GetApiSurfaceDecisions();
        size_t readyCount = 0;
        for (const auto& surface : surfaces)
        {
            if (surface.m_consumerReady)
            {
                ++readyCount;
                EXPECT_EQ(surface.m_surfaceId, "runtime-report");
                EXPECT_EQ(surface.m_consumerBinding, "mods/Tainted-Diagnostic Tool");
            }
            else
            {
                EXPECT_FALSE(surface.m_blockers.empty());
            }
        }
        EXPECT_EQ(readyCount, 1);
    }

    TEST(TaintedFrameworkEditorServicesTests, ActivationPlanIsReadOnlyAndDeterministic)
    {
        Service service;
        const auto first = service.BuildActivationPlan("1.23.401", "Mono", "Mono");
        const auto second = service.BuildActivationPlan("1.23.401", "Mono", "Mono");
        EXPECT_EQ(first.m_planId, second.m_planId);
        EXPECT_EQ(first.m_extensionId, "extension.tainted-framework");
        EXPECT_FALSE(first.m_runtimeInvocationAllowed);
        EXPECT_FALSE(first.m_fileWriteAllowed);
        EXPECT_FALSE(first.m_catalogMutationAllowed);
        EXPECT_TRUE(first.m_candidateEvidenceSubmissionAllowed);
        EXPECT_EQ(first.m_configuration.size(), 3);
        EXPECT_FALSE(first.m_diagnostics.empty());
    }

    TEST(TaintedFrameworkEditorServicesTests, BlockedPlanCannotSubmitCandidateEvidence)
    {
        Service service;
        const auto plan = service.BuildActivationPlan("unknown", "IL2CPP", "IL2CPP");
        EXPECT_EQ(plan.m_compatibility.m_status, ReadinessStatus::Blocked);
        EXPECT_FALSE(plan.m_candidateEvidenceSubmissionAllowed);
        EXPECT_FALSE(plan.m_runtimeInvocationAllowed);
        EXPECT_FALSE(plan.m_fileWriteAllowed);
        EXPECT_FALSE(plan.m_catalogMutationAllowed);
    }
} // namespace TaintedGrailModdingSDK
