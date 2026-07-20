/*
 * Copyright (c) Contributors to the Open 3D Engine Project.
 * For complete copyright and license terms please see the LICENSE at the root of this distribution.
 *
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 */

#pragma once

#include <AzCore/Component/Component.h>
#include <AzToolsFramework/API/ToolsApplicationAPI.h>

namespace TaintedGrailModdingSDK
{
    class ActorTroopEditorPaneSystemComponent final
        : public AZ::Component
        , private AzToolsFramework::EditorEvents::Bus::Handler
    {
    public:
        AZ_COMPONENT(
            ActorTroopEditorPaneSystemComponent,
            "{82CE01DC-8D67-4E04-A2D1-93ED4E05F113}");

        static void Reflect(AZ::ReflectContext* context);

        void Activate() override;
        void Deactivate() override;

    private:
        void NotifyRegisterViews() override;

        bool m_viewRegistered = false;
    };
} // namespace TaintedGrailModdingSDK
