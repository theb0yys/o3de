/*
 * Copyright (c) Contributors to the Open 3D Engine Project.
 * For complete copyright and license terms please see the LICENSE at the root of this distribution.
 *
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 */

namespace
{
        const AdapterWorkOrderStep* FindStep(
            const AdapterWorkOrderPlan& plan,
            const AZStd::string& capability,
            const AZStd::string& subjectId)
        {
            for (const AdapterWorkOrderStep& step : plan.m_steps)
            {
                if (step.m_capability == capability
                    && step.m_subjectId == subjectId)
                {
                    return &step;
                }
            }
            return nullptr;
        }
} // namespace
