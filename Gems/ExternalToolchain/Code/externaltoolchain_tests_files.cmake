#
# Copyright (c) Contributors to the Open 3D Engine Project.
# For complete copyright and license terms please see the LICENSE at the root of this distribution.
#
# SPDX-License-Identifier: Apache-2.0 OR MIT
#

set(FILES
    Tests/Main.cpp
    Tests/ExternalToolchainConfigurationTests.cpp
    Tests/ExternalToolchainDiscoveryTests.cpp
    Tests/ExternalToolchainRegistryTests.cpp
)

# Focused tests also use repeated fixture-local helper names. Compile each test
# source independently so unity mode preserves ordinary translation-unit scope.
set(SKIP_UNITY_BUILD_INCLUSION_FILES)
foreach(source_file IN LISTS FILES)
    if(source_file MATCHES "\\.cpp$")
        list(APPEND SKIP_UNITY_BUILD_INCLUSION_FILES ${source_file})
    endif()
endforeach()
