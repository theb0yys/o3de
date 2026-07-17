/*
 * Copyright (c) Contributors to the Open 3D Engine Project.
 * For complete copyright and license terms please see the LICENSE at the root of this distribution.
 *
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 */

#include "TaintedGrailModdingSDKSystemComponent.h"

#include "FoundationModels.h"
#include "FoundationService.h"
#include "FoundationStatusWidget.h"
#include "PackManagerWidget.h"
#include "SourceEvidenceIntakeWidget.h"

#include <AzCore/Debug/Trace.h>
#include <AzCore/Math/Crc.h>
#include <AzCore/Serialization/SerializeContext.h>
#include <AzToolsFramework/API/ViewPaneOptions.h>

namespace TaintedGrailModdingSDK
{
    namespace
    {
        constexpr const char* FoundationStatusViewPaneName = "Tainted Grail SDK Status";
        constexpr const char* PackManagerViewPaneName = "Tainted Grail Pack Manager";
        constexpr const char* SourceIntakeViewPaneName = "Tainted Grail Source Intake";
    }

    void TaintedGrailModdingSDKSystemComponent::Reflect(AZ::ReflectContext* context)
    {
        GameProfile::Reflect(context);
        WorkspaceModel::Reflect(context);
        PackManifest::Reflect(context);
        SourceImporterContract::Reflect(context);
        SourceRecord::Reflect(context);
        EvidenceRecord::Reflect(context);
        ImportIssue::Reflect(context);
        SourceDocument::Reflect(context);
        EvidenceDocument::Reflect(context);
        CatalogRecord::Reflect(context);
        BlockerRecord::Reflect(context);
        DomainCoverage::Reflect(context);
        FoundationSnapshot::Reflect(context);

        if (auto* serializeContext = azrtti_cast<AZ::SerializeContext*>(context))
        {
            serializeContext->Class<TaintedGrailModdingSDKSystemComponent, AZ::Component>()
                ->Version(4);
        }
    }

    void TaintedGrailModdingSDKSystemComponent::GetProvidedServices(
        AZ::ComponentDescriptor::DependencyArrayType& provided)
    {
        provided.push_back(AZ_CRC_CE("TaintedGrailModdingSDKService"));
    }

    void TaintedGrailModdingSDKSystemComponent::GetIncompatibleServices(
        AZ::ComponentDescriptor::DependencyArrayType& incompatible)
    {
        incompatible.push_back(AZ_CRC_CE("TaintedGrailModdingSDKService"));
    }

    void TaintedGrailModdingSDKSystemComponent::Activate()
    {
        FoundationService::Get().Initialize();
        AzToolsFramework::EditorEvents::Bus::Handler::BusConnect();

        AZ_Printf(
            "TaintedGrailModdingSDK",
            "Editor foundation activated. FoA runtime execution remains disabled.\n");
    }

    void TaintedGrailModdingSDKSystemComponent::Deactivate()
    {
        if (m_viewRegistered)
        {
            AzToolsFramework::UnregisterViewPane(FoundationStatusViewPaneName);
            AzToolsFramework::UnregisterViewPane(PackManagerViewPaneName);
            AzToolsFramework::UnregisterViewPane(SourceIntakeViewPaneName);
            m_viewRegistered = false;
        }

        AzToolsFramework::EditorEvents::Bus::Handler::BusDisconnect();
        FoundationService::Get().Shutdown();
        AZ_Printf("TaintedGrailModdingSDK", "Editor foundation deactivated.\n");
    }

    void TaintedGrailModdingSDKSystemComponent::NotifyRegisterViews()
    {
        if (m_viewRegistered)
        {
            return;
        }

        AzToolsFramework::ViewPaneOptions statusOptions;
        statusOptions.paneRect = QRect(100, 100, 760, 900);
        statusOptions.preferedDockingArea = Qt::RightDockWidgetArea;
        statusOptions.isDeletable = true;
        statusOptions.isPreview = true;
        statusOptions.saveKeyName = QStringLiteral("TaintedGrailModdingSDK.FoundationStatus");

        AzToolsFramework::RegisterViewPane<FoundationStatusWidget>(
            FoundationStatusViewPaneName,
            "Tainted Grail SDK",
            statusOptions);

        AzToolsFramework::ViewPaneOptions packOptions;
        packOptions.paneRect = QRect(120, 120, 820, 920);
        packOptions.preferedDockingArea = Qt::LeftDockWidgetArea;
        packOptions.isDeletable = true;
        packOptions.isPreview = true;
        packOptions.saveKeyName = QStringLiteral("TaintedGrailModdingSDK.PackManager");

        AzToolsFramework::RegisterViewPane<PackManagerWidget>(
            PackManagerViewPaneName,
            "Tainted Grail SDK",
            packOptions);

        AzToolsFramework::ViewPaneOptions intakeOptions;
        intakeOptions.paneRect = QRect(140, 140, 1000, 900);
        intakeOptions.preferedDockingArea = Qt::BottomDockWidgetArea;
        intakeOptions.isDeletable = true;
        intakeOptions.isPreview = true;
        intakeOptions.saveKeyName = QStringLiteral("TaintedGrailModdingSDK.SourceIntake");

        AzToolsFramework::RegisterViewPane<SourceEvidenceIntakeWidget>(
            SourceIntakeViewPaneName,
            "Tainted Grail SDK",
            intakeOptions);

        m_viewRegistered = true;
    }
} // namespace TaintedGrailModdingSDK
