/*
 * Copyright (c) Contributors to the Open 3D Engine Project.
 * For complete copyright and license terms please see the LICENSE at the root of this distribution.
 *
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 */

    TEST(TaintedGrailAdapterWorkOrderPlanningTests, CanonicalSerializationIsDeterministic)
    {
        ReadyFixture firstFixture = MakeReadyFixture(false);
        ReadyFixture secondFixture = MakeReadyFixture(true);
        AdapterWorkOrderPlanningService service;
        const AdapterWorkOrderPlanSet first = service.BuildPlans(
            firstFixture.m_workspace,
            firstFixture.m_packs,
            firstFixture.m_adapterRegistry,
            firstFixture.m_sourceRegistry,
            firstFixture.m_catalog,
            firstFixture.m_blockers);
        const AdapterWorkOrderPlanSet second = service.BuildPlans(
            secondFixture.m_workspace,
            secondFixture.m_packs,
            secondFixture.m_adapterRegistry,
            secondFixture.m_sourceRegistry,
            secondFixture.m_catalog,
            secondFixture.m_blockers);

        ASSERT_EQ(first.m_generatedPlanCount, 1);
        ASSERT_EQ(second.m_generatedPlanCount, 1);
        EXPECT_EQ(
            first.m_plans.front().m_planId,
            second.m_plans.front().m_planId);
        EXPECT_EQ(
            first.m_plans.front().m_canonicalJson,
            second.m_plans.front().m_canonicalJson);
    }

    TEST(TaintedGrailAdapterWorkOrderPlanningTests, PlanningDoesNotMutateInputs)
    {
        ReadyFixture fixture = MakeReadyFixture();
        const size_t declarationCountBefore =
            fixture.m_adapterRegistry.GetDeclarations().size();
        const size_t sourceCountBefore = fixture.m_sourceRegistry.GetSources().size();
        const size_t evidenceCountBefore = fixture.m_sourceRegistry.GetEvidence().size();
        const size_t recordCountBefore = fixture.m_catalog.GetRecords().size();
        const size_t relationshipCountBefore =
            fixture.m_catalog.GetRelationships().size();
        const size_t validationCountBefore =
            fixture.m_catalog.GetValidationHistory().size();
        const size_t governanceCountBefore =
            fixture.m_catalog.GetGovernanceHistory().size();

        AdapterWorkOrderPlanningService service;
        const AdapterWorkOrderPlanSet result = service.BuildPlans(
            fixture.m_workspace,
            fixture.m_packs,
            fixture.m_adapterRegistry,
            fixture.m_sourceRegistry,
            fixture.m_catalog,
            fixture.m_blockers);
        ASSERT_EQ(result.m_generatedPlanCount, 1);

        EXPECT_EQ(
            fixture.m_adapterRegistry.GetDeclarations().size(),
            declarationCountBefore);
        EXPECT_EQ(fixture.m_sourceRegistry.GetSources().size(), sourceCountBefore);
        EXPECT_EQ(fixture.m_sourceRegistry.GetEvidence().size(), evidenceCountBefore);
        EXPECT_EQ(fixture.m_catalog.GetRecords().size(), recordCountBefore);
        EXPECT_EQ(
            fixture.m_catalog.GetRelationships().size(),
            relationshipCountBefore);
        EXPECT_EQ(
            fixture.m_catalog.GetValidationHistory().size(),
            validationCountBefore);
        EXPECT_EQ(
            fixture.m_catalog.GetGovernanceHistory().size(),
            governanceCountBefore);
    }
