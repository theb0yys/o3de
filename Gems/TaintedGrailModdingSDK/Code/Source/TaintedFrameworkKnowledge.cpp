/*
 * Copyright (c) Contributors to the Open 3D Engine Project.
 * For complete copyright and license terms please see the LICENSE at the root of this distribution.
 *
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 */

#include "TaintedFrameworkKnowledge.h"

namespace TaintedGrailModdingSDK::TaintedFrameworkKnowledge
{
    namespace
    {
        KnowledgePack BuildKnowledgePack()
        {
            KnowledgePack pack;
            pack.m_frameworkId = "framework.tainted";
            pack.m_frameworkVersion = "0.1.33";
            pack.m_pluginGuid = "kane.tgfoa.tainted-framework";
            pack.m_upstreamRepository =
                "theb0yys/Tainted-Grail-The-Fall-of-Avalon-mods";
            pack.m_upstreamCommit =
                "d7e740e7f167b73152b53409e483dab07d80d048";
            pack.m_upstreamBranch = "main";
            pack.m_capturedAtUtc = "2026-07-21T16:58:00Z";
            pack.m_licenseExpression = "NOASSERTION";

            pack.m_sources = {
                { "mods/tainted-framework/README.md",
                  "de3763a50023f467a82370f3c8bcb56f48a7ce65" },
                { "mods/tainted-framework/docs/api-surfaces.md",
                  "d08eaa8245de2931bc1f68ecc865a6dc8a70f90f" },
                { "mods/tainted-framework/docs/compatibility.md",
                  "b6cbd59b46cca19a4b085fea66bd9e416e19d279" },
                { "mods/tainted-framework/release/manifest.md",
                  "55ad7e964c83c5ac17d582bf11d6e50e6adb2a8b" },
                { "mods/tainted-framework/src/Tainted.Core/Plugins/"
                  "TaintedScaffoldPluginCatalogFactory.cs",
                  "8170dbd1f99727db44e89ea36b9b1df278df010d" },
                { "mods/tainted-framework/src/Tainted.Host.Mono/Plugin.cs",
                  "f73491e1f6766ff5d328f686ea339c24f1548151" },
                { "mods/tainted-framework/src/Tainted.Host.IL2CPP/Plugin.cs",
                  "b34239da98387261bdda56cc02c590c710fc4b22" },
            };

            pack.m_components = {
                { "tainted.abstractions", ComponentClassification::PortableAuthoringContract,
                  "mods/tainted-framework/src/Tainted.Abstractions", "BCL-only public abstractions." },
                { "tainted.contracts", ComponentClassification::PortableAuthoringContract,
                  "mods/tainted-framework/src/Tainted.Contracts", "Manifest and identity contracts." },
                { "tainted.core", ComponentClassification::EditorUtilityCandidate,
                  "mods/tainted-framework/src/Tainted.Core", "Runtime-neutral policy and catalog logic." },
                { "tainted.plugin-catalog", ComponentClassification::PortableFixture,
                  "mods/tainted-framework/src/Tainted.Core/Plugins", "Deterministic self-catalog contracts." },
                { "tainted.configuration", ComponentClassification::PortableAuthoringContract,
                  "mods/tainted-framework/src/Tainted.Abstractions/Configuration", "Configuration vocabulary." },
                { "tainted.diagnostics", ComponentClassification::PortableFixture,
                  "mods/tainted-framework/src/Tainted.Abstractions/Reporting", "Deterministic report contracts." },
                { "tainted.host.mono", ComponentClassification::MonoRuntimeOnly,
                  "mods/tainted-framework/src/Tainted.Host.Mono", "BepInEx Mono host; prohibited from Editor linkage." },
                { "tainted.host.il2cpp", ComponentClassification::Il2CppRuntimeOnly,
                  "mods/tainted-framework/src/Tainted.Host.IL2CPP", "IL2CPP host evidence; upstream status blocked." },
                { "tainted.runtime-consumer", ComponentClassification::GameLinked,
                  "mods/Tainted-Diagnostic Tool", "Exact diagnostics-only first consumer." },
                { "tainted.gates", ComponentClassification::DocumentationEvidence,
                  "mods/tainted-framework/docs/gates", "Build, package and live-load evidence." },
                { "tainted.release", ComponentClassification::DocumentationEvidence,
                  "mods/tainted-framework/release", "Release manifest and changelog." },
                { "tainted.runtime-bootstrap", ComponentClassification::ProhibitedInEditor,
                  "mods/tainted-framework/src/Tainted.Host.*", "No BepInEx, Unity or game host invocation from O3DE." },
                { "tainted.editor-services", ComponentClassification::Deferred,
                  "mods/tainted-framework/src/Tainted.Core", "Reviewed editor-facing port is a later unit." },
            };

            pack.m_compatibility = {
                { "0.1.33", "1.23.401", "Mono", "Mono", "5.4.23.3", "live_load_validated",
                  "mods/tainted-framework/release/manifest.md" },
                { "0.1.33", "unknown", "IL2CPP", "IL2CPP", "6", "blocked",
                  "mods/tainted-framework/release/manifest.md" },
                { "0.1.33", "n/a", "Shared", "none", "none", "contracts_only",
                  "mods/tainted-framework/README.md" },
            };

            pack.m_apiSurfaces = {
                { "runtime-report", "candidate", "mods/Tainted-Diagnostic Tool", true },
                { "runtime-fingerprint", "candidate", "disabled", false },
                { "runtime-readiness", "candidate", "disabled", false },
                { "runtime-compatibility", "candidate", "disabled", false },
                { "host-safety", "candidate", "disabled", false },
                { "contract-manifest", "candidate", "disabled", false },
                { "plugin-registration", "candidate", "disabled", false },
                { "service-registry", "candidate", "disabled", false },
                { "service-activation", "candidate", "disabled", false },
                { "report-bundle", "candidate", "disabled", false },
                { "report-export", "blocked", "disabled", false },
            };

            pack.m_configurationKeys = {
                "Framework.Enabled",
                "Framework.DiagnosticsOnly",
                "Framework.ReportVerbosity",
            };
            pack.m_diagnosticVocabulary = {
                "runtime-report",
                "runtime-fingerprint",
                "runtime-readiness",
                "runtime-compatibility",
                "host-safety",
                "contract-manifest",
                "plugin-registration",
                "service-registry",
                "service-activation",
            };
            pack.m_knownLimitations = {
                "IL2CPP host support is blocked in the pinned upstream release.",
                "Only runtime-report diagnostics is consumer-ready, and only for the named Mono consumer.",
                "No public release archive is asserted by the pinned upstream manifest.",
                "The upstream licence could not be established from a repository licence file and remains NOASSERTION.",
                "No runtime host source may enter the O3DE Editor build graph.",
            };
            return pack;
        }
    } // namespace

    const KnowledgePack& GetCanonicalKnowledgePack()
    {
        static const KnowledgePack pack = BuildKnowledgePack();
        return pack;
    }

    bool RegisterExtensionConsumer(
        ExtensionAPI::Service& extensionApi,
        AZStd::string* error)
    {
        ExtensionAPI::ExtensionDeclaration declaration;
        declaration.m_extensionId = "extension.tainted-framework";
        declaration.m_displayName = "Tainted Framework Knowledge Consumer";
        declaration.m_version = "0.1.33";
        declaration.m_supportedGameVersions = { "1.23.401" };
        declaration.m_supportedBranches = { "Mono" };
        declaration.m_capabilities = {
            ExtensionAPI::Capability::ReadActiveProfile,
            ExtensionAPI::Capability::QueryCatalog,
            ExtensionAPI::Capability::SubmitCandidateEvidence,
        };
        return extensionApi.RegisterExtension(declaration, error);
    }
} // namespace TaintedGrailModdingSDK::TaintedFrameworkKnowledge
