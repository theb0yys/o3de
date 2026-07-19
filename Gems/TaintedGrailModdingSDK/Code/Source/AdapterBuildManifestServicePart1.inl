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
        template<class EnumType>
        struct EnumName
        {
            EnumType m_value;
            const char* m_name;
        };

        constexpr EnumName<AdapterBuildDependencyKind> DependencyKinds[] = {
            { AdapterBuildDependencyKind::Hard, "hard" },
            { AdapterBuildDependencyKind::Soft, "soft" },
        };

        constexpr EnumName<AdapterBuildManifestStatus> ManifestStatuses[] = {
            { AdapterBuildManifestStatus::Ready, "ready" },
            { AdapterBuildManifestStatus::PlanMismatch, "plan_mismatch" },
            { AdapterBuildManifestStatus::ToolchainUnresolved, "toolchain_unresolved" },
            { AdapterBuildManifestStatus::InputMissing, "input_missing" },
            { AdapterBuildManifestStatus::FingerprintMissing, "fingerprint_missing" },
            { AdapterBuildManifestStatus::PathInvalid, "path_invalid" },
            { AdapterBuildManifestStatus::RedistributionBlocked, "redistribution_blocked" },
        };

        template<class EnumType, size_t Count>
        AZStd::string EnumToString(
            EnumType value,
            const EnumName<EnumType> (&names)[Count])
        {
            for (const EnumName<EnumType>& name : names)
            {
                if (name.m_value == value)
                {
                    return name.m_name;
                }
            }
            return "unknown";
        }

        template<class EnumType, size_t Count>
        bool TryParseEnum(
            const AZStd::string& value,
            EnumType& result,
            const EnumName<EnumType> (&names)[Count])
        {
            for (const EnumName<EnumType>& name : names)
            {
                if (value == name.m_name)
                {
                    result = name.m_value;
                    return true;
                }
            }
            return false;
        }

        bool Contains(
            const AZStd::vector<AZStd::string>& values,
            const AZStd::string& value)
        {
            return AZStd::find(values.begin(), values.end(), value) != values.end();
        }

        void AddReason(
            AZStd::vector<AZStd::string>& reasons,
            const AZStd::string& reason)
        {
            if (!reason.empty() && !Contains(reasons, reason))
            {
                reasons.push_back(reason);
            }
        }

        void SortUnique(AZStd::vector<AZStd::string>& values)
        {
            AZStd::sort(values.begin(), values.end());
            values.erase(AZStd::unique(values.begin(), values.end()), values.end());
        }

        bool IsLowerHex(char value)
        {
            return (value >= '0' && value <= '9')
                || (value >= 'a' && value <= 'f');
        }

        bool IsLowerAlphaNumeric(char value)
        {
            return (value >= 'a' && value <= 'z')
                || (value >= '0' && value <= '9');
        }

        bool IsCommitSha(const AZStd::string& value)
        {
            if (value.size() != 40)
            {
                return false;
            }
            for (char character : value)
            {
                if (!IsLowerHex(character))
                {
                    return false;
                }
            }
            return true;
        }

        bool IsSha256Fingerprint(const AZStd::string& value)
        {
            constexpr size_t PrefixLength = 7;
            constexpr size_t DigestLength = 64;
            if (value.size() != PrefixLength + DigestLength
                || value.substr(0, PrefixLength) != "sha256:")
            {
                return false;
            }
            for (size_t index = PrefixLength; index < value.size(); ++index)
            {
                if (!IsLowerHex(value[index]))
                {
                    return false;
                }
            }
            return true;
        }

        bool IsStableNamespacedId(const AZStd::string& value)
        {
            if (value.size() < 3 || value.find('.') == AZStd::string::npos
                || !IsLowerAlphaNumeric(value.front())
                || !IsLowerAlphaNumeric(value.back()))
            {
                return false;
            }
            for (char character : value)
            {
                if (!IsLowerAlphaNumeric(character)
                    && character != '.'
                    && character != '-'
                    && character != '_')
                {
                    return false;
                }
            }
            return true;
        }

        bool IsSafeRelativePath(const AZStd::string& value)
        {
            if (value.empty() || value.front() == '/' || value.front() == '\\')
            {
                return false;
            }
            if (value.size() > 1 && value[1] == ':')
            {
                return false;
            }

            size_t start = 0;
            while (start <= value.size())
            {
                const size_t end = value.find('/', start);
                const size_t length = end == AZStd::string::npos
                    ? value.size() - start
                    : end - start;
                if (length == 0)
                {
                    return false;
                }
                const AZStd::string component = value.substr(start, length);
                if (component == "." || component == "..")
                {
                    return false;
                }
                for (char character : component)
                {
                    const unsigned char byte = static_cast<unsigned char>(character);
                    if (byte <= 0x20 || byte == 0x7f || character == '\\' || character == ':')
                    {
                        return false;
                    }
                }
                if (end == AZStd::string::npos)
                {
                    break;
                }
                start = end + 1;
            }
            return true;
        }

        bool PathIsInsideRoot(
            const AZStd::string& root,
            const AZStd::string& path)
        {
            if (!IsSafeRelativePath(root) || !IsSafeRelativePath(path))
            {
                return false;
            }
            AZStd::string normalizedRoot = root;
            if (normalizedRoot.back() != '/')
            {
                normalizedRoot.push_back('/');
            }
            return path.size() > normalizedRoot.size()
                && path.substr(0, normalizedRoot.size()) == normalizedRoot;
        }

        bool HasMaterialRole(
            const AZStd::vector<AdapterBuildMaterial>& materials,
            const AZStd::string& role)
        {
            for (const AdapterBuildMaterial& material : materials)
            {
                if (material.m_role == role)
                {
                    return true;
                }
            }
            return false;
        }

        bool HasOutputRole(
            const AZStd::vector<AdapterBuildExpectedOutput>& outputs,
            const AZStd::string& role)
        {
            for (const AdapterBuildExpectedOutput& output : outputs)
            {
                if (output.m_role == role)
                {
                    return true;
                }
            }
            return false;
        }

        void SortDependencies(AZStd::vector<AdapterBuildDependency>& dependencies)
        {
            AZStd::sort(
                dependencies.begin(),
                dependencies.end(),
                [](const AdapterBuildDependency& left, const AdapterBuildDependency& right)
                {
                    if (left.m_pluginId != right.m_pluginId)
                    {
                        return left.m_pluginId < right.m_pluginId;
                    }
                    if (left.m_version != right.m_version)
                    {
                        return left.m_version < right.m_version;
                    }
                    return ToString(left.m_kind) < ToString(right.m_kind);
                });
        }

        void SortMaterials(AZStd::vector<AdapterBuildMaterial>& materials)
        {
            AZStd::sort(
                materials.begin(),
                materials.end(),
                [](const AdapterBuildMaterial& left, const AdapterBuildMaterial& right)
                {
                    if (left.m_materialId != right.m_materialId)
                    {
                        return left.m_materialId < right.m_materialId;
                    }
                    return left.m_role < right.m_role;
                });
        }

        void SortOutputs(AZStd::vector<AdapterBuildExpectedOutput>& outputs)
        {
            AZStd::sort(
                outputs.begin(),
                outputs.end(),
                [](const AdapterBuildExpectedOutput& left, const AdapterBuildExpectedOutput& right)
                {
                    return left.m_relativePath < right.m_relativePath;
                });
        }

        bool HasDuplicateDependencyIds(
            const AZStd::vector<AdapterBuildDependency>& dependencies)
        {
            AZStd::vector<AZStd::string> ids;
            ids.reserve(dependencies.size());
            for (const AdapterBuildDependency& dependency : dependencies)
            {
                ids.push_back(dependency.m_pluginId);
            }
            AZStd::sort(ids.begin(), ids.end());
            return AZStd::adjacent_find(ids.begin(), ids.end()) != ids.end();
        }

        bool HasDuplicateMaterialIds(
            const AZStd::vector<AdapterBuildMaterial>& materials)
        {
            AZStd::vector<AZStd::string> ids;
            ids.reserve(materials.size());
            for (const AdapterBuildMaterial& material : materials)
            {
                ids.push_back(material.m_materialId);
            }
            AZStd::sort(ids.begin(), ids.end());
            return AZStd::adjacent_find(ids.begin(), ids.end()) != ids.end();
        }

        bool HasDuplicateOutputPaths(
            const AZStd::vector<AdapterBuildExpectedOutput>& outputs)
        {
            AZStd::vector<AZStd::string> paths;
            paths.reserve(outputs.size());
            for (const AdapterBuildExpectedOutput& output : outputs)
            {
                paths.push_back(output.m_relativePath);
            }
            AZStd::sort(paths.begin(), paths.end());
            return AZStd::adjacent_find(paths.begin(), paths.end()) != paths.end();
        }

        bool PlanBindingMatches(
            const AdapterBuildManifestRequest& request,
            AZStd::vector<AZStd::string>& reasons)
        {
            bool valid = true;
            const AdapterWorkOrderPlan& plan = request.m_plan;
            if (plan.m_packId != request.m_pack.m_packId
                || plan.m_packVersion != request.m_pack.m_version)
            {
                AddReason(reasons, "The canonical plan does not match the exact pack identity and version.");
                valid = false;
            }
            if (plan.m_adapterId != request.m_declaration.m_adapterId
                || plan.m_adapterVersion != request.m_declaration.m_version
                || plan.m_requiredAdapterVersion != request.m_pack.m_requiredAdapterVersion)
            {
                AddReason(reasons, "The canonical plan does not match the adapter declaration or required version.");
                valid = false;
            }
            if (plan.m_profileId != request.m_profile.m_profileId
                || plan.m_gameVersion != request.m_profile.m_gameVersion
                || plan.m_branch != request.m_profile.m_branch
                || plan.m_runtimeTarget != request.m_profile.m_runtimeTarget)
            {
                AddReason(reasons, "The canonical plan does not match the exact game-profile binding.");
                valid = false;
            }
            if (plan.m_planId.empty() || plan.m_canonicalJson.empty())
            {
                AddReason(reasons, "A generated canonical plan is required.");
                valid = false;
            }
            if (plan.m_executionAllowed)
            {
                AddReason(reasons, "A build manifest cannot accept a plan that allows execution.");
                valid = false;
            }
            for (const AdapterWorkOrderStep& step : plan.m_steps)
            {
                if (step.m_executionAllowed)
                {
                    AddReason(reasons, "Every canonical plan step must retain ExecutionAllowed=false.");
                    valid = false;
                    break;
                }
            }
            return valid;
        }
    } // namespace

    AZStd::string ToString(AdapterBuildDependencyKind kind)
    {
        return EnumToString(kind, DependencyKinds);
    }

    AZStd::string ToString(AdapterBuildManifestStatus status)
    {
        return EnumToString(status, ManifestStatuses);
    }

    bool TryParseAdapterBuildDependencyKind(
        const AZStd::string& value,
        AdapterBuildDependencyKind& kind)
    {
        return TryParseEnum(value, kind, DependencyKinds);
    }

    bool TryParseAdapterBuildManifestStatus(
        const AZStd::string& value,
        AdapterBuildManifestStatus& status)
    {
        return TryParseEnum(value, status, ManifestStatuses);
    }
} // namespace TaintedGrailModdingSDK
