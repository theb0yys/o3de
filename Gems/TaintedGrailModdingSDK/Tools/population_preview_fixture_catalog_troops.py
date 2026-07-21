#!/usr/bin/env python3
#
# Copyright (c) Contributors to the Open 3D Engine Project.
# For complete copyright and license terms please see the LICENSE at the root of this distribution.
#
# SPDX-License-Identifier: Apache-2.0 OR MIT
#
"""Troop-profile and membership validation for the population fixture."""

from __future__ import annotations

import math
from typing import Any

from population_preview_fixture_contract import (
    EXPECTED_STATE,
    require,
    require_evidence_subjects,
    require_list,
    require_sorted_unique,
    require_stable_id,
)


def validate_troops_and_members(
    catalog: dict[str, Any],
    evidence_by_id: dict[str, dict[str, Any]],
    records: dict[str, dict[str, Any]],
    actor_profiles: dict[str, dict[str, Any]],
) -> tuple[
    dict[str, dict[str, Any]],
    dict[str, list[dict[str, Any]]],
]:
    troop_values = require_list(
        catalog.get("TroopProfiles"),
        "catalog.TroopProfiles",
    )
    require(
        [value.get("RecordId") for value in troop_values]
        == sorted(value.get("RecordId") for value in troop_values),
        "Troop profiles must be sorted",
    )
    require(
        len(troop_values) == EXPECTED_STATE["troop_profile_count"],
        "Unexpected troop-profile count",
    )
    troop_profiles: dict[str, dict[str, Any]] = {}
    for profile in troop_values:
        require(isinstance(profile, dict), "Troop profiles must be objects")
        record_id = require_stable_id(profile.get("RecordId"), "TroopProfile.RecordId")
        require(
            record_id in records
            and records[record_id].get("RecordKind") == "troop",
            f"Troop profile has no canonical troop: {record_id}",
        )
        require(
            profile.get("TroopKind")
            in ("party", "patrol", "encounter_group", "reinforcement", "other"),
            f"Unsupported troop kind: {record_id}",
        )
        minimum = profile.get("MinimumSize")
        maximum = profile.get("MaximumSize")
        require(
            isinstance(minimum, int)
            and isinstance(maximum, int)
            and minimum > 0
            and minimum <= maximum <= 1000,
            f"Invalid troop size range: {record_id}",
        )
        leader_id = require_stable_id(
            profile.get("LeaderActorRecordId"),
            f"{record_id}.LeaderActorRecordId",
        )
        require(
            leader_id in actor_profiles,
            f"Troop leader has no typed actor profile: {record_id}",
        )
        leader_subject = records[leader_id]["SubjectRef"]
        require(
            profile.get("LeaderActorSubjectRef") == leader_subject,
            f"Troop leader exact subject mismatch: {record_id}",
        )
        require_evidence_subjects(
            profile.get("EvidenceIds"),
            evidence_by_id,
            {records[record_id]["SubjectRef"], leader_subject},
            f"troop profile {record_id}",
        )
        require_sorted_unique(profile.get("Tags"), f"{record_id}.Tags")
        troop_profiles[record_id] = profile

    member_values = require_list(
        catalog.get("TroopMembers"),
        "catalog.TroopMembers",
    )
    require(
        [value.get("LinkId") for value in member_values]
        == sorted(value.get("LinkId") for value in member_values),
        "Troop members must be sorted",
    )
    require(
        len(member_values) == EXPECTED_STATE["troop_member_count"],
        "Unexpected troop-member count",
    )
    members_by_troop: dict[str, list[dict[str, Any]]] = {}
    member_ids: set[str] = set()
    actor_subjects_by_troop: dict[str, set[str]] = {}
    for member in member_values:
        require(isinstance(member, dict), "Troop members must be objects")
        link_id = require_stable_id(member.get("LinkId"), "TroopMember.LinkId")
        require(link_id not in member_ids, f"Duplicate troop member: {link_id}")
        member_ids.add(link_id)
        troop_id = require_stable_id(
            member.get("TroopRecordId"),
            f"{link_id}.TroopRecordId",
        )
        require(troop_id in troop_profiles, f"Member has no typed troop: {link_id}")
        actor_id = require_stable_id(
            member.get("ActorRecordId"),
            f"{link_id}.ActorRecordId",
        )
        require(actor_id in actor_profiles, f"Member actor is not typed: {link_id}")
        actor_subject = records[actor_id]["SubjectRef"]
        require(
            member.get("ActorSubjectRef") == actor_subject,
            f"Member exact actor subject mismatch: {link_id}",
        )
        troop_subject = records[troop_id]["SubjectRef"]
        require_evidence_subjects(
            member.get("EvidenceIds"),
            evidence_by_id,
            {
                f"population-troop-member:{link_id}",
                troop_subject,
                actor_subject,
            },
            f"troop member {link_id}",
        )
        require(
            member.get("Role")
            in ("leader", "melee", "ranged", "support", "specialist", "other"),
            f"Unsupported troop member role: {link_id}",
        )
        minimum = member.get("MinimumCount")
        maximum = member.get("MaximumCount")
        weight = member.get("Weight")
        require(
            isinstance(minimum, int)
            and isinstance(maximum, int)
            and minimum > 0
            and minimum <= maximum <= 1000,
            f"Invalid member count range: {link_id}",
        )
        require(
            isinstance(weight, (int, float))
            and math.isfinite(weight)
            and weight >= 0,
            f"Invalid member weight: {link_id}",
        )
        require_sorted_unique(member.get("Conditions"), f"{link_id}.Conditions")
        seen_subjects = actor_subjects_by_troop.setdefault(troop_id, set())
        require(
            actor_subject not in seen_subjects,
            f"Duplicate exact actor subject in troop: {actor_subject}",
        )
        seen_subjects.add(actor_subject)
        members_by_troop.setdefault(troop_id, []).append(member)

    for troop_id, profile in troop_profiles.items():
        members = members_by_troop.get(troop_id, [])
        require(members, f"Troop requires at least one typed member: {troop_id}")
        total_minimum = sum(member["MinimumCount"] for member in members)
        total_maximum = sum(member["MaximumCount"] for member in members)
        require(
            total_minimum <= profile["MaximumSize"]
            and total_maximum >= profile["MinimumSize"],
            f"Troop member ranges do not overlap profile size: {troop_id}",
        )
        leader_rows = [
            member for member in members if member.get("Role") == "leader"
        ]
        require(
            len(leader_rows) == 1,
            f"Troop requires exactly one typed leader row: {troop_id}",
        )
        require(
            leader_rows[0]["ActorRecordId"]
            == profile["LeaderActorRecordId"],
            f"Troop leader row does not match profile leader: {troop_id}",
        )

    return troop_profiles, members_by_troop
