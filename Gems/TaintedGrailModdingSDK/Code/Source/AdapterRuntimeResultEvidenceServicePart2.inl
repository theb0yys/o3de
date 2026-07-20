/*
 * Copyright (c) Contributors to the Open 3D Engine Project.
 * For complete copyright and license terms please see the LICENSE at the root of this distribution.
 *
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 */

        SourceDocument BuildSourceDocument(
            const AZStd::string& sourceId,
            const AZStd::string& title,
            const AZStd::string& sourceKind,
            const AZStd::string& locator,
            const AZStd::string& fingerprint,
            const AdapterRuntimeResultEnvelope& envelope,
            const AZStd::string& mediaType,
            const AZStd::string& limitations)
        {
            SourceDocument document;
            document.m_source.m_sourceId = sourceId;
            document.m_source.m_title = title;
            document.m_source.m_sourceKind = sourceKind;
            document.m_source.m_locator = locator;
            document.m_source.m_fingerprint = fingerprint;
            document.m_source.m_profileId = envelope.m_profileId;
            document.m_source.m_gameVersion = envelope.m_gameVersion;
            document.m_source.m_branch = envelope.m_branch;
            document.m_source.m_runtimeTarget = envelope.m_runtimeTarget;
            document.m_source.m_toolName = envelope.m_adapterId;
            document.m_source.m_toolVersion = envelope.m_adapterVersion;
            document.m_source.m_importerId = "tg.adapter-runtime-result";
            document.m_source.m_importerVersion = "1";
            document.m_source.m_capturedAt = envelope.m_capturedAt;
            document.m_source.m_importedAt = envelope.m_capturedAt;
            document.m_source.m_limitations = limitations;
            document.m_source.m_mediaType = mediaType;
            document.m_source.m_importStatus = "contract_validated";
            return document;
        }

        EvidenceRecord BuildEvidence(
            const AZStd::string& evidenceId,
            const SourceRecord& source,
            const AdapterRuntimeResultEnvelope& envelope,
            const AZStd::string& subjectRef,
            const AZStd::string& claim,
            const AZStd::string& evidenceKind,
            const AZStd::string& locator,
            const AZStd::string& recordPath)
        {
            EvidenceRecord evidence;
            evidence.m_evidenceId = evidenceId;
            evidence.m_sourceId = source.m_sourceId;
            evidence.m_sourceFingerprint = source.m_fingerprint;
            evidence.m_profileId = envelope.m_profileId;
            evidence.m_gameVersion = envelope.m_gameVersion;
            evidence.m_branch = envelope.m_branch;
            evidence.m_subjectRef = subjectRef;
            evidence.m_claim = claim;
            evidence.m_evidenceKind = evidenceKind;
            evidence.m_confidence = "unrated";
            evidence.m_locator = locator;
            evidence.m_recordPath = recordPath;
            evidence.m_extractedAt = envelope.m_capturedAt;
            return evidence;
        }

        AZStd::string ResultSubject(const AdapterRuntimeResultEnvelope& envelope)
        {
            return "runtime-result:" + envelope.m_resultId;
        }

        AZStd::string StepClaim(const AdapterRuntimeStepResult& step)
        {
            return "Adapter runtime result reported " + ToString(step.m_outcome)
                + " for plan step " + step.m_stepId
                + " (" + step.m_capability + ").";
        }

        const AdapterRuntimeStepResult* FindRuntimeStep(
            const AZStd::vector<const AdapterRuntimeStepResult*>& steps,
            const AZStd::string& stepId)
        {
            for (const AdapterRuntimeStepResult* step : steps)
            {
                if (step->m_stepId == stepId)
                {
                    return step;
                }
            }
            return nullptr;
        }

        void BuildPrimaryEvidence(
            const AdapterWorkOrderPlan& plan,
            const AdapterRuntimeResultEnvelope& envelope,
            AdapterRuntimeEvidenceReturn& result)
        {
            const AZStd::string sourceId = "source.adapter-runtime." + envelope.m_resultId;
            const AZStd::string locator = "runtime-results/" + envelope.m_resultId + ".json";
            SourceDocument sourceDocument = BuildSourceDocument(
                sourceId,
                "Adapter runtime result " + envelope.m_resultId,
                "adapter_runtime_result",
                locator,
                envelope.m_resultFingerprint,
                envelope,
                "application/vnd.taintedgrail.adapter-runtime-result+json",
                "Contract-validated result metadata only; validation and permission remain unchanged.");

            EvidenceDocument evidenceDocument;
            evidenceDocument.m_sourceId = sourceId;
            evidenceDocument.m_sourceFingerprint = envelope.m_resultFingerprint;
            evidenceDocument.m_profileId = envelope.m_profileId;
            evidenceDocument.m_gameVersion = envelope.m_gameVersion;
            evidenceDocument.m_branch = envelope.m_branch;

            AZStd::vector<const AdapterRuntimeStepResult*> steps;
            steps.reserve(envelope.m_stepResults.size());
            for (const AdapterRuntimeStepResult& step : envelope.m_stepResults)
            {
                steps.push_back(&step);
            }
            AZStd::sort(
                steps.begin(),
                steps.end(),
                [](const AdapterRuntimeStepResult* left, const AdapterRuntimeStepResult* right)
                {
                    if (left->m_sequence != right->m_sequence)
                    {
                        return left->m_sequence < right->m_sequence;
                    }
                    return left->m_stepId < right->m_stepId;
                });

            for (const AdapterRuntimeStepResult* step : steps)
            {
                const AZStd::string sequence = UnsignedString(step->m_sequence);
                evidenceDocument.m_evidence.push_back(BuildEvidence(
                    "evidence.adapter-runtime." + envelope.m_resultId + ".step." + sequence,
                    sourceDocument.m_source,
                    envelope,
                    step->m_subjectRef,
                    StepClaim(*step),
                    "adapter_runtime_step_result",
                    locator,
                    "StepResults/" + sequence));
            }

            AZStd::vector<const AdapterRuntimeFailure*> failures;
            failures.reserve(envelope.m_failures.size());
            for (const AdapterRuntimeFailure& failure : envelope.m_failures)
            {
                failures.push_back(&failure);
            }
            AZStd::sort(
                failures.begin(),
                failures.end(),
                [](const AdapterRuntimeFailure* left, const AdapterRuntimeFailure* right)
                {
                    return left->m_failureId < right->m_failureId;
                });
            for (const AdapterRuntimeFailure* failure : failures)
            {
                const AdapterRuntimeStepResult* step = FindRuntimeStep(steps, failure->m_stepId);
                const AZStd::string subjectRef = step
                    ? step->m_subjectRef
                    : ResultSubject(envelope);
                const AZStd::string claim = "Adapter runtime failure " + failure->m_failureId
                    + " reported kind " + ToString(failure->m_kind)
                    + ", code " + failure->m_code + ": " + failure->m_message;
                evidenceDocument.m_evidence.push_back(BuildEvidence(
                    "evidence.adapter-runtime." + envelope.m_resultId
                        + ".failure." + failure->m_failureId,
                    sourceDocument.m_source,
                    envelope,
                    subjectRef,
                    claim,
                    "adapter_runtime_failure",
                    locator,
                    "Failures/" + failure->m_failureId));
            }

            const AdapterRuntimeRecoveryResult recoveries[] = {
                envelope.m_cleanupResult,
                envelope.m_rollbackResult,
            };
            const char* recoveryNames[] = { "cleanup", "rollback" };
            for (size_t index = 0; index < 2; ++index)
            {
                const AdapterRuntimeRecoveryResult& recovery = recoveries[index];
                const AdapterRuntimeStepResult* step = FindRuntimeStep(steps, recovery.m_stepId);
                const AZStd::string subjectRef = step
                    ? step->m_subjectRef
                    : ResultSubject(envelope);
                evidenceDocument.m_evidence.push_back(BuildEvidence(
                    "evidence.adapter-runtime." + envelope.m_resultId
                        + ".recovery." + recoveryNames[index],
                    sourceDocument.m_source,
                    envelope,
                    subjectRef,
                    AZStd::string("Adapter runtime ") + recoveryNames[index]
                        + " result reported " + ToString(recovery.m_outcome)
                        + " for step " + recovery.m_stepId + ".",
                    AZStd::string("adapter_runtime_") + recoveryNames[index] + "_result",
                    locator,
                    AZStd::string("Recovery/") + recoveryNames[index]));
            }

            evidenceDocument.m_evidence.push_back(BuildEvidence(
                "evidence.adapter-runtime." + envelope.m_resultId + ".plan-binding",
                sourceDocument.m_source,
                envelope,
                ResultSubject(envelope),
                "Runtime result binds exactly to plan " + plan.m_planId
                    + " with declared plan fingerprint " + envelope.m_planFingerprint + ".",
                "adapter_runtime_plan_binding",
                locator,
                "PlanBinding"));

            result.m_sourceDocuments.push_back(AZStd::move(sourceDocument));
            result.m_evidenceDocuments.push_back(AZStd::move(evidenceDocument));
        }

