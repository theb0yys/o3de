/*
 * Copyright (c) Contributors to the Open 3D Engine Project.
 * For complete copyright and license terms please see the LICENSE at the root of this distribution.
 *
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 */

#pragma once

#include <AzCore/RTTI/RTTI.h>
#include <AzCore/std/containers/vector.h>
#include <AzCore/std/string/string.h>

namespace AZ
{
    class ReflectContext;
}

namespace TaintedGrailModdingSDK
{
    struct EconomyItemProfile
    {
        AZ_TYPE_INFO(EconomyItemProfile, "{3C7228A8-9CA0-4F43-AE77-69988EDC8AE8}");

        static void Reflect(AZ::ReflectContext* context);

        AZStd::string m_recordId;
        AZStd::string m_category;
        AZStd::string m_subtype;
        AZ::u32 m_stackLimit = 0;
        double m_weight = 0.0;
        double m_baseValue = 0.0;
        AZStd::string m_rarity;
        AZStd::string m_quality;
        double m_durability = 0.0;
        bool m_questItem = false;
        bool m_uniqueItem = false;
        bool m_hiddenItem = false;
        AZStd::string m_localisationNameRef;
        AZStd::string m_localisationDescriptionRef;
        AZStd::string m_iconRef;
        AZStd::string m_assetRef;
        AZStd::vector<AZStd::string> m_tags;
        AZStd::vector<AZStd::string> m_evidenceIds;
    };

    struct EconomyRecipeProfile
    {
        AZ_TYPE_INFO(EconomyRecipeProfile, "{155DA50A-F825-4AB7-9419-D6E7B110A8E8}");

        static void Reflect(AZ::ReflectContext* context);

        AZStd::string m_recordId;
        AZStd::string m_recipeType;
        AZStd::string m_recipeTab;
        AZStd::vector<AZStd::string> m_stationRecordIds;
        AZStd::string m_unlockMode;
        AZStd::vector<AZStd::string> m_unlockSubjectRefs;
        AZStd::string m_duplicateKey;
        AZStd::string m_persistenceMode;
        bool m_hiddenRecipe = false;
        AZStd::vector<AZStd::string> m_evidenceIds;
    };

    struct EconomyRecipeIngredient
    {
        AZ_TYPE_INFO(EconomyRecipeIngredient, "{F1974030-F4D8-4610-B9F4-4432328F7029}");

        static void Reflect(AZ::ReflectContext* context);

        AZStd::string m_linkId;
        AZStd::string m_recipeRecordId;
        AZStd::string m_itemRecordId;
        AZStd::string m_itemSubjectRef;
        AZ::u32 m_quantity = 1;
        AZStd::string m_alternativeGroup;
        bool m_consumed = true;
        AZStd::vector<AZStd::string> m_conditions;
        AZStd::vector<AZStd::string> m_evidenceIds;
    };

    struct EconomyRecipeOutput
    {
        AZ_TYPE_INFO(EconomyRecipeOutput, "{264BF1DF-3DB4-423A-8FA4-B438BAAB051F}");

        static void Reflect(AZ::ReflectContext* context);

        AZStd::string m_linkId;
        AZStd::string m_recipeRecordId;
        AZStd::string m_itemRecordId;
        AZStd::string m_itemSubjectRef;
        AZ::u32 m_quantity = 1;
        double m_chance = 1.0;
        bool m_byProduct = false;
        AZStd::vector<AZStd::string> m_conditions;
        AZStd::vector<AZStd::string> m_evidenceIds;
    };
} // namespace TaintedGrailModdingSDK
