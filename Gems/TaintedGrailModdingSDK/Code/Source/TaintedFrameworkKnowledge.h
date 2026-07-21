/*
 * Copyright (c) Contributors to the Open 3D Engine Project.
 * For complete copyright and license terms please see the LICENSE at the root of this distribution.
 *
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 */

#pragma once

#include "ExtensionAPI.h"

#include <AzCore/std/containers/vector.h>
#include <AzCore/std/string/string.h>

namespace TaintedGrailModdingSDK
{
    namespace TaintedFrameworkKnowledge
    {
        enum class ComponentClassification
        {
            PortableAuthoringContract,
            PortableFixture,
            DocumentationEvidence,
            MonoRuntimeOnly,
            Il2CppRuntimeOnly,
            GameLinked,
            EditorUtilityCandidate,
            Deferred,
            ProhibitedInEditor,
        };

        struct SourceBinding
        {
            AZStd::string m_path;
            AZStd::string m_gitBlobSha1;
        };

        struct Component
        {
            AZStd::string m_componentId;
            ComponentClassification m_classification =
                ComponentClassification::Deferred;
            AZStd::string m_sourcePath;
            AZStd::string m_summary;
        };

        struct CompatibilityObservation
        {
            AZStd::string m_frameworkVersion;
            AZStd::string m_gameVersion;
            AZStd::string m_branch;
            AZStd::string m_runtimeTarget;
            AZStd::string m_bepInExVersion;
            AZStd::string m_status;
            AZStd::string m_evidencePath;
        };

        struct ApiSurface
        {
            AZStd::string m_surfaceId;
            AZStd::string m_status;
            AZStd::string m_consumerBinding;
            bool m_consumerReady = false;
        };

        struct KnowledgePack
        {
            AZStd::string m_frameworkId;
            AZStd::string m_frameworkVersion;
            AZStd::string m_pluginGuid;
            AZStd::string m_upstreamRepository;
            AZStd::string m_upstreamCommit;
            AZStd::string m_upstreamBranch;
            AZStd::string m_capturedAtUtc;
            AZStd::string m_licenseExpression;
            AZStd::vector<SourceBinding> m_sources;
            AZStd::vector<Component> m_components;
            AZStd::vector<CompatibilityObservation> m_compatibility;
            AZStd::vector<ApiSurface> m_apiSurfaces;
            AZStd::vector<AZStd::string> m_configurationKeys;
            AZStd::vector<AZStd::string> m_diagnosticVocabulary;
            AZStd::vector<AZStd::string> m_knownLimitations;
        };

        const KnowledgePack& GetCanonicalKnowledgePack();

        bool RegisterExtensionConsumer(
            ExtensionAPI::Service& extensionApi,
            AZStd::string* error = nullptr);
    } // namespace TaintedFrameworkKnowledge
} // namespace TaintedGrailModdingSDK
