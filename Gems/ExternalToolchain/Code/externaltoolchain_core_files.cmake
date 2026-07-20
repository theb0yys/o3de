#
# Copyright (c) Contributors to the Open 3D Engine Project.
# For complete copyright and license terms please see the LICENSE at the root of this distribution.
#
# SPDX-License-Identifier: Apache-2.0 OR MIT
#

set(FILES
    Source/ExternalToolchainConfigurationService.cpp
    Source/ExternalToolchainConfigurationService.h
    Source/ExternalToolchainDiscoveryService.cpp
    Source/ExternalToolchainDiscoveryService.h
    Source/ExternalToolchainRegistry.cpp
    Source/ExternalToolchainRegistry.h
    Source/ExternalToolchainTypes.cpp
)

# Core implementations use file-local helpers with intentionally narrow names.
# Keep them in separate translation units so unity concatenation cannot merge
# unrelated anonymous namespaces.
set(SKIP_UNITY_BUILD_INCLUSION_FILES)
foreach(source_file IN LISTS FILES)
    if(source_file MATCHES "\\.cpp$")
        list(APPEND SKIP_UNITY_BUILD_INCLUSION_FILES ${source_file})
    endif()
endforeach()
