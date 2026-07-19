/*
 * Copyright (c) Contributors to the Open 3D Engine Project.
 * For complete copyright and license terms please see the LICENSE at the root of this distribution.
 *
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 */

#pragma once

#include "AdapterWorkOrderPlanningService.h"

#include <AzCore/base.h>
#include <AzCore/std/containers/vector.h>
#include <AzCore/std/string/string.h>

namespace TaintedGrailModdingSDK
{
    enum class AdapterBuildDependencyKind : AZ::u8
    {
        Hard,
        Soft,
    };

    enum class AdapterBuildManifestStatus : AZ::u8
    {
        Ready,
        PlanMismatch,
        ToolchainUnresolved,
        InputMissing,
        FingerprintMissing,
        PathInvalid,
        RedistributionBlocked,
    };

    AZStd::string ToString(AdapterBuildDependencyKind kind);
    AZStd::string ToString(AdapterBuildManifestStatus status);
    bool TryParseAdapterBuildDependencyKind(
        const AZStd::string& value,
        AdapterBuildDependencyKind& kind);
    bool TryParseAdapterBuildManifestStatus(
        const AZStd::string& value,
        AdapterBuildManifestStatus& status);

    struct AdapterBuildDependency
    {
        AZStd::string m_pluginId;
        AZStd::string m_version;
        AdapterBuildDependencyKind m_kind = AdapterBuildDependencyKind::Hard;
    };

    struct AdapterBuildMaterial
    {
        AZStd::string m_materialId;
        AZStd::string m_role;
        AZStd::string m_locator;
        AZStd::string m_mediaType;
        AZStd::string m_fingerprint;
        bool m_required = true;
        bool m_includeInPackage = false;
        bool m_redistributable = false;
    };

    struct AdapterBuildExpectedOutput
    {
        AZStd::string m_relativePath;
        AZStd::string m_role;
        AZStd::string m_mediaType;
        bool m_redistributable = true;
    };

    struct AdapterBuildEnvironment
    {
        AZStd::string m_builderId;
        AZStd::string m_builderVersion;
        AZStd::string m_sourceCommit;
        AZStd::string m_o3deRevision;
        AZStd::string m_configuration;
        AZStd::string m_targetFramework;
        AZStd::string m_compilerId;
        AZStd::string m_compilerVersion;
        bool m_deterministicBuild = false;
        bool m_continuousIntegrationBuild = false;
        bool m_pathMapEnabled = false;
    };

    struct AdapterBuildManifestRequest
    {
        AdapterWorkOrderPlan m_plan;
        PackManifest m_pack;
        GameProfile m_profile;
        AdapterDeclaration m_declaration;
        AdapterBuildEnvironment m_environment;
        AZStd::string m_planFingerprint;
        AZStd::string m_pluginGuid;
        AZStd::string m_pluginName;
        AZStd::string m_pluginVersion;
        AZStd::string m_packageRoot;
        AZStd::vector<AdapterBuildDependency> m_dependencies;
        AZStd::vector<AdapterBuildMaterial> m_materials;
        AZStd::vector<AdapterBuildExpectedOutput> m_expectedOutputs;
    };

    struct AdapterBuildManifest
    {
        AZ::u32 m_formatVersion = 1;
        AZStd::string m_manifestId;
        AZStd::string m_buildType = "foa.adapter.plugin";
        AZStd::string m_packId;
        AZStd::string m_packVersion;
        AZStd::string m_adapterId;
        AZStd::string m_adapterVersion;
        AZStd::string m_requiredAdapterVersion;
        AZStd::string m_profileId;
        AZStd::string m_gameVersion;
        AZStd::string m_branch;
        AZStd::string m_runtimeTarget;
        AZStd::string m_unityVersion;
        AZStd::string m_bepInExVersion;
        AZStd::string m_planId;
        AZStd::string m_planFingerprint;
        AZStd::string m_planCanonicalJson;
        AZStd::string m_pluginGuid;
        AZStd::string m_pluginName;
        AZStd::string m_pluginVersion;
        AZStd::string m_packageRoot;
        AdapterBuildEnvironment m_environment;
        AZStd::vector<AdapterBuildDependency> m_dependencies;
        AZStd::vector<AdapterBuildMaterial> m_materials;
        AZStd::vector<AdapterBuildExpectedOutput> m_expectedOutputs;
        AdapterBuildManifestStatus m_status = AdapterBuildManifestStatus::InputMissing;
        AZStd::vector<AZStd::string> m_reasons;
        AZStd::string m_canonicalJson;
        bool m_buildAllowed = false;
    };

    class AdapterBuildManifestService
    {
    public:
        AdapterBuildManifest BuildManifest(
            const AdapterBuildManifestRequest& request) const;
        AZStd::string SerializeCanonicalManifest(
            const AdapterBuildManifest& manifest) const;
    };
} // namespace TaintedGrailModdingSDK
