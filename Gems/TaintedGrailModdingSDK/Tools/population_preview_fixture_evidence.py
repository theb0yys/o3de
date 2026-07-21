#!/usr/bin/env python3
#
# Copyright (c) Contributors to the Open 3D Engine Project.
# For complete copyright and license terms please see the LICENSE at the root of this distribution.
#
# SPDX-License-Identifier: Apache-2.0 OR MIT
#
"""Source, evidence, and canonical-record checks for the population fixture."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from population_preview_fixture_common import (
    BRANCH,
    EXPECTED_STATE,
    GAME_VERSION,
    PACK_ID,
    PROFILE_ID,
    RUNTIME_TARGET,
    SOURCE_ID,
    SOURCE_INPUT_PATH,
    STABLE_ID_PATTERN,
    is_reserved_population_subject,
    require,
    require_list,
    require_sorted_unique,
    require_stable_id,
    require_string,
    sha256_bytes,
)

def validate_source_and_evidence(
    root: Path,
    source_document: dict[str, Any],
    evidence_document: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    require(source_document.get("SchemaVersion") == 1, "Unsupported source schema")
    require(
        evidence_document.get("SchemaVersion") == 1,
        "Unsupported evidence schema",
    )
    source = source_document.get("Source")
    require(isinstance(source, dict), "Source document requires a Source object")
    source_input = (root / SOURCE_INPUT_PATH).read_bytes()
    expected_fingerprint = f"sha256:{sha256_bytes(source_input)}"
    require(
        source.get("Fingerprint") == expected_fingerprint,
        "Source fingerprint does not match source input",
    )
    require(
        source.get("ByteSize") == len(source_input),
        "Source byte size does not match source input",
    )
    require(source.get("SourceId") == SOURCE_ID, "Source identity mismatch")
    require(source.get("ProfileId") == PROFILE_ID, "Source profile mismatch")
    require(source.get("GameVersion") == GAME_VERSION, "Source version mismatch")
    require(source.get("Branch") == BRANCH, "Source branch mismatch")
    require(
        source.get("RuntimeTarget") == RUNTIME_TARGET,
        "Source runtime target mismatch",
    )
    require(source.get("ImportStatus") == "imported", "Source must be imported")
    require(
        evidence_document.get("SourceId") == SOURCE_ID,
        "Evidence source identity mismatch",
    )
    require(
        evidence_document.get("SourceFingerprint") == expected_fingerprint,
        "Evidence source fingerprint mismatch",
    )

    evidence_by_id: dict[str, dict[str, Any]] = {}
    evidence_records = require_list(
        evidence_document.get("Evidence"),
        "evidence.Evidence",
    )
    for record in evidence_records:
        require(isinstance(record, dict), "Evidence entries must be objects")
        evidence_id = require_stable_id(record.get("EvidenceId"), "EvidenceId")
        require(
            evidence_id.startswith("preview.population.evidence."),
            f"Evidence outside population preview namespace: {evidence_id}",
        )
        require(
            evidence_id not in evidence_by_id,
            f"Duplicate evidence identity: {evidence_id}",
        )
        require(record.get("SourceId") == SOURCE_ID, "Evidence source mismatch")
        require(
            record.get("SourceFingerprint") == expected_fingerprint,
            f"Evidence fingerprint mismatch: {evidence_id}",
        )
        require(record.get("ProfileId") == PROFILE_ID, "Evidence profile mismatch")
        require(
            record.get("GameVersion") == GAME_VERSION,
            "Evidence version mismatch",
        )
        require(record.get("Branch") == BRANCH, "Evidence branch mismatch")
        subject = require_string(
            record.get("SubjectRef"),
            f"{evidence_id}.SubjectRef",
        )
        require(
            is_reserved_population_subject(subject),
            f"Evidence subject outside population preview namespace: {subject}",
        )
        require(
            require_string(record.get("Claim"), f"{evidence_id}.Claim"),
            f"{evidence_id} requires a claim",
        )
        evidence_by_id[evidence_id] = record
    require(
        len(evidence_by_id) == EXPECTED_STATE["evidence_count"],
        "Unexpected population evidence count",
    )
    return evidence_by_id


def require_evidence_subjects(
    evidence_ids: Any,
    evidence_by_id: dict[str, dict[str, Any]],
    allowed_subjects: set[str],
    label: str,
) -> list[str]:
    values = require_sorted_unique(evidence_ids, f"{label}.EvidenceIds")
    require(bool(values), f"{label} requires evidence")
    for evidence_id in values:
        require(
            evidence_id in evidence_by_id,
            f"{label} references unknown evidence: {evidence_id}",
        )
        require(
            evidence_by_id[evidence_id].get("SubjectRef") in allowed_subjects,
            f"{label} evidence is bound to the wrong exact subject: {evidence_id}",
        )
    return values


def validate_record(
    record: dict[str, Any],
    evidence_by_id: dict[str, dict[str, Any]],
) -> tuple[str, str]:
    record_id = require_stable_id(record.get("RecordId"), "RecordId")
    require(
        record_id.startswith("preview.population."),
        f"Record outside population preview namespace: {record_id}",
    )
    require(record.get("Domain") == "population", f"Wrong domain: {record_id}")
    require(
        record.get("RecordKind")
        in ("actor", "actor_template", "troop"),
        f"Unsupported population record kind: {record_id}",
    )
    require(
        record.get("IdentityKind") == "synthetic",
        f"Population record must be synthetic: {record_id}",
    )
    require(
        record.get("OwnerPackId") == PACK_ID,
        f"Population record has wrong owner: {record_id}",
    )
    require(
        record.get("NativeRefExact") == "",
        f"Synthetic population record claims native identity: {record_id}",
    )
    subject = require_string(
        record.get("SubjectRef"),
        f"{record_id}.SubjectRef",
    )
    require(
        subject.startswith("subject:preview:population:"),
        f"Population subject is outside preview namespace: {record_id}",
    )
    require_evidence_subjects(
        record.get("EvidenceIds"),
        evidence_by_id,
        {subject},
        f"record {record_id}",
    )
    allowed = require_sorted_unique(
        record.get("AllowedUsages"),
        f"{record_id}.AllowedUsages",
    )
    forbidden = require_sorted_unique(
        record.get("ForbiddenUsages"),
        f"{record_id}.ForbiddenUsages",
    )
    require(
        not set(allowed).intersection(forbidden),
        f"Record has conflicting permission state: {record_id}",
    )
    require(
        record.get("ValidationState") == "validated",
        f"Record must be validated: {record_id}",
    )
    require(
        record.get("StalenessState") == "current",
        f"Record must be current: {record_id}",
    )
    return record_id, subject


