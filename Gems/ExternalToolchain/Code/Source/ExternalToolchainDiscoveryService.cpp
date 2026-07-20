/*
 * Copyright (c) Contributors to the Open 3D Engine Project.
 * For complete copyright and license terms please see the LICENSE at the root of this distribution.
 *
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 */

#include "ExternalToolchainDiscoveryService.h"

#include <AzCore/PlatformDef.h>
#include <AzCore/std/algorithm.h>
#include <AzCore/std/chrono/chrono.h>
#include <AzCore/std/containers/unordered_set.h>
#include <AzCore/std/sort.h>
#include <AzCore/std/string/string_view.h>
#include <AzCore/std/utility/move.h>

#include <filesystem>
#include <string>

#if AZ_TRAIT_USE_WINDOWS_FILE_API
#   include <Windows.h>
#else
#   include <sys/stat.h>
#   include <unistd.h>
#endif

namespace ExternalToolchain
{
    namespace
    {
        constexpr const char* DiscoveryEnabledPath =
            "/O3DE/ExternalToolchain/Host/Discovery/Enabled";
        constexpr const char* MaximumProvidersPath =
            "/O3DE/ExternalToolchain/Host/Discovery/MaximumProviders";
        constexpr const char* MaximumProbesPerProviderPath =
            "/O3DE/ExternalToolchain/Host/Discovery/MaximumProbesPerProvider";
        constexpr const char* ProviderBudgetMillisecondsPath =
            "/O3DE/ExternalToolchain/Host/Discovery/ProviderBudgetMilliseconds";
        constexpr AZ::u32 HardProbeTimeoutMilliseconds = 250;

        ProviderOperationResult Success(AZStd::string message)
        {
            return ProviderOperationResult{ true, AZStd::move(message) };
        }

        ProviderOperationResult Failure(AZStd::string message)
        {
            return ProviderOperationResult{ false, AZStd::move(message) };
        }

        bool ContainsString(
            const AZStd::vector<AZStd::string>& values,
            const AZStd::string& value)
        {
            return AZStd::find(values.begin(), values.end(), value) != values.end();
        }

        bool StartsWith(const AZStd::string& value, const char* prefix)
        {
            const AZStd::string_view prefixView(prefix);
            return value.size() >= prefixView.size()
                && AZStd::string_view(value.data(), prefixView.size()) == prefixView;
        }

        bool IsAsciiAlpha(char value)
        {
            return (value >= 'A' && value <= 'Z')
                || (value >= 'a' && value <= 'z');
        }

        bool IsNetworkOrUriPath(const AZStd::string& value)
        {
            return StartsWith(value, "//")
                || StartsWith(value, "\\\\")
                || value.find("://") != AZStd::string::npos;
        }

        bool IsAbsoluteHostPath(
            const AZStd::string& value,
            const AZStd::string& platformId)
        {
            if (platformId == "windows")
            {
                return value.size() >= 3
                    && IsAsciiAlpha(value[0])
                    && value[1] == ':'
                    && (value[2] == '/' || value[2] == '\\');
            }
            if (platformId == "linux" || platformId == "mac")
            {
                return StartsWith(value, "/")
                    && !(value.size() >= 2 && value[1] == '/');
            }
            return false;
        }

        bool HasTraversalSegment(const AZStd::string& value)
        {
            AZStd::string normalized = value;
            AZStd::replace(normalized.begin(), normalized.end(), '\\', '/');
            size_t start = 0;
            while (start <= normalized.size())
            {
                const size_t end = normalized.find('/', start);
                const size_t length = end == AZStd::string::npos
                    ? normalized.size() - start
                    : end - start;
                if (normalized.substr(start, length) == "..")
                {
                    return true;
                }
                if (end == AZStd::string::npos)
                {
                    break;
                }
                start = end + 1;
            }
            return false;
        }

        AZStd::string PathString(const std::filesystem::path& value)
        {
            const std::string text = value.generic_string();
            return AZStd::string(text.data(), text.size());
        }

        std::filesystem::path PathFromUtf8(const AZStd::string& value)
        {
#if defined(__cpp_lib_char8_t)
            return std::filesystem::path(std::u8string(
                reinterpret_cast<const char8_t*>(value.data()),
                value.size()));
#else
            return std::filesystem::u8path(value.c_str());
#endif
        }

        AZStd::string NormalizeLocalPath(const AZStd::string& value)
        {
            std::error_code error;
            const std::filesystem::path path =
                PathFromUtf8(value).lexically_normal();
            (void)error;
            return PathString(path);
        }

        AZStd::string MakePathIdentity(
            AZStd::string normalizedPath,
            const AZStd::string& platformId)
        {
            if (platformId == "windows")
            {
                for (char& character : normalizedPath)
                {
                    if (character >= 'A' && character <= 'Z')
                    {
                        character = static_cast<char>(character - 'A' + 'a');
                    }
                }
            }
            return normalizedPath;
        }

        const ExternalToolResolvedConfigurationValue* FindResolvedValue(
            const AZStd::vector<ExternalToolResolvedConfigurationValue>& values,
            const AZStd::string& key)
        {
            for (const ExternalToolResolvedConfigurationValue& value : values)
            {
                if (value.m_key == key)
                {
                    return &value;
                }
            }
            return nullptr;
        }

        int StatusPriority(DiscoveryStatus status)
        {
            switch (status)
            {
            case DiscoveryStatus::Misconfigured:
                return 8;
            case DiscoveryStatus::ProbeFailed:
                return 7;
            case DiscoveryStatus::UnsupportedVersion:
                return 6;
            case DiscoveryStatus::NotInstalled:
                return 5;
            case DiscoveryStatus::NotRun:
                return 4;
            case DiscoveryStatus::Disabled:
                return 3;
            case DiscoveryStatus::UnsupportedPlatform:
                return 2;
            case DiscoveryStatus::Ambiguous:
                return 1;
            case DiscoveryStatus::Installed:
                return 0;
            }
            return 0;
        }

        AZ::u64 BoundValue(
            AZ::u64 value,
            AZ::u64 minimum,
            AZ::u64 maximum)
        {
            return value < minimum ? minimum : (value > maximum ? maximum : value);
        }

        bool ReadBoundedUInt64(
            const ExternalToolchainSettingsSource& settings,
            const char* path,
            AZ::u64 fallback,
            AZ::u64 minimum,
            AZ::u64 maximum,
            AZ::u64& value)
        {
            value = fallback;
            const ExternalToolchainSettingValueType type =
                settings.GetValueType(path);
            if (type == ExternalToolchainSettingValueType::Missing)
            {
                return true;
            }
            if (type != ExternalToolchainSettingValueType::UnsignedInteger
                || !settings.GetUInt64(path, value))
            {
                value = fallback;
                return false;
            }
            value = BoundValue(value, minimum, maximum);
            return true;
        }

        bool ReadOptionalBool(
            const ExternalToolchainSettingsSource& settings,
            const char* path,
            bool fallback,
            bool& value)
        {
            value = fallback;
            const ExternalToolchainSettingValueType type =
                settings.GetValueType(path);
            if (type == ExternalToolchainSettingValueType::Missing)
            {
                return true;
            }
            if (type != ExternalToolchainSettingValueType::Boolean
                || !settings.GetBool(path, value))
            {
                value = false;
                return false;
            }
            return true;
        }

        AZ::u64 ElapsedMilliseconds(
            const AZStd::chrono::steady_clock::time_point& started)
        {
            const auto elapsed =
                AZStd::chrono::duration_cast<AZStd::chrono::milliseconds>(
                    AZStd::chrono::steady_clock::now() - started);
            return elapsed.count() <= 0
                ? 0
                : static_cast<AZ::u64>(elapsed.count());
        }

        bool ProbeAppliesToPlatform(
            const ExternalToolDiscoveryProbeDescriptor& probe,
            const AZStd::string& platformId)
        {
            return probe.m_platforms.empty()
                || ContainsString(probe.m_platforms, platformId);
        }

        bool VersionWithinBounds(
            const AZStd::string& version,
            const ExternalToolDiscoveryProbeDescriptor& probe,
            AZStd::string& message)
        {
            if (!probe.m_versionConfigurationKey.empty() && version.empty())
            {
                message =
                    "A probe that declares a version key requires one configured semantic version.";
                return false;
            }
            if (version.empty())
            {
                if (!probe.m_minimumSupportedVersion.empty()
                    || !probe.m_maximumSupportedVersion.empty())
                {
                    message =
                        "A configured semantic tool version is required for compatibility checks.";
                    return false;
                }
                return true;
            }
            if (!IsValidSemanticVersion(version))
            {
                message = "Configured tool version is not valid semantic versioning.";
                return false;
            }

            int comparison = 0;
            if (!probe.m_minimumSupportedVersion.empty())
            {
                if (!TryCompareSemanticVersions(
                        version,
                        probe.m_minimumSupportedVersion,
                        comparison))
                {
                    message = "Minimum supported version comparison failed.";
                    return false;
                }
                if (comparison < 0)
                {
                    message = "Configured tool version is below the supported minimum.";
                    return false;
                }
            }
            if (!probe.m_maximumSupportedVersion.empty())
            {
                if (!TryCompareSemanticVersions(
                        version,
                        probe.m_maximumSupportedVersion,
                        comparison))
                {
                    message = "Maximum supported version comparison failed.";
                    return false;
                }
                if (comparison > 0)
                {
                    message = "Configured tool version is above the supported maximum.";
                    return false;
                }
            }
            return true;
        }

        bool PathIdentitiesMatch(
            const std::filesystem::path& left,
            const std::filesystem::path& right)
        {
            AZStd::string leftText = PathString(left.lexically_normal());
            AZStd::string rightText = PathString(right.lexically_normal());
#if AZ_TRAIT_USE_WINDOWS_FILE_API
            leftText = MakePathIdentity(AZStd::move(leftText), "windows");
            rightText = MakePathIdentity(AZStd::move(rightText), "windows");
#endif
            return leftText == rightText;
        }

        ExternalToolPathObservation InspectLocalPathSynchronously(
            const AZStd::string& path)
        {
            ExternalToolPathObservation observation;
            std::error_code error;
            const std::filesystem::path input =
                PathFromUtf8(path).lexically_normal();
            const std::filesystem::file_status status =
                std::filesystem::symlink_status(input, error);
            if (error)
            {
                observation.m_message =
                    "Path metadata could not be read without crossing the local-discovery boundary.";
                return observation;
            }
            if (!std::filesystem::exists(status))
            {
                observation.m_boundarySafe = true;
                observation.m_message = "Path does not exist.";
                return observation;
            }
            if (std::filesystem::is_symlink(status))
            {
                observation.m_message =
                    "Symbolic links and filesystem indirection are prohibited.";
                return observation;
            }

#if AZ_TRAIT_USE_WINDOWS_FILE_API
            const std::wstring root = input.root_name().wstring() + L"\\";
            const UINT driveType = GetDriveTypeW(root.c_str());
            if (driveType != DRIVE_FIXED && driveType != DRIVE_RAMDISK)
            {
                observation.m_message =
                    "Discovery is restricted to fixed local or RAM-backed storage.";
                return observation;
            }
            const DWORD attributes = GetFileAttributesW(input.c_str());
            if (attributes == INVALID_FILE_ATTRIBUTES)
            {
                observation.m_message = "Windows path attributes could not be read.";
                return observation;
            }
            if ((attributes & FILE_ATTRIBUTE_REPARSE_POINT) != 0)
            {
                observation.m_message =
                    "Windows reparse points, junctions, and redirected storage are prohibited.";
                return observation;
            }
#else
            struct stat rootStatus{};
            if (::stat("/", &rootStatus) != 0)
            {
                observation.m_message = "The host root storage identity is unavailable.";
                return observation;
            }
            std::filesystem::path current = input.root_path();
            for (const std::filesystem::path& component : input.relative_path())
            {
                current /= component;
                struct stat linkStatus{};
                struct stat resolvedStatus{};
                if (::lstat(current.c_str(), &linkStatus) != 0
                    || S_ISLNK(linkStatus.st_mode))
                {
                    observation.m_message =
                        "Symbolic links and unresolved path components are prohibited.";
                    return observation;
                }
                if (::stat(current.c_str(), &resolvedStatus) != 0
                    || resolvedStatus.st_dev != rootStatus.st_dev)
                {
                    observation.m_message =
                        "Mount-point or redirected-storage boundaries are prohibited.";
                    return observation;
                }
            }
#endif

            const std::filesystem::path resolved =
                std::filesystem::canonical(input, error);
            if (error || !PathIdentitiesMatch(input, resolved))
            {
                observation.m_message =
                    "The final filesystem identity differs from the declared local path.";
                return observation;
            }

            observation.m_exists = true;
            observation.m_isDirectory = std::filesystem::is_directory(status);
            observation.m_boundarySafe = true;
            observation.m_resolvedPath = PathString(resolved);
            observation.m_message = observation.m_isDirectory
                ? "Local directory exists without filesystem indirection."
                : "Local file exists without filesystem indirection.";
            return observation;
        }

    } // namespace

    ExternalToolPathObservation SystemFileExternalToolPathProbe::Inspect(
        const AZStd::string& path) const
    {
        return Inspect(path, HardProbeTimeoutMilliseconds);
    }

    ExternalToolPathObservation SystemFileExternalToolPathProbe::Inspect(
        const AZStd::string& path,
        AZ::u32 timeoutMilliseconds) const
    {
        const AZ::u32 boundedTimeout = AZStd::min(
            AZStd::max<AZ::u32>(timeoutMilliseconds, 1),
            HardProbeTimeoutMilliseconds);
        const auto started = AZStd::chrono::steady_clock::now();
        ExternalToolPathObservation observation =
            InspectLocalPathSynchronously(path);
        if (ElapsedMilliseconds(started) > boundedTimeout)
        {
            observation.m_exists = false;
            observation.m_isDirectory = false;
            observation.m_boundarySafe = false;
            observation.m_resolvedPath.clear();
            observation.m_timedOut = true;
            observation.m_message =
                "Path inspection exceeded the bounded discovery timeout. The synchronous inspection completed before returning, so no worker survives Gem shutdown.";
        }
        return observation;
    }

    ExternalToolchainDiscoveryService::ExternalToolchainDiscoveryService(
        const ExternalToolPathProbe& pathProbe,
        const ExternalToolchainSettingsSource& settingsSource)
        : m_pathProbe(pathProbe)
        , m_settingsSource(settingsSource)
    {
    }

    ProviderOperationResult ExternalToolchainDiscoveryService::Refresh(
        const AZStd::vector<ExternalToolProviderDescriptor>& providers,
        const ExternalToolchainConfigurationService& configurationService,
        const AZStd::string& platformId)
    {
        bool discoveryEnabled = true;
        AZ::u64 maximumProviders = 64;
        AZ::u64 maximumProbes = 16;
        AZ::u64 providerBudgetMilliseconds = 250;
        const bool settingsValid = ReadOptionalBool(
            m_settingsSource,
            DiscoveryEnabledPath,
            true,
            discoveryEnabled)
            && ReadBoundedUInt64(
            m_settingsSource,
            MaximumProvidersPath,
            64,
            1,
            1024,
            maximumProviders)
            && ReadBoundedUInt64(
            m_settingsSource,
            MaximumProbesPerProviderPath,
            16,
            1,
            128,
            maximumProbes)
            && ReadBoundedUInt64(
            m_settingsSource,
            ProviderBudgetMillisecondsPath,
            250,
            1,
            5000,
            providerBudgetMilliseconds);

        AZStd::vector<ExternalToolProviderDescriptor> orderedProviders = providers;
        AZStd::sort(
            orderedProviders.begin(),
            orderedProviders.end(),
            [](const ExternalToolProviderDescriptor& left,
               const ExternalToolProviderDescriptor& right)
            {
                return left.m_providerId < right.m_providerId;
            });

        if (!settingsValid)
        {
            m_results.clear();
            m_results.reserve(orderedProviders.size());
            for (const ExternalToolProviderDescriptor& provider : orderedProviders)
            {
                ExternalToolDiscoveryResult result;
                result.m_providerId = provider.m_providerId;
                result.m_status = DiscoveryStatus::Misconfigured;
                result.m_diagnostics.push_back(
                    "A host discovery setting has the wrong value type.");
                m_results.push_back(AZStd::move(result));
            }
            return Failure(
                "Host discovery settings are malformed and discovery was not run.");
        }

        if (providers.size() > maximumProviders)
        {
            m_results.clear();
            return Failure(
                "Registered provider count exceeds the configured discovery limit.");
        }

        m_results.clear();
        m_results.reserve(orderedProviders.size());
        for (const ExternalToolProviderDescriptor& provider : orderedProviders)
        {
            if (!discoveryEnabled)
            {
                ExternalToolDiscoveryResult result;
                result.m_providerId = provider.m_providerId;
                result.m_status = DiscoveryStatus::Disabled;
                result.m_diagnostics.push_back(
                    "Host discovery is disabled by Settings Registry configuration.");
                m_results.push_back(AZStd::move(result));
                continue;
            }
            m_results.push_back(DiscoverProvider(
                provider,
                configurationService,
                platformId,
                maximumProbes,
                providerBudgetMilliseconds));
        }
        return Success("Provider discovery refreshed.");
    }

    const AZStd::vector<ExternalToolDiscoveryResult>&
    ExternalToolchainDiscoveryService::GetResults() const
    {
        return m_results;
    }

    const ExternalToolDiscoveryResult*
    ExternalToolchainDiscoveryService::FindResult(
        const AZStd::string& providerId) const
    {
        for (const ExternalToolDiscoveryResult& result : m_results)
        {
            if (result.m_providerId == providerId)
            {
                return &result;
            }
        }
        return nullptr;
    }

    void ExternalToolchainDiscoveryService::Clear()
    {
        m_results.clear();
    }

    ExternalToolDiscoveryResult
    ExternalToolchainDiscoveryService::DiscoverProvider(
        const ExternalToolProviderDescriptor& provider,
        const ExternalToolchainConfigurationService& configurationService,
        const AZStd::string& platformId,
        AZ::u64 maximumProbes,
        AZ::u64 providerBudgetMilliseconds) const
    {
        const auto providerStarted = AZStd::chrono::steady_clock::now();
        ExternalToolDiscoveryResult result;
        result.m_providerId = provider.m_providerId;

        if (!provider.m_platforms.empty()
            && !ContainsString(provider.m_platforms, platformId))
        {
            result.m_status = DiscoveryStatus::UnsupportedPlatform;
            result.m_diagnostics.push_back(
                "Provider does not declare support for the current host platform.");
            return result;
        }

        bool providerEnabled = true;
        ConfigurationLayer enabledLayer = ConfigurationLayer::ProviderDefault;
        if (!configurationService.ResolveProviderEnabled(
            provider,
            providerEnabled,
            enabledLayer))
        {
            result.m_status = DiscoveryStatus::Misconfigured;
            result.m_diagnostics.push_back(
                "The provider enabled setting has the wrong value type.");
            return result;
        }
        if (!providerEnabled)
        {
            result.m_status = DiscoveryStatus::Disabled;
            result.m_diagnostics.push_back(AZStd::string::format(
                "Provider is disabled by the %s configuration layer.",
                ToString(enabledLayer).c_str()));
            return result;
        }
        if (provider.m_discoveryProbes.empty())
        {
            result.m_status = DiscoveryStatus::NotRun;
            result.m_diagnostics.push_back("Provider declares no discovery probes.");
            return result;
        }
        if (provider.m_discoveryProbes.size() > maximumProbes)
        {
            result.m_status = DiscoveryStatus::ProbeFailed;
            result.m_diagnostics.push_back(
                "Provider probe count exceeds the configured per-provider limit.");
            return result;
        }

        const AZStd::vector<ExternalToolResolvedConfigurationValue>
            resolvedConfiguration = configurationService.ResolveAll(provider);
        AZStd::vector<ExternalToolDiscoveryProbeDescriptor> probes =
            provider.m_discoveryProbes;
        AZStd::sort(
            probes.begin(),
            probes.end(),
            [](const ExternalToolDiscoveryProbeDescriptor& left,
               const ExternalToolDiscoveryProbeDescriptor& right)
            {
                return left.m_probeId < right.m_probeId;
            });

        AZStd::unordered_set<AZStd::string> seenPaths;
        size_t applicableProbeCount = 0;
        for (const ExternalToolDiscoveryProbeDescriptor& probe : probes)
        {
            if (!ProbeAppliesToPlatform(probe, platformId))
            {
                continue;
            }
            ++applicableProbeCount;

            ExternalToolInstallationCandidate candidate;
            candidate.m_providerId = provider.m_providerId;
            candidate.m_probeId = probe.m_probeId;
            if (ElapsedMilliseconds(providerStarted) >= providerBudgetMilliseconds)
            {
                candidate.m_status = DiscoveryStatus::ProbeFailed;
                candidate.m_message =
                    "Provider discovery budget was exhausted before this probe.";
                result.m_candidates.push_back(AZStd::move(candidate));
                continue;
            }

            const ExternalToolResolvedConfigurationValue* pathValue =
                FindResolvedValue(
                    resolvedConfiguration,
                    probe.m_pathConfigurationKey);
            if (!pathValue || !pathValue->m_configured)
            {
                candidate.m_status = probe.m_required
                    ? DiscoveryStatus::Misconfigured
                    : DiscoveryStatus::NotInstalled;
                candidate.m_message = "The probe path configuration is missing.";
                result.m_candidates.push_back(AZStd::move(candidate));
                continue;
            }
            if (!pathValue->m_valueValid)
            {
                candidate.m_status = DiscoveryStatus::Misconfigured;
                candidate.m_message =
                    "The probe path configuration has an invalid type or value.";
                result.m_candidates.push_back(AZStd::move(candidate));
                continue;
            }

            candidate.m_pathLayer = pathValue->m_layer;
            candidate.m_path = pathValue->m_value;
            if (IsNetworkOrUriPath(candidate.m_path)
                || !IsAbsoluteHostPath(candidate.m_path, platformId)
                || HasTraversalSegment(candidate.m_path))
            {
                candidate.m_status = DiscoveryStatus::Misconfigured;
                candidate.m_message =
                    "Discovery paths must be host-native absolute local paths without URI, network, or traversal syntax.";
                result.m_candidates.push_back(AZStd::move(candidate));
                continue;
            }

            candidate.m_path = NormalizeLocalPath(candidate.m_path);
            const AZStd::string identity =
                MakePathIdentity(candidate.m_path, platformId);
            if (!seenPaths.insert(identity).second)
            {
                candidate.m_status = DiscoveryStatus::Misconfigured;
                candidate.m_message =
                    "A duplicate candidate path cannot satisfy a distinct discovery probe.";
                result.m_candidates.push_back(AZStd::move(candidate));
                continue;
            }

            const auto probeStarted = AZStd::chrono::steady_clock::now();
            const ExternalToolPathObservation observation =
                m_pathProbe.Inspect(candidate.m_path, probe.m_timeoutMilliseconds);
            candidate.m_elapsedMilliseconds = ElapsedMilliseconds(probeStarted);
            if (observation.m_timedOut)
            {
                candidate.m_status = DiscoveryStatus::ProbeFailed;
                candidate.m_message = observation.m_message;
                result.m_candidates.push_back(AZStd::move(candidate));
                continue;
            }
            if (!observation.m_boundarySafe)
            {
                candidate.m_status = DiscoveryStatus::Misconfigured;
                candidate.m_message = observation.m_message;
                result.m_candidates.push_back(AZStd::move(candidate));
                continue;
            }
            if (ElapsedMilliseconds(providerStarted) > providerBudgetMilliseconds)
            {
                candidate.m_status = DiscoveryStatus::ProbeFailed;
                candidate.m_message =
                    "Provider discovery budget was exceeded during bounded path inspection.";
                result.m_candidates.push_back(AZStd::move(candidate));
                continue;
            }

            if (!observation.m_resolvedPath.empty())
            {
                candidate.m_path = observation.m_resolvedPath;
            }
            candidate.m_pathExists = observation.m_exists;
            candidate.m_kindMatches = observation.m_exists
                && ((probe.m_kind == DiscoveryProbeKind::Directory
                        && observation.m_isDirectory)
                    || (probe.m_kind == DiscoveryProbeKind::File
                        && !observation.m_isDirectory));
            if (!observation.m_exists)
            {
                candidate.m_status = DiscoveryStatus::NotInstalled;
                candidate.m_message = observation.m_message;
                result.m_candidates.push_back(AZStd::move(candidate));
                continue;
            }
            if (!candidate.m_kindMatches)
            {
                candidate.m_status = DiscoveryStatus::Misconfigured;
                candidate.m_message =
                    "Discovered path does not match the declared file/directory kind.";
                result.m_candidates.push_back(AZStd::move(candidate));
                continue;
            }

            if (!probe.m_versionConfigurationKey.empty())
            {
                const ExternalToolResolvedConfigurationValue* versionValue =
                    FindResolvedValue(
                        resolvedConfiguration,
                        probe.m_versionConfigurationKey);
                if (!versionValue
                    || !versionValue->m_configured
                    || !versionValue->m_valueValid
                    || versionValue->m_value.empty())
                {
                    candidate.m_status = DiscoveryStatus::Misconfigured;
                    candidate.m_message =
                        "A versioned probe requires one configured valid semantic version.";
                    result.m_candidates.push_back(AZStd::move(candidate));
                    continue;
                }
                candidate.m_version = versionValue->m_value;
            }

            AZStd::string versionMessage;
            if (!VersionWithinBounds(candidate.m_version, probe, versionMessage))
            {
                candidate.m_status = candidate.m_version.empty()
                        || !IsValidSemanticVersion(candidate.m_version)
                    ? DiscoveryStatus::Misconfigured
                    : DiscoveryStatus::UnsupportedVersion;
                candidate.m_message = AZStd::move(versionMessage);
                result.m_candidates.push_back(AZStd::move(candidate));
                continue;
            }

            candidate.m_status = DiscoveryStatus::Installed;
            candidate.m_message =
                "Resolved fixed local path satisfies the exact declared probe.";
            result.m_candidates.push_back(AZStd::move(candidate));
        }

        if (applicableProbeCount == 0)
        {
            result.m_status = DiscoveryStatus::NotRun;
            result.m_diagnostics.push_back(
                "Provider declares no discovery probes for the current platform.");
            return result;
        }

        result.m_elapsedMilliseconds = ElapsedMilliseconds(providerStarted);
        bool requiredProbeFailed = false;
        DiscoveryStatus requiredFailureStatus = DiscoveryStatus::NotInstalled;
        int requiredFailurePriority = StatusPriority(requiredFailureStatus);
        AZStd::vector<const ExternalToolInstallationCandidate*> installed;
        for (const ExternalToolInstallationCandidate& candidate : result.m_candidates)
        {
            if (candidate.m_status == DiscoveryStatus::Installed)
            {
                installed.push_back(&candidate);
            }
            const auto probe = AZStd::find_if(
                probes.begin(),
                probes.end(),
                [&candidate](const ExternalToolDiscoveryProbeDescriptor& value)
                {
                    return value.m_probeId == candidate.m_probeId;
                });
            if (probe != probes.end()
                && probe->m_required
                && candidate.m_status != DiscoveryStatus::Installed)
            {
                requiredProbeFailed = true;
                const int priority = StatusPriority(candidate.m_status);
                if (priority > requiredFailurePriority)
                {
                    requiredFailurePriority = priority;
                    requiredFailureStatus = candidate.m_status;
                }
            }
        }

        if (result.m_candidates.size() != applicableProbeCount)
        {
            requiredProbeFailed = true;
            requiredFailureStatus = DiscoveryStatus::ProbeFailed;
            result.m_diagnostics.push_back(
                "Every applicable probe must emit one candidate result.");
        }
        if (requiredProbeFailed)
        {
            result.m_status = requiredFailureStatus;
            result.m_diagnostics.push_back(
                "One or more required discovery probes did not succeed.");
            return result;
        }
        if (installed.size() == 1)
        {
            result.m_status = DiscoveryStatus::Installed;
            result.m_selectedPath = installed.front()->m_path;
            result.m_selectedVersion = installed.front()->m_version;
            return result;
        }
        if (installed.size() > 1)
        {
            result.m_status = DiscoveryStatus::Ambiguous;
            result.m_diagnostics.push_back(
                "Multiple distinct compatible installations were discovered; configuration must select one exact path.");
            return result;
        }

        result.m_status = DiscoveryStatus::NotInstalled;
        int priority = StatusPriority(result.m_status);
        for (const ExternalToolInstallationCandidate& candidate : result.m_candidates)
        {
            const int candidatePriority = StatusPriority(candidate.m_status);
            if (candidatePriority > priority)
            {
                priority = candidatePriority;
                result.m_status = candidate.m_status;
            }
        }
        return result;
    }

    AZStd::string GetCurrentHostPlatformId()
    {
        return AZ_TRAIT_OS_PLATFORM_CODENAME_LOWER;
    }
} // namespace ExternalToolchain
