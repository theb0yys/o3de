/*
 * Copyright (c) Contributors to the Open 3D Engine Project.
 * For complete copyright and license terms please see the LICENSE at the root of this distribution.
 *
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 */

#include "EconomyModels.h"

#include <AzCore/Serialization/SerializeContext.h>

namespace TaintedGrailModdingSDK
{
    void EconomyItemProfile::Reflect(AZ::ReflectContext* context)
    {
        if (auto* serializeContext = azrtti_cast<AZ::SerializeContext*>(context))
        {
            serializeContext->Class<EconomyItemProfile>()
                ->Version(1)
                ->Field("RecordId", &EconomyItemProfile::m_recordId)
                ->Field("Category", &EconomyItemProfile::m_category)
                ->Field("Subtype", &EconomyItemProfile::m_subtype)
                ->Field("StackLimit", &EconomyItemProfile::m_stackLimit)
                ->Field("Weight", &EconomyItemProfile::m_weight)
                ->Field("BaseValue", &EconomyItemProfile::m_baseValue)
                ->Field("Rarity", &EconomyItemProfile::m_rarity)
                ->Field("Quality", &EconomyItemProfile::m_quality)
                ->Field("Durability", &EconomyItemProfile::m_durability)
                ->Field("QuestItem", &EconomyItemProfile::m_questItem)
                ->Field("UniqueItem", &EconomyItemProfile::m_uniqueItem)
                ->Field("HiddenItem", &EconomyItemProfile::m_hiddenItem)
                ->Field("LocalisationNameRef", &EconomyItemProfile::m_localisationNameRef)
                ->Field("LocalisationDescriptionRef", &EconomyItemProfile::m_localisationDescriptionRef)
                ->Field("IconRef", &EconomyItemProfile::m_iconRef)
                ->Field("AssetRef", &EconomyItemProfile::m_assetRef)
                ->Field("Tags", &EconomyItemProfile::m_tags)
                ->Field("EvidenceIds", &EconomyItemProfile::m_evidenceIds);
        }
    }

    void EconomyRecipeProfile::Reflect(AZ::ReflectContext* context)
    {
        if (auto* serializeContext = azrtti_cast<AZ::SerializeContext*>(context))
        {
            serializeContext->Class<EconomyRecipeProfile>()
                ->Version(1)
                ->Field("RecordId", &EconomyRecipeProfile::m_recordId)
                ->Field("RecipeType", &EconomyRecipeProfile::m_recipeType)
                ->Field("RecipeTab", &EconomyRecipeProfile::m_recipeTab)
                ->Field("StationRecordIds", &EconomyRecipeProfile::m_stationRecordIds)
                ->Field("UnlockMode", &EconomyRecipeProfile::m_unlockMode)
                ->Field("UnlockSubjectRefs", &EconomyRecipeProfile::m_unlockSubjectRefs)
                ->Field("DuplicateKey", &EconomyRecipeProfile::m_duplicateKey)
                ->Field("PersistenceMode", &EconomyRecipeProfile::m_persistenceMode)
                ->Field("HiddenRecipe", &EconomyRecipeProfile::m_hiddenRecipe)
                ->Field("EvidenceIds", &EconomyRecipeProfile::m_evidenceIds);
        }
    }

    void EconomyRecipeIngredient::Reflect(AZ::ReflectContext* context)
    {
        if (auto* serializeContext = azrtti_cast<AZ::SerializeContext*>(context))
        {
            serializeContext->Class<EconomyRecipeIngredient>()
                ->Version(1)
                ->Field("LinkId", &EconomyRecipeIngredient::m_linkId)
                ->Field("RecipeRecordId", &EconomyRecipeIngredient::m_recipeRecordId)
                ->Field("ItemRecordId", &EconomyRecipeIngredient::m_itemRecordId)
                ->Field("ItemSubjectRef", &EconomyRecipeIngredient::m_itemSubjectRef)
                ->Field("Quantity", &EconomyRecipeIngredient::m_quantity)
                ->Field("AlternativeGroup", &EconomyRecipeIngredient::m_alternativeGroup)
                ->Field("Consumed", &EconomyRecipeIngredient::m_consumed)
                ->Field("Conditions", &EconomyRecipeIngredient::m_conditions)
                ->Field("EvidenceIds", &EconomyRecipeIngredient::m_evidenceIds);
        }
    }

    void EconomyRecipeOutput::Reflect(AZ::ReflectContext* context)
    {
        if (auto* serializeContext = azrtti_cast<AZ::SerializeContext*>(context))
        {
            serializeContext->Class<EconomyRecipeOutput>()
                ->Version(1)
                ->Field("LinkId", &EconomyRecipeOutput::m_linkId)
                ->Field("RecipeRecordId", &EconomyRecipeOutput::m_recipeRecordId)
                ->Field("ItemRecordId", &EconomyRecipeOutput::m_itemRecordId)
                ->Field("ItemSubjectRef", &EconomyRecipeOutput::m_itemSubjectRef)
                ->Field("Quantity", &EconomyRecipeOutput::m_quantity)
                ->Field("Chance", &EconomyRecipeOutput::m_chance)
                ->Field("ByProduct", &EconomyRecipeOutput::m_byProduct)
                ->Field("Conditions", &EconomyRecipeOutput::m_conditions)
                ->Field("EvidenceIds", &EconomyRecipeOutput::m_evidenceIds);
        }
    }
} // namespace TaintedGrailModdingSDK
