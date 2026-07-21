/*
 * Copyright (c) Contributors to the Open 3D Engine Project.
 * For complete copyright and license terms please see the LICENSE at the root of this distribution.
 *
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 */

#pragma once

#include <TaintedGrailMerlinWorkshop/TaintedGrailMerlinWorkshopTypeIds.h>

#include <AzCore/Component/Component.h>

namespace TaintedGrailMerlinWorkshop
{
    class EditorSystemComponent final
        : public AZ::Component
    {
    public:
        AZ_COMPONENT(EditorSystemComponent, EditorSystemComponentTypeId);

        static void Reflect(AZ::ReflectContext* context);
        static void GetProvidedServices(
            AZ::ComponentDescriptor::DependencyArrayType& provided);
        static void GetIncompatibleServices(
            AZ::ComponentDescriptor::DependencyArrayType& incompatible);
        static void GetRequiredServices(
            AZ::ComponentDescriptor::DependencyArrayType& required);

        void Activate() override;
        void Deactivate() override;
    };
} // namespace TaintedGrailMerlinWorkshop
