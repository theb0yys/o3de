#
# Copyright (c) Contributors to the Open 3D Engine Project.
# For complete copyright and license terms please see the LICENSE at the root of this distribution.
#
# SPDX-License-Identifier: Apache-2.0 OR MIT
#

if(NOT PAL_TRAIT_BUILD_HOST_TOOLS)
    return()
endif()

ly_add_target(
    NAME ${gem_name}.Provider.Static STATIC
    NAMESPACE Gem
    FILES_CMAKE
        taintedgrailmerlinworkshop_provider_files.cmake
    INCLUDE_DIRECTORIES
        PUBLIC
            Include
    BUILD_DEPENDENCIES
        PUBLIC
            Gem::ExternalToolchain.API
            AZ::AzCore
)

ly_add_target(
    NAME ${gem_name}.Editor GEM_MODULE
    NAMESPACE Gem
    FILES_CMAKE
        taintedgrailmerlinworkshop_editor_files.cmake
    INCLUDE_DIRECTORIES
        PRIVATE
            Include
            Source
    BUILD_DEPENDENCIES
        PRIVATE
            Gem::${gem_name}.Provider.Static
            AZ::AzCore
)

ly_add_source_properties(
    SOURCES
        Source/Editor/TaintedGrailMerlinWorkshopEditorModule.cpp
    PROPERTY COMPILE_DEFINITIONS
        VALUES
            O3DE_GEM_NAME=${gem_name}
            O3DE_GEM_VERSION=${gem_version}
)

ly_create_alias(NAME ${gem_name}.Builders NAMESPACE Gem TARGETS Gem::${gem_name}.Editor)
ly_create_alias(NAME ${gem_name}.Tools NAMESPACE Gem TARGETS Gem::${gem_name}.Editor)

o3de_add_variant_dependencies_for_gem_dependencies(
    GEM_NAME ${gem_name}
    VARIANTS Tools Builders
)

if(PAL_TRAIT_BUILD_TESTS_SUPPORTED AND PAL_TRAIT_TEST_GOOGLE_TEST_SUPPORTED)
    ly_add_target(
        NAME ${gem_name}.Tests ${PAL_TRAIT_TEST_TARGET_TYPE}
        NAMESPACE Gem
        FILES_CMAKE
            taintedgrailmerlinworkshop_tests_files.cmake
        INCLUDE_DIRECTORIES
            PRIVATE
                Include
                Tests
        BUILD_DEPENDENCIES
            PRIVATE
                Gem::${gem_name}.Provider.Static
                AZ::AzTest
    )

    ly_add_googletest(
        NAME Gem::${gem_name}.Tests
        LABELS REQUIRES_tiaf
    )
endif()
