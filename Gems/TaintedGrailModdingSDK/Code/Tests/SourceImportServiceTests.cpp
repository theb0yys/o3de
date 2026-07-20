/*
 * Copyright (c) Contributors to the Open 3D Engine Project.
 * For complete copyright and license terms please see the LICENSE at the root of this distribution.
 *
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 */

#include "SourceImportService.h"

#include <AzTest/AzTest.h>

#include <QDir>
#include <QFile>
#include <QTemporaryDir>

namespace TaintedGrailModdingSDK
{
    namespace
    {
        AZStd::string ToAzString(const QString& value)
        {
            const QByteArray utf8 = value.toUtf8();
            return AZStd::string(utf8.constData(), static_cast<size_t>(utf8.size()));
        }

        GameProfile ConfiguredProfile()
        {
            GameProfile profile;
            profile.m_profileId = "test.csv";
            profile.m_displayName = "CSV Test";
            profile.m_installPath = "C:/Game";
            profile.m_gameVersion = "1.0.0";
            profile.m_branch = "mono";
            profile.m_runtimeTarget = "Mono";
            profile.m_unityVersion = "2022.3.0";
            profile.m_bepInExVersion = "5.4.0";
            profile.m_managedAssembliesPath = "C:/Game/Managed";
            profile.m_pluginPath = "C:/Game/BepInEx/plugins";
            return profile;
        }

        SourceImportResult ImportCsv(
            const QByteArray& bytes,
            AZ::Outcome<SourceImportResult, AZStd::string>& outcome,
            QTemporaryDir& temporary)
        {
            const QString path = QDir(temporary.path()).filePath("evidence.csv");
            QFile file(path);
            EXPECT_TRUE(file.open(QIODevice::WriteOnly));
            EXPECT_EQ(file.write(bytes), bytes.size());
            file.close();

            SourceImportRequest request;
            request.m_inputPath = ToAzString(path);
            request.m_title = "CSV evidence";
            request.m_sourceKind = "csv-register";
            request.m_preferredImporterId = "tg.structured-csv";
            request.m_capturedAt = "2026-07-20T10:00:00Z";
            outcome = SourceImportService().Import(request, ConfiguredProfile());
            return outcome.IsSuccess() ? outcome.GetValue() : SourceImportResult{};
        }

        bool HasIssueCode(
            const SourceImportResult& result,
            const AZStd::string& code)
        {
            for (const ImportIssue& issue : result.m_evidenceDocument.m_issues)
            {
                if (issue.m_code == code)
                {
                    return true;
                }
            }
            return false;
        }
    } // namespace

    TEST(SourceImportServiceTests, QuotedCsvFieldsMayContainNewlines)
    {
        QTemporaryDir temporary;
        ASSERT_TRUE(temporary.isValid());
        AZ::Outcome<SourceImportResult, AZStd::string> outcome;
        const SourceImportResult result = ImportCsv(
            "subject_ref,claim\r\nsubject:item,\"line one\r\nline two\"\r\n",
            outcome,
            temporary);

        ASSERT_TRUE(outcome.IsSuccess()) << outcome.GetError().c_str();
        ASSERT_EQ(result.m_evidenceDocument.m_evidence.size(), 1);
        EXPECT_EQ(
            result.m_evidenceDocument.m_evidence.front().m_claim,
            "line one\r\nline two");
        EXPECT_EQ(result.m_sourceDocument.m_source.m_importStatus, "imported");
    }

    TEST(SourceImportServiceTests, UnterminatedQuotedCsvFieldFailsClosed)
    {
        QTemporaryDir temporary;
        ASSERT_TRUE(temporary.isValid());
        AZ::Outcome<SourceImportResult, AZStd::string> outcome;
        const SourceImportResult result = ImportCsv(
            "subject_ref,claim\nsubject:item,\"unterminated",
            outcome,
            temporary);

        ASSERT_TRUE(outcome.IsSuccess()) << outcome.GetError().c_str();
        EXPECT_TRUE(HasIssueCode(result, "schema.invalid-csv-grammar"));
        EXPECT_EQ(result.m_sourceDocument.m_source.m_importStatus, "error");
    }

    TEST(SourceImportServiceTests, InvalidUtf8CsvFailsClosed)
    {
        QTemporaryDir temporary;
        ASSERT_TRUE(temporary.isValid());
        QByteArray bytes("subject_ref,claim\nsubject:item,");
        bytes.append(static_cast<char>(0xc3));
        bytes.append(static_cast<char>(0x28));
        AZ::Outcome<SourceImportResult, AZStd::string> outcome;
        const SourceImportResult result = ImportCsv(bytes, outcome, temporary);

        ASSERT_TRUE(outcome.IsSuccess()) << outcome.GetError().c_str();
        EXPECT_TRUE(HasIssueCode(result, "schema.invalid-utf8"));
        EXPECT_EQ(result.m_sourceDocument.m_source.m_importStatus, "error");
    }

    TEST(SourceImportServiceTests, CsvEvidenceRowCountIsBounded)
    {
        QTemporaryDir temporary;
        ASSERT_TRUE(temporary.isValid());
        QByteArray bytes("subject_ref,claim\n");
        bytes.reserve(3 * 1024 * 1024);
        for (int index = 0; index < 100000; ++index)
        {
            bytes.append("subject:item,claim\n");
        }
        AZ::Outcome<SourceImportResult, AZStd::string> outcome;
        const SourceImportResult result = ImportCsv(bytes, outcome, temporary);

        ASSERT_TRUE(outcome.IsSuccess()) << outcome.GetError().c_str();
        EXPECT_TRUE(HasIssueCode(result, "schema.invalid-csv-grammar"));
        EXPECT_EQ(result.m_sourceDocument.m_source.m_importStatus, "error");
    }
} // namespace TaintedGrailModdingSDK
