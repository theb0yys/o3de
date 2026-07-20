/*
 * Copyright (c) Contributors to the Open 3D Engine Project.
 * For complete copyright and license terms please see the LICENSE at the root of this distribution.
 *
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 */

#include "PathPolicyService.h"

#include "ResearchContractValidation.h"

#include <AzCore/PlatformDef.h>
#if AZ_TRAIT_USE_WINDOWS_FILE_API
#   include <AzCore/PlatformIncl.h>
#endif

#include <atomic>
#include <algorithm>
#include <cerrno>
#include <cctype>
#include <chrono>
#include <filesystem>
#include <string>
#include <system_error>

#if !AZ_TRAIT_USE_WINDOWS_FILE_API
#   include <fcntl.h>
#   include <sys/stat.h>
#   include <unistd.h>
#endif

namespace TaintedGrailModdingSDK
{
    namespace
    {
        namespace Filesystem = std::filesystem;

#if AZ_TRAIT_USE_WINDOWS_FILE_API
        constexpr bool PlatformPathsAreCaseInsensitive = true;
#else
        constexpr bool PlatformPathsAreCaseInsensitive = false;
#endif

        std::atomic<AZ::u64> s_writeProbeCounter{ 0 };

        Filesystem::path FromUtf8(const AZStd::string& value)
        {
#if defined(__cpp_lib_char8_t)
            return Filesystem::path(std::u8string(
                reinterpret_cast<const char8_t*>(value.data()),
                value.size()));
#else
            return Filesystem::u8path(value.c_str());
#endif
        }

        AZStd::string ToUtf8(const Filesystem::path& value)
        {
#if defined(__cpp_lib_char8_t)
            const std::u8string text = value.generic_u8string();
            return AZStd::string(
                reinterpret_cast<const char*>(text.data()),
                text.size());
#else
            const std::string text = value.generic_u8string();
            return AZStd::string(text.data(), text.size());
#endif
        }

        bool HasStorageIndirection(const Filesystem::path& canonicalPath)
        {
            Filesystem::path current = canonicalPath.root_path();
            for (const Filesystem::path& component : canonicalPath.relative_path())
            {
                current /= component;
                std::error_code error;
                const Filesystem::file_status linkStatus =
                    Filesystem::symlink_status(current, error);
                if (error || Filesystem::is_symlink(linkStatus))
                {
                    return true;
                }
#if AZ_TRAIT_USE_WINDOWS_FILE_API
                const DWORD attributes = GetFileAttributesW(current.c_str());
                if (attributes == INVALID_FILE_ATTRIBUTES
                    || (attributes & FILE_ATTRIBUTE_REPARSE_POINT) != 0)
                {
                    return true;
                }
#else
                struct stat pathStatus{};
                if (::lstat(current.c_str(), &pathStatus) != 0
                    || S_ISLNK(pathStatus.st_mode))
                {
                    return true;
                }
#endif
            }
            return false;
        }

        AZ::Outcome<Filesystem::path, AZStd::string> ResolveExistingDirectory(
            const AZStd::string& value,
            const Filesystem::path& basePath,
            const char* label)
        {
            if (value.empty())
            {
                return AZ::Failure(AZStd::string(label) + " is required.");
            }

            Filesystem::path declared = FromUtf8(value);
            if (declared.is_relative())
            {
                declared = basePath / declared;
            }

            std::error_code error;
            declared = Filesystem::absolute(declared, error).lexically_normal();
            if (error)
            {
                return AZ::Failure(
                    AZStd::string("Unable to make ") + label
                    + " absolute: " + error.message().c_str());
            }
            if (!Filesystem::exists(declared, error)
                || error
                || !Filesystem::is_directory(declared, error)
                || error)
            {
                return AZ::Failure(
                    AZStd::string(label)
                    + " must be an existing directory: " + ToUtf8(declared));
            }

            const Filesystem::path canonical =
                Filesystem::canonical(declared, error);
            if (error)
            {
                return AZ::Failure(
                    AZStd::string("Unable to resolve canonical ") + label
                    + ": " + error.message().c_str());
            }
            if (HasStorageIndirection(declared))
            {
                return AZ::Failure(
                    AZStd::string(label)
                    + " must not traverse symbolic links, junctions, or reparse points: "
                    + ToUtf8(declared));
            }
            return AZ::Success(canonical);
        }

        AZ::Outcome<void, AZStd::string> RequireWritableDirectory(
            const Filesystem::path& directory,
            const char* label)
        {
            for (int attempt = 0; attempt < 8; ++attempt)
            {
                const AZ::u64 suffix =
                    static_cast<AZ::u64>(
                        std::chrono::steady_clock::now().time_since_epoch().count())
                    ^ s_writeProbeCounter.fetch_add(1);
                const Filesystem::path probe = directory /
                    (".tg-sdk-write-probe-" + std::to_string(suffix) + ".tmp");
#if AZ_TRAIT_USE_WINDOWS_FILE_API
                const HANDLE handle = CreateFileW(
                    probe.c_str(),
                    GENERIC_WRITE,
                    0,
                    nullptr,
                    CREATE_NEW,
                    FILE_ATTRIBUTE_TEMPORARY | FILE_FLAG_OPEN_REPARSE_POINT,
                    nullptr);
                if (handle == INVALID_HANDLE_VALUE)
                {
                    const DWORD createError = GetLastError();
                    if (createError == ERROR_FILE_EXISTS
                        || createError == ERROR_ALREADY_EXISTS)
                    {
                        continue;
                    }
                    return AZ::Failure(
                        AZStd::string(label)
                        + " is not writable through exclusive no-follow creation: "
                        + ToUtf8(directory));
                }
                DWORD bytesWritten = 0;
                constexpr char ProbeContent[] = "tg-sdk-write-probe";
                const bool writeSucceeded = WriteFile(
                    handle,
                    ProbeContent,
                    static_cast<DWORD>(sizeof(ProbeContent) - 1),
                    &bytesWritten,
                    nullptr)
                    && bytesWritten == sizeof(ProbeContent) - 1
                    && FlushFileBuffers(handle);
                const bool closeSucceeded = CloseHandle(handle) != 0;
                const bool removed = DeleteFileW(probe.c_str()) != 0;
#else
                const int descriptor = ::open(
                    probe.c_str(),
                    O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW,
                    S_IRUSR | S_IWUSR);
                if (descriptor < 0)
                {
                    if (errno == EEXIST)
                    {
                        continue;
                    }
                    return AZ::Failure(
                        AZStd::string(label)
                        + " is not writable through exclusive no-follow creation: "
                        + ToUtf8(directory));
                }
                constexpr char ProbeContent[] = "tg-sdk-write-probe";
                const ssize_t written = ::write(
                    descriptor,
                    ProbeContent,
                    sizeof(ProbeContent) - 1);
                const bool writeSucceeded =
                    written == static_cast<ssize_t>(sizeof(ProbeContent) - 1)
                    && ::fsync(descriptor) == 0;
                const bool closeSucceeded = ::close(descriptor) == 0;
                const bool removed = ::unlink(probe.c_str()) == 0;
#endif
                if (!writeSucceeded || !closeSucceeded || !removed)
                {
                    return AZ::Failure(
                        AZStd::string(label)
                        + " failed the exclusive create/write/remove probe: "
                        + ToUtf8(directory));
                }
                return AZ::Success();
            }
            return AZ::Failure(
                AZStd::string("Unable to allocate a unique writable probe for ")
                + label + ".");
        }

        bool PathsOverlap(
            const Filesystem::path& left,
            const Filesystem::path& right)
        {
            const AZStd::string leftText = ToUtf8(left);
            const AZStd::string rightText = ToUtf8(right);
            return PathPolicyService::IsCanonicalPathContained(
                       leftText,
                       rightText,
                       PlatformPathsAreCaseInsensitive)
                || PathPolicyService::IsCanonicalPathContained(
                       rightText,
                       leftText,
                       PlatformPathsAreCaseInsensitive);
        }

        AZ::Outcome<Filesystem::path, AZStd::string>
        RequireWorkspaceContainedDirectory(
            const AZStd::string& value,
            const Filesystem::path& canonicalWorkspaceRoot,
            const char* label,
            bool requireWritable)
        {
            auto resolved = ResolveExistingDirectory(
                value,
                canonicalWorkspaceRoot,
                label);
            if (!resolved.IsSuccess())
            {
                return AZ::Failure(AZStd::string(resolved.GetError()));
            }
            if (!PathPolicyService::IsCanonicalPathContained(
                    ToUtf8(canonicalWorkspaceRoot),
                    ToUtf8(resolved.GetValue()),
                    PlatformPathsAreCaseInsensitive))
            {
                return AZ::Failure(
                    AZStd::string(label)
                    + " must remain inside the canonical workspace root: "
                    + ToUtf8(resolved.GetValue()));
            }
            if (resolved.GetValue() == canonicalWorkspaceRoot)
            {
                return AZ::Failure(
                    AZStd::string(label)
                    + " must be a dedicated child directory, not the workspace root.");
            }
            if (requireWritable)
            {
                auto writable = RequireWritableDirectory(
                    resolved.GetValue(),
                    label);
                if (!writable.IsSuccess())
                {
                    return AZ::Failure(AZStd::string(writable.GetError()));
                }
            }
            return resolved;
        }

        bool DirectoryContainsAssemblyFile(const Filesystem::path& directory)
        {
            std::error_code error;
            size_t inspected = 0;
            for (Filesystem::directory_iterator iterator(directory, error);
                 !error && iterator != Filesystem::directory_iterator();
                 iterator.increment(error))
            {
                if (++inspected > 4096)
                {
                    return false;
                }
                const Filesystem::file_status status =
                    iterator->symlink_status(error);
                if (error)
                {
                    return false;
                }
                std::string extension = iterator->path().extension().string();
                std::transform(
                    extension.begin(),
                    extension.end(),
                    extension.begin(),
                    [](unsigned char value)
                    {
                        return static_cast<char>(std::tolower(value));
                    });
                if (Filesystem::is_regular_file(status) && extension == ".dll")
                {
                    return true;
                }
            }
            return false;
        }

        AZ::Outcome<void, AZStd::string> ValidateProfilePaths(
            const GameProfile& profile,
            const Filesystem::path& canonicalWorkspaceRoot)
        {
            if (!profile.IsConfigured())
            {
                return AZ::Failure(
                    AZStd::string("Profile ") + profile.m_profileId
                    + ": identity, exact version context, runtime target, and required paths are invalid.");
            }

            auto installPath = ResolveExistingDirectory(
                profile.m_installPath,
                canonicalWorkspaceRoot,
                "InstallPath");
            if (!installPath.IsSuccess())
            {
                return AZ::Failure(
                    AZStd::string("Profile ") + profile.m_profileId
                    + ": " + installPath.GetError());
            }
            auto managedPath = ResolveExistingDirectory(
                profile.m_managedAssembliesPath,
                canonicalWorkspaceRoot,
                "ManagedAssembliesPath");
            if (!managedPath.IsSuccess())
            {
                return AZ::Failure(
                    AZStd::string("Profile ") + profile.m_profileId
                    + ": " + managedPath.GetError());
            }
            if (!PathPolicyService::IsCanonicalPathContained(
                    ToUtf8(installPath.GetValue()),
                    ToUtf8(managedPath.GetValue()),
                    PlatformPathsAreCaseInsensitive)
                || managedPath.GetValue() == installPath.GetValue())
            {
                return AZ::Failure(
                    AZStd::string("Profile ") + profile.m_profileId
                    + ": ManagedAssembliesPath must be a dedicated directory inside the canonical InstallPath.");
            }
            if (!DirectoryContainsAssemblyFile(managedPath.GetValue()))
            {
                return AZ::Failure(
                    AZStd::string("Profile ") + profile.m_profileId
                    + ": ManagedAssembliesPath must contain at least one regular assembly file.");
            }

            if (profile.m_runtimeTarget == "Mono")
            {
                auto pluginPath = ResolveExistingDirectory(
                    profile.m_pluginPath,
                    canonicalWorkspaceRoot,
                    "PluginPath");
                if (!pluginPath.IsSuccess())
                {
                    return AZ::Failure(
                        AZStd::string("Profile ") + profile.m_profileId
                        + ": " + pluginPath.GetError());
                }
                if (!PathPolicyService::IsCanonicalPathContained(
                        ToUtf8(installPath.GetValue()),
                        ToUtf8(pluginPath.GetValue()),
                        PlatformPathsAreCaseInsensitive)
                    || pluginPath.GetValue() == installPath.GetValue())
                {
                    return AZ::Failure(
                        AZStd::string("Profile ") + profile.m_profileId
                        + ": PluginPath must be a dedicated directory inside InstallPath for Mono profiles.");
                }
            }
            else if (!profile.m_pluginPath.empty())
            {
                return AZ::Failure(
                    AZStd::string("Profile ") + profile.m_profileId
                    + ": IL2CPP profiles must not carry a Mono BepInEx plugin path.");
            }

            if (!profile.m_diagnosticsPath.empty())
            {
                auto diagnostics = RequireWorkspaceContainedDirectory(
                    profile.m_diagnosticsPath,
                    canonicalWorkspaceRoot,
                    "DiagnosticsPath",
                    true);
                if (!diagnostics.IsSuccess())
                {
                    return AZ::Failure(
                        AZStd::string("Profile ") + profile.m_profileId
                        + ": " + diagnostics.GetError());
                }
            }
            if (!profile.m_extractedDataPath.empty())
            {
                auto extracted = RequireWorkspaceContainedDirectory(
                    profile.m_extractedDataPath,
                    canonicalWorkspaceRoot,
                    "ExtractedDataPath",
                    true);
                if (!extracted.IsSuccess())
                {
                    return AZ::Failure(
                        AZStd::string("Profile ") + profile.m_profileId
                        + ": " + extracted.GetError());
                }
            }
            return AZ::Success();
        }
    } // namespace

    AZ::Outcome<void, AZStd::string> PathPolicyService::ValidateWorkspacePaths(
        const WorkspaceModel& workspace,
        const AZStd::string& canonicalWorkspaceRoot) const
    {
        if (canonicalWorkspaceRoot.empty())
        {
            return AZ::Failure(AZStd::string(
                "The canonical workspace root is required."));
        }

        auto root = ResolveExistingDirectory(
            canonicalWorkspaceRoot,
            {},
            "WorkspaceRoot");
        if (!root.IsSuccess())
        {
            return AZ::Failure(AZStd::string(root.GetError()));
        }
        auto rootWritable = RequireWritableDirectory(
            root.GetValue(),
            "WorkspaceRoot");
        if (!rootWritable.IsSuccess())
        {
            return AZ::Failure(AZStd::string(rootWritable.GetError()));
        }

        auto output = RequireWorkspaceContainedDirectory(
            workspace.m_outputPath,
            root.GetValue(),
            "OutputPath",
            true);
        if (!output.IsSuccess())
        {
            return AZ::Failure(AZStd::string(output.GetError()));
        }
        auto staging = RequireWorkspaceContainedDirectory(
            workspace.m_stagingPath,
            root.GetValue(),
            "StagingPath",
            true);
        if (!staging.IsSuccess())
        {
            return AZ::Failure(AZStd::string(staging.GetError()));
        }
        auto deployment = RequireWorkspaceContainedDirectory(
            workspace.m_deploymentPath,
            root.GetValue(),
            "DeploymentPath",
            true);
        if (!deployment.IsSuccess())
        {
            return AZ::Failure(AZStd::string(deployment.GetError()));
        }

        if (PathsOverlap(output.GetValue(), staging.GetValue())
            || PathsOverlap(output.GetValue(), deployment.GetValue())
            || PathsOverlap(staging.GetValue(), deployment.GetValue()))
        {
            return AZ::Failure(AZStd::string(
                "OutputPath, StagingPath, and DeploymentPath must be pairwise distinct, non-overlapping storage identities."));
        }

        const GameProfile* activeProfile = workspace.FindActiveGameProfile();
        if (!activeProfile || !activeProfile->IsConfigured())
        {
            return AZ::Failure(AZStd::string(
                "The active game profile binding is invalid or incomplete."));
        }

        AZStd::vector<AZStd::string> profileIds;
        for (const GameProfile& profile : workspace.m_gameProfiles)
        {
            if (!IsStableContractId(profile.m_profileId)
                || AZStd::find(
                       profileIds.begin(),
                       profileIds.end(),
                       profile.m_profileId)
                    != profileIds.end())
            {
                return AZ::Failure(AZStd::string(
                    "Workspace game-profile identities must be stable and unique."));
            }
            profileIds.push_back(profile.m_profileId);
            auto result = ValidateProfilePaths(profile, root.GetValue());
            if (!result.IsSuccess())
            {
                return AZ::Failure(AZStd::string(result.GetError()));
            }
        }

        return AZ::Success();
    }
} // namespace TaintedGrailModdingSDK
