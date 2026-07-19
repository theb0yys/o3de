/*
 * Copyright (c) Contributors to the Open 3D Engine Project.
 * For complete copyright and license terms please see the LICENSE at the root of this distribution.
 *
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 */

namespace
{
        const AdapterCapability AllCapabilities[] = {
            AdapterCapability::ItemGrant,
            AdapterCapability::RecipeLearn,
            AdapterCapability::RecipeAppend,
            AdapterCapability::CustomItemRegistration,
            AdapterCapability::CustomRecipeRegistration,
            AdapterCapability::VendorMutation,
            AdapterCapability::LootMutation,
            AdapterCapability::RewardMutation,
            AdapterCapability::Persistence,
            AdapterCapability::Cleanup,
            AdapterCapability::Rollback,
        };

        struct ReadyFixture
        {
            WorkspaceModel m_workspace;
            AZStd::vector<PackManifest> m_packs;
            AdapterContractRegistry m_adapterRegistry;
            SourceEvidenceRegistry m_sourceRegistry;
            CatalogDatabase m_catalog;
            AZStd::vector<BlockerRecord> m_blockers;
        };

        bool Contains(
            const AZStd::vector<AZStd::string>& values,
            const AZStd::string& value)
        {
            return AZStd::find(values.begin(), values.end(), value) != values.end();
        }

        GameProfile MakeProfile()
        {
            GameProfile profile;
            profile.m_profileId = "profile.work-order";
            profile.m_gameVersion = "game.work-order";
            profile.m_branch = "branch.work-order";
            profile.m_runtimeTarget = "Mono";
            return profile;
        }

        WorkspaceModel MakeWorkspace()
        {
            WorkspaceModel workspace;
            workspace.m_activeGameProfileId = "profile.work-order";
            workspace.m_gameProfiles = { MakeProfile() };
            return workspace;
        }

        PackManifest MakePack()
        {
            PackManifest pack;
            pack.m_packId = "owner.work-order-pack";
            pack.m_version = "2.0.0";
            pack.m_requiredAdapterVersion = "1.2.0";
            pack.m_saveImpact = "compatible";
            pack.m_buildConfiguration = "Profile";
            pack.m_releaseChannel = "preview";
            return pack;
        }

        SourceRecord MakeSource()
        {
            SourceRecord source;
            source.m_sourceId = "source.work-order";
            source.m_fingerprint = "fingerprint.work-order";
            source.m_profileId = "profile.work-order";
            source.m_gameVersion = "game.work-order";
            source.m_branch = "branch.work-order";
            source.m_runtimeTarget = "Mono";
            source.m_importerId = "work-order.tests";
            source.m_importerVersion = "1.0.0";
            return source;
        }

        EvidenceRecord MakeEvidence(
            AZStd::string evidenceId,
            AZStd::string subjectRef)
        {
            EvidenceRecord evidence;
            evidence.m_evidenceId = AZStd::move(evidenceId);
            evidence.m_sourceId = "source.work-order";
            evidence.m_sourceFingerprint = "fingerprint.work-order";
            evidence.m_profileId = "profile.work-order";
            evidence.m_gameVersion = "game.work-order";
            evidence.m_branch = "branch.work-order";
            evidence.m_subjectRef = AZStd::move(subjectRef);
            evidence.m_claim = "Project-owned deterministic work-order plan evidence.";
            return evidence;
        }

        AdapterDeclaration MakeDeclaration()
        {
            AdapterDeclaration declaration;
            declaration.m_adapterId = "owner.work-order-adapter";
            declaration.m_displayName = "Work-Order Planning Test Adapter";
            declaration.m_version = "1.3.0";
            declaration.m_runtimeTargets = { "Mono" };
            declaration.m_identityEvidenceIds = { "evidence.adapter.identity" };
            for (AdapterCapability capability : AllCapabilities)
            {
                AdapterCapabilityDeclaration capabilityDeclaration;
                capabilityDeclaration.m_capability = capability;
                capabilityDeclaration.m_evidenceIds = {
                    "evidence.adapter.capability." + ToString(capability),
                };
                declaration.m_capabilities.push_back(
                    AZStd::move(capabilityDeclaration));
            }
            return declaration;
        }

} // namespace
