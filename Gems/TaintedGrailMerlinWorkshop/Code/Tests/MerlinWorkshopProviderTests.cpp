/*
 * Copyright (c) Contributors to the Open 3D Engine Project.
 * For complete copyright and license terms please see the LICENSE at the root of this distribution.
 *
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 */

#include <TaintedGrailMerlinWorkshop/MerlinWorkshopProvider.h>

#include <AzTest/AzTest.h>

namespace TaintedGrailMerlinWorkshop
{
    namespace
    {
        const ExternalToolchain::ExternalToolConfigurationDescriptor*
            FindConfiguration(
                const ExternalToolchain::ExternalToolProviderDescriptor& descriptor,
                const char* key)
        {
            for (const auto& configuration : descriptor.m_configuration)
            {
                if (configuration.m_key == key)
                {
                    return &configuration;
                }
            }
            return nullptr;
        }
    } // namespace

    TEST(MerlinWorkshopProviderTests, DescriptorIsOptionalAndDiscoveryOnly)
    {
        const ExternalToolchain::ExternalToolProviderDescriptor descriptor =
            CreateMerlinWorkshopProviderDescriptor();

        EXPECT_EQ(descriptor.m_providerId, ProviderId);
        EXPECT_EQ(descriptor.m_providerVersion, ProviderVersion);
        EXPECT_EQ(
            descriptor.m_toolFamily,
            ExternalToolchain::ToolFamily::EngineBridge);
        EXPECT_EQ(descriptor.m_platforms, AZStd::vector<AZStd::string>{ "windows" });
        EXPECT_FALSE(descriptor.m_enabledByDefault);

        EXPECT_TRUE(descriptor.m_capabilities.m_supportsInteractive);
        EXPECT_FALSE(descriptor.m_capabilities.m_supportsBatch);
        EXPECT_FALSE(descriptor.m_capabilities.m_supportsHeadless);
        EXPECT_TRUE(descriptor.m_capabilities.m_producesAssetSources);
        EXPECT_FALSE(descriptor.m_capabilities.m_supportsStructuredIpc);

        ASSERT_EQ(descriptor.m_commands.size(), 1);
        EXPECT_EQ(
            descriptor.m_commands.front().m_mode,
            ExternalToolchain::CommandMode::Probe);
        EXPECT_EQ(
            descriptor.m_commands.front().m_commandId,
            "inspect-workshop-project");
        EXPECT_FALSE(descriptor.m_commands.front().m_supportsCancellation);
        EXPECT_FALSE(descriptor.m_commands.front().m_requiresProject);
        EXPECT_FALSE(descriptor.m_commands.front().m_requiresSelection);

        ASSERT_EQ(descriptor.m_discoveryProbes.size(), 1);
        const auto& probe = descriptor.m_discoveryProbes.front();
        EXPECT_EQ(
            probe.m_kind,
            ExternalToolchain::DiscoveryProbeKind::Directory);
        EXPECT_EQ(probe.m_pathConfigurationKey, "project-root");
        EXPECT_EQ(probe.m_versionConfigurationKey, "workshop-version");
        EXPECT_EQ(probe.m_minimumSupportedVersion, QualifiedWorkshopVersion);
        EXPECT_EQ(probe.m_maximumSupportedVersion, QualifiedWorkshopVersion);
        EXPECT_TRUE(probe.m_required);
    }

    TEST(MerlinWorkshopProviderTests, DescriptorPinsOfficialReleaseIdentity)
    {
        const ExternalToolchain::ExternalToolProviderDescriptor descriptor =
            CreateMerlinWorkshopProviderDescriptor();

        const auto* projectRoot = FindConfiguration(descriptor, "project-root");
        ASSERT_NE(projectRoot, nullptr);
        EXPECT_EQ(
            projectRoot->m_kind,
            ExternalToolchain::ConfigurationValueKind::Path);
        EXPECT_TRUE(projectRoot->m_required);
        EXPECT_TRUE(projectRoot->m_defaultValue.empty());

        const auto* workshopVersion =
            FindConfiguration(descriptor, "workshop-version");
        ASSERT_NE(workshopVersion, nullptr);
        EXPECT_EQ(
            workshopVersion->m_kind,
            ExternalToolchain::ConfigurationValueKind::SemanticVersion);
        EXPECT_EQ(
            workshopVersion->m_defaultValue,
            QualifiedWorkshopVersion);

        const auto* releaseTag =
            FindConfiguration(descriptor, "workshop-release-tag");
        ASSERT_NE(releaseTag, nullptr);
        EXPECT_EQ(
            releaseTag->m_defaultValue,
            QualifiedWorkshopReleaseTag);

        const auto* workshopRevision =
            FindConfiguration(descriptor, "workshop-revision");
        ASSERT_NE(workshopRevision, nullptr);
        EXPECT_EQ(
            workshopRevision->m_defaultValue,
            QualifiedWorkshopRevision);

        const auto* unityVersion =
            FindConfiguration(descriptor, "unity-editor-version");
        ASSERT_NE(unityVersion, nullptr);
        EXPECT_EQ(
            unityVersion->m_defaultValue,
            QualifiedUnityEditorVersion);

        const auto* unityRevision =
            FindConfiguration(descriptor, "unity-editor-revision");
        ASSERT_NE(unityRevision, nullptr);
        EXPECT_EQ(
            unityRevision->m_defaultValue,
            QualifiedUnityEditorRevision);
    }
} // namespace TaintedGrailMerlinWorkshop
