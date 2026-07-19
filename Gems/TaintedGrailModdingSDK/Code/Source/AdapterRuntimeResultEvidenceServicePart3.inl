        void BuildLogEvidence(
            const AdapterRuntimeResultEnvelope& envelope,
            AdapterRuntimeEvidenceReturn& result)
        {
            AZStd::vector<const AdapterRuntimeLogReference*> logs;
            logs.reserve(envelope.m_logReferences.size());
            for (const AdapterRuntimeLogReference& log : envelope.m_logReferences)
            {
                logs.push_back(&log);
            }
            AZStd::sort(
                logs.begin(),
                logs.end(),
                [](const AdapterRuntimeLogReference* left, const AdapterRuntimeLogReference* right)
                {
                    return left->m_logId < right->m_logId;
                });

            for (const AdapterRuntimeLogReference* log : logs)
            {
                const AZStd::string sourceId = "source.adapter-runtime-log."
                    + envelope.m_resultId + "." + log->m_logId;
                SourceDocument sourceDocument = BuildSourceDocument(
                    sourceId,
                    "Adapter runtime log " + log->m_logId,
                    "adapter_runtime_log",
                    log->m_reference,
                    log->m_fingerprint,
                    envelope,
                    "text/plain",
                    "Referenced log content is not opened, persisted, or inspected by Slice 10.");

                EvidenceDocument evidenceDocument;
                evidenceDocument.m_sourceId = sourceId;
                evidenceDocument.m_sourceFingerprint = log->m_fingerprint;
                evidenceDocument.m_profileId = envelope.m_profileId;
                evidenceDocument.m_gameVersion = envelope.m_gameVersion;
                evidenceDocument.m_branch = envelope.m_branch;

                AZStd::vector<AZStd::string> stepIds = log->m_stepIds;
                SortUnique(stepIds);
                if (stepIds.empty())
                {
                    evidenceDocument.m_evidence.push_back(BuildEvidence(
                        "evidence.adapter-runtime-log." + envelope.m_resultId
                            + "." + log->m_logId + ".result",
                        sourceDocument.m_source,
                        envelope,
                        ResultSubject(envelope),
                        "Runtime " + ToString(log->m_kind) + " log " + log->m_logId
                            + " is referenced with fingerprint " + log->m_fingerprint + ".",
                        "adapter_runtime_log_reference",
                        log->m_reference,
                        "LogReferences/" + log->m_logId));
                }
                else
                {
                    for (size_t index = 0; index < stepIds.size(); ++index)
                    {
                        const AdapterRuntimeStepResult* step = FindStepResult(
                            envelope,
                            stepIds[index]);
                        const AZStd::string subjectRef = step
                            ? step->m_subjectRef
                            : ResultSubject(envelope);
                        evidenceDocument.m_evidence.push_back(BuildEvidence(
                            "evidence.adapter-runtime-log." + envelope.m_resultId
                                + "." + log->m_logId + "." + UnsignedString(index + 1),
                            sourceDocument.m_source,
                            envelope,
                            subjectRef,
                            "Runtime " + ToString(log->m_kind) + " log " + log->m_logId
                                + " references plan step " + stepIds[index]
                                + " with fingerprint " + log->m_fingerprint + ".",
                            "adapter_runtime_log_reference",
                            log->m_reference,
                            "LogReferences/" + log->m_logId + "/" + UnsignedString(index + 1)));
                    }
                }
                result.m_sourceDocuments.push_back(AZStd::move(sourceDocument));
                result.m_evidenceDocuments.push_back(AZStd::move(evidenceDocument));
            }
        }

        void FinalizeCounts(AdapterRuntimeEvidenceReturn& result)
        {
            result.m_sourceDocumentCount = static_cast<AZ::u64>(result.m_sourceDocuments.size());
            result.m_evidenceRecordCount = 0;
            for (const EvidenceDocument& document : result.m_evidenceDocuments)
            {
                result.m_evidenceRecordCount += static_cast<AZ::u64>(document.m_evidence.size());
            }
        }
