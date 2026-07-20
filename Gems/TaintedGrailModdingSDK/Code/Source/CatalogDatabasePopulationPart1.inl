namespace TaintedGrailModdingSDK
{
    namespace
    {
        constexpr AZ::u32 MaximumPopulationLevel = 1000;
        constexpr AZ::u32 MaximumPopulationCount = 1000;

        void SetPopulationError(AZStd::string* error, AZStd::string message)
        {
            if (error)
            {
                *error = AZStd::move(message);
            }
        }

        bool IsPopulationRecord(const CatalogRecord* record, const char* kind)
        {
            return record
                && record->m_domain == "population"
                && record->m_recordKind == kind;
        }

        bool IsPopulationTemplateRecord(const CatalogRecord* record)
        {
            return record
                && record->m_domain == "population"
                && (record->m_recordKind == "template"
                    || record->m_recordKind == "actor_template");
        }

        bool IsBoundedPopulationText(
            const AZStd::string& value,
            size_t maximumLength,
            bool allowEmpty)
        {
            if ((!allowEmpty && value.empty()) || value.size() > maximumLength)
            {
                return false;
            }
            for (char character : value)
            {
                const unsigned char byte = static_cast<unsigned char>(character);
                if (byte < 0x20 || byte == 0x7f)
                {
                    return false;
                }
            }
            return true;
        }

        bool HasUniqueBoundedPopulationValues(
            const AZStd::vector<AZStd::string>& values,
            size_t maximumLength)
        {
            AZStd::vector<AZStd::string> sorted = values;
            for (const AZStd::string& value : sorted)
            {
                if (!IsBoundedPopulationText(value, maximumLength, false))
                {
                    return false;
                }
            }
            AZStd::sort(sorted.begin(), sorted.end());
            return AZStd::adjacent_find(sorted.begin(), sorted.end())
                == sorted.end();
        }

        bool HasUniquePopulationEvidenceIds(
            const AZStd::vector<AZStd::string>& values)
        {
            if (values.empty())
            {
                return false;
            }
            AZStd::vector<AZStd::string> sorted = values;
            for (const AZStd::string& value : sorted)
            {
                if (!IsStableContractId(value))
                {
                    return false;
                }
            }
            AZStd::sort(sorted.begin(), sorted.end());
            return AZStd::adjacent_find(sorted.begin(), sorted.end())
                == sorted.end();
        }

        bool HasValidOptionalRange(
            AZ::u32 minimum,
            AZ::u32 maximum,
            AZ::u32 upperBound)
        {
            const bool hasMinimum = minimum != 0;
            const bool hasMaximum = maximum != 0;
            if (hasMinimum != hasMaximum)
            {
                return false;
            }
            return !hasMinimum
                || (minimum <= maximum && maximum <= upperBound);
        }

        AZStd::string ResolveActorSubject(
            const CatalogDatabase& catalog,
            const AZStd::string& actorRecordId,
            const AZStd::string& actorSubjectRef)
        {
            if (!actorRecordId.empty())
            {
                const CatalogRecord* actor = catalog.FindByRecordId(actorRecordId);
                return actor ? actor->m_subjectRef : AZStd::string{};
            }
            return actorSubjectRef;
        }

        template<class Value, class Less>
        void SortPopulationValues(AZStd::vector<Value>& values, Less less)
        {
            AZStd::sort(values.begin(), values.end(), less);
        }
    } // namespace

    bool CatalogDatabase::UpsertPopulationActorProfile(
        const PopulationActorProfile& profile,
        AZStd::string* error)
    {
        if (!ValidatePopulationActorProfile(profile, error))
        {
            return false;
        }
        for (PopulationActorProfile& existing : m_populationActorProfiles)
        {
            if (existing.m_recordId == profile.m_recordId)
            {
                existing = profile;
                SortPopulationValues(
                    m_populationActorProfiles,
                    [](const PopulationActorProfile& left,
                       const PopulationActorProfile& right)
                    {
                        return left.m_recordId < right.m_recordId;
                    });
                return true;
            }
        }
        m_populationActorProfiles.push_back(profile);
        SortPopulationValues(
            m_populationActorProfiles,
            [](const PopulationActorProfile& left,
               const PopulationActorProfile& right)
            {
                return left.m_recordId < right.m_recordId;
            });
        return true;
    }

    bool CatalogDatabase::UpsertPopulationTroopProfile(
        const PopulationTroopProfile& profile,
        AZStd::string* error)
    {
        if (!ValidatePopulationTroopProfile(profile, error))
        {
            return false;
        }
        for (PopulationTroopProfile& existing : m_populationTroopProfiles)
        {
            if (existing.m_recordId == profile.m_recordId)
            {
                existing = profile;
                SortPopulationValues(
                    m_populationTroopProfiles,
                    [](const PopulationTroopProfile& left,
                       const PopulationTroopProfile& right)
                    {
                        return left.m_recordId < right.m_recordId;
                    });
                return true;
            }
        }
        m_populationTroopProfiles.push_back(profile);
        SortPopulationValues(
            m_populationTroopProfiles,
            [](const PopulationTroopProfile& left,
               const PopulationTroopProfile& right)
            {
                return left.m_recordId < right.m_recordId;
            });
        return true;
    }

    bool CatalogDatabase::UpsertPopulationTroopMember(
        const PopulationTroopMember& member,
        AZStd::string* error)
    {
        if (!ValidatePopulationTroopMember(member, error))
        {
            return false;
        }
        for (PopulationTroopMember& existing : m_populationTroopMembers)
        {
            if (existing.m_linkId == member.m_linkId)
            {
                existing = member;
                SortPopulationValues(
                    m_populationTroopMembers,
                    [](const PopulationTroopMember& left,
                       const PopulationTroopMember& right)
                    {
                        return left.m_linkId < right.m_linkId;
                    });
                return true;
            }
        }
        m_populationTroopMembers.push_back(member);
        SortPopulationValues(
            m_populationTroopMembers,
            [](const PopulationTroopMember& left,
               const PopulationTroopMember& right)
            {
                return left.m_linkId < right.m_linkId;
            });
        return true;
    }

    const PopulationActorProfile* CatalogDatabase::FindPopulationActorProfile(
        const AZStd::string& recordId) const
    {
        for (const PopulationActorProfile& profile : m_populationActorProfiles)
        {
            if (profile.m_recordId == recordId)
            {
                return &profile;
            }
        }
        return nullptr;
    }

    const PopulationTroopProfile* CatalogDatabase::FindPopulationTroopProfile(
        const AZStd::string& recordId) const
    {
        for (const PopulationTroopProfile& profile : m_populationTroopProfiles)
        {
            if (profile.m_recordId == recordId)
            {
                return &profile;
            }
        }
        return nullptr;
    }

    AZStd::vector<PopulationTroopMember>
    CatalogDatabase::FindPopulationMembersForTroop(
        const AZStd::string& troopRecordId) const
    {
        AZStd::vector<PopulationTroopMember> matches;
        for (const PopulationTroopMember& member : m_populationTroopMembers)
        {
            if (member.m_troopRecordId == troopRecordId)
            {
                matches.push_back(member);
            }
        }
        SortPopulationValues(
            matches,
            [](const PopulationTroopMember& left,
               const PopulationTroopMember& right)
            {
                return left.m_linkId < right.m_linkId;
            });
        return matches;
    }

    const AZStd::vector<PopulationActorProfile>&
    CatalogDatabase::GetPopulationActorProfiles() const
    {
        return m_populationActorProfiles;
    }

    const AZStd::vector<PopulationTroopProfile>&
    CatalogDatabase::GetPopulationTroopProfiles() const
    {
        return m_populationTroopProfiles;
    }

    const AZStd::vector<PopulationTroopMember>&
    CatalogDatabase::GetPopulationTroopMembers() const
    {
        return m_populationTroopMembers;
    }
} // namespace TaintedGrailModdingSDK
