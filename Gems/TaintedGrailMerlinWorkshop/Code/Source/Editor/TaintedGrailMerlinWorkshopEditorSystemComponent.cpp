/*
 * Copyright (c) Contributors to the Open 3D Engine Project.
 * For complete copyright and license terms please see the LICENSE at the root of this distribution.
 *
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 */

#include "TaintedGrailMerlinWorkshopEditorSystemComponent.h"

#include <TaintedGrailMerlinWorkshop/MerlinWorkshopProvider.h>

#include <ExternalToolchain/ExternalToolchainBus.h>

#include <AzCore/Debug/Trace.h>
#include <AzCore/Math/Crc.h>
#include <AzCore/Serialization/SerializeContext.h>

namespace TaintedGrailMerlinWorkshop
{
    void EditorSystemComponent::Reflect(AZ::ReflectContext* context)
    {
        if (auto* serializeContext = azrtti_cast<AZ::SerializeContext*>(context))
        {
            serializeContext
                ->Class<EditorSystemComponent, AZ::Component>()
                ->Version(1);
        }
    }

    void EditorSystemComponent::GetProvidedServices(
        AZ::ComponentDescriptor::DependencyArrayType& provided)
    {
        provided.push_back(AZ_CRC_CE("TaintedGrailMerlinWorkshopProviderService"));
    }

    void EditorSystemComponent::GetIncompatibleServices(
        AZ::ComponentDescriptor::DependencyArrayType& incompatible)
    {
        incompatible.push_back(
            AZ_CRC_CE("TaintedGrailMerlinWorkshopProviderService"));
    }

    void EditorSystemComponent::GetRequiredServices(
        AZ::ComponentDescriptor::DependencyArrayType& required)
    {
        required.push_back(AZ_CRC_CE("ExternalToolchainService"));
    }

    void EditorSystemComponent::Activate()
    {
        ExternalToolchain::ProviderOperationResult result;
        ExternalToolchain::ExternalToolchainRequestBus::BroadcastResult(
            result,
            &ExternalToolchain::ExternalToolchainRequests::RegisterProvider,
            CreateMerlinWorkshopProviderDescriptor());

        AZ_Error(
            "TaintedGrailMerlinWorkshop",
            result.m_success,
            "Merlin Workshop provider registration failed: %s",
            result.m_message.c_str());
        if (result.m_success)
        {
            AZ_Printf(
                "TaintedGrailMerlinWorkshop",
                "Registered optional provider %s; discovery remains disabled by default.\n",
                ProviderId);
        }
    }

    void EditorSystemComponent::Deactivate()
    {
    }
} // namespace TaintedGrailMerlinWorkshop
