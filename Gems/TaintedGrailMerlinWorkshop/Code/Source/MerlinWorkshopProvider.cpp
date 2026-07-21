/*
 * Copyright (c) Contributors to the Open 3D Engine Project.
 * For complete copyright and license terms please see the LICENSE at the root of this distribution.
 *
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 */

#include <TaintedGrailMerlinWorkshop/MerlinWorkshopProvider.h>

#include <AzCore/std/utility/move.h>

namespace TaintedGrailMerlinWorkshop
{
    namespace
    {
        ExternalToolchain::ExternalToolConfigurationDescriptor MakeConfiguration(
            const char* key,
            const char* displayName,
            ExternalToolchain::ConfigurationValueKind kind,
            const char* defaultValue,
            bool required)
        {
            ExternalToolchain::ExternalToolConfigurationDescriptor configuration;
            configuration.m_key = key;
            configuration.m_displayName = displayName;
            configuration.m_kind = kind;
            configuration.m_defaultValue = defaultValue;
            configuration.m_required = required;
            return configuration;
        }
    } // namespace

    ExternalToolchain::ExternalToolProviderDescriptor
        CreateMerlinWorkshopProviderDescriptor()
    {
        using namespace ExternalToolchain;

        ExternalToolCommandDescriptor inspectCommand;
        inspectCommand.m_commandId = "inspect-workshop-project";
        inspectCommand.m_displayName = "Inspect Merlin Workshop Project";
        inspectCommand.m_mode = CommandMode::Probe;
        inspectCommand.m_inputKinds = { "application/vnd.unity.project" };
        inspectCommand.m_outputKinds = {
            "application/vnd.foa.merlin-workshop.discovery+json" };
        inspectCommand.m_supportsCancellation = false;
        inspectCommand.m_requiresProject = false;
        inspectCommand.m_requiresSelection = false;

        ExternalToolDiscoveryProbeDescriptor projectProbe;
        projectProbe.m_probeId = "configured-workshop-project";
        projectProbe.m_kind = DiscoveryProbeKind::Directory;
        projectProbe.m_pathConfigurationKey = "project-root";
        projectProbe.m_versionConfigurationKey = "workshop-version";
        projectProbe.m_minimumSupportedVersion = QualifiedWorkshopVersion;
        projectProbe.m_maximumSupportedVersion = QualifiedWorkshopVersion;
        projectProbe.m_platforms = { "windows" };
        projectProbe.m_timeoutMilliseconds = 100;
        projectProbe.m_required = true;

        ExternalToolProviderDescriptor descriptor;
        descriptor.m_providerId = ProviderId;
        descriptor.m_displayName = "Merlin Workshop";
        descriptor.m_providerVersion = ProviderVersion;
        descriptor.m_minimumHostApiVersion = { 1, 1, 0 };
        descriptor.m_toolFamily = ToolFamily::EngineBridge;
        descriptor.m_platforms = { "windows" };
        descriptor.m_capabilities.m_supportsInteractive = true;
        descriptor.m_capabilities.m_supportsBatch = false;
        descriptor.m_capabilities.m_supportsHeadless = false;
        descriptor.m_capabilities.m_producesAssetSources = true;
        descriptor.m_capabilities.m_supportsStructuredIpc = false;
        descriptor.m_commands.push_back(AZStd::move(inspectCommand));
        descriptor.m_configuration = {
            MakeConfiguration(
                "project-root",
                "Merlin Workshop project root",
                ConfigurationValueKind::Path,
                "",
                true),
            MakeConfiguration(
                "unity-editor-revision",
                "Unity Editor revision",
                ConfigurationValueKind::String,
                QualifiedUnityEditorRevision,
                true),
            MakeConfiguration(
                "unity-editor-version",
                "Unity Editor version",
                ConfigurationValueKind::String,
                QualifiedUnityEditorVersion,
                true),
            MakeConfiguration(
                "workshop-release-tag",
                "Merlin Workshop release tag",
                ConfigurationValueKind::String,
                QualifiedWorkshopReleaseTag,
                true),
            MakeConfiguration(
                "workshop-revision",
                "Merlin Workshop source revision",
                ConfigurationValueKind::String,
                QualifiedWorkshopRevision,
                true),
            MakeConfiguration(
                "workshop-version",
                "Merlin Workshop version",
                ConfigurationValueKind::SemanticVersion,
                QualifiedWorkshopVersion,
                true),
        };
        descriptor.m_discoveryProbes.push_back(AZStd::move(projectProbe));
        descriptor.m_enabledByDefault = false;
        return descriptor;
    }
} // namespace TaintedGrailMerlinWorkshop
