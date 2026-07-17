/*
 * Copyright (c) Contributors to the Open 3D Engine Project.
 * For complete copyright and license terms please see the LICENSE at the root of this distribution.
 *
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 */

#include "FoundationService.h"

namespace TaintedGrailModdingSDK
{
    bool FoundationService::UpsertEconomyItemProfile(
        const EconomyItemProfile& profile,
        AZStd::string* error)
    {
        CatalogDatabase candidate = m_catalog;
        AZStd::string catalogError;
        if (!candidate.UpsertEconomyItem(profile, &catalogError))
        {
            if (error)
            {
                *error = catalogError;
            }
            return false;
        }
        return PersistCatalogCandidate(candidate, error);
    }

    bool FoundationService::UpsertEconomyRecipeProfile(
        const EconomyRecipeProfile& profile,
        AZStd::string* error)
    {
        CatalogDatabase candidate = m_catalog;
        AZStd::string catalogError;
        if (!candidate.UpsertEconomyRecipe(profile, &catalogError))
        {
            if (error)
            {
                *error = catalogError;
            }
            return false;
        }
        return PersistCatalogCandidate(candidate, error);
    }

    bool FoundationService::UpsertEconomyRecipeIngredient(
        const EconomyRecipeIngredient& ingredient,
        AZStd::string* error)
    {
        CatalogDatabase candidate = m_catalog;
        AZStd::string catalogError;
        if (!candidate.UpsertRecipeIngredient(ingredient, &catalogError))
        {
            if (error)
            {
                *error = catalogError;
            }
            return false;
        }
        return PersistCatalogCandidate(candidate, error);
    }

    bool FoundationService::UpsertEconomyRecipeOutput(
        const EconomyRecipeOutput& output,
        AZStd::string* error)
    {
        CatalogDatabase candidate = m_catalog;
        AZStd::string catalogError;
        if (!candidate.UpsertRecipeOutput(output, &catalogError))
        {
            if (error)
            {
                *error = catalogError;
            }
            return false;
        }
        return PersistCatalogCandidate(candidate, error);
    }
} // namespace TaintedGrailModdingSDK
