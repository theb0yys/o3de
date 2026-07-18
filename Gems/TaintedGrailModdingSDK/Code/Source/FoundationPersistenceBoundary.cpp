/*
 * Copyright (c) Contributors to the Open 3D Engine Project.
 * For complete copyright and license terms please see the LICENSE at the root of this distribution.
 *
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 */

#include "FoundationPersistenceBoundary.h"

#include <AzCore/std/utility/move.h>

#include <filesystem>
#include <system_error>

namespace TaintedGrailModdingSDK
{
    namespace
    {
        AZ::Outcome<void, AZStd::string> EnsureValidatedParentDirectory(
            const AZStd::string& filePath)
        {
            const std::filesystem::path parent = std::filesystem::u8path(filePath.c_str()).parent_path();
            if (parent.empty())
            {
                return AZ::Success();
            }

            std::error_code error;
            std::filesystem::create_directories(parent, error);
            if (error)
            {
                return AZ::Failure(
                    AZStd::string("Unable to create the validated persistence directory: ")
                    + filePath + ": " + error.message().c_str());
            }
            return AZ::Success();
        }
    } // namespace

    FoundationWorkspacePersistenceBoundary::FoundationWorkspacePersistenceBoundary(
        const PathPolicyService& pathPolicy)
        : m_pathPolicy(pathPolicy)
    {
    }

    AZ::Outcome<void, AZStd::string> FoundationWorkspacePersistenceBoundary::Save(
        const WorkspaceModel& workspace,
        const AZStd::string& filePath) const
    {
        AZ::Outcome<AZStd::string, AZStd::string> resolved = m_pathPolicy.ResolveWorkspaceDocumentPath(
            filePath,
            false);
        if (!resolved.IsSuccess())
        {
            return AZ::Failure(AZStd::string(resolved.GetError()));
        }

        AZ::Outcome<void, AZStd::string> directoryResult =
            EnsureValidatedParentDirectory(resolved.GetValue());
        if (!directoryResult.IsSuccess())
        {
            return AZ::Failure(AZStd::string(directoryResult.GetError()));
        }

        resolved = m_pathPolicy.ResolveWorkspaceDocumentPath(resolved.GetValue(), false);
        if (!resolved.IsSuccess())
        {
            return AZ::Failure(AZStd::string(resolved.GetError()));
        }

        AZ::Outcome<void, AZStd::string> saved = m_persistence.Save(workspace, resolved.GetValue());
        if (saved.IsSuccess())
        {
            m_lastResolvedPath = resolved.GetValue();
        }
        return saved;
    }

    AZ::Outcome<WorkspaceModel, AZStd::string> FoundationWorkspacePersistenceBoundary::Load(
        const AZStd::string& filePath) const
    {
        AZ::Outcome<AZStd::string, AZStd::string> resolved = m_pathPolicy.ResolveWorkspaceDocumentPath(
            filePath,
            true);
        if (!resolved.IsSuccess())
        {
            return AZ::Failure(AZStd::string(resolved.GetError()));
        }
        AZ::Outcome<WorkspaceModel, AZStd::string> loaded = m_persistence.Load(resolved.GetValue());
        if (loaded.IsSuccess())
        {
            m_lastResolvedPath = resolved.GetValue();
        }
        return loaded;
    }

    const AZStd::string& FoundationWorkspacePersistenceBoundary::GetLastResolvedPath() const
    {
        return m_lastResolvedPath;
    }

    FoundationPackPersistenceBoundary::FoundationPackPersistenceBoundary(
        const PathPolicyService& pathPolicy,
        WorkspaceProvider workspaceProvider,
        WorkspacePathProvider workspacePathProvider)
        : m_pathPolicy(pathPolicy)
        , m_workspaceProvider(AZStd::move(workspaceProvider))
        , m_workspacePathProvider(AZStd::move(workspacePathProvider))
    {
    }

    AZ::Outcome<void, AZStd::string> FoundationPackPersistenceBoundary::Save(
        const PackManifest& pack,
        const AZStd::string& filePath) const
    {
        AZ::Outcome<AZStd::string, AZStd::string> resolved = m_pathPolicy.ResolvePackManifestPath(
            m_workspaceProvider(),
            m_workspacePathProvider(),
            filePath,
            false);
        if (!resolved.IsSuccess())
        {
            return AZ::Failure(AZStd::string(resolved.GetError()));
        }

        AZ::Outcome<void, AZStd::string> directoryResult =
            EnsureValidatedParentDirectory(resolved.GetValue());
        if (!directoryResult.IsSuccess())
        {
            return AZ::Failure(AZStd::string(directoryResult.GetError()));
        }

        resolved = m_pathPolicy.ResolvePackManifestPath(
            m_workspaceProvider(),
            m_workspacePathProvider(),
            resolved.GetValue(),
            false);
        if (!resolved.IsSuccess())
        {
            return AZ::Failure(AZStd::string(resolved.GetError()));
        }
        return m_persistence.Save(pack, resolved.GetValue());
    }

    AZ::Outcome<PackManifest, AZStd::string> FoundationPackPersistenceBoundary::Load(
        const AZStd::string& filePath) const
    {
        AZ::Outcome<AZStd::string, AZStd::string> resolved = m_pathPolicy.ResolvePackManifestPath(
            m_workspaceProvider(),
            m_workspacePathProvider(),
            filePath,
            true);
        if (!resolved.IsSuccess())
        {
            return AZ::Failure(AZStd::string(resolved.GetError()));
        }
        return m_persistence.Load(resolved.GetValue());
    }
} // namespace TaintedGrailModdingSDK
