/*
 * Copyright (c) Contributors to the Open 3D Engine Project.
 * For complete copyright and license terms please see the LICENSE at the root of this distribution.
 *
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 */

        const AdapterCapabilityMatrixRow* FindMatrixRow(
            const MatrixGroup& group,
            AdapterCapability capability)
        {
            const AZStd::string capabilityName = ToString(capability);
            for (const AdapterCapabilityMatrixRow* row : group.m_rows)
            {
                if (row->m_capability == capabilityName)
                {
                    return row;
                }
            }
            return nullptr;
        }

        MatrixGroup& FindOrAddGroup(
            AZStd::vector<MatrixGroup>& groups,
            const PackManifest* pack,
            const AdapterDeclaration* declaration,
            const AZStd::string& adapterId)
        {
            for (MatrixGroup& group : groups)
            {
                if (group.m_pack == pack && group.m_adapterId == adapterId)
                {
                    return group;
                }
            }
            MatrixGroup group;
            group.m_pack = pack;
            group.m_declaration = declaration;
            group.m_adapterId = adapterId;
            groups.push_back(AZStd::move(group));
            return groups.back();
        }

        AZStd::vector<MatrixGroup> BuildGroups(
            const AdapterCapabilityMatrix& matrix,
            const AZStd::vector<PackManifest>& packs,
            const AdapterContractRegistry& adapterRegistry)
        {
            AZStd::vector<MatrixGroup> groups;
            for (const AdapterCapabilityMatrixRow& row : matrix.m_rows)
            {
                const PackManifest* pack = FindPack(packs, row.m_packId);
                const AdapterDeclaration* declaration = row.m_adapterId == "none"
                    ? nullptr
                    : adapterRegistry.FindByAdapterId(row.m_adapterId);
                MatrixGroup& group = FindOrAddGroup(
                    groups,
                    pack,
                    declaration,
                    row.m_adapterId);
                group.m_rows.push_back(&row);
            }
            AZStd::sort(
                groups.begin(),
                groups.end(),
                [](const MatrixGroup& left, const MatrixGroup& right)
                {
                    const AZStd::string leftPack = left.m_pack
                        ? left.m_pack->m_packId
                        : AZStd::string{};
                    const AZStd::string rightPack = right.m_pack
                        ? right.m_pack->m_packId
                        : AZStd::string{};
                    if (leftPack != rightPack)
                    {
                        return leftPack < rightPack;
                    }
                    return left.m_adapterId < right.m_adapterId;
                });
            return groups;
        }

        AdapterWorkOrderRefusal BuildCompatibilityRefusal(
            const MatrixGroup& group,
            const GameProfile* profile)
        {
            AdapterWorkOrderRefusal refusal;
            if (group.m_pack)
            {
                refusal.m_planId = BuildPlanId(
                    *group.m_pack,
                    group.m_declaration,
                    profile);
                refusal.m_packId = group.m_pack->m_packId;
            }
            refusal.m_adapterId = group.m_adapterId;
            refusal.m_adapterVersion = group.m_declaration
                ? group.m_declaration->m_version
                : AZStd::string{};
            refusal.m_runtimeTarget = profile
                ? profile->m_runtimeTarget
                : AZStd::string("unknown");

            if (!group.m_pack)
            {
                refusal.m_reasons.push_back(
                    "The compatibility matrix referenced an unknown pack.");
            }
            if (group.m_rows.size() != sizeof(AllCapabilities) / sizeof(AllCapabilities[0]))
            {
                refusal.m_reasons.push_back(
                    "A canonical plan requires exactly one compatibility row for every typed capability.");
            }
            for (const AdapterCapabilityMatrixRow* row : group.m_rows)
            {
                if (row->m_status == "supported")
                {
                    continue;
                }
                AddUnique(refusal.m_failedCapabilities, row->m_capability);
                AddUnique(
                    refusal.m_compatibilityStatuses,
                    row->m_capability + ":" + row->m_status);
                AddAllUnique(refusal.m_subjectIds, row->m_subjectIds);
                AddAllUnique(refusal.m_reasons, row->m_reasons);
            }
            SortUnique(refusal.m_failedCapabilities);
            SortUnique(refusal.m_compatibilityStatuses);
            SortUnique(refusal.m_subjectIds);
            SortUnique(refusal.m_reasons);
            return refusal;
        }

        bool GroupIsSupported(const MatrixGroup& group)
        {
            if (!group.m_pack
                || !group.m_declaration
                || group.m_rows.size() != sizeof(AllCapabilities) / sizeof(AllCapabilities[0]))
            {
                return false;
            }
            for (const AdapterCapabilityMatrixRow* row : group.m_rows)
            {
                if (row->m_status != "supported")
                {
                    return false;
                }
            }
            return true;
        }

        void AppendUnsigned(AZStd::string& output, AZ::u64 value)
        {
            char buffer[32];
            size_t position = sizeof(buffer);
            do
            {
                buffer[--position] = static_cast<char>('0' + (value % 10));
                value /= 10;
            } while (value != 0);
            output.append(buffer + position, sizeof(buffer) - position);
        }

        void AppendJsonString(AZStd::string& output, const AZStd::string& value)
        {
            static const char Hex[] = "0123456789abcdef";
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

