/*
 * Copyright (c) Contributors to the Open 3D Engine Project.
 * For complete copyright and license terms please see the LICENSE at the root of this distribution.
 *
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 */

#pragma once

#include "AdapterRuntimeResultEvidenceService.h"
#include "AdapterWorkOrderPlanningService.h"
#include "FoundationNotificationBus.h"

#include <QWidget>

class QLabel;
class QTableWidget;

namespace TaintedGrailModdingSDK
{
    class AdapterRuntimeResultEvidenceWidget final
        : public QWidget
        , private FoundationNotificationBus::Handler
    {
    public:
        explicit AdapterRuntimeResultEvidenceWidget(QWidget* parent = nullptr);
        ~AdapterRuntimeResultEvidenceWidget() override;

    private:
        void OnFoundationChanged() override;
        void Refresh();

        AdapterWorkOrderPlanningService m_planningService;
        AdapterRuntimeResultEvidenceService m_resultService;
        QLabel* m_summary = nullptr;
        QTableWidget* m_table = nullptr;
    };
} // namespace TaintedGrailModdingSDK
