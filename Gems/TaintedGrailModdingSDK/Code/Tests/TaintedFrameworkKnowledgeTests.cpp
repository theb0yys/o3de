/*
 * Copyright (c) Contributors to the Open 3D Engine Project.
 * For complete copyright and license terms please see the LICENSE at the root of this distribution.
 *
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 */

#include <AzTest/AzTest.h>

#include "FoundationService.h"
#include "TaintedFrameworkKnowledge.h"

namespace TaintedGrailModdingSDK
{
    namespace
    {
        WorkspaceModel MakeWorkspace(AZStd::string branch = "Mono")
        {
            GameProfile profile;
            profile.m_profileId = "profile.foa.tainted-framework";
            profile.m_displayName = "FoA Tainted Framework fixture";
            profile.m_installPath = "C:/fixture/game";
            profile.m_gameVersion = "1.23.401";
            profile.m_branch = AZStd::move(branch);
            profile.m_runtimeTarget = "Mono";
            profile.m_unityVersion = "2022.3.20f1";
            profile.m_bepInExVersion = "5.4.23.3";
            profile.m_managedAssembliesPath = "C:/fixture/game/Managed";
            profile.m_pluginPath = "C:/fixture/game/BepInEx/plugins";

            WorkspaceModel workspace;
            workspace.m_workspaceId = "workspace.tainted-framework.fixture";
            workspace.m_displayName = "Tainted Framework fixture";
            workspace.m_rootPath = "C:/fixture/workspace";
            workspace.m_activeGameProfileId = profile.m_profileId;
            workspace.m_gameProfiles.push_back(AZStd::move(profile));
            return workspace;
        }
    } // namespace

    TEST(TaintedFrameworkKnowledgeTests, CanonicalPackPinsExactUpstreamAndSeparatesBranches)
    {
        const auto& pack = TaintedFrameworkKnowledge::GetCanonicalKnowledgePack();
        EXPECT_EQ(pack.m_frameworkId, "framework.tainted");
        EXPECT_EQ(pack.m_frameworkVersion, "0.1.33");
        EXPECT_EQ(pack.m_upstreamCommit,
            "d7e740e7f167b73152b53409e483dab07d80d048");
        EXPECT_EQ(pack.m_licenseExpression, "NOASSERTION");
        ASSERT_EQ(pack.m_compatibility.size(), 3);
        EXPECT_EQ(pack.m_compatibility[0].m_branch, "Mono");
        EXPECT_EQ(pack.m_compatibility[0].m_status, "live_load_validated");
        EXPECT_EQ(pack.m_compatibility[1].m_branch, "IL2CPP");
        EXPECT_EQ(pack.m_compatibility[1].m_status, "blocked");
    }

    TEST(TaintedFrameworkKnowledgeTests, OnlyExactRuntimeReportConsumerIsReady)
    {
        const auto& pack = TaintedFrameworkKnowledge::GetCanonicalKnowledgePack();
        size_t readyCount = 0;
        for (const auto& surface : pack.m_apiSurfaces)
        {
            if (surface.m_consumerReady)
            {
                ++readyCount;
                EXPECT_EQ(surface.m_surfaceId, "runtime-report");
                EXPECT_EQ(surface.m_consumerBinding, "mods/Tainted-Diagnostic Tool");
            }
        }
        EXPECT_EQ(readyCount, 1);
    }

    TEST(TaintedFrameworkKnowledgeTests, FirstConsumerRegistersDeterministicallyThroughExtensionApi)
    {
        FoundationService foundation(FoundationWorkspaceLoadDependencies{});
        foundation.SetWorkspace(MakeWorkspace());
        AZStd::string error;
        ASSERT_TRUE(TaintedFrameworkKnowledge::RegisterExtensionConsumer(
            foundation.GetExtensionAPI(), &error)) << error.c_str();

        const auto declarations = foundation.GetExtensionAPI().GetRegisteredExtensions();
        ASSERT_EQ(declarations.size(), 1);
        EXPECT_EQ(declarations[0].m_extensionId, "extension.tainted-framework");
        EXPECT_EQ(declarations[0].m_version, "0.1.33");
        EXPECT_EQ(declarations[0].m_supportedBranches,
            AZStd::vector<AZStd::string>({ "Mono" }));
        EXPECT_EQ(declarations[0].m_supportedGameVersions,
            AZStd::vector<AZStd::string>({ "1.23.401" }));
        EXPECT_EQ(declarations[0].m_capabilities.size(), 3);

        EXPECT_FALSE(TaintedFrameworkKnowledge::RegisterExtensionConsumer(
            foundation.GetExtensionAPI(), &error));
    }

    TEST(TaintedFrameworkKnowledgeTests, BranchDriftFailsAtExtensionAuthorization)
    {
        FoundationService foundation(FoundationWorkspaceLoadDependencies{});
        foundation.SetWorkspace(MakeWorkspace("IL2CPP"));
        AZStd::string error;
        ASSERT_TRUE(TaintedFrameworkKnowledge::RegisterExtensionConsumer(
            foundation.GetExtensionAPI(), &error));

        ExtensionAPI::ProfileView profile;
        EXPECT_FALSE(foundation.GetExtensionAPI().GetActiveProfile(
            "extension.tainted-framework", profile, &error));
    }
} // namespace TaintedGrailModdingSDK
