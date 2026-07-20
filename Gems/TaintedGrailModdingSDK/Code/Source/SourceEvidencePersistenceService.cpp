/*
 * Copyright (c) Contributors to the Open 3D Engine Project.
 * For complete copyright and license terms please see the LICENSE at the root of this distribution.
 *
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 */

#include "SourceEvidencePersistenceService.h"

#include "PersistenceJsonUtils.h"
#include "ResearchContractValidation.h"

#include <AzCore/PlatformDef.h>
#include <AzCore/Serialization/Json/JsonUtils.h>

#include <QDir>
#include <QDirIterator>
#include <QFile>
#include <QFileInfo>

namespace TaintedGrailModdingSDK
{
    namespace
    {
        AZStd::string ToAzString(const QString& value)
        {
            const QByteArray utf8 = value.toUtf8();
            return AZStd::string(utf8.constData(), static_cast<size_t>(utf8.size()));
        }

        QString ToQString(const AZStd::string& value)
        {
            return QString::fromUtf8(value.c_str());
        }

        ImportIssue MakeLoadIssue(
            const AZStd::string& code,
            const AZStd::string& message,
            const AZStd::string& locator)
        {
            ImportIssue issue;
            issue.m_issueId = "issue.workspace-load.";
            issue.m_issueId += AZStd::string::format(
                "%llu",
                static_cast<unsigned long long>(qHash(ToQString(locator))));
            issue.m_severity = "error";
            issue.m_code = code;
            issue.m_message = message;
            issue.m_locator = locator;
            return issue;
        }

        bool IsContainedPath(const QString& rootPath, const QString& candidatePath)
        {
            const QString cleanRoot = QDir::cleanPath(QFileInfo(rootPath).absoluteFilePath());
            const QString cleanCandidate =
                QDir::cleanPath(QFileInfo(candidatePath).absoluteFilePath());
            const QString relative = QDir(cleanRoot).relativeFilePath(cleanCandidate);
            return !QDir::isAbsolutePath(relative)
                && relative != QStringLiteral("..")
                && !relative.startsWith(QStringLiteral("../"))
                && !relative.startsWith(QStringLiteral("..\\"));
        }

        bool PathsIdentifySameLocation(const QString& left, const QString& right)
        {
#if AZ_TRAIT_USE_WINDOWS_FILE_API
            return left.compare(right, Qt::CaseInsensitive) == 0;
#else
            return left == right;
#endif
        }

        QString ResolveDirectCanonicalDirectory(const QString& path)
        {
            const QFileInfo info(path);
            if (!info.exists() || !info.isDir() || info.isSymLink())
            {
                return {};
            }
            const QString declared = QDir::cleanPath(info.absoluteFilePath());
            const QString canonical = QDir::cleanPath(info.canonicalFilePath());
            return !canonical.isEmpty()
                    && PathsIdentifySameLocation(declared, canonical)
                ? canonical
                : QString();
        }

        bool IsDirectCanonicalFileWithin(
            const QString& rootPath,
            const QString& candidatePath)
        {
            const QFileInfo info(candidatePath);
            if (!info.exists() || !info.isFile() || info.isSymLink())
            {
                return false;
            }
            const QString declared = QDir::cleanPath(info.absoluteFilePath());
            const QString canonical = QDir::cleanPath(info.canonicalFilePath());
            return !canonical.isEmpty()
                && PathsIdentifySameLocation(declared, canonical)
                && IsContainedPath(rootPath, canonical);
        }

        bool RemovePendingDirectory(const QString& pendingDirectory)
        {
            return QDir(pendingDirectory).removeRecursively()
                && !QFileInfo::exists(pendingDirectory);
        }
    } // namespace

    AZ::Outcome<SourceEvidenceDocumentPaths, AZStd::string>
    SourceEvidencePersistenceService::SaveDocuments(
        const SourceDocument& sourceDocument,
        const EvidenceDocument& evidenceDocument,
        const AZStd::string& workspaceRoot) const
    {
        if (workspaceRoot.empty())
        {
            return AZ::Failure(AZStd::string(
                "A workspace root is required before source documents can be saved."));
        }
        if (!sourceDocument.UsesSupportedSchema()
            || !evidenceDocument.UsesSupportedSchema())
        {
            return AZ::Failure(AZStd::string(
                "Source or evidence document uses an unsupported schema version."));
        }
        if (!IsSafePersistenceId(sourceDocument.m_source.m_sourceId))
        {
            return AZ::Failure(AZStd::string(
                "A persistence-safe stable source ID is required before source documents can be saved."));
        }
        if (evidenceDocument.m_sourceId != sourceDocument.m_source.m_sourceId
            || evidenceDocument.m_sourceFingerprint
                != sourceDocument.m_source.m_fingerprint)
        {
            return AZ::Failure(AZStd::string(
                "The evidence document does not match the source identity and fingerprint."));
        }

        const QString declaredWorkspacePath =
            QDir::cleanPath(QFileInfo(ToQString(workspaceRoot)).absoluteFilePath());
        const QString workspacePath =
            ResolveDirectCanonicalDirectory(declaredWorkspacePath);
        if (workspacePath.isEmpty())
        {
            return AZ::Failure(AZStd::string(
                "The workspace root must be an existing canonical directory without storage indirection before source documents can be saved."));
        }

        const QString sourcesRoot =
            QDir(workspacePath).filePath(QStringLiteral("Sources"));
        if (!QDir().mkpath(sourcesRoot))
        {
            return AZ::Failure(AZStd::string(
                "Unable to create a contained Sources directory inside the workspace."));
        }
        const QString canonicalSourcesRoot =
            ResolveDirectCanonicalDirectory(sourcesRoot);
        if (canonicalSourcesRoot.isEmpty()
            || !IsContainedPath(workspacePath, canonicalSourcesRoot))
        {
            return AZ::Failure(AZStd::string(
                "The workspace Sources directory must not be a symbolic link, junction, reparse point, or redirected storage path."));
        }

        const QString sourceId = ToQString(sourceDocument.m_source.m_sourceId);
        const QString finalDirectory = QDir(canonicalSourcesRoot).filePath(sourceId);
        const QString pendingDirectory = QDir(canonicalSourcesRoot).filePath(
            sourceId + QStringLiteral(".pending-")
                + ToQString(sourceDocument.m_source.m_fingerprint.substr(7, 12)));
        if (!IsContainedPath(canonicalSourcesRoot, finalDirectory)
            || !IsContainedPath(canonicalSourcesRoot, pendingDirectory))
        {
            return AZ::Failure(AZStd::string(
                "The source document directory escapes the workspace Sources boundary."));
        }
        if (QFileInfo::exists(finalDirectory))
        {
            return AZ::Failure(AZStd::string(
                "The source document identity already has durable state."));
        }
        if (QFileInfo::exists(pendingDirectory))
        {
            if (ResolveDirectCanonicalDirectory(pendingDirectory).isEmpty()
                || !RemovePendingDirectory(pendingDirectory))
            {
                return AZ::Failure(AZStd::string(
                    "Stale pending source state could not be safely removed; manual workspace repair is required."));
            }
        }
        if (!QDir().mkpath(pendingDirectory))
        {
            return AZ::Failure(AZStd::string(
                "Unable to create a pending source document directory inside the workspace."));
        }
        const QString canonicalPendingDirectory =
            ResolveDirectCanonicalDirectory(pendingDirectory);
        if (canonicalPendingDirectory.isEmpty()
            || !IsContainedPath(canonicalSourcesRoot, canonicalPendingDirectory))
        {
            return AZ::Failure(AZStd::string(
                "The pending source directory crossed a filesystem indirection boundary."));
        }

        const QString pendingSourcePath = QDir(canonicalPendingDirectory).filePath(
            QStringLiteral("source.tgsource.json"));
        const QString pendingEvidencePath = QDir(canonicalPendingDirectory).filePath(
            QStringLiteral("evidence.tgevidence.json"));
        const AZ::Outcome<void, AZStd::string> sourceSave =
            AZ::JsonSerializationUtils::SaveObjectToFile(
                &sourceDocument,
                ToAzString(pendingSourcePath));
        if (!sourceSave.IsSuccess())
        {
            if (!RemovePendingDirectory(canonicalPendingDirectory))
            {
                return AZ::Failure(AZStd::string(
                    "Source document save failed and pending-state cleanup also failed: ")
                    + sourceSave.GetError());
            }
            return AZ::Failure(AZStd::string(sourceSave.GetError()));
        }

        const AZ::Outcome<void, AZStd::string> evidenceSave =
            AZ::JsonSerializationUtils::SaveObjectToFile(
                &evidenceDocument,
                ToAzString(pendingEvidencePath));
        if (!evidenceSave.IsSuccess())
        {
            if (!RemovePendingDirectory(canonicalPendingDirectory))
            {
                return AZ::Failure(AZStd::string(
                    "Evidence document save failed and pending-state cleanup also failed: ")
                    + evidenceSave.GetError());
            }
            return AZ::Failure(AZStd::string(evidenceSave.GetError()));
        }
        if (!QDir().rename(canonicalPendingDirectory, finalDirectory))
        {
            if (!RemovePendingDirectory(canonicalPendingDirectory))
            {
                return AZ::Failure(AZStd::string(
                    "Source/evidence publication failed and pending-state cleanup also failed."));
            }
            return AZ::Failure(AZStd::string(
                "Unable to atomically publish the source/evidence document pair."));
        }

        const QString canonicalFinalDirectory =
            ResolveDirectCanonicalDirectory(finalDirectory);
        if (canonicalFinalDirectory.isEmpty()
            || !IsContainedPath(canonicalSourcesRoot, canonicalFinalDirectory))
        {
            return AZ::Failure(AZStd::string(
                "The published source directory does not retain a contained canonical filesystem identity."));
        }

        SourceEvidenceDocumentPaths paths;
        paths.m_sourceDocumentPath = ToAzString(
            QDir(canonicalFinalDirectory).filePath(QStringLiteral("source.tgsource.json")));
        paths.m_evidenceDocumentPath = ToAzString(
            QDir(canonicalFinalDirectory).filePath(QStringLiteral("evidence.tgevidence.json")));
        return AZ::Success(AZStd::move(paths));
    }

    AZ::Outcome<void, AZStd::string>
    SourceEvidencePersistenceService::LoadWorkspaceDocuments(
        const AZStd::string& workspaceRoot,
        AZStd::vector<SourceDocument>& sourceDocuments,
        AZStd::vector<EvidenceDocument>& evidenceDocuments,
        AZStd::vector<ImportIssue>& loadIssues) const
    {
        sourceDocuments.clear();
        evidenceDocuments.clear();
        loadIssues.clear();

        if (workspaceRoot.empty())
        {
            return AZ::Failure(AZStd::string(
                "A workspace root is required before source documents can be loaded."));
        }

        const QString declaredWorkspacePath =
            QDir::cleanPath(QFileInfo(ToQString(workspaceRoot)).absoluteFilePath());
        const QString workspacePath =
            ResolveDirectCanonicalDirectory(declaredWorkspacePath);
        if (workspacePath.isEmpty())
        {
            return AZ::Failure(AZStd::string(
                "The workspace root must be an existing canonical directory without storage indirection before source documents can be loaded."));
        }
        const QString sourcesRoot =
            QDir(workspacePath).filePath(QStringLiteral("Sources"));
        if (!QFileInfo::exists(sourcesRoot))
        {
            return AZ::Success();
        }
        const QString canonicalSourcesRoot =
            ResolveDirectCanonicalDirectory(sourcesRoot);
        if (canonicalSourcesRoot.isEmpty()
            || !IsContainedPath(workspacePath, canonicalSourcesRoot))
        {
            return AZ::Failure(AZStd::string(
                "The workspace Sources path is not a contained directory."));
        }

        QDirIterator iterator(
            canonicalSourcesRoot,
            QStringList() << QStringLiteral("source.tgsource.json"),
            QDir::Files,
            QDirIterator::Subdirectories);
        while (iterator.hasNext())
        {
            const QString sourcePath = iterator.next();
            const QFileInfo sourceInfo(sourcePath);
            const QString sourceDirectory = sourceInfo.absolutePath();
            const QString sourceId = QFileInfo(sourceDirectory).fileName();
            const QString parentDirectory = QFileInfo(sourceDirectory).absolutePath();
            if (!PathsIdentifySameLocation(
                    QDir::cleanPath(parentDirectory),
                    QDir::cleanPath(canonicalSourcesRoot))
                || !IsSafePersistenceId(ToAzString(sourceId))
                || ResolveDirectCanonicalDirectory(sourceDirectory).isEmpty()
                || !IsDirectCanonicalFileWithin(canonicalSourcesRoot, sourcePath))
            {
                loadIssues.push_back(MakeLoadIssue(
                    "document.source-path-invalid",
                    "Source documents must be direct children of Sources under a persistence-safe source ID.",
                    ToAzString(sourcePath)));
                continue;
            }

            SourceDocument sourceDocument;
            const AZ::Outcome<void, AZStd::string> sourceLoad =
                PersistenceJsonUtils::LoadObjectFromFile(
                    sourceDocument,
                    ToAzString(sourcePath));
            if (!sourceLoad.IsSuccess())
            {
                loadIssues.push_back(MakeLoadIssue(
                    "document.source-load-failed",
                    AZStd::string(sourceLoad.GetError()),
                    ToAzString(sourcePath)));
                continue;
            }
            if (!sourceDocument.UsesSupportedSchema()
                || sourceDocument.m_source.m_sourceId != ToAzString(sourceId))
            {
                loadIssues.push_back(MakeLoadIssue(
                    "document.source-schema-or-id-invalid",
                    "The source document schema or directory identity is invalid.",
                    ToAzString(sourcePath)));
                continue;
            }

            const QString evidencePath = QDir(sourceDirectory).filePath(
                QStringLiteral("evidence.tgevidence.json"));
            EvidenceDocument evidenceDocument;
            if (!IsDirectCanonicalFileWithin(canonicalSourcesRoot, evidencePath))
            {
                loadIssues.push_back(MakeLoadIssue(
                    "document.evidence-path-invalid",
                    "The source document has no direct canonical matching evidence document.",
                    ToAzString(evidencePath)));
                continue;
            }

            const AZ::Outcome<void, AZStd::string> evidenceLoad =
                PersistenceJsonUtils::LoadObjectFromFile(
                    evidenceDocument,
                    ToAzString(evidencePath));
            if (!evidenceLoad.IsSuccess())
            {
                loadIssues.push_back(MakeLoadIssue(
                    "document.evidence-load-failed",
                    AZStd::string(evidenceLoad.GetError()),
                    ToAzString(evidencePath)));
                continue;
            }
            if (!evidenceDocument.UsesSupportedSchema()
                || evidenceDocument.m_sourceId
                    != sourceDocument.m_source.m_sourceId
                || evidenceDocument.m_sourceFingerprint
                    != sourceDocument.m_source.m_fingerprint)
            {
                loadIssues.push_back(MakeLoadIssue(
                    "document.source-evidence-mismatch",
                    "The evidence document does not match the source schema, identity, and fingerprint.",
                    ToAzString(evidencePath)));
                continue;
            }

            sourceDocuments.push_back(AZStd::move(sourceDocument));
            evidenceDocuments.push_back(AZStd::move(evidenceDocument));
        }

        return AZ::Success();
    }
} // namespace TaintedGrailModdingSDK
