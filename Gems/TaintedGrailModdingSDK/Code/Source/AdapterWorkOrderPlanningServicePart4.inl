/*
 * Copyright (c) Contributors to the Open 3D Engine Project.
 * For complete copyright and license terms please see the LICENSE at the root of this distribution.
 *
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 */

            if (record.m_recordKind == "item")
            {
                if (const EconomyItemProfile* profile = catalog.FindEconomyItem(record.m_recordId))
                {
                    AddArgument(step.m_arguments, "item_profile_record_id", profile->m_recordId);
                    AddArgument(step.m_arguments, "item_category", profile->m_category);
                    AddArgument(step.m_arguments, "item_subtype", profile->m_subtype);
                    AddArgument(
                        step.m_arguments,
                        "item_stack_limit",
                        UnsignedString(profile->m_stackLimit));
                    AddArgument(
                        step.m_arguments,
                        "item_weight",
                        DoubleString(profile->m_weight));
                    AddArgument(
                        step.m_arguments,
                        "item_base_value",
                        DoubleString(profile->m_baseValue));
                    AddArgument(step.m_arguments, "item_rarity", profile->m_rarity);
                    AddArgument(step.m_arguments, "item_quality", profile->m_quality);
                    AddArgument(
                        step.m_arguments,
                        "item_durability",
                        DoubleString(profile->m_durability));
                    AddArgument(
                        step.m_arguments,
                        "item_quest",
                        BoolString(profile->m_questItem));
                    AddArgument(
                        step.m_arguments,
                        "item_unique",
                        BoolString(profile->m_uniqueItem));
                    AddArgument(
                        step.m_arguments,
                        "item_hidden",
                        BoolString(profile->m_hiddenItem));
                    AddArgument(
                        step.m_arguments,
                        "localisation_name_ref",
                        profile->m_localisationNameRef);
                    AddArgument(
                        step.m_arguments,
                        "localisation_description_ref",
                        profile->m_localisationDescriptionRef);
                    AddArgument(step.m_arguments, "icon_ref", profile->m_iconRef);
                    AddArgument(step.m_arguments, "asset_ref", profile->m_assetRef);
                    AddArguments(step.m_arguments, "item_tag", profile->m_tags);
                }
            }
            else if (record.m_recordKind == "recipe")
            {
                if (const EconomyRecipeProfile* profile = catalog.FindEconomyRecipe(record.m_recordId))
                {
                    AddArgument(step.m_arguments, "recipe_profile_record_id", profile->m_recordId);
                    AddArgument(step.m_arguments, "recipe_type", profile->m_recipeType);
                    AddArgument(step.m_arguments, "recipe_tab", profile->m_recipeTab);
                    AddArgument(step.m_arguments, "duplicate_key", profile->m_duplicateKey);
                    AddArgument(step.m_arguments, "persistence_mode", profile->m_persistenceMode);
                    AddArgument(step.m_arguments, "unlock_mode", profile->m_unlockMode);
                    AddArgument(
                        step.m_arguments,
                        "recipe_hidden",
                        BoolString(profile->m_hiddenRecipe));
                    AddArguments(
                        step.m_arguments,
                        "station_record_id",
                        profile->m_stationRecordIds);
                    AddArguments(
                        step.m_arguments,
                        "unlock_subject_ref",
                        profile->m_unlockSubjectRefs);
                }
                for (const EconomyRecipeIngredient& ingredient
                    : catalog.FindIngredientsForRecipe(record.m_recordId))
                {
                    const AZStd::string prefix = "ingredient." + ingredient.m_linkId + ".";
                    AddArgument(step.m_arguments, prefix + "link_id", ingredient.m_linkId);
                    AddArgument(step.m_arguments, prefix + "item_record_id", ingredient.m_itemRecordId);
                    AddArgument(step.m_arguments, prefix + "item_subject_ref", ingredient.m_itemSubjectRef);
                    AddArgument(
                        step.m_arguments,
                        prefix + "quantity",
                        UnsignedString(ingredient.m_quantity));
                    AddArgument(
                        step.m_arguments,
                        prefix + "alternative_group",
                        ingredient.m_alternativeGroup);
                    AddArgument(
                        step.m_arguments,
                        prefix + "consumed",
                        BoolString(ingredient.m_consumed));
                    AddArguments(step.m_arguments, prefix + "condition", ingredient.m_conditions);
                }
                for (const EconomyRecipeOutput& output
                    : catalog.FindOutputsForRecipe(record.m_recordId))
                {
                    const AZStd::string prefix = "output." + output.m_linkId + ".";
                    AddArgument(step.m_arguments, prefix + "link_id", output.m_linkId);
                    AddArgument(step.m_arguments, prefix + "item_record_id", output.m_itemRecordId);
                    AddArgument(step.m_arguments, prefix + "item_subject_ref", output.m_itemSubjectRef);
                    AddArgument(
                        step.m_arguments,
                        prefix + "quantity",
                        UnsignedString(output.m_quantity));
                    AddArgument(
                        step.m_arguments,
                        prefix + "chance",
                        DoubleString(output.m_chance));
                    AddArgument(
                        step.m_arguments,
                        prefix + "by_product",
                        BoolString(output.m_byProduct));
                    AddArguments(step.m_arguments, prefix + "condition", output.m_conditions);
                }
            }
            SortArguments(step.m_arguments);
        }

        AZStd::string BuildPlanId(
            const PackManifest& pack,
            const AdapterDeclaration* declaration,
            const GameProfile* profile)
        {
            AZStd::string planId = "workorder.plan:";
            planId += pack.m_packId;
            planId += "@";
            planId += pack.m_version;
            planId += ":";
            planId += declaration ? declaration->m_adapterId : AZStd::string("none");
            planId += "@";
            planId += declaration ? declaration->m_version : AZStd::string("none");
            planId += ":";
            planId += profile ? profile->m_profileId : AZStd::string("unknown");
            planId += "@";
            planId += profile ? profile->m_gameVersion : AZStd::string("unknown");
            planId += ":";
            planId += profile ? profile->m_branch : AZStd::string("unknown");
            planId += ":";
            planId += profile ? profile->m_runtimeTarget : AZStd::string("unknown");
            return planId;
        }

        AZStd::string BuildStepId(
            const AZStd::string& planId,
            const AZStd::string& capability,
            const AZStd::string& subjectKind,
            const AZStd::string& subjectId)
        {
            return planId + ":step:" + capability + ":" + subjectKind + ":" + subjectId;
        }

        AdapterWorkOrderStep BuildPackStep(
            const AdapterWorkOrderPlan& plan,
            const PackManifest& pack,
            AdapterCapability capability,
            const AdapterCapabilityMatrixRow& matrixRow)
        {
            AdapterWorkOrderStep step;
            step.m_capability = ToString(capability);
            step.m_subjectKind = "pack";
            step.m_subjectId = pack.m_packId;
            step.m_subjectRef = "pack:" + pack.m_packId;
            step.m_stepId = BuildStepId(
                plan.m_planId,
                step.m_capability,
                step.m_subjectKind,
                step.m_subjectId);
            step.m_declarationEvidenceIds = matrixRow.m_declarationEvidenceIds;
            AddArgument(step.m_arguments, "pack_id", pack.m_packId);
            AddArgument(step.m_arguments, "pack_version", pack.m_version);
            AddArgument(
                step.m_arguments,
                "required_adapter_version",
                pack.m_requiredAdapterVersion);
            AddArgument(step.m_arguments, "save_impact", pack.m_saveImpact);
            AddArgument(step.m_arguments, "build_configuration", pack.m_buildConfiguration);
            AddArgument(step.m_arguments, "release_channel", pack.m_releaseChannel);
            SortArguments(step.m_arguments);
            SortUnique(step.m_declarationEvidenceIds);
            return step;
        }

        bool RecordInputEvidenceIsValid(
            const CatalogRecord& record,
            const GameProfile& profile,
            const SourceEvidenceRegistry& sourceRegistry,
            const CatalogDatabase& catalog,
            AZStd::string& reason)
        {
            if (!EvidenceSetIsValid(
                    record.m_evidenceIds,
                    record.m_subjectRef,
                    profile,
                    sourceRegistry))
            {
                reason = "The catalog record lacks exact profile-bound input evidence.";
                return false;
            }

