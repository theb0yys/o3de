#!/usr/bin/env python3
#
# Copyright (c) Contributors to the Open 3D Engine Project.
# For complete copyright and license terms please see the LICENSE at the root of this distribution.
#
# SPDX-License-Identifier: Apache-2.0 OR MIT
#
"""Record and actor-profile validation for the population fixture."""

from __future__ import annotations

from typing import Any

from population_preview_fixture_contract import (
    ACTOR_LEADER_ID,
    ACTOR_SCOUT_ID,
    BRANCH,
    EXPECTED_STATE,
    GAME_VERSION,
    PROFILE_ID,
    TEMPLATE_GUARD_ID,
    TROOP_PATROL_ID,
    UNRESOLVED_TEMPLATE_SUBJECT,
    WORKSPACE_ID,
    require,
    require_evidence_subjects,
    require_list,
    require_sorted_unique,
    require_stable_id,
    require_string,
    validate_record,
)


def validate_records_and_actors(
    catalog: dict[str, Any],
    evidence_by_id: dict[str, dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    require(catalog.get("SchemaVersion") == 2, "Population catalog requires schema 2")
    require(catalog.get("WorkspaceId") == WORKSPACE_ID, "Catalog workspace mismatch")
    require(catalog.get("ProfileId") == PROFILE_ID, "Catalog profile mismatch")
    require(catalog.get("GameVersion") == GAME_VERSION, "Catalog version mismatch")
    require(catalog.get("Branch") == BRANCH, "Catalog branch mismatch")
    for field in (
        "EconomyItems",
        "EconomyRecipes",
        "RecipeIngredients",
        "RecipeOutputs",
    ):
        require(catalog.get(field) == [], f"{field} must remain empty")

    record_values = require_list(catalog.get("Records"), "catalog.Records")
    record_ids = [record.get("RecordId") for record in record_values]
    require(record_ids == sorted(record_ids), "Population records must be sorted")
    records: dict[str, dict[str, Any]] = {}
    subjects: dict[str, str] = {}
    for record in record_values:
        require(isinstance(record, dict), "Catalog records must be objects")
        record_id, subject = validate_record(record, evidence_by_id)
        require(record_id not in records, f"Duplicate record identity: {record_id}")
        require(subject not in subjects, f"Duplicate exact subject: {subject}")
        records[record_id] = record
        subjects[subject] = record_id
    require(
        len(records) == EXPECTED_STATE["record_count"],
        "Unexpected population record count",
    )

    expected_kinds = {
        ACTOR_LEADER_ID: "actor",
        ACTOR_SCOUT_ID: "actor",
        TEMPLATE_GUARD_ID: "actor_template",
        TROOP_PATROL_ID: "troop",
    }
    require(
        {record_id: value.get("RecordKind") for record_id, value in records.items()}
        == expected_kinds,
        "Population fixture record-kind contract mismatch",
    )

    allowed_spawn = sorted(
        record_id
        for record_id, value in records.items()
        if "spawn_candidate" in value.get("AllowedUsages", [])
    )
    forbidden_spawn = sorted(
        record_id
        for record_id, value in records.items()
        if "spawn_candidate" in value.get("ForbiddenUsages", [])
    )
    require(
        allowed_spawn == EXPECTED_STATE["allowed_spawn_candidate_record_ids"],
        "Allowed spawn-candidate fixture state mismatch",
    )
    require(
        forbidden_spawn == EXPECTED_STATE["forbidden_spawn_candidate_record_ids"],
        "Forbidden spawn-candidate fixture state mismatch",
    )

    actor_values = require_list(
        catalog.get("ActorProfiles"),
        "catalog.ActorProfiles",
    )
    require(
        [value.get("RecordId") for value in actor_values]
        == sorted(value.get("RecordId") for value in actor_values),
        "Actor profiles must be sorted",
    )
    require(
        len(actor_values) == EXPECTED_STATE["actor_profile_count"],
        "Unexpected actor-profile count",
    )
    actor_profiles: dict[str, dict[str, Any]] = {}
    for profile in actor_values:
        require(isinstance(profile, dict), "Actor profiles must be objects")
        record_id = require_stable_id(profile.get("RecordId"), "ActorProfile.RecordId")
        require(
            record_id in records
            and records[record_id].get("RecordKind") == "actor",
            f"Actor profile has no canonical actor: {record_id}",
        )
        require(
            profile.get("ActorKind")
            in ("npc", "creature", "animal", "construct", "other"),
            f"Unsupported actor kind: {record_id}",
        )
        require_string(profile.get("Archetype"), f"{record_id}.Archetype")
        minimum = profile.get("MinimumLevel")
        maximum = profile.get("MaximumLevel")
        require(
            isinstance(minimum, int)
            and isinstance(maximum, int)
            and minimum > 0
            and minimum <= maximum <= 1000,
            f"Invalid actor level range: {record_id}",
        )
        template_record_id = profile.get("TemplateRecordId", "")
        template_subject = profile.get("TemplateSubjectRef", "")
        allowed_subjects = {records[record_id]["SubjectRef"]}
        if template_record_id:
            require(
                template_record_id in records
                and records[template_record_id].get("RecordKind")
                in ("actor_template", "template"),
                f"Invalid resolved actor template: {record_id}",
            )
            resolved_subject = records[template_record_id]["SubjectRef"]
            require(
                not template_subject or template_subject == resolved_subject,
                f"Resolved actor template subject mismatch: {record_id}",
            )
            allowed_subjects.add(resolved_subject)
        if template_subject:
            require(
                template_subject.startswith("subject:preview:population:"),
                f"Actor template subject outside preview namespace: {record_id}",
            )
            allowed_subjects.add(template_subject)
        require_evidence_subjects(
            profile.get("EvidenceIds"),
            evidence_by_id,
            allowed_subjects,
            f"actor profile {record_id}",
        )
        require_sorted_unique(profile.get("Tags"), f"{record_id}.Tags")
        require(record_id not in actor_profiles, f"Duplicate actor profile: {record_id}")
        actor_profiles[record_id] = profile

    unresolved_templates = sorted(
        profile.get("TemplateSubjectRef")
        for profile in actor_profiles.values()
        if profile.get("TemplateSubjectRef")
        and not profile.get("TemplateRecordId")
    )
    require(
        unresolved_templates == EXPECTED_STATE["unresolved_template_subjects"],
        "Unresolved template fixture state mismatch",
    )

    return records, actor_profiles
