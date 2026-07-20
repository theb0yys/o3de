/*
 * Copyright (c) Contributors to the Open 3D Engine Project.
 * For complete copyright and license terms please see the LICENSE at the root of this distribution.
 *
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 */

#include "CatalogGovernanceService.h"
#include "CatalogTransactionService.h"

#include <AzTest/AzTest.h>

namespace TaintedGrailModdingSDK
{
    namespace
    {
        WorkspaceModel MakeWorkspace(const AZStd::string& profileId = "foa.test")
        {
            GameProfile profile;
            profile.m_profileId = profileId;
            profile.m_displayName = "FoA Test";
            profile.m_installPath = "/test/foa";
            profile.m_gameVersion = "1.0-test";
            profile.m_branch = "mono";
            profile.m_runtimeTarget = "Mono";
            profile.m_managedAssembliesPath = "/test/foa/Managed";

            WorkspaceModel workspace;
            workspace.m_workspaceId = "test.workspace";
            workspace.m_rootPath = "/test/workspace";
            workspace.m_activeGameProfileId = profile.m_profileId;
            workspace.m_gameProfiles.push_back(profile);
            return workspace;
        }

        SourceEvidenceRegistry MakeRegistry(
            const AZStd::string& evidenceSubject,
            const AZStd::string& profileId = "foa.test")
        {
            SourceRecord source;
            source.m_sourceId = "source.test";
            source.m_title = "Catalog governance hardening fixture";
            source.m_sourceKind = "test-fixture";
            source.m_locator = "Sources/source.test/input.json";
            source.m_fingerprint = "sha256:" + AZStd::string(64, 'a');
            source.m_profileId = profileId;
            source.m_gameVersion = "1.0-test";
            source.m_branch = "mono";
            source.m_runtimeTarget = "Mono";
            source.m_toolName = "catalog-governance-tests";
            source.m_toolVersion = "1.0.0";
            source.m_importerId = "test.importer";
            source.m_importerVersion = "1.0.0";
            source.m_capturedAt = "2026-07-17T00:00:00Z";
            source.m_importedAt = "2026-07-17T00:00:02Z";
            source.m_limitations = "Synthetic deterministic test fixture.";
            source.m_mediaType = "application/json";
            source.m_byteSize = 128;
            source.m_importStatus = "imported";

            EvidenceRecord evidence;
            evidence.m_evidenceId = "evidence.test";
            evidence.m_sourceId = source.m_sourceId;
            evidence.m_sourceFingerprint = source.m_fingerprint;
            evidence.m_profileId = source.m_profileId;
            evidence.m_gameVersion = source.m_gameVersion;
            evidence.m_branch = source.m_branch;
            evidence.m_subjectRef = evidenceSubject;
            evidence.m_claim = "Test claim";
            evidence.m_evidenceKind = "structured_record";
            evidence.m_confidence = "documented";
            evidence.m_locator = source.m_locator;
            evidence.m_recordPath = "/records/0";
            evidence.m_extractedAt = "2026-07-17T00:00:01Z";

            SourceEvidenceRegistry registry;
            AZStd::string error;
            EXPECT_TRUE(registry.RegisterSource(source, &error));
            EXPECT_TRUE(registry.RegisterEvidence(evidence, &error));
            return registry;
        }

        CatalogRecord MakeRecord(
            const AZStd::string& recordId = "record.test",
            const AZStd::string& subjectRef = "subject:test")
        {
            CatalogRecord record;
            record.m_recordId = recordId;
            record.m_domain = "test";
            record.m_recordKind = "test-record";
            record.m_subjectRef = subjectRef;
            record.m_nativeRefExact = "native:";
            record.m_nativeRefExact += recordId;
            record.m_identityKind = "native";
            record.m_researchStage = "S5";
            record.m_confidence = "documented";
            record.m_operationalRisk = "medium";
            record.m_validationState = "unvalidated";
            record.m_stalenessState = "unknown";
            record.m_forbiddenUsages = { "no_unvalidated_runtime_use" };
            record.m_evidenceIds = { "evidence.test" };
            return record;
        }

        CatalogGovernanceRequest MakeMaturityRequest()
        {
            CatalogGovernanceRequest request;
            request.m_subjectKind = "record";
            request.m_subjectId = "record.test";
            request.m_axis = "maturity";
            request.m_value = "S6";
            request.m_evidenceIds = { "evidence.test" };
            request.m_reviewer = "reviewer";
            return request;
        }

        CatalogValidationRequest MakeValidationRequest()
        {
            CatalogValidationRequest request;
            request.m_subjectKind = "record";
            request.m_subjectId = "record.test";
            request.m_state = "validated";
            request.m_method = "unit-test";
            request.m_evidenceIds = { "evidence.test" };
            request.m_validator = "validator";
            return request;
        }

        CatalogValidationEvent MakeValidationEvent(const AZStd::string& validationId)
        {
            CatalogValidationEvent event;
            event.m_validationId = validationId;
            event.m_subjectKind = "record";
            event.m_subjectId = "record.test";
            event.m_recordId = "record.test";
            event.m_state = "validated";
            event.m_method = "fixture";
            event.m_validator = "fixture-validator";
            event.m_checkedAt = "2026-07-17T00:00:03Z";
            event.m_profileId = "foa.test";
            event.m_gameVersion = "1.0-test";
            event.m_branch = "mono";
            event.m_evidenceIds = { "evidence.test" };
            return event;
        }
    } // namespace

    TEST(TaintedGrailCatalogGovernanceHardeningTests, UnknownEvidenceLeavesOriginalCatalogUnchanged)
    {
        const WorkspaceModel workspace = MakeWorkspace();
        const SourceEvidenceRegistry registry = MakeRegistry("subject:test");
        CatalogDatabase catalog;
        AZStd::string error;
        ASSERT_TRUE(catalog.InsertNew(MakeRecord(), &error));

        CatalogGovernanceRequest request = MakeMaturityRequest();
        request.m_evidenceIds = { "evidence.missing" };
        const CatalogGovernanceService service;
        EXPECT_FALSE(service.ApplyDecision(request, workspace, registry, catalog).IsSuccess());

        const CatalogRecord* original = catalog.FindByRecordId("record.test");
        ASSERT_NE(original, nullptr);
        EXPECT_EQ(original->m_researchStage, "S5");
        EXPECT_TRUE(catalog.GetGovernanceHistory().empty());
    }

    TEST(TaintedGrailCatalogGovernanceHardeningTests, WrongEvidenceSubjectLeavesOriginalCatalogUnchanged)
    {
        const WorkspaceModel workspace = MakeWorkspace();
        const SourceEvidenceRegistry registry = MakeRegistry("subject:other");
        CatalogDatabase catalog;
        AZStd::string error;
        ASSERT_TRUE(catalog.InsertNew(MakeRecord(), &error));

        const CatalogGovernanceService service;
        EXPECT_FALSE(service.ApplyDecision(MakeMaturityRequest(), workspace, registry, catalog).IsSuccess());
        EXPECT_EQ(catalog.FindByRecordId("record.test")->m_researchStage, "S5");
        EXPECT_TRUE(catalog.GetGovernanceHistory().empty());
    }

    TEST(TaintedGrailCatalogGovernanceHardeningTests, WrongEvidenceProfileLeavesOriginalCatalogUnchanged)
    {
        const WorkspaceModel workspace = MakeWorkspace();
        const SourceEvidenceRegistry registry = MakeRegistry("subject:test", "foa.other");
        CatalogDatabase catalog;
        AZStd::string error;
        ASSERT_TRUE(catalog.InsertNew(MakeRecord(), &error));

        const CatalogGovernanceService service;
        EXPECT_FALSE(service.ApplyDecision(MakeMaturityRequest(), workspace, registry, catalog).IsSuccess());
        EXPECT_EQ(catalog.FindByRecordId("record.test")->m_researchStage, "S5");
        EXPECT_TRUE(catalog.GetGovernanceHistory().empty());
    }

    TEST(TaintedGrailCatalogGovernanceHardeningTests, DuplicateGovernanceIdRollsBackStateChange)
    {
        const WorkspaceModel workspace = MakeWorkspace();
        const GameProfile* profile = workspace.FindActiveGameProfile();
        ASSERT_NE(profile, nullptr);
        const SourceEvidenceRegistry registry = MakeRegistry("subject:test");
        CatalogDatabase catalog;
        AZStd::string error;
        ASSERT_TRUE(catalog.InsertNew(MakeRecord(), &error));

        CatalogGovernanceEvent existing;
        existing.m_eventId = "governance.record.record.test.2";
        existing.m_subjectKind = "record";
        existing.m_subjectId = "record.test";
        existing.m_axis = "maturity";
        existing.m_previousValue = "S4";
        existing.m_newValue = "S5";
        existing.m_evidenceIds = { "evidence.test" };
        existing.m_reviewer = "fixture-reviewer";
        existing.m_decidedAt = "2026-07-17T00:00:04Z";
        ASSERT_TRUE(catalog.AddGovernanceEventBound(
            existing,
            workspace,
            *profile,
            registry,
            &error));

        const CatalogGovernanceService service;
        EXPECT_FALSE(service.ApplyDecision(
            MakeMaturityRequest(),
            workspace,
            registry,
            catalog,
            existing.m_eventId).IsSuccess());
        EXPECT_EQ(catalog.FindByRecordId("record.test")->m_researchStage, "S5");
        ASSERT_EQ(catalog.GetGovernanceHistory().size(), 1);
        EXPECT_EQ(catalog.GetGovernanceHistory().front().m_eventId, existing.m_eventId);
    }

    TEST(TaintedGrailCatalogGovernanceHardeningTests, DuplicateValidationIdRollsBackStateChange)
    {
        const WorkspaceModel workspace = MakeWorkspace();
        const GameProfile* profile = workspace.FindActiveGameProfile();
        ASSERT_NE(profile, nullptr);
        const SourceEvidenceRegistry registry = MakeRegistry("subject:test");
        CatalogDatabase catalog;
        AZStd::string error;
        ASSERT_TRUE(catalog.InsertNew(MakeRecord(), &error));
        const AZStd::string duplicateId = "validation.record.record.test.2";
        ASSERT_TRUE(catalog.AddValidationEventBound(
            MakeValidationEvent(duplicateId),
            workspace,
            *profile,
            registry,
            &error));

        const CatalogGovernanceService service;
        EXPECT_FALSE(service.ApplyValidation(
            MakeValidationRequest(),
            workspace,
            registry,
            catalog,
            duplicateId).IsSuccess());
        EXPECT_EQ(catalog.FindByRecordId("record.test")->m_validationState, "unvalidated");
        EXPECT_EQ(catalog.GetValidationHistory().size(), 1);
    }

    TEST(TaintedGrailCatalogGovernanceHardeningTests, PersistenceFailureDoesNotPublishCandidate)
    {
        const WorkspaceModel workspace = MakeWorkspace();
        const GameProfile* profile = workspace.FindActiveGameProfile();
        ASSERT_NE(profile, nullptr);
        const SourceEvidenceRegistry registry = MakeRegistry("subject:test");

        CatalogDatabase published;
        AZStd::string error;
        ASSERT_TRUE(published.InsertNew(MakeRecord(), &error));
        CatalogDatabase candidate = published;
        CatalogRecord changed = *candidate.FindByRecordId("record.test");
        changed.m_researchStage = "S6";
        ASSERT_TRUE(candidate.Upsert(changed, &error));

        const CatalogTransactionService transaction;
        const CatalogTransactionService::SaveCallback failSave = [](
            const CatalogDocument&,
            const AZStd::string&) -> AZ::Outcome<AZStd::string, AZStd::string>
        {
            return AZ::Failure(AZStd::string("injected persistence failure"));
        };
        EXPECT_FALSE(transaction.Commit(
            candidate,
            workspace,
            *profile,
            registry,
            failSave).IsSuccess());
        EXPECT_EQ(published.FindByRecordId("record.test")->m_researchStage, "S5");
        EXPECT_EQ(candidate.FindByRecordId("record.test")->m_researchStage, "S6");
    }

    TEST(TaintedGrailCatalogGovernanceHardeningTests, CorruptedDuplicateHistoryDocumentDoesNotReplaceCatalog)
    {
        const WorkspaceModel workspace = MakeWorkspace();
        const GameProfile* profile = workspace.FindActiveGameProfile();
        ASSERT_NE(profile, nullptr);
        const SourceEvidenceRegistry registry = MakeRegistry("subject:test");
        CatalogDatabase catalog;
        AZStd::string error;
        ASSERT_TRUE(catalog.InsertNew(MakeRecord("record.original", "subject:original"), &error));

        CatalogDocument corrupted;
        corrupted.m_schemaVersion = 1;
        corrupted.m_workspaceId = workspace.m_workspaceId;
        corrupted.m_profileId = profile->m_profileId;
        corrupted.m_gameVersion = profile->m_gameVersion;
        corrupted.m_branch = profile->m_branch;
        corrupted.m_records = { MakeRecord() };
        const CatalogValidationEvent duplicate = MakeValidationEvent("validation.duplicate");
        corrupted.m_validationHistory = { duplicate, duplicate };

        EXPECT_FALSE(catalog.ReplaceFromBoundDocument(
            corrupted,
            workspace,
            *profile,
            registry,
            &error));
        ASSERT_NE(catalog.FindByRecordId("record.original"), nullptr);
        EXPECT_EQ(catalog.GetRecords().size(), 1);
        EXPECT_TRUE(catalog.GetValidationHistory().empty());
    }

    TEST(TaintedGrailCatalogGovernanceHardeningTests, InvalidTypedStateDocumentDoesNotReplaceCatalog)
    {
        const WorkspaceModel workspace = MakeWorkspace();
        const GameProfile* profile = workspace.FindActiveGameProfile();
        ASSERT_NE(profile, nullptr);
        const SourceEvidenceRegistry registry = MakeRegistry("subject:test");
        CatalogDatabase catalog;
        AZStd::string error;
        ASSERT_TRUE(catalog.InsertNew(MakeRecord("record.original", "subject:original"), &error));

        CatalogRecord malformed = MakeRecord();
        malformed.m_validationState = "validted";
        CatalogDocument corrupted;
        corrupted.m_schemaVersion = 1;
        corrupted.m_workspaceId = workspace.m_workspaceId;
        corrupted.m_profileId = profile->m_profileId;
        corrupted.m_gameVersion = profile->m_gameVersion;
        corrupted.m_branch = profile->m_branch;
        corrupted.m_records = { malformed };

        EXPECT_FALSE(catalog.ReplaceFromBoundDocument(
            corrupted,
            workspace,
            *profile,
            registry,
            &error));
        ASSERT_NE(catalog.FindByRecordId("record.original"), nullptr);
        EXPECT_EQ(catalog.GetRecords().size(), 1);
    }

    TEST(TaintedGrailCatalogGovernanceHardeningTests, IntegrityReplaysValidationAndPermissionChronologically)
    {
        const WorkspaceModel workspace = MakeWorkspace();
        const GameProfile* profile = workspace.FindActiveGameProfile();
        ASSERT_NE(profile, nullptr);
        const SourceEvidenceRegistry registry = MakeRegistry("subject:test");

        CatalogRecord finalRecord = MakeRecord();
        finalRecord.m_validationState = "validated";
        finalRecord.m_stalenessState = "current";
        finalRecord.m_forbiddenUsages.clear();

        CatalogValidationEvent first =
            MakeValidationEvent("validation.record.test.first");
        first.m_checkedAt = "2026-07-17T00:00:03Z";
        CatalogValidationEvent second =
            MakeValidationEvent("validation.record.test.second");
        second.m_checkedAt = "2026-07-17T00:00:05Z";

        CatalogGovernanceEvent permission;
        permission.m_eventId = "governance.record.test.permission.first";
        permission.m_subjectKind = "record";
        permission.m_subjectId = "record.test";
        permission.m_axis = "permission";
        permission.m_previousValue = "unset";
        permission.m_newValue = "allow";
        permission.m_usage = "display_only";
        permission.m_evidenceIds = { "evidence.test" };
        permission.m_validationIds = { first.m_validationId };
        permission.m_reviewer = "fixture-reviewer";
        permission.m_decidedAt = "2026-07-17T00:00:04Z";

        CatalogDocument document;
        document.m_schemaVersion = 1;
        document.m_workspaceId = workspace.m_workspaceId;
        document.m_profileId = profile->m_profileId;
        document.m_gameVersion = profile->m_gameVersion;
        document.m_branch = profile->m_branch;
        document.m_records = { finalRecord };
        document.m_validationHistory = { first, second };
        document.m_governanceHistory = { permission };

        CatalogDatabase catalog;
        AZStd::string error;
        EXPECT_TRUE(catalog.ReplaceFromBoundDocument(
            document,
            workspace,
            *profile,
            registry,
            &error)) << error.c_str();
        ASSERT_NE(catalog.FindByRecordId("record.test"), nullptr);
        EXPECT_TRUE(
            catalog.FindByRecordId("record.test")->m_allowedUsages.empty());
    }

    TEST(TaintedGrailCatalogGovernanceHardeningTests, BackdatedPermissionCannotUseFutureValidation)
    {
        const WorkspaceModel workspace = MakeWorkspace();
        const GameProfile* profile = workspace.FindActiveGameProfile();
        ASSERT_NE(profile, nullptr);
        const SourceEvidenceRegistry registry = MakeRegistry("subject:test");
        CatalogDatabase catalog;
        AZStd::string error;
        ASSERT_TRUE(catalog.InsertNew(MakeRecord(), &error));

        CatalogValidationEvent validation =
            MakeValidationEvent("validation.record.test.future");
        validation.m_checkedAt = "2026-07-17T00:00:05Z";
        ASSERT_TRUE(catalog.AddValidationEventBound(
            validation, workspace, *profile, registry, &error));

        CatalogGovernanceEvent permission;
        permission.m_eventId = "governance.record.test.backdated";
        permission.m_subjectKind = "record";
        permission.m_subjectId = "record.test";
        permission.m_axis = "permission";
        permission.m_newValue = "allow";
        permission.m_usage = "display_only";
        permission.m_evidenceIds = { "evidence.test" };
        permission.m_validationIds = { validation.m_validationId };
        permission.m_reviewer = "fixture-reviewer";
        permission.m_decidedAt = "2026-07-17T00:00:04Z";

        EXPECT_FALSE(catalog.AddGovernanceEventBound(
            permission, workspace, *profile, registry, &error));
        EXPECT_NE(error.find("no later"), AZStd::string::npos);
    }
} // namespace TaintedGrailModdingSDK
