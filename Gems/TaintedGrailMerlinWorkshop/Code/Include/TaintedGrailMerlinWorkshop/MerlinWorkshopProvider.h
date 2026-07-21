/*
 * Copyright (c) Contributors to the Open 3D Engine Project.
 * For complete copyright and license terms please see the LICENSE at the root of this distribution.
 *
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 */

#pragma once

#include <ExternalToolchain/ExternalToolchainTypes.h>

namespace TaintedGrailMerlinWorkshop
{
    inline constexpr const char* ProviderId = "foa.merlin-workshop";
    inline constexpr const char* ProviderVersion = "0.1.0";
    inline constexpr const char* QualifiedWorkshopVersion = "1.1.0";
    inline constexpr const char* QualifiedWorkshopReleaseTag = "v1.1.0";
    inline constexpr const char* QualifiedWorkshopRevision =
        "073bdab3e09d6adad5003339fc49b021738d71e6";
    inline constexpr const char* QualifiedUnityEditorVersion = "6000.0.60f1";
    inline constexpr const char* QualifiedUnityEditorRevision = "61dfb374e36f";

    ExternalToolchain::ExternalToolProviderDescriptor
        CreateMerlinWorkshopProviderDescriptor();
} // namespace TaintedGrailMerlinWorkshop
