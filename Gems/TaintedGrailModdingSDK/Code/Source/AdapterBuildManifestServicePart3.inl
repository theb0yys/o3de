/*
 * Copyright (c) Contributors to the Open 3D Engine Project.
 * For complete copyright and license terms please see the LICENSE at the root of this distribution.
 *
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 */

namespace TaintedGrailModdingSDK
{
    namespace
    {
        void AppendJsonString(
            AZStd::string& output,
            const AZStd::string& value)
        {
            static constexpr char Hex[] = "0123456789abcdef";
            output.push_back('"');
            for (char character : value)
            {
                const unsigned char byte = static_cast<unsigned char>(character);
                switch (character)
                {
                case '"':
                    output += "\\\"";
                    break;
                case '\\':
                    output += "\\\\";
                    break;
                case '\b':
                    output += "\\b";
                    break;
                case '\f':
                    output += "\\f";
                    break;
                case '\n':
                    output += "\\n";
                    break;
                case '\r':
                    output += "\\r";
                    break;
                case '\t':
                    output += "\\t";
                    break;
                default:
                    if (byte < 0x20)
                    {
                        output += "\\u00";
                        output.push_back(Hex[(byte >> 4) & 0x0f]);
                        output.push_back(Hex[byte & 0x0f]);
                    }
                    else
                    {
                        output.push_back(character);
                    }
                    break;
                }
            }
            output.push_back('"');
        }

        void AppendUnsigned(AZStd::string& output, AZ::u64 value)
        {
            std::ostringstream stream;
            stream.imbue(std::locale::classic());
            stream << value;
            output += stream.str().c_str();
        }

        void AppendBoolean(AZStd::string& output, bool value)
        {
            output += value ? "true" : "false";
        }

        void AppendStringArray(
            AZStd::string& output,
            const AZStd::vector<AZStd::string>& values)
        {
            output.push_back('[');
            for (size_t index = 0; index < values.size(); ++index)
            {
                if (index != 0)
                {
                    output.push_back(',');
                }
                AppendJsonString(output, values[index]);
            }
            output.push_back(']');
        }
    } // namespace

    AZStd::string AdapterBuildManifestService::SerializeCanonicalManifest(
        const AdapterBuildManifest& manifest) const
    {
        AdapterBuildManifest canonical = manifest;
        SortDependencies(canonical.m_dependencies);
        SortMaterials(canonical.m_materials);
        SortOutputs(canonical.m_expectedOutputs);
        SortUnique(canonical.m_reasons);

        AZStd::string output;
        output += "{\"FormatVersion\":";
        AppendUnsigned(output, canonical.m_formatVersion);
        output += ",\"ManifestId\":";
        AppendJsonString(output, canonical.m_manifestId);
        output += ",\"BuildType\":";
        AppendJsonString(output, canonical.m_buildType);
        output += ",\"Status\":";
        AppendJsonString(output, ToString(canonical.m_status));
        output += ",\"BuildAllowed\":";
        AppendBoolean(output, canonical.m_buildAllowed);
        output += ",\"PackId\":";
        AppendJsonString(output, canonical.m_packId);
        output += ",\"PackVersion\":";
        AppendJsonString(output, canonical.m_packVersion);
        output += ",\"AdapterId\":";
        AppendJsonString(output, canonical.m_adapterId);
        output += ",\"AdapterVersion\":";
        AppendJsonString(output, canonical.m_adapterVersion);
        output += ",\"RequiredAdapterVersion\":";
        AppendJsonString(output, canonical.m_requiredAdapterVersion);
        output += ",\"ProfileId\":";
        AppendJsonString(output, canonical.m_profileId);
        output += ",\"GameVersion\":";
        AppendJsonString(output, canonical.m_gameVersion);
        output += ",\"Branch\":";
        AppendJsonString(output, canonical.m_branch);
        output += ",\"RuntimeTarget\":";
        AppendJsonString(output, canonical.m_runtimeTarget);
        output += ",\"UnityVersion\":";
        AppendJsonString(output, canonical.m_unityVersion);
        output += ",\"BepInExVersion\":";
        AppendJsonString(output, canonical.m_bepInExVersion);
        output += ",\"PlanId\":";
        AppendJsonString(output, canonical.m_planId);
        output += ",\"PlanFingerprint\":";
        AppendJsonString(output, canonical.m_planFingerprint);
        output += ",\"PlanCanonicalJson\":";
        AppendJsonString(output, canonical.m_planCanonicalJson);
        output += ",\"Plugin\":{\"Guid\":";
        AppendJsonString(output, canonical.m_pluginGuid);
        output += ",\"Name\":";
        AppendJsonString(output, canonical.m_pluginName);
        output += ",\"Version\":";
        AppendJsonString(output, canonical.m_pluginVersion);
        output += ",\"PackageRoot\":";
        AppendJsonString(output, canonical.m_packageRoot);
        output += "},\"BuildDefinition\":{\"BuilderId\":";
        AppendJsonString(output, canonical.m_environment.m_builderId);
        output += ",\"BuilderVersion\":";
        AppendJsonString(output, canonical.m_environment.m_builderVersion);
        output += ",\"SourceCommit\":";
        AppendJsonString(output, canonical.m_environment.m_sourceCommit);
        output += ",\"O3deRevision\":";
        AppendJsonString(output, canonical.m_environment.m_o3deRevision);
        output += ",\"Configuration\":";
        AppendJsonString(output, canonical.m_environment.m_configuration);
        output += ",\"TargetFramework\":";
        AppendJsonString(output, canonical.m_environment.m_targetFramework);
        output += ",\"CompilerId\":";
        AppendJsonString(output, canonical.m_environment.m_compilerId);
        output += ",\"CompilerVersion\":";
        AppendJsonString(output, canonical.m_environment.m_compilerVersion);
        output += ",\"DeterministicBuild\":";
        AppendBoolean(output, canonical.m_environment.m_deterministicBuild);
        output += ",\"ContinuousIntegrationBuild\":";
        AppendBoolean(output, canonical.m_environment.m_continuousIntegrationBuild);
        output += ",\"PathMapEnabled\":";
        AppendBoolean(output, canonical.m_environment.m_pathMapEnabled);
        output += "},\"Dependencies\":[";

        for (size_t index = 0; index < canonical.m_dependencies.size(); ++index)
        {
            if (index != 0)
            {
                output.push_back(',');
            }
            const AdapterBuildDependency& dependency = canonical.m_dependencies[index];
            output += "{\"PluginId\":";
            AppendJsonString(output, dependency.m_pluginId);
            output += ",\"Version\":";
            AppendJsonString(output, dependency.m_version);
            output += ",\"Kind\":";
            AppendJsonString(output, ToString(dependency.m_kind));
            output.push_back('}');
        }

        output += "],\"ResolvedMaterials\":[";
        for (size_t index = 0; index < canonical.m_materials.size(); ++index)
        {
            if (index != 0)
            {
                output.push_back(',');
            }
            const AdapterBuildMaterial& material = canonical.m_materials[index];
            output += "{\"MaterialId\":";
            AppendJsonString(output, material.m_materialId);
            output += ",\"Role\":";
            AppendJsonString(output, material.m_role);
            output += ",\"Locator\":";
            AppendJsonString(output, material.m_locator);
            output += ",\"MediaType\":";
            AppendJsonString(output, material.m_mediaType);
            output += ",\"Fingerprint\":";
            AppendJsonString(output, material.m_fingerprint);
            output += ",\"Required\":";
            AppendBoolean(output, material.m_required);
            output += ",\"IncludeInPackage\":";
            AppendBoolean(output, material.m_includeInPackage);
            output += ",\"Redistributable\":";
            AppendBoolean(output, material.m_redistributable);
            output.push_back('}');
        }

        output += "],\"ExpectedOutputs\":[";
        for (size_t index = 0; index < canonical.m_expectedOutputs.size(); ++index)
        {
            if (index != 0)
            {
                output.push_back(',');
            }
            const AdapterBuildExpectedOutput& expected = canonical.m_expectedOutputs[index];
            output += "{\"RelativePath\":";
            AppendJsonString(output, expected.m_relativePath);
            output += ",\"Role\":";
            AppendJsonString(output, expected.m_role);
            output += ",\"MediaType\":";
            AppendJsonString(output, expected.m_mediaType);
            output += ",\"Redistributable\":";
            AppendBoolean(output, expected.m_redistributable);
            output.push_back('}');
        }
        output += "],\"Reasons\":";
        AppendStringArray(output, canonical.m_reasons);
        output.push_back('}');
        return output;
    }
} // namespace TaintedGrailModdingSDK
