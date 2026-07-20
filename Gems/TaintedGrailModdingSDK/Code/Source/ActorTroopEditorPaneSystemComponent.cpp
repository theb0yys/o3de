/*
 * Copyright (c) Contributors to the Open 3D Engine Project.
 * For complete copyright and license terms please see the LICENSE at the root of this distribution.
 *
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 */

#include "ActorTroopEditorPaneSystemComponent.h"

#include "ActorTroopEditorWidget.h"

#include <AzCore/Serialization/SerializeContext.h>
#include <AzToolsFramework/API/ViewPaneOptions.h>
#include <QtCore/QRect>
#include <QtCore/QString>
#include <QtCore/qnamespace.h>

namespace TaintedGrailModdingSDK
{
    namespace
    {
        constexpr const char* ActorTroopEditorViewPaneName =
            "Tainted Grail Actor and Troop Editor";
    }

    void ActorTroopEditorPaneSystemComponent::Reflect(
        AZ::ReflectContext* context)
    {
        if (auto* serializeContext = azrtti_cast<AZ::SerializeContext*>(context))
        {
            serializeContext
                ->Class<ActorTroopEditorPaneSystemComponent, AZ::Component>()
                ->Version(1);
        }
    }

    void ActorTroopEditorPaneSystemComponent::Activate()
    {
        AzToolsFramework::EditorEvents::Bus::Handler::BusConnect();
    }

    void ActorTroopEditorPaneSystemComponent::Deactivate()
    {
        if (m_viewRegistered)
        {
            AzToolsFramework::UnregisterViewPane(
                ActorTroopEditorViewPaneName);
            m_viewRegistered = false;
        }
        AzToolsFramework::EditorEvents::Bus::Handler::BusDisconnect();
    }

    void ActorTroopEditorPaneSystemComponent::NotifyRegisterViews()
    {
        if (m_viewRegistered)
        {
            return;
        }

        AzToolsFramework::ViewPaneOptions options;
        options.paneRect = QRect(200, 160, 1460, 1040);
        options.preferedDockingArea = Qt::RightDockWidgetArea;
        options.isDeletable = true;
        options.isPreview = true;
        options.saveKeyName =
            QStringLiteral("TaintedGrailModdingSDK.ActorTroopEditor");
        AzToolsFramework::RegisterViewPane<ActorTroopEditorWidget>(
            ActorTroopEditorViewPaneName,
            "Tainted Grail SDK",
            options);
        m_viewRegistered = true;
    }
} // namespace TaintedGrailModdingSDK
