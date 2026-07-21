#!/usr/bin/env python3
#
# Copyright (c) Contributors to the Open 3D Engine Project.
# For complete copyright and license terms please see the LICENSE at the root of this distribution.
#
# SPDX-License-Identifier: Apache-2.0 OR MIT
#
"""Relationship, validation, and governance checks for the population fixture."""

from __future__ import annotations

from typing import Any

from population_preview_fixture_contract import (
    EXPECTED_STATE,
    RELATIONSHIP_LEADER_TEMPLATE_ID,
    require,
    require_evidence_subjects,
    require_list,
    require_stable_id,
)


def validate_relationships_and_history(
    catalog: dict[str, Any],
    evidence_by_id: dict[str, dict[str, Any]],
    records: dict[str, dict[str, Any]],
) -> None:
    relationship_values = require_list(
        catalog.get("Relationships"),
        "catalog.Relationships",
    )
    require(
        len(relationship_values) == EXPECTED_STATE["relationship_count"],
        "Unexpected population relationship count",
    )
    relationship_ids: set[str] = set()
    for relationship in relationship_values:
        require(isinstance(relationship, dict), "Relationships must be objects")
        relationship_id = require_stable_id(
            relationship.get("RelationshipId"),
            "RelationshipId",
        )
        require(
            relationship_id.startswith("preview.population.relationship."),
            "Relationship outside population preview namespace",
        )
        require(
            relationship_id not in relationship_ids,
            f"Duplicate relationship: {relationship_id}",
        )
        relationship_ids.add(relationship_id)
        require(
            relationship.get("FromRecordId") in records,
            f"Unknown relationship source: {relationship_id}",
        )
        require(
            relationship.get("ToRecordId") in records,
            f"Unknown relationship target: {relationship_id}",
        )
        require(
            relationship.get("TargetSubjectRef") == "",
            f"Population fixture relationship must be resolved: {relationship_id}",
        )
        require_evidence_subjects(
            relationship.get("EvidenceIds"),
            evidence_by_id,
            {f"relationship:{relationship_id}"},
            f"relationship {relationship_id}",
        )

    validations = require_list(
        catalog.get("ValidationHistory"),
        "catalog.ValidationHistory",
    )
    validation_ids: set[str] = set()
    for validation in validations:
        require(isinstance(validation, dict), "Validation rows must be objects")
        validation_id = require_stable_id(
            validation.get("ValidationId"),
            "ValidationId",
        )
        require(
            validation_id not in validation_ids,
            f"Duplicate validation identity: {validation_id}",
        )
        validation_ids.add(validation_id)
        subject_kind = validation.get("SubjectKind")
        subject_id = validation.get("SubjectId")
        known = records if subject_kind == "record" else {
            RELATIONSHIP_LEADER_TEMPLATE_ID: relationship_values[0]
        }
        require(
            subject_kind in ("record", "relationship") and subject_id in known,
            f"Validation references unknown subject: {validation_id}",
        )
        evidence_subject = (
            records[subject_id]["SubjectRef"]
            if subject_kind == "record"
            else f"relationship:{subject_id}"
        )
        require_evidence_subjects(
            validation.get("EvidenceIds"),
            evidence_by_id,
            {evidence_subject},
            f"validation {validation_id}",
        )

    governance = require_list(
        catalog.get("GovernanceHistory"),
        "catalog.GovernanceHistory",
    )
    effective: dict[str, str] = {}
    for event in governance:
        require(isinstance(event, dict), "Governance rows must be objects")
        require(event.get("SubjectKind") == "record", "Governance subject must be record")
        subject_id = event.get("SubjectId")
        require(subject_id in records, "Governance references unknown record")
        require(event.get("Axis") == "permission", "Governance axis mismatch")
        require(event.get("Usage") == "spawn_candidate", "Governance usage mismatch")
        require(
            event.get("NewValue") in ("allow", "forbid"),
            "Governance value mismatch",
        )
        require(
            event.get("Reviewer") == "preview.population.maintainer",
            "Governance reviewer mismatch",
        )
        for validation_id in require_list(
            event.get("ValidationIds"),
            "Governance.ValidationIds",
        ):
            require(
                validation_id in validation_ids,
                f"Governance references unknown validation: {validation_id}",
            )
        require_evidence_subjects(
            event.get("EvidenceIds"),
            evidence_by_id,
            {records[subject_id]["SubjectRef"]},
            f"governance {event.get('EventId')}",
        )
        effective[subject_id] = event["NewValue"]

    require(
        sorted(
            subject_id
            for subject_id, value in effective.items()
            if value == "allow"
        )
        == EXPECTED_STATE["allowed_spawn_candidate_record_ids"],
        "Governance allow state mismatch",
    )
    require(
        sorted(
            subject_id
            for subject_id, value in effective.items()
            if value == "forbid"
        )
        == EXPECTED_STATE["forbidden_spawn_candidate_record_ids"],
        "Governance forbid state mismatch",
    )
