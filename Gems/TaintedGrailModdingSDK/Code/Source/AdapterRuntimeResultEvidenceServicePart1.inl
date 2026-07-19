        void AddIssue(
            AdapterRuntimeEvidenceReturn& result,
            const AZStd::string& code,
            const AZStd::string& message,
            const AZStd::string& stepId = {})
        {
            AdapterRuntimeResultIssue issue;
            issue.m_code = code;
            issue.m_message = message;
            issue.m_stepId = stepId;
            result.m_issues.push_back(AZStd::move(issue));
        }

        AZStd::string UnsignedString(AZ::u64 value)
        {
            char buffer[32];
            size_t position = sizeof(buffer);
            do
            {
                buffer[--position] = static_cast<char>('0' + (value % 10));
                value /= 10;
            } while (value != 0);
            return AZStd::string(buffer + position, sizeof(buffer) - position);
        }

        void SortUnique(AZStd::vector<AZStd::string>& values)
        {
            AZStd::sort(values.begin(), values.end());
            values.erase(AZStd::unique(values.begin(), values.end()), values.end());
        }

        bool EqualStringSets(
            const AZStd::vector<AZStd::string>& left,
            const AZStd::vector<AZStd::string>& right)
        {
            AZStd::vector<AZStd::string> leftSorted = left;
            AZStd::vector<AZStd::string> rightSorted = right;
            SortUnique(leftSorted);
            SortUnique(rightSorted);
            return leftSorted == rightSorted;
        }

        const AdapterWorkOrderStep* FindPlanStep(
            const AdapterWorkOrderPlan& plan,
            const AZStd::string& stepId)
        {
            for (const AdapterWorkOrderStep& step : plan.m_steps)
            {
                if (step.m_stepId == stepId)
                {
                    return &step;
                }
            }
            return nullptr;
        }

        const AdapterWorkOrderStep* FindPlanCapabilityStep(
            const AdapterWorkOrderPlan& plan,
            const AZStd::string& capability)
        {
            const AdapterWorkOrderStep* match = nullptr;
            for (const AdapterWorkOrderStep& step : plan.m_steps)
            {
                if (step.m_capability == capability)
                {
                    if (match)
                    {
                        return nullptr;
                    }
                    match = &step;
                }
            }
            return match;
        }

        const AdapterRuntimeStepResult* FindStepResult(
            const AdapterRuntimeResultEnvelope& envelope,
            const AZStd::string& stepId)
        {
            for (const AdapterRuntimeStepResult& step : envelope.m_stepResults)
            {
                if (step.m_stepId == stepId)
                {
                    return &step;
                }
            }
            return nullptr;
        }

        const AdapterRuntimeFailure* FindFailure(
            const AdapterRuntimeResultEnvelope& envelope,
            const AZStd::string& failureId)
        {
            for (const AdapterRuntimeFailure& failure : envelope.m_failures)
            {
                if (failure.m_failureId == failureId)
                {
                    return &failure;
                }
            }
            return nullptr;
        }

        const AdapterRuntimeLogReference* FindLog(
            const AdapterRuntimeResultEnvelope& envelope,
            const AZStd::string& logId)
        {
            for (const AdapterRuntimeLogReference& log : envelope.m_logReferences)
            {
                if (log.m_logId == logId)
                {
                    return &log;
                }
            }
            return nullptr;
        }

        bool RecoveryMatchesStep(
            const AdapterRuntimeRecoveryResult& recovery,
            const AdapterRuntimeStepResult& step)
        {
            return recovery.m_stepId == step.m_stepId
                && recovery.m_outcome == step.m_outcome
                && EqualStringSets(recovery.m_failureIds, step.m_failureIds)
                && EqualStringSets(recovery.m_logReferenceIds, step.m_logReferenceIds)
                && recovery.m_outputFingerprint == step.m_outputFingerprint;
        }

        void ValidatePlanBinding(
            const AdapterWorkOrderPlan& plan,
            const AdapterRuntimeResultEnvelope& envelope,
            AdapterRuntimeEvidenceReturn& result)
        {
            if (plan.m_executionAllowed)
            {
                AddIssue(
                    result,
                    "runtime_result.plan_execution_flag",
                    "Runtime results cannot bind to a plan that allows execution.");
            }
            for (const AdapterWorkOrderStep& step : plan.m_steps)
            {
                if (step.m_executionAllowed)
                {
                    AddIssue(
                        result,
                        "runtime_result.step_execution_flag",
                        "Runtime results cannot bind to a step that allows execution.",
                        step.m_stepId);
                }
            }
            if (envelope.m_planId != plan.m_planId)
            {
                AddIssue(
                    result,
                    "runtime_result.plan_id_mismatch",
                    "The result envelope is bound to a different plan identity.");
            }
            if (envelope.m_planCanonicalJson != plan.m_canonicalJson)
            {
                AddIssue(
                    result,
                    "runtime_result.plan_canonical_mismatch",
                    "The result envelope does not contain the exact canonical plan JSON.");
            }
            if (envelope.m_packId != plan.m_packId
                || envelope.m_packVersion != plan.m_packVersion)
            {
                AddIssue(
                    result,
                    "runtime_result.pack_binding_mismatch",
                    "The result envelope pack identity or version does not match the plan.");
            }
            if (envelope.m_adapterId != plan.m_adapterId
                || envelope.m_adapterVersion != plan.m_adapterVersion)
            {
                AddIssue(
                    result,
                    "runtime_result.adapter_binding_mismatch",
                    "The result envelope adapter identity or version does not match the plan.");
            }
            if (envelope.m_profileId != plan.m_profileId
                || envelope.m_gameVersion != plan.m_gameVersion
                || envelope.m_branch != plan.m_branch
                || envelope.m_runtimeTarget != plan.m_runtimeTarget)
            {
                AddIssue(
                    result,
                    "runtime_result.profile_binding_mismatch",
                    "The result envelope profile, game version, branch, or runtime target does not match the plan.");
            }
        }

        void ValidateStepBindings(
            const AdapterWorkOrderPlan& plan,
            const AdapterRuntimeResultEnvelope& envelope,
            AdapterRuntimeEvidenceReturn& result)
        {
            if (envelope.m_stepResults.size() != plan.m_steps.size())
            {
                AddIssue(
                    result,
                    "runtime_result.step_count_mismatch",
                    "The envelope must contain exactly one result for every canonical plan step.");
            }

            for (const AdapterWorkOrderStep& planStep : plan.m_steps)
            {
                const AdapterRuntimeStepResult* runtimeStep = FindStepResult(
                    envelope,
                    planStep.m_stepId);
                if (!runtimeStep)
                {
                    AddIssue(
                        result,
                        "runtime_result.step_missing",
                        "The envelope is missing a canonical plan step result.",
                        planStep.m_stepId);
                    continue;
                }
                if (runtimeStep->m_sequence != planStep.m_sequence
                    || runtimeStep->m_capability != planStep.m_capability
                    || runtimeStep->m_subjectKind != planStep.m_subjectKind
                    || runtimeStep->m_subjectId != planStep.m_subjectId
                    || runtimeStep->m_subjectRef != planStep.m_subjectRef)
                {
                    AddIssue(
                        result,
                        "runtime_result.step_binding_mismatch",
                        "The attempted step identity, sequence, capability, or subject does not match the plan.",
                        planStep.m_stepId);
                }
            }
            for (const AdapterRuntimeStepResult& runtimeStep : envelope.m_stepResults)
            {
                if (!FindPlanStep(plan, runtimeStep.m_stepId))
                {
                    AddIssue(
                        result,
                        "runtime_result.step_unknown",
                        "The envelope contains a step identity that is not present in the canonical plan.",
                        runtimeStep.m_stepId);
                }
            }
        }

        void ValidateRecoveryBindings(
            const AdapterWorkOrderPlan& plan,
            const AdapterRuntimeResultEnvelope& envelope,
            AdapterRuntimeEvidenceReturn& result)
        {
            const AdapterWorkOrderStep* cleanupPlanStep = FindPlanCapabilityStep(plan, "cleanup");
            const AdapterWorkOrderStep* rollbackPlanStep = FindPlanCapabilityStep(plan, "rollback");
            if (!cleanupPlanStep || !rollbackPlanStep)
            {
                AddIssue(
                    result,
                    "runtime_result.recovery_plan_missing",
                    "The canonical plan must contain exactly one cleanup step and one rollback step.");
                return;
            }

            const AdapterRuntimeStepResult* cleanupStep = FindStepResult(
                envelope,
                cleanupPlanStep->m_stepId);
            const AdapterRuntimeStepResult* rollbackStep = FindStepResult(
                envelope,
                rollbackPlanStep->m_stepId);
            if (!cleanupStep
                || !RecoveryMatchesStep(envelope.m_cleanupResult, *cleanupStep))
            {
                AddIssue(
                    result,
                    "runtime_result.cleanup_mismatch",
                    "The explicit cleanup result must exactly match the cleanup step result.",
                    cleanupPlanStep->m_stepId);
            }
            if (!rollbackStep
                || !RecoveryMatchesStep(envelope.m_rollbackResult, *rollbackStep))
            {
                AddIssue(
                    result,
                    "runtime_result.rollback_mismatch",
                    "The explicit rollback result must exactly match the rollback step result.",
                    rollbackPlanStep->m_stepId);
            }
        }

        void ValidateFailureAndLogBindings(
            const AdapterWorkOrderPlan& plan,
            const AdapterRuntimeResultEnvelope& envelope,
            AdapterRuntimeEvidenceReturn& result)
        {
            for (const AdapterRuntimeStepResult& step : envelope.m_stepResults)
            {
                for (const AZStd::string& failureId : step.m_failureIds)
                {
                    const AdapterRuntimeFailure* failure = FindFailure(envelope, failureId);
                    if (!failure || (!failure->m_stepId.empty() && failure->m_stepId != step.m_stepId))
                    {
                        AddIssue(
                            result,
                            "runtime_result.failure_binding_mismatch",
                            "A step failure does not resolve to the same attempted step identity.",
                            step.m_stepId);
                    }
                }
                for (const AZStd::string& logId : step.m_logReferenceIds)
                {
                    const AdapterRuntimeLogReference* log = FindLog(envelope, logId);
                    if (!log
                        || (!log->m_stepIds.empty()
                            && AZStd::find(
                                log->m_stepIds.begin(),
                                log->m_stepIds.end(),
                                step.m_stepId) == log->m_stepIds.end()))
                    {
                        AddIssue(
                            result,
                            "runtime_result.log_binding_mismatch",
                            "A step log reference does not resolve back to the same attempted step identity.",
                            step.m_stepId);
                    }
                }
            }
            for (const AdapterRuntimeFailure& failure : envelope.m_failures)
            {
                if (!failure.m_stepId.empty() && !FindPlanStep(plan, failure.m_stepId))
                {
                    AddIssue(
                        result,
                        "runtime_result.failure_step_unknown",
                        "A failure references a step outside the canonical plan.",
                        failure.m_stepId);
                }
            }
        }

