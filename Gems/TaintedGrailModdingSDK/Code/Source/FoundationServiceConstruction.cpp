/*
 * Copyright (c) Contributors to the Open 3D Engine Project.
 * For complete copyright and license terms please see the LICENSE at the root of this distribution.
 *
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 */

#include "FoundationService.h"

namespace TaintedGrailModdingSDK
{
    FoundationService::FoundationService()
        : m_workspacePersistence(m_pathPolicy)
        , m_packPersistence(
            m_pathPolicy,
            [this]() -> const WorkspaceModel&
            {
                return m_workspace;
            },
            [this]() -> const AZStd::string&
            {
                return m_workspacePersistence.GetLastResolvedPath();
            })
    {
    }
} // namespace TaintedGrailModdingSDK
